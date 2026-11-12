from ...constants import EQUIPMENT_INTERNAL_TO_DISPLAY, NativeFunctions, vendor_location_name
from ..batch_io import read_blocks
from .asm import MARKER
from .entitlements import GADGET_OWNED_OFFSET, GADGET_STRIDE
from .vendor_only import VendorOnly
from .weapon_pickup import WeaponPickup
from .equipment_only import EquipmentOnly


class LocationHooks:
    def __init__(self, pine):
        # Checked here rather than at import so generation/fuzzing under -O can still load the world.
        if not __debug__:
            raise RuntimeError("Native hook validation must not run with Python assertions disabled")
        self.pine = pine
        self.patches = []
        self.module = None
        self.marker_address = None
        self.tables = {}
        self.locations = {}
        self.reported = set()
        self.installed = False
        self.permanent = False
        self.entitlement_table = None
        self.gadget_base = None
        self.extra_ranges = []
        self.gain_storage_prepared = False
        self.catalog_only_ranges = []

    def prepare(self, symbols, *, pickup_locations, vendor_locations, checked=(), entitlements=None,
                vendor_enabled=True):
        """Build a complete, signature-checked patch plan without writing RAM."""
        if self.permanent:
            raise RuntimeError("Disc-installed hooks cannot use the build-time patch planner")
        self.extra_ranges = []
        self.gain_storage_prepared = False
        self.catalog_only_ranges = []
        if self.installed:
            raise RuntimeError("Cannot prepare a build plan on bound runtime hooks")
        pickup_locations = {slot: EQUIPMENT_INTERNAL_TO_DISPLAY.get(name, name)
                            for slot, name in pickup_locations.items()}
        vendor_locations = {slot: vendor_location_name(EQUIPMENT_INTERNAL_TO_DISPLAY.get(name, name))
                            for slot, name in vendor_locations.items()}
        p = self.pine
        give = symbols.get(NativeFunctions.WEAPON_PICKUP_GIVE_WEAPON)
        if give is None and not vendor_enabled:
            plan = EquipmentOnly(p).prepare(symbols, checked, entitlements)
        elif give is None:
            plan = VendorOnly(p).prepare(symbols, vendor_locations, checked, entitlements)
        else:
            plan = WeaponPickup(p).prepare(
                symbols, give, pickup_locations=pickup_locations,
                vendor_locations=vendor_locations, checked=checked, entitlements=entitlements,
                vendor_enabled=vendor_enabled,
            )
        self.patches = plan.patches
        self.locations = plan.locations
        self.tables = plan.tables
        self.reported = plan.reported
        self.marker_address = plan.marker_address
        self.module = plan.module
        self.entitlement_table = plan.entitlement_table
        self.gadget_base = plan.gadget_base
        self.extra_ranges = plan.extra_ranges
        return len(self.patches)

    def poll(self):
        if not self.installed:
            return []
        tables = self._read_if_current([(table, 40) for table in self.tables.values()])
        if tables is None:
            # A savestate or same-level reload can replace code without
            # changing the module id. The client must reload and bind the disc-installed tables.
            self.installed = False
            return []
        found = []
        for kind, flags in zip(self.tables, tables):
            for slot, name in self.locations[kind].items():
                if flags[slot] == 2 and name not in self.reported:
                    found.append(name)
                    self.reported.add(name)
        return found

    def is_current(self):
        return self._read_if_current([]) is not None

    def _read_if_current(self, spans):
        if self.marker_address is None:
            return None
        module, marker, *data = read_blocks(self.pine, [(0x206328, 4), (self.marker_address, len(MARKER)), *spans])
        if int.from_bytes(module, "little") != self.module or marker != MARKER:
            return None
        return data

    def sync_checked(self, checked):
        """Server-confirmed checks suppress offers/spawns, never grant items."""
        if not self.installed:
            self.reported.update(checked)
            return
        kinds = list(self.locations)
        tables = self._read_if_current([(self.tables[kind], 40) for kind in kinds])
        if tables is None:
            self.installed = False
            return
        checked = set(checked)
        writes = [(self.tables[kind] + slot, 2)
                  for kind, flags in zip(kinds, tables)
                  for slot, name in self.locations[kind].items() if name in checked and flags[slot] != 2]
        if writes:
            self.pine.batch_write_int8(writes)
        self.reported.update(checked)

    def sync_entitlements(self, entitlements):
        """Keep the pre-object-init snapshot current for native restarts too, and apply changed
        ownership to the live gadget list so items received mid-level appear without a reload."""
        if self.entitlement_table is None or not self.installed:
            return
        flags = bytearray(40)
        for slot, value in entitlements.items():
            if not 0 <= slot < 40 or type(value) is not bool:
                raise ValueError("Invalid AP entitlement")
            flags[slot] = 2 if value else 1
        current = self._read_if_current([(self.entitlement_table, 40)])
        if current is None or current[0] == flags:
            return
        self.pine.write_bytes(self.entitlement_table, bytes(flags))
        # Same store the object-init routine makes: owned = flag - 1, for managed slots only.
        live = [(self.gadget_base + slot * GADGET_STRIDE + GADGET_OWNED_OFFSET, flag - 1)
                for slot, flag in enumerate(flags) if flag and flag != current[0][slot]]
        if live:
            self.pine.batch_write_int32(live)
