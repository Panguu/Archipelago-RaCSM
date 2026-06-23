from __future__ import annotations

from enum import IntEnum

from ..interface_orchestrator.memory.accessor import MemoryAccessor
from ..interface_orchestrator.state.base_state import BaseState
from ..interface_orchestrator.storage.local import LocalStorage
from ..interface_orchestrator.structs.address_map import AddressMap
from .address_maps import PLAYER_ADDRS
from .structs.game import PlayerMovementStruct

# ── Player movement state enum (data) ────────────────────────────────────────────

class PlayerMovementState(IntEnum):
    Alive           = 0x00
    FishDeath       = 0x29
    FadeDeath       = 0x2A
    Electrocution   = 0x2B
    VoidDeath       = 0x2C
    UnknownDeath    = 0x2D
    SwimDeath       = 0x2E
    MysteriousDeath = 0x2F
    Pickup          = 0x43

    @staticmethod
    def is_dead(state: int) -> bool:
        return PlayerMovementState.FishDeath <= state <= PlayerMovementState.MysteriousDeath



# ── Player state (runtime) ───────────────────────────────────────────────────────

class PlayerState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self.movement_state: PlayerMovementState = PlayerMovementState.Alive
        self.health: int = 0
        self._health_addr: int | None = None
        self._current_planet: int | None = None

    def on_exit(self) -> None:
        self.movement_state = PlayerMovementState.Alive
        self.health = 0

    def set_planet(self, planet_id: int) -> None:
        addrs = PLAYER_ADDRS.get(planet_id)
        self._health_addr = addrs[1] if addrs else None
        self._current_planet = planet_id

    def _register_handlers(self) -> None:
        struct_cls = self._movement_struct()
        if struct_cls is not None:
            self.accessor.on_struct_change(struct_cls, self._on_movement_change)

    def _unregister_handlers(self) -> None:
        struct_cls = self._movement_struct()
        if struct_cls is not None:
            self.accessor.remove_struct_handler(struct_cls, self._on_movement_change)

    def _movement_struct(self) -> type[PlayerMovementStruct] | None:
        for cls in self.addresses.structs():
            if issubclass(cls, PlayerMovementStruct) and cls is not PlayerMovementStruct:
                return cls
        return None

    def _on_movement_change(self, address: int, new_bytes: bytes) -> None:
        del address
        raw = new_bytes[0] if new_bytes else 0
        try:
            new_state = PlayerMovementState(raw)
        except ValueError:
            new_state = PlayerMovementState.Alive

        if self._health_addr is not None:
            self.health = int.from_bytes(
                self.accessor.read_raw(self._health_addr, 4), "little"
            )

        prev = self.movement_state
        self.movement_state = new_state
        self._on_transition(prev, new_state)

    def _on_transition(self, prev: PlayerMovementState, current: PlayerMovementState) -> None:
        was_dead   = PlayerMovementState.is_dead(int(prev))
        is_dead    = PlayerMovementState.is_dead(int(current))
        was_pickup = prev    == PlayerMovementState.Pickup
        is_pickup  = current == PlayerMovementState.Pickup

        if is_dead and not was_dead:
            self.on_death(current)
        elif not is_dead and was_dead:
            self.on_respawn()

        if is_pickup and not was_pickup:
            self.on_pickup_start()
        elif not is_pickup and was_pickup:
            self.on_pickup_end()

    def sync(self) -> None:
        struct_cls = self._movement_struct()
        if struct_cls is None:
            return
        raw = self.accessor.read_raw(struct_cls.BASE_ADDRESS, 1)
        try:
            self.movement_state = PlayerMovementState(raw[0])
        except ValueError:
            pass
        if self._health_addr is not None:
            self.health = int.from_bytes(
                self.accessor.read_raw(self._health_addr, 4), "little"
            )

    @property
    def is_dead(self) -> bool:
        return PlayerMovementState.is_dead(int(self.movement_state))

    @property
    def is_picking_up(self) -> bool:
        return self.movement_state == PlayerMovementState.Pickup

    def on_death(self, _cause: PlayerMovementState) -> None:
        del _cause

    def on_respawn(self) -> None:
        pass

    def on_pickup_start(self) -> None:
        pass

    def on_pickup_end(self) -> None:
        pass

    def __repr__(self) -> str:
        return f"PlayerState(movement={self.movement_state.name}, health={self.health})"
