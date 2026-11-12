from ...constants import NativeFunctions
from ..symbols import require
from .asm import MARKER, branch, capture, jump, packed, words
from .entitlements import Entitlements
from .gameFlags import GameFlags
from .patch import PatchSet
from .plan import PatchPlan


class WeaponPickup(PatchSet):
    def prepare(self, symbols, give, *, pickup_locations, vendor_locations, checked, entitlements,
                vendor_enabled=True):
        self.patches = []
        p = self.pine
        """Build a complete, signature-checked patch plan without writing RAM.

        `give` is WeaponPickup_GiveWeapon__FP4Moby's resolved address -- the
        caller (patches/hooks.py's LocationHooks.prepare()) already confirmed
        it exists before dispatching here; a missing export means this module
        has no pickup code at all, and VendorOnly.prepare() applies instead.
        """
        wait, wait_pickup, getter, setter = require(symbols,
            NativeFunctions.WEAPON_PICKUP_UPDATE_WAIT,
            NativeFunctions.WEAPON_PICKUP_UPDATE_WAIT_FOR_PICKUP,
            NativeFunctions.GADGET_PLAYER_HAS_GADGET,
            NativeFunctions.GADGET_SET_GADGET_OWNERSHIP_STATUS,
        )
        (module, prologue, grant, grant_args, tail, gate, gate_args, collect, collect_args,
         *epilogue) = p.batch_read_int32([
            0x206328, give, give + 0x50, give + 0x54, give + 0x58, wait + 0x50, wait + 0x54,
            wait_pickup + 0x48, wait_pickup + 0x4C, *range(give + 0x278, give + 0x294, 4)])
        assert prologue == 0x27BDFF90, "Pickup prologue changed"
        assert grant == jump(setter, True), "Pickup grant call changed"
        assert grant_args == 0x2CC60002, "Pickup grant arguments changed"
        assert tail == 0x8E450000, "Pickup tail changed"
        assert epilogue == [
            0xDFB00040, 0xDFB10048, 0xDFB20050, 0xDFB30058,
            0xDFBF0060, 0x03E00008, 0x27BD0070], "Pickup epilogue changed"
        assert gate == jump(getter, True), "Pickup ownership gate changed"
        assert gate_args == 0x8E640000, "Pickup gate arguments changed"
        assert collect == jump(getter, True), "Collection ownership gate changed"
        assert collect_args == 0x8E040000, "Collection gate arguments changed"
        if vendor_enabled:
            sellable, purchase = require(symbols, NativeFunctions.GADGET_IS_SELLABLE,
                                         NativeFunctions.SCRNVENDOR_PROCESS_PURCHASE)
            sellable_gate, purchase_grant, *purchase_tail, builder_call = p.batch_read_int32([
                sellable + 12, purchase + 0x1EC, purchase + 0x1F4, purchase + 0x1F8, purchase + 0x338])
            assert sellable_gate == jump(getter, True), "Sellable gate changed"
            assert purchase_grant == jump(setter, True), "Purchase grant changed"
            assert purchase_tail == [0x8E430010, 0x24020026]
            assert builder_call >> 26 == 3, "Vendor rebuild call changed"
            builder = (builder_call & 0x03FFFFFF) << 2
            body = words(p.read_bytes(builder, 0x800))
            assert body[0] == 0x27BDFF70, "Vendor builder changed"
            # Only base-offer ownership calls immediately following IsSellable.
            # Ammo and mod ownership calls retain their gameplay semantics.
            sites = []
            for i, instruction in enumerate(body):
                if instruction != jump(getter, True):
                    continue
                previous_call = next((body[j] for j in range(i - 1, max(-1, i - 7), -1)
                                      if body[j] >> 26 == 3), None)
                if previous_call == jump(sellable, True):
                    sites.append(builder + i * 4)
            assert len(sites) == 4, f"Unexpected base-offer gates: {len(sites)}"

        locations = {"pickup": dict(pickup_locations)}
        if vendor_enabled:
            locations["vendor"] = dict(vendor_locations)
        for mapping in locations.values():
            if any(not 0 <= slot < 40 for slot in mapping):
                raise ValueError("Gadget ids must be between 0 and 39")
        reported = set(checked)
        arena = give + 0x60
        tables = {}
        data = bytearray(MARKER)
        assert len(data) == 16
        for kind in locations:
            tables[kind] = arena + len(data)
            # AP ownership can leave pickup-only weapons unowned. Do not let
            # those become native, zero-cost offers with no vendor check.
            flags = bytearray([4] * 40) if kind == "vendor" and vendor_locations else bytearray(40)
            for slot, name in locations[kind].items():
                flags[slot] = 2 if name in reported else 1
            data.extend(flags)
        routines = {}
        for kind, record in ((kind, record) for kind in locations for record in (False, True)):
            routines[kind, record] = arena + len(data)
            data.extend(GameFlags(p).prepare(
                address=routines[kind, record], table=tables[kind],
                fallback=setter if record else getter, record=record).replacement)
        init_edits = []
        entitlement_table = base = None
        if entitlements is not None:
            if any(not 0 <= slot < 40 or type(value) is not bool for slot, value in entitlements.items()):
                raise ValueError("Entitlements require gadget ids 0..39 and boolean ownership")
            base, init, load, restart = require(symbols,
                "GADGET_g_GadgetList", NativeFunctions.MOBY_INIT_MOBYS, NativeFunctions.LEVEL_LOAD_LEVEL, NativeFunctions.LEVEL_RESTART,
            )
            sites_words = p.batch_read_int32([load + 0x2F0, load + 0x2F4, restart + 0x12C, restart + 0x130])
            assert sites_words == [jump(init, True), 0] * 2, "Object init call changed"
            entitlement_table = arena + len(data)
            flags = bytearray(44)  # 40 slots, invocation byte, alignment padding
            for slot, value in entitlements.items():
                flags[slot] = 2 if value else 1
            data.extend(flags)
            routine = arena + len(data)
            data.extend(Entitlements(p).prepare(
                address=routine, table=entitlement_table, gadget_base=base,
                fallback=init).replacement)
            init_edits = [(site, packed([jump(routine, True)]))
                          for site in (load + 0x2F0, restart + 0x12C)]
        assert arena + len(data) <= give + 0x278, "Replacement exceeds intercepted tail"
        edits = [(give + 0x58, packed([branch(give + 0x58, give + 0x278), 0])),
                 (arena, bytes(data)),
                 (give + 0x50, packed([jump(routines["pickup", True], True)])),
                 (wait + 0x50, packed([jump(routines["pickup", False], True)])),
                 (wait_pickup + 0x48, packed([jump(routines["pickup", False], True)]))]
        if vendor_enabled:
            edits.extend([
                (sellable + 12, packed([jump(routines["vendor", False], True)])),
                (purchase + 0x1EC, packed([jump(routines["vendor", True], True)])),
                (purchase + 0x1F4, packed([branch(purchase + 0x1F4, purchase + 0x338), 0]))])
            edits.extend((site, packed([jump(routines["vendor", False], True)])) for site in sites)
        edits.extend(init_edits)
        plan = PatchPlan(
            patches=capture(p, edits), locations=locations, tables=tables, reported=reported,
            marker_address=arena, module=module, entitlement_table=entitlement_table, gadget_base=base,
        )
        self.patches = plan.patches
        self.plan = plan
        return plan
