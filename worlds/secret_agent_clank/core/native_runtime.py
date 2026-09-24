"""Install native location hooks before each loaded module starts gameplay."""
from ..constants.native_modules import CASE_MODULES
from .main_menu import is_main_menu
from .patches import PICKUP_LOCATIONS, VENDOR_LOCATIONS
from .patches.loader_gate import LoaderGate
from .patches.mission_travel import MissionTravel
from .patches.starting_case import StartingCase
from .patches.connection_warning import ConnectionWarning
from .patches.titan_vendor import TitanOffers, TitanVendor
from .symbols import RuntimeSymbols


class NativeRuntime:
    def __init__(self, pine, hooks, log):
        self.pine, self.hooks, self.log = pine, hooks, log
        self.gate = LoaderGate(pine)
        self.awaiting_start = False
        self.reset_notice = False
        self.generation = 0
        self.wrench = None
        self.progression = None
        self.weapon_mods = None
        self.vendor_modules = None
        self.presentation = None
        self.connection_warning = ConnectionWarning(pine)
        self.ap_connected = False
        self.owned_cases = frozenset()
        self.starting_case = StartingCase(pine, log)

    def configure_vendors(self, case_names):
        self.vendor_modules = {CASE_MODULES[name] for name in case_names}

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
            target = self.gate.held_module()
            if target == 0:
                self.hooks.installed = False
                self.awaiting_start = False
                self.reset_notice = False
                self.gate.release()
                return False
            if target is not None:
                symbols = RuntimeSymbols(p)
                symbols.refresh()
                self.hooks.installed = False
                vendor_enabled = self.vendor_modules is None or target in self.vendor_modules
                self.hooks.prepare(symbols, pickup_locations=PICKUP_LOCATIONS,
                                   vendor_locations=VENDOR_LOCATIONS if vendor_enabled else {}, checked=checked,
                                   entitlements=entitlements)
                if self.wrench is not None:
                    self.hooks.patches.extend(self.wrench.prepare(symbols, target))
                self.hooks.patches.extend(MissionTravel(p).prepare(symbols))
                if self.weapon_mods is not None:
                    self.hooks.patches.extend(self.weapon_mods.prepare(
                        symbols, self.hooks, target, checked, vendor_enabled))
                if self.progression is not None:
                    if self.progression.ng_plus and vendor_enabled:
                        self.hooks.patches.extend(TitanVendor(p).prepare(symbols, self.hooks, checked))
                    elif vendor_enabled:
                        self.hooks.patches.extend(TitanOffers(p).prepare(symbols))
                    self.hooks.patches.extend(self.progression.prepare(
                        symbols, self.hooks, target, vendor_enabled=vendor_enabled))
                if self.presentation is not None and vendor_enabled:
                    self.hooks.patches.extend(self.presentation.prepare(symbols, self.hooks))
                self.hooks.patches.extend(self.connection_warning.prepare(symbols, self.hooks))
                self.hooks.install_at_loader_gate(self.gate)
                self.connection_warning.refresh(self.ap_connected)
                self.hooks.sync_vendor_cases(self.owned_cases, loader_gate=self.gate)
                self.generation += 1
                self.gate.release()
                self.awaiting_start = True
                self.reset_notice = False
                self.log(f"[SAC] Hooks loaded for {target}")
                return False
            if is_main_menu(p):
                self.awaiting_start = False
                self.reset_notice = False
                return False
            if p.read_int32(self.gate.STATE) == 4 or p.read_int32(0x206324) != 0xFFFFFFFF:
                return False
            if self.hooks.installed and self.hooks.is_current():
                self.connection_warning.refresh(self.ap_connected)
                if p.read_int32(0x206338) != 3:
                    return False
                if self.hooks.entitlement_table is not None and not p.read_int8(self.hooks.entitlement_table + 40):
                    return False
                self.hooks.sync_checked(checked)
                self.hooks.sync_vendor_cases(self.owned_cases)
                self.hooks.sync_entitlements(entitlements)
                return True
            if not self.reset_notice:
                self.log("[SAC] Native checks are mandatory. Reset the level in-game once to initialize AP; do not load a savestate.")
                self.reset_notice = True
            return False
        except Exception:
            self.close()
            raise

    def close(self):
        try:
            if (self.hooks.installed and self.pine.get_game_id() == "SCUS-97623"
                    and self.hooks.is_current()
                    and self.pine.read_int32(0x206324) == 0xFFFFFFFF):
                self.connection_warning.refresh(False)
        finally:
            self.gate.release()
            self.starting_case.close()
            self.awaiting_start = False
