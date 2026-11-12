import logging
from collections.abc import Callable

from ...constants import CASE_ID_TO_CASE, SACOperatives
from ..address_maps import CASE_ADDRESSES, CASE_IDLE_VALUE, CURRENT_CASE_ADDRESS, FORCE_CASE_ADDRESS
from ..case_menu import CaseMenu
from ..mission_failure import MissionFailure
from ..player import ActivePlayer, CharacterState
from ..patches import LoaderStateReader
from ..symbols import RuntimeSymbols
from ..vendor import VendorState
from .inventory import ItemInventory
from .weapons import WeaponInventory
from ...pypine import Pine


logger = logging.getLogger("CommonClient")


class CaseInventory:

    def __init__(self, pine: Pine) -> None:
        self.pine = pine

        self.ratchet = CharacterState(pine)
        self.clank   = CharacterState(pine)
        self.qwark   = CharacterState(pine)
        self.active_player = ActivePlayer(pine)
        self.mission_failure = MissionFailure(pine)
        self.ratchet_items = WeaponInventory(pine)
        self.clank_items   = ItemInventory(pine)
        self.vendor        = VendorState(pine)
        self.symbols = RuntimeSymbols(pine)
        self.case_menu = CaseMenu(pine)
        self.weapon_base: int | None = None

        self.case_id:     int | None = None
        self.planet_name: str | None = None
        self.is_ready:    bool = False
        self._prev_case_id: int | None = None

        self.on_transition_start: Callable[[], None] = lambda: None
        self.on_death:            Callable[[str], None] = lambda cause: None
        self.on_respawn:          Callable[[], None] = lambda: None

        self._prev_dead: bool = False
        self._death_armed = False
        self._awaiting_remote_death = False

    def set_case(self, case_id: int) -> None:
        self.case_id = case_id
        case = CASE_ID_TO_CASE.get(case_id)
        self.planet_name = case.planet if case else None

        addrs = CASE_ADDRESSES.get(case_id)
        self.ratchet.set_addrs(addrs.ratchet_state if addrs else None, addrs.ratchet_health if addrs else None)
        self.clank.set_addrs(addrs.clank_state if addrs else None, addrs.clank_health if addrs else None)
        self.qwark.set_addrs(addrs.qwark_state if addrs else None, addrs.qwark_health if addrs else None)
        self.weapon_base = self.symbols.get("GADGET_g_GadgetList")
        self.ratchet_items.set_base(self.weapon_base)
        self.clank_items.set_addrs(addrs.clank_gadget_addrs if addrs else None)
        self.vendor.bind_runtime(self.symbols)
        self.case_menu.bind_runtime(self.symbols)
        detect_deaths = case is not None and case.operative not in (SACOperatives.QWARK, SACOperatives.GADGETBOTS)
        self.active_player.bind_runtime(self.symbols, detect_deaths=detect_deaths)

        if case_id not in CASE_ID_TO_CASE:
            logger.warning(
                f"[SAC] Unknown case id 0x{case_id:X} -- no addresses bound, every accessor is a no-op."
            )

    def check_transition(self, *, allow_bind=True) -> bool:
        """Bind overlay addresses only after the loader and gameplay settle."""
        addresses = (CURRENT_CASE_ADDRESS, FORCE_CASE_ADDRESS, LoaderStateReader.STATE, 0x206338)
        state = self.pine.batch_read_int32(addresses)
        current, requested, loader, game = state
        changing = (not allow_bind or current != self._prev_case_id or requested != 0xFFFFFFFF
                    or loader != 5 or game != 3)
        if changing or (self.is_ready and not self._valid_weapon_table()):
            self.is_ready = False
            self.on_transition_start()
            self.ratchet_items.set_base(None)
            self.clank_items.set_addrs(None)
            self.vendor.set_addr(None)
            self.weapon_base = None
            self.symbols.clear()
            self.active_player.bind_runtime(self.symbols)
            self._death_armed = False
            self._awaiting_remote_death = False
            self.case_menu.bind_runtime(self.symbols)
            self._prev_case_id = current
            return False
        if self.is_ready or current == CASE_IDLE_VALUE or (current not in CASE_ID_TO_CASE and current != 31):
            return False
        self.symbols.refresh()
        self.weapon_base = self.symbols.get("GADGET_g_GadgetList")
        if not self._valid_weapon_table():
            return False
        if self.pine.batch_read_int32(addresses) != state:
            self.weapon_base = None
            self.symbols.clear()
            return False
        self.set_case(current)
        self.is_ready = True
        return True

    def _valid_weapon_table(self) -> bool:
        if self.weapon_base is None:
            return False
        for slot, name in ((2, b"blaster\0"), (17, b"fountainpen\0"), (32, b"jetboots\0")):
            pointer = self.pine.read_int32(self.weapon_base + slot * 0x74)
            if not 0x100000 <= pointer < 0x2000000 - len(name):
                return False
            if self.pine.read_bytes(pointer, len(name)) != name:
                return False
        return True

    def check_mission_failure(self) -> bool:
        if not self.mission_failure.active():
            return False
        self._awaiting_remote_death = False
        if self._prev_dead:
            return False
        self._prev_dead = True
        sample = self.active_player.death_state_sample() if self.is_ready else None
        self.on_death(sample[1] if sample is not None and sample[1] else 'failed a mission')
        return True

    def check_death(self) -> bool:
        if self.mission_failure.active():
            return self.check_mission_failure()
        if not self.is_ready:
            return False
        sample = self.active_player.death_state_sample()
        if sample is None:
            # Gadgetbots (and Qwark until its states are verified) use the
            # failure latch. A fresh ready module with no latch is a respawn.
            if (self.active_player.state_offset is None and self._prev_dead
                    and not self._awaiting_remote_death):
                self._prev_dead = False
                self.on_respawn()
            return False
        is_dead = sample[1] is not None
        if self._awaiting_remote_death:
            if not is_dead:
                return False
            self._awaiting_remote_death = False
        if not is_dead:
            self._death_armed = True
        elif not self._death_armed:
            return False
        newly_dead    = is_dead and not self._prev_dead
        newly_revived = self._prev_dead and not is_dead
        self._prev_dead = is_dead
        if newly_dead:
            self.on_death(sample[1])
        elif newly_revived:
            self.on_respawn()
        return newly_dead

    def receive_death(self) -> bool:
        # Recheck loader state: the worker can receive a network death between
        # ticks, after the old overlay has already started unloading.
        if (not self.is_ready or self.pine.batch_read_int32(
                (CURRENT_CASE_ADDRESS, FORCE_CASE_ADDRESS, LoaderStateReader.STATE, 0x206338))
                != [self.case_id, 0xFFFFFFFF, 5, 3]):
            return False
        if not self.active_player.kill():
            return False
        # Suppress this entire death, regardless of how long its animation or
        # reload takes. It must never echo back to the other DeathLink players.
        self._prev_dead = True
        self._death_armed = True
        self._awaiting_remote_death = True
        return True

    def __repr__(self) -> str:
        return f"CaseInventory(case_id={self.case_id}, planet={self.planet_name!r}, is_ready={self.is_ready})"
