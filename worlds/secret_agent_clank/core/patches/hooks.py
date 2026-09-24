"""Runtime-facing API for native location interception on SCUS-97623 -- picks the applicable patch plan (patches/weapon_pickup.py's common case, or patches/vendor_only.py for modules like Treehouse with a vendor but no WeaponPickup code) and owns install/poll/sync/restore against a live PINE connection."""
from ...constants.native_functions import NativeFunctions
from ...constants.weapon_mods import WEAPON_MODS
from ...constants.weapons import CASE_BY_WEAPON_NAME, EQUIPMENT_INTERNAL_TO_DISPLAY
from ..inventories.weapons import WEAPON_ORDER
from .asm import MARKER
from .vendor_only import VendorOnly
from .weapon_pickup import WeaponPickup


class LocationHooks:
    def __init__(self, pine):
        self.pine = pine
        self.patches = []
        self.module = None
        self.marker_address = None
        self.tables = {}
        self.locations = {}
        self.reported = set()
        self.installed = False
        self.entitlement_table = None

    def prepare(self, symbols, *, pickup_locations, vendor_locations, checked=(), entitlements=None):
        """Build a complete, signature-checked patch plan without writing RAM."""
        self.extra_ranges = []
        if self.installed:
            raise RuntimeError("Restore installed hooks before preparing a new plan")
        p = self.pine
        give = symbols.get(NativeFunctions.WEAPON_PICKUP_GIVE_WEAPON)
        if give is None:
            plan = VendorOnly(p).prepare(symbols, vendor_locations, checked, entitlements)
        else:
            plan = WeaponPickup(p).prepare(
                symbols, give, pickup_locations=pickup_locations,
                vendor_locations=vendor_locations, checked=checked, entitlements=entitlements,
            )
        self.patches = plan.patches
        self.locations = plan.locations
        self.tables = plan.tables
        self.reported = plan.reported
        self.marker_address = plan.marker_address
        self.module = plan.module
        self.entitlement_table = plan.entitlement_table
        return len(self.patches)

    def install(self, screen_address):
        """Research-only: install in an idle vendor/Case Files, without input."""
        p = self.pine
        if not self.patches or self.installed:
            raise RuntimeError("No fresh patch plan")
        assert p.get_game_id() == "SCUS-97623"
        assert p.read_int32(0x206328) == self.module and p.read_int32(0x206324) == 0xFFFFFFFF
        assert p.read_int32(screen_address) in (8, 14, 16), "Open vendor or Case Files before installing"
        self._install_plan()

    def install_at_loader_gate(self, gate):
        """Experimental installation before the native level thread starts."""
        if gate.pine is not self.pine:
            raise RuntimeError("Loader barrier must share this PINE connection")
        target = gate.held_module()
        if target is None:
            raise RuntimeError("New level is not held before startup")
        if not self.patches or self.installed:
            raise RuntimeError("No fresh patch plan")
        self.module = target
        self._install_plan()

    def _install_plan(self):
        p = self.pine
        for patch in self.patches:
            assert p.read_bytes(patch.address, len(patch.original)) == patch.original, "Code changed since planning"
        attempted = []
        try:
            for patch in self.patches:
                attempted.append(patch)
                p.write_bytes(patch.address, patch.replacement)
            for patch in self.patches:
                assert p.read_bytes(patch.address, len(patch.replacement)) == patch.replacement
            for kind, table in self.tables.items():
                flags = p.read_bytes(table, 40)
                for slot, name in self.locations[kind].items():
                    unchecked = 3 if kind == "titan" else 1
                    assert flags[slot] == (2 if name in self.reported else unchecked)
        except Exception:
            # Caller keeps native execution parked throughout installation.
            # Undo even a partially transmitted write before releasing it.
            for patch in reversed(attempted):
                p.write_bytes(patch.address, patch.original)
                if p.read_bytes(patch.address, len(patch.original)) != patch.original:
                    raise RuntimeError("Hook installation rollback readback failed")
            raise
        self.installed = True

    def poll(self):
        if not self.installed:
            return []
        if not self.is_current():
            # A savestate or same-level reload can replace code without
            # changing the module id. The client must install again.
            self.installed = False
            return []
        found = []
        for kind, table in self.tables.items():
            flags = self.pine.read_bytes(table, 40)
            for slot, name in self.locations[kind].items():
                if flags[slot] == 2 and name not in self.reported:
                    found.append(name)
                    self.reported.add(name)
        return found

    def is_current(self):
        return (self.marker_address is not None
                and self.pine.read_int32(0x206328) == self.module
                and self.pine.read_bytes(self.marker_address, len(MARKER)) == MARKER)

    def sync_checked(self, checked):
        """Server-confirmed checks suppress offers/spawns, never grant items."""
        if not self.installed:
            self.reported.update(checked)
            return
        if not self.is_current():
            self.installed = False
            return
        checked = set(checked)
        writes = [(self.tables[kind] + slot, 2)
                  for kind, mapping in self.locations.items()
                  for slot, name in mapping.items() if name in checked
                  and self.pine.read_int8(self.tables[kind] + slot) != 2]
        if writes:
            self.pine.batch_write_int8(writes)
        self.reported.update(checked)

    def sync_entitlements(self, entitlements):
        """Keep the pre-object-init snapshot current for native restarts too."""
        if self.entitlement_table is None or not self.installed or not self.is_current():
            return
        flags = bytearray(40)
        for slot, value in entitlements.items():
            if not 0 <= slot < 40 or type(value) is not bool:
                raise ValueError("Invalid AP entitlement")
            flags[slot] = 2 if value else 1
        if self.pine.read_bytes(self.entitlement_table, 40) != flags:
            self.pine.write_bytes(self.entitlement_table, bytes(flags))

    def sync_vendor_cases(self, owned_cases, *, loader_gate=None):
        """Hide a locked offer with flag 4, distinct from purchased flag 2 -- base/mod
        readers return flag - 1 (nonzero hides the offer), Titan readers only ever
        offer flag 3, and polling only ever reports flag 2 as purchased."""
        if not self.installed:
            return
        if loader_gate is not None:
            # The current-module global still names the outgoing level while
            # the incoming module is held before startup.
            if loader_gate.pine is not self.pine or loader_gate.held_module() != self.module:
                raise RuntimeError("Vendor case flags require the held module")
        elif not self.is_current():
            return
        mod_weapons = {mod.mod_id: mod.weapon for mod in WEAPON_MODS}
        writes = []
        for kind in ("vendor", "mods", "titan"):
            for slot in self.locations.get(kind, {}):
                weapon = (mod_weapons.get(slot) if kind == "mods" else
                          EQUIPMENT_INTERNAL_TO_DISPLAY.get(WEAPON_ORDER[slot]))
                case = CASE_BY_WEAPON_NAME.get(weapon)
                address = self.tables[kind] + slot
                flag = self.pine.read_int8(address)
                if flag == 2:
                    continue
                desired = 4 if case is not None and case not in owned_cases else (3 if kind == "titan" else 1)
                if flag != desired:
                    writes.append((address, desired))
        if writes:
            self.pine.batch_write_int8(writes)

    def restore(self):
        if not self.installed:
            return
        p = self.pine
        assert p.get_game_id() == "SCUS-97623"
        assert p.read_int32(0x206328) == self.module and p.read_int32(0x206324) == 0xFFFFFFFF
        assert p.read_bytes(self.marker_address, len(MARKER)) == MARKER
        # Restore entry calls before reclaiming their routines, and restore
        # the original pickup tail branch last.
        for patch in reversed(self.patches):
            p.write_bytes(patch.address, patch.original)
        self.installed = False
