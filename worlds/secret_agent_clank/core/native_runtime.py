import logging

from .address_maps import CURRENT_CASE_ADDRESS, FORCE_CASE_ADDRESS
from .main_menu import is_main_menu
from ..constants import (
    CASES_BY_OPERATIVE,
    CASE_MODULES,
    SACOperatives,
)
from .patches import (
    ConnectionWarning,
    StartingCase,
)


CLANK_MODULES = frozenset(CASE_MODULES[case.name] for case in CASES_BY_OPERATIVE[SACOperatives.CLANK])
NON_VENDOR_CASES = frozenset(case.name for operative in
                            (SACOperatives.QWARK, SACOperatives.GADGETBOTS)
                            for case in CASES_BY_OPERATIVE[operative])


logger = logging.getLogger("CommonClient")


class NativeRuntime:
    def __init__(self, pine, hooks, log, debug=None):
        self.pine, self.hooks, self.log = pine, hooks, log
        self.debug = debug or logger.debug
        self.startup_barrier = None  # PermanentRuntime supplies the ISO startup barrier.
        self.awaiting_start = False
        self.reload_requested = False
        self.generation = 0
        self.keycard_hunt = None
        self.wrench = None
        self.progression = None
        self.weapon_mods = None
        self.skins = None
        self.vendor_modules = set(CLANK_MODULES) | {
            CASE_MODULES[case.name] for case in CASES_BY_OPERATIVE[SACOperatives.RATCHET]}
        self.vendor_locations = None
        self.vendor_catalog = None
        self.presentation = None
        self.connection_warning = ConnectionWarning(pine)
        self.ap_connected = False
        self.owned_cases = frozenset()
        self.vendor_cases = frozenset()
        self.available_vendor_locations = None
        self.starting_case = StartingCase()
        self.mission_travel = None
        self.on_mission_complete = lambda case_name: None

    def configure_vendors(self, case_names):
        self.vendor_modules = {CASE_MODULES[name] for name in case_names if name not in NON_VENDOR_CASES}

    def vendor_enabled_for_module(self, module):
        if module not in self.vendor_modules:
            return False
        if module == 4:
            return bool(self.pine.read_int8(0x206C89) & 1)
        if module == 11:
            return not bool(self.pine.read_int8(0x206CA8) & 1)
        return True

    def _sync_vendor_access(self):
        if self.available_vendor_locations is None:
            self.vendor_catalog.sync_cases(self.vendor_cases)
        else:
            self.vendor_catalog.sync_locations(self.available_vendor_locations)

    def _require_held_module(self, target):
        if self.startup_barrier.held_module() != target:
            raise RuntimeError("Loaded module changed or left the loader barrier during hook setup")

    def _gameplay_settled(self, *, require_current=True):
        """Reject outgoing modules and every intermediate loader state."""
        module, requested, loader, game = self.pine.batch_read_int32(
            (CURRENT_CASE_ADDRESS, FORCE_CASE_ADDRESS, self.startup_barrier.STATE, 0x206338))
        return ((not require_current or module == self.hooks.module) and requested == 0xFFFFFFFF
                and loader == 5 and game == 3)

    def _reload_current_level(self):
        """Recover missing hooks through a fresh native load, once per attempt."""
        if self.reload_requested:
            return
        p = self.pine
        addresses = (CURRENT_CASE_ADDRESS, FORCE_CASE_ADDRESS, self.startup_barrier.STATE, 0x206338)
        state = p.batch_read_int32(addresses)
        module, requested, loader, game = state
        if (module not in CASE_MODULES.values() or requested != 0xFFFFFFFF
                or loader != 5 or game != 3):
            return
        if p.batch_read_int32(addresses) != state or is_main_menu(p):
            return
        self.reload_requested = True
        self.hooks.installed = False
        p.write_int32(FORCE_CASE_ADDRESS, module)
        self.debug(f"[SAC] Reloading current level (module {module}) to initialize native checks.")
