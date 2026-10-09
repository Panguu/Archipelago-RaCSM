"""Install native location hooks before each loaded module starts gameplay."""
import logging

from ..constants.native_modules import CASE_MODULES
from ..constants.planets import CASES_BY_OPERATIVE
from ..constants.operatives import SACOperatives
from ..constants.vendor import vendor_location_name
from ..constants.weapons import EQUIPMENT_INTERNAL_TO_DISPLAY
from .address_maps import CURRENT_CASE_ADDRESS, FORCE_CASE_ADDRESS
from .main_menu import is_main_menu
from .patches import PICKUP_LOCATIONS, VENDOR_LOCATIONS
from .patches.connection_warning import ConnectionWarning
from .patches.loader_gate import LoaderBarrierLost, LoaderGate
from .patches.mission_travel import MissionTravel
from .patches.starting_case import StartingCase
from .patches.titan_vendor import TitanOffers, TitanVendor
from .patches.vendor_catalog import VendorCatalog
from .symbols import RuntimeSymbols


CLANK_MODULES = frozenset(CASE_MODULES[case.name] for case in CASES_BY_OPERATIVE[SACOperatives.CLANK])
NON_VENDOR_CASES = frozenset(case.name for operative in
                            (SACOperatives.QWARK, SACOperatives.GADGETBOTS)
                            for case in CASES_BY_OPERATIVE[operative])


logger = logging.getLogger("CommonClient")


class NativeRuntime:
    def __init__(self, pine, hooks, log, debug=None):
        self.pine, self.hooks, self.log = pine, hooks, log
        # Diagnostics only shown while the client's /debug is on.
        self.debug = debug or logger.debug
        self.gate = LoaderGate(pine)
        self.awaiting_start = False
        self.reload_requested = False
        self.generation = 0
        self._stealth_wait_logged = False
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
        self.starting_case = StartingCase(pine, log)
        self.mission_travel = None
        self.on_quasar_complete = lambda: None

    def configure_vendors(self, case_names):
        self.vendor_modules = {CASE_MODULES[name] for name in case_names if name not in NON_VENDOR_CASES}

    def vendor_enabled_for_module(self, module):
        if module not in self.vendor_modules:
            return False
        # These two DLLs are shared with Gadgetbots and Qwark respectively.
        # Read the resident USA save flags, already set by Case Files / New
        # Game before the loader gate. The incoming DLL's pGV is not yet bound.
        # GLOBAL flag A9 = Asyanica Clank; C8 = Rionosis Qwark (save + 0x4E0).
        if module == 4:
            return bool(self.pine.read_int8(0x206C89) & 1)
        if module == 11:
            return not bool(self.pine.read_int8(0x206CA8) & 1)
        return True

    def service(self, checked, entitlements):
        """Return True only when gameplay may use this module's installed hooks."""
        p = self.pine
        try:
            if self.starting_case.service():
                self.awaiting_start = False
                self.hooks.installed = False
                if not self.gate.armed:
                    self.gate.arm()
                return False
            if self.awaiting_start:
                if (p.read_int32(self.gate.STATE) == 4
                        or p.read_int32(0x206324) != 0xFFFFFFFF
                        or p.read_int32(0x206338) != 3):
                    return False
                if (p.read_int32(0x206328) != self.hooks.module
                        or (self.hooks.entitlement_table is not None
                            and not p.read_int8(self.hooks.entitlement_table + 40))):
                    return False
                self.awaiting_start = False
            if not self.gate.armed:
                self.gate.arm()
            try:
                target = self.gate.held_module()
            except LoaderBarrierLost as exc:
                # A fresh load cannot fix a barrier that disappears on every
                # transition. Stop sync instead of repeatedly reloading.
                self.gate.armed = False
                self.hooks.installed = False
                raise LoaderBarrierLost(
                    f"{exc}. Game sync stopped; automatic reload is disabled "
                    "because the loader barrier did not persist through the transition."
                ) from exc
            if target == 0:
                self.hooks.installed = False
                self.awaiting_start = False
                self.reload_requested = False
                self.gate.release()
                return False
            if target is not None:
                stealth = getattr(self.progression, "stealth", None)
                if stealth is not None and stealth.cases and not stealth.loaded:
                    if not self._stealth_wait_logged:
                        self.debug("[SAC] Loading is held while waiting for saved stealth "
                                 "progress from the AP server. Use /sac_info to inspect the wait.")
                        self._stealth_wait_logged = True
                    return False  # Keep the loader parked until slot progress is known.
                self._stealth_wait_logged = False
                symbols = RuntimeSymbols(p)
                symbols.refresh()
                self.hooks.installed = False
                vendor_enabled = self.vendor_enabled_for_module(target)
                self.hooks.prepare(symbols, pickup_locations=PICKUP_LOCATIONS,
                                   vendor_locations={slot: name for slot, name in VENDOR_LOCATIONS.items()
                                       if vendor_enabled and (self.vendor_locations is None or
                                           vendor_location_name(EQUIPMENT_INTERNAL_TO_DISPLAY.get(name, name)) in self.vendor_locations)}, checked=checked,
                                   entitlements=entitlements, vendor_enabled=vendor_enabled)
                if self.wrench is not None:
                    self.hooks.patches.extend(self.wrench.prepare(symbols, target))
                self.mission_travel = MissionTravel(p)
                self.hooks.patches.extend(self.mission_travel.prepare(symbols, module=target))
                if self.skins is not None:
                    self.hooks.patches.extend(self.skins.prepare(symbols))
                if self.weapon_mods is not None:
                    self.hooks.patches.extend(self.weapon_mods.prepare(
                        symbols, self.hooks, target, checked, vendor_enabled))
                if self.progression is not None:
                    if self.progression.max_challenge_mode and vendor_enabled:
                        self.hooks.patches.extend(TitanVendor(p).prepare(symbols, self.hooks, checked, self.vendor_locations))
                    elif vendor_enabled:
                        self.hooks.patches.extend(TitanOffers(p).prepare(symbols))
                self.vendor_catalog = VendorCatalog(p) if vendor_enabled else None
                if self.vendor_catalog is not None:
                    self.hooks.patches.extend(self.vendor_catalog.prepare(symbols, self.hooks))
                if self.presentation is not None and vendor_enabled:
                    self.hooks.patches.extend(self.presentation.prepare(symbols, self.hooks))
                elif self.presentation is not None:
                    self.presentation.mailbox = self.presentation.timer = None
                    self.presentation.patches = []
                self.hooks.patches.extend(self.connection_warning.prepare(symbols, self.hooks))
                if self.progression is not None:
                    self.hooks.patches.extend(self.progression.prepare(
                        symbols, self.hooks, target, vendor_enabled=vendor_enabled))
                self.hooks.install_at_loader_gate(self.gate)
                if self.vendor_catalog is not None:
                    self.vendor_catalog.challenge_level = self.progression.ng_plus if self.progression is not None else 0
                    self.vendor_catalog.sync_cases(self.owned_cases)
                if self.skins is not None:
                    self.skins.sync()
                self.connection_warning.refresh(self.ap_connected)
                self.generation += 1
                self.gate.release()
                self.awaiting_start = True
                self.reload_requested = False
                self.debug(f"[SAC] Hooks loaded for {target} (vendor patches {'enabled' if vendor_enabled else 'disabled'})")
                return False
            if is_main_menu(p):
                self.awaiting_start = False
                self.reload_requested = False
                return False
            if not self._gameplay_settled(require_current=False):
                return False
            if self.hooks.installed and self.hooks.is_current():
                if self.hooks.entitlement_table is not None and not p.read_int8(self.hooks.entitlement_table + 40):
                    return False
                # Recheck after inspecting module-local memory: travel may
                # have started during those PINE round trips.
                if not self._gameplay_settled():
                    return False
                mailbox = getattr(self.mission_travel, "completion_mailbox", None)
                if self.hooks.module == 24 and mailbox is not None and p.read_int32(mailbox) == 1:
                    self.on_quasar_complete()
                    self._reload_current_level()
                    return False
                self.connection_warning.refresh(self.ap_connected)
                if self.vendor_catalog is not None:
                    self.vendor_catalog.challenge_level = self.progression.ng_plus if self.progression is not None else 0
                    self.vendor_catalog.sync_cases(self.owned_cases)
                self.hooks.sync_checked(checked)
                self.hooks.sync_entitlements(entitlements)
                if self.skins is not None:
                    self.skins.sync()
                return True
            self._reload_current_level()
            return False
        except Exception:
            self.close()
            raise

    def _gameplay_settled(self, *, require_current=True):
        """Reject outgoing modules and every intermediate loader state."""
        module, requested, loader, game = self.pine.batch_read_int32(
            (CURRENT_CASE_ADDRESS, FORCE_CASE_ADDRESS, self.gate.STATE, 0x206338))
        return ((not require_current or module == self.hooks.module) and requested == 0xFFFFFFFF
                and loader == 5 and game == 3)

    def _reload_current_level(self):
        """Recover missing hooks through a fresh native load, once per attempt."""
        if self.reload_requested:
            return
        p = self.pine
        addresses = (CURRENT_CASE_ADDRESS, FORCE_CASE_ADDRESS, self.gate.STATE, 0x206338)
        state = p.batch_read_int32(addresses)
        module, requested, loader, game = state
        if (module not in CASE_MODULES.values() or requested != 0xFFFFFFFF
                or loader != 5 or game != 3):
            return
        # Never replace travel that began while we were examining the state.
        if p.batch_read_int32(addresses) != state or is_main_menu(p):
            return
        # Mark first: a lost write acknowledgement must not cause repeated reloads.
        self.reload_requested = True
        self.hooks.installed = False
        p.write_int32(FORCE_CASE_ADDRESS, module)
        self.debug(f"[SAC] Reloading current level (module {module}) to initialize native checks.")

    def close(self):
        try:
            if (self.hooks.installed and self.pine.get_game_id() == "SCUS-97623"
                    and self.hooks.is_current()
                    and self._gameplay_settled()):
                self.connection_warning.refresh(False)
        finally:
            self.gate.release()
            self.starting_case.close()
            self.awaiting_start = False
            self.reload_requested = False
            self._stealth_wait_logged = False
