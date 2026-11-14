import math
import struct

from .case_menu import ee_pointer
from ..pypine import Pine


class CharacterState:
    DEAD_STATE_VALUES: frozenset[int] = frozenset()

    def __init__(self, pine: Pine) -> None:
        self.pine = pine
        self.state_addr:  int | None = None
        self.health_addr: int | None = None

    def set_addrs(self, state_addr: int | None, health_addr: int | None) -> None:
        self.state_addr = state_addr
        self.health_addr = health_addr

    @property
    def movement_state(self) -> int:
        if self.state_addr is None:
            return 0
        return self.pine.read_int32(self.state_addr)

    @property
    def health(self) -> float:
        if self.health_addr is None:
            return 0.0
        return self.pine.read_float(self.health_addr)

    @health.setter
    def health(self, value: float) -> None:
        if self.health_addr is None:
            return
        self.pine.write_float(self.health_addr, value)

    @property
    def is_dead(self) -> bool:
        if self.state_addr is None or not self.DEAD_STATE_VALUES:
            return False
        return self.movement_state in self.DEAD_STATE_VALUES

    def __repr__(self) -> str:
        return f"CharacterState(state_addr={self.state_addr!r}, health_addr={self.health_addr!r})"


class ActivePlayer:
    """Resolve the current operative through the native hit-point accessors."""

    def __init__(self, pine):
        self.pine = pine
        self.pointer_address = None
        self.state_kind = None
        self.state_offset = None
        self.state_vtables = set()
        self.death_vtables = {}

    def bind_runtime(self, symbols, *, detect_deaths=True):
        self.pointer_address = None
        self.state_kind = self.state_offset = None
        self.state_vtables = set()
        self.death_vtables = {}
        getter = symbols.get("PLAYER_GetHitPoints__Fv")
        setter = symbols.get("PLAYER_SetHitPoints__FP6PLAYERf")
        if getter is None or setter is None:
            return
        hi, stack, low = struct.unpack("<3I", self.pine.read_bytes(getter, 12))
        if (hi & 0xFFFF0000 != 0x3C020000 or stack != 0x27BDFFE0
                or low & 0xFFFF0000 != 0x8C440000
                or self.pine.read_bytes(setter, 8) != struct.pack("<2I", 0x03E00008, 0xE48C0274)):
            raise RuntimeError("Native player health accessor changed")
        offset = low & 0xFFFF
        pointer = ((hi & 0xFFFF) << 16) + (offset - 0x10000 if offset & 0x8000 else offset)
        if not ee_pointer(pointer):
            raise RuntimeError("Invalid native player pointer address")
        self.pointer_address = pointer
        if detect_deaths:
            self._bind_death_states(symbols)

    def _bind_death_states(self, symbols):
        ratchet = symbols.get("RATCHET_IsDying__FPC7RATCHET")
        if ratchet is not None and self.pine.read_bytes(ratchet, 16) == struct.pack(
                '<4I', 0x94820AB4, 0x2442FFDE, 0x03E00008, 0x2C42000B):
            # The retail predicate reads a halfword and accepts 0x22..0x2C.
            self.state_kind, self.state_offset = "Ratchet", 0xAB4
            return
        clank = symbols.get("CLANK_IsDying__FP6PLAYER")
        if clank is None:
            return
        # Clank compares the active State pointer with five embedded states.
        words = struct.unpack('<16I', self.pine.read_bytes(clank, 64))
        if words[0] == 0x03E00008:  # Unused-operative stub in another module.
            return
        if (words[0] != 0x8C830AB8 or
                [words[i] for i in (1, 4, 6, 8, 10)] !=
                [0x24820C3C, 0x24820BA8, 0x24820C48, 0x24820C54, 0x24820D00]):
            raise RuntimeError("Native Clank death-state predicate changed")
        names = {
            '_vt$5Death': 'died',
            '_vt$11FallToDeath': 'fell to their death',
            '_vt$10ClankDrown': 'drowned',
            '_vt$11MissionFail': 'failed a mission',
            '_vt$15MissionFailFall': 'failed a mission by falling',
        }
        self.death_vtables = {symbols.get(name): cause for name, cause in names.items()}
        if None in self.death_vtables:
            raise RuntimeError("Native Clank death-state tables are missing")
        values = symbols if isinstance(symbols, dict) else symbols.values
        self.state_vtables = {address for name, address in values.items() if name.startswith('_vt$')}
        self.state_kind, self.state_offset = "Clank", 0xAB8

    def death_state_sample(self):
        """Return (player, death cause or None), without consulting health."""
        if self.pointer_address is None or self.state_offset is None:
            return None
        player = self.pine.read_int32(self.pointer_address)
        if not ee_pointer(player, self.state_offset + 4):
            return None
        if self.state_kind == "Ratchet":
            state = struct.unpack('<h', self.pine.read_bytes(player + self.state_offset, 2))[0]
            if not 0 <= state < 0x4D:
                return None
            # Ratchet's death states aren't mapped to causes yet, so report the raw state.
            cause = f'died (Ratchet state 0x{state:02X})' if 0x22 <= state <= 0x2C else None
            return player, cause
        state = self.pine.read_int32(player + self.state_offset)
        if not ee_pointer(state, 12):
            return None
        vtable = self.pine.read_int32(state + 8)
        if vtable not in self.state_vtables:
            return None
        return player, self.death_vtables.get(vtable)

    def _health(self):
        if self.pointer_address is None:
            return None
        player = self.pine.read_int32(self.pointer_address)
        if not ee_pointer(player, 0x27C):
            return None
        health, maximum = struct.unpack("<2f", self.pine.read_bytes(player + 0x274, 8))
        if not math.isfinite(health) or not math.isfinite(maximum) or maximum <= 0:
            return None
        return player, health, maximum

    def health_sample(self):
        sample = self._health()
        return None if sample is None else sample[:2]

    def kill(self):
        sample = self.health_sample()
        if sample is None or sample[1] <= 0:
            return False
        self.pine.write_int32(sample[0] + 0x274, 0)
        return True

    def damage(self, percent):
        """Take `percent` of max health, never going below 1. False if there's no player yet."""
        sample = self._health()
        if sample is None:
            return False
        player, health, maximum = sample
        if health > 1:
            self.pine.write_float(player + 0x274, max(1.0, health - maximum * percent / 100))
        return True

    def lower_health(self, value):
        """False if there's no player yet."""
        sample = self.health_sample()
        if sample is None:
            return False
        if sample[1] > value:
            self.pine.write_float(sample[0] + 0x274, value)
        return True

    def current_player(self):
        if self.pointer_address is None:
            return None
        player = self.pine.read_int32(self.pointer_address)
        return player if ee_pointer(player, 0x348) else None
