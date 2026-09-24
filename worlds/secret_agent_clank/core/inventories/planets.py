"""Case-transition detection plus every case-dependent accessor (Ratchet/ Clank/Qwark state+health, Ratchet/Clank item inventories), rebound via CaseInventory.set_case() whenever the current case changes."""
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from ...constants.planets import CASE_ID_TO_CASE
from ..address_maps import CASE_ADDRESSES, CASE_IDLE_VALUE, CURRENT_CASE_ADDRESS, FORCE_CASE_ADDRESS
from ..case_menu import CaseMenu
from ..player import CharacterState
from ..symbols import RuntimeSymbols
from ..vendor import VendorState
from .inventory import ItemInventory
from .weapons import WeaponInventory

if TYPE_CHECKING:
    from ...pypine import Pine

logger = logging.getLogger("CommonClient")


class CaseInventory:

    def __init__(self, pine: "Pine") -> None:
        self.pine = pine

        self.ratchet = CharacterState(pine)
        self.clank   = CharacterState(pine)
        self.qwark   = CharacterState(pine)
        # Historical attribute name: this array contains both characters' gear.
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

        # Invalidate bindings before a transition; death handling is separate.
        self.on_transition_start: Callable[[], None] = lambda: None
        self.on_death:            Callable[[], None] = lambda: None
        self.on_respawn:          Callable[[], None] = lambda: None

        self._prev_dead: bool = False

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

        if case_id not in CASE_ID_TO_CASE:
            logger.warning(
                f"[SAC] Unknown case id 0x{case_id:X} -- no addresses bound, every accessor is a no-op."
            )

    def check_transition(self) -> bool:
        """Require a settled request and a validated resident GadgetData table."""
        current = self.pine.read_int32(CURRENT_CASE_ADDRESS)
        requested = self.pine.read_int32(FORCE_CASE_ADDRESS)
        changing = current != self._prev_case_id or requested != 0xFFFFFFFF
        if changing or (self.is_ready and not self._valid_weapon_table()):
            self.is_ready = False
            self.on_transition_start()
            self.ratchet_items.set_base(None)
            self.clank_items.set_addrs(None)
            self.vendor.set_addr(None)
            self.weapon_base = None
            self.symbols.clear()
            self.case_menu.bind_runtime(self.symbols)
            self._prev_case_id = current
            return False
        if self.is_ready or current == CASE_IDLE_VALUE or (current not in CASE_ID_TO_CASE and current != 31):
            return False
        # A stable id alone is insufficient: resolve and validate the module,
        # then check the transition request again after the potentially long scan.
        self.symbols.refresh()
        self.weapon_base = self.symbols.get("GADGET_g_GadgetList")
        if not self._valid_weapon_table():
            return False
        if (self.pine.read_int32(CURRENT_CASE_ADDRESS) != current
                or self.pine.read_int32(FORCE_CASE_ADDRESS) != 0xFFFFFFFF):
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

    def force_case(self, case_id: int) -> None:
        """Write FORCE_CASE_ADDRESS to trigger a transition straight to case_id -- the same mechanism the game itself uses when moving between cases/planets."""
        if case_id not in CASE_ID_TO_CASE or case_id in (6, 12):
            raise ValueError(f"No independently loadable module is verified for case {case_id}")
        self.pine.write_int32(FORCE_CASE_ADDRESS, case_id)

    def check_death(self) -> bool:
        if not self.is_ready:
            return False
        is_dead = self.ratchet.is_dead
        newly_dead    = is_dead and not self._prev_dead
        newly_revived = self._prev_dead and not is_dead
        self._prev_dead = is_dead
        if newly_dead:
            self.on_death()
        elif newly_revived:
            self.on_respawn()
        return newly_dead

    def __repr__(self) -> str:
        return f"CaseInventory(case_id={self.case_id}, planet={self.planet_name!r}, is_ready={self.is_ready})"
