from ..constants import CASE_MODULES, SACCases, WEAPON_ORDER, NATIVE_FINISH_CASES, SKINS_BY_CHARACTER, QWARK_GIANT_SKINS
from .native_runtime import NativeRuntime
from .main_menu import is_main_menu
from .patches.asm import packed
from .patches.bindings import FIELDS, decode_binding
from .patches.identity import PatchedGameGuard, CodeProbe, WrongPatchedGame
from .patches.iso_startup_barrier import ISOStartupBarrier
from .patches.mission_travel import MissionTravel
from .patches.vendor_catalog import VendorCatalog


class PermanentRuntime(NativeRuntime):
    def __init__(self, pine, hooks, log, debug, build):
        super().__init__(pine, hooks, log, debug)
        self.build = build
        if "loader_routine" not in build:
            raise RuntimeError("This ISO build predates the arm-only loader barrier. "
                               "Rebuild data/ with patcher.build from the clean ISO.")
        self.startup_barrier = ISOStartupBarrier(pine, build["loader_routine"])
        self.guard = PatchedGameGuard(build["build_id"], build["elf_crc"], (
            CodeProbe(ISOStartupBarrier.SIGNATURE_START, self.startup_barrier.code),
            CodeProbe(self.startup_barrier.routine, self.startup_barrier.routine_code)))
        self.bound = None
        self.frontend_config = None

    def verify(self):
        """Run before any worker command that could touch native memory."""
        self.guard.verify(self.pine)
        p = self.pine
        state = tuple(p.batch_read_int32([self.startup_barrier.STATE, self.startup_barrier.STATUS, self.startup_barrier.TARGET, self.startup_barrier.HANDLE]))
        loader, status, target, base = state
        if status == 1 and loader in (4, 5):
            record = self.build["modules"].get(str(target))
            if record is None or base % 16 or not 0x100000 <= base <= 0x2000000 - record["size"]:
                raise WrongPatchedGame("Unknown loaded SAC module")
            identity = bytes.fromhex(record["identity"])
            if not identity or p.read_bytes(base + record["identity_offset"], len(identity)) != identity:
                raise WrongPatchedGame("Loaded level is not this patched build; incompatible ISO or savestate")
            if tuple(p.batch_read_int32([self.startup_barrier.STATE, self.startup_barrier.STATUS, self.startup_barrier.TARGET, self.startup_barrier.HANDLE])) != state:
                return None
            return target, base
        return None

    def _bind(self, target, base):
        record = self.build["modules"][str(target)]
        if target == 0:
            self.frontend_config = base + record["config_offset"]
            self.hooks.installed = False
            self.bound = (target, base)
            return
        self.mission_travel = MissionTravel(self.pine)
        self.vendor_catalog = VendorCatalog(self.pine) if record["vendor"] else None
        objects = {"hooks": self.hooks, "wrench": self.wrench, "mission_travel": self.mission_travel,
                   "skins": self.skins, "weapon_mods": self.weapon_mods, "progression": self.progression,
                   "vendor_catalog": self.vendor_catalog, "presentation": self.presentation,
                   "connection_warning": self.connection_warning, "keycard_hunt": self.keycard_hunt,
                   "mission_failure": self.progression.mission_failure, "stealth": self.progression.stealth}
        self.presentation.mailbox = self.presentation.timer = None
        for name, fields in record["objects"].items():
            obj = objects[name]
            allowed = set(FIELDS.get(name, ())) | ({"binding"} if name in ("mission_failure", "stealth") else set())
            allowed |= {"code"} if name in ("connection_warning", "keycard_hunt") else set()
            allowed |= {"pointer_address"} if name == "skins" else set()
            for field, recipe in fields.items():
                if field not in allowed:
                    raise WrongPatchedGame(f"Unknown native binding: {name}.{field}")
                value = decode_binding(recipe, base)
                if name == "skins" and field == "pointer_address":
                    obj.flags.pointer_address = value
                else:
                    setattr(obj, field, value)
        self.hooks.patches = []
        self.hooks.reported = set()
        self.hooks.installed = True
        self.wrench.sites = []
        self.weapon_mods.validated = False
        self.progression.ng_address = None
        self.progression.pending_definitions = tuple(self.progression.levels)
        self.bound = (target, base)

    def _configure_frontend(self):
        name = self.starting_case.case_name
        config = packed([CASE_MODULES[name] if name is not None else 1,
                         int(name == SACCases.ASYANICA_ROOFTOPS), int(name == SACCases.SUCK_AND_JIVE)])
        self.pine.write_bytes(self.frontend_config, config)

    def _initialize(self, checked, entitlements):
        p, hooks = self.pine, self.hooks
        checked = set(checked)
        for kind, table in hooks.tables.items():
            count = 32 if kind == "mods" else 20 if kind == "titan" else 40
            # Unmapped slots have native fallback/suppression sentinels (0 or
            # 4). Preserve those; treating every slot as a completed AP check
            # would silently suppress ordinary game pickups.
            flags = bytearray(p.read_bytes(table, count))
            for slot, name in hooks.locations[kind].items():
                available = kind == "pickup" or self.vendor_locations is None or name in self.vendor_locations
                flags[slot] = 2 if name in checked or not available else 3 if kind == "titan" else 1
                if not available:
                    hooks.reported.add(name)
            p.write_bytes(table, bytes(flags))
        hooks.reported.update(checked)
        if hooks.entitlement_table is not None:
            flags = bytearray(41)
            for slot, owned in entitlements.items():
                if type(slot) is not int or not 0 <= slot < 40 or type(owned) is not bool:
                    raise ValueError("Invalid AP entitlement")
                flags[slot] = 2 if owned else 1
            p.write_bytes(hooks.entitlement_table, bytes(flags))
        self._sync_configuration()
        if self.vendor_catalog is not None:
            self.vendor_catalog.challenge_level = self.progression.ng_plus
            self._sync_vendor_access()
        binding = self.progression.stealth.binding
        if binding is not None:
            p.write_int32(binding[1], self.progression.stealth.counts.get(binding[0], 0))
        self.connection_warning.refresh(self.ap_connected)

    def _sync_configuration(self):
        p, progression = self.pine, self.progression
        p.write_bytes(progression.config_address, packed([progression.weapon_xp, progression.health_xp, progression.bolts]))
        if progression.cap_address is not None:
            caps = bytes((progression.levels.get(name, 0) if progression.manual else
                          0 if progression.enabled else 255) for name in WEAPON_ORDER)
            p.write_bytes(progression.cap_address, caps)
        if progression.pickup_challenge_address is not None:
            p.write_int32(progression.pickup_challenge_address, progression.ng_plus)
        if self.wrench.ownership_address is not None:
            p.write_int32(self.wrench.ownership_address, int(not self.wrench.enabled or self.wrench.count > 0))
        choices = [self.skins.selected.get(character, 0) for character in SKINS_BY_CHARACTER]
        choices.append(QWARK_GIANT_SKINS.get(self.skins.selected.get("qwark", 0), 0))
        p.write_bytes(self.skins.config_address, bytes(choices))
        if self.keycard_hunt.table is not None:
            p.write_int32(self.keycard_hunt.table, self.keycard_hunt.mask)
            p.write_int32(self.keycard_hunt.enable_address, int(self.keycard_hunt.enabled))

    def service(self, checked, entitlements):
        identity = self.verify()
        self.startup_barrier.attach()
        target = self.startup_barrier.held_module(settled=True)
        if target is not None:
            if identity is None or identity[0] != target:
                return False
            stealth = self.progression.stealth
            if stealth.cases and not stealth.loaded:
                return False
            self._bind(*identity)
            if target == 0:
                self._configure_frontend()
            else:
                self._initialize(checked, entitlements)
            self._require_held_module(target)
            if self.verify() != identity:
                return False
            self.startup_barrier.release()
            self.generation += 1
            self.awaiting_start = target != 0
            self.reload_requested = False
            return False
        if identity is None:
            return False
        if identity[0] == 0 and is_main_menu(self.pine):
            if self.bound != identity:
                self._bind(*identity)
            self._configure_frontend()
            return False
        if not self._gameplay_settled(require_current=False):
            return False
        if self.bound != identity or not self.hooks.installed:
            # Connecting mid-level must reinitialize on the game thread before
            # any pickups spawn; writing tables into an already running level
            # cannot safely recreate those initialization decisions.
            self._reload_current_level()
            return False
        if self.hooks.entitlement_table is not None and not self.pine.read_int8(self.hooks.entitlement_table + 40):
            return False
        self.awaiting_start = False
        self._sync_configuration()
        self.hooks.sync_checked(checked)
        self.hooks.sync_entitlements(entitlements)
        self.connection_warning.refresh(self.ap_connected)
        if self.vendor_catalog is not None:
            self.vendor_catalog.challenge_level = self.progression.ng_plus
            self._sync_vendor_access()
        mailbox = self.mission_travel.completion_mailbox
        if self.hooks.module in NATIVE_FINISH_CASES and mailbox is not None and self.pine.read_int32(mailbox) == 1:
            self.on_mission_complete(NATIVE_FINISH_CASES[self.hooks.module])
            self._reload_current_level()
            return False
        return True

    def close(self, *, disarm=True):
        """Stop servicing. Disarming lets later loads run without a client.

        Pass disarm=False when memory failed verification, so nothing is written to it.
        """
        self.hooks.installed = False
        self.bound = None
        self.awaiting_start = False
        self.reload_requested = False
        self.startup_barrier.detach(disarm=disarm)
