from ...constants import NativeFunctions
from ..symbols import forbid, require
from .asm import MARKER, branch, capture, check, jump, packed, words
from .entitlements import Entitlements
from .game_flags import GameFlags
from .patch import PatchSet
from .plan import PatchPlan


class VendorOnly(PatchSet):
    def prepare(self, symbols, locations, checked, entitlements):
        self.patches = []
        p = self.pine
        forbid(symbols, NativeFunctions.WEAPON_PICKUP_UPDATE_WAIT, NativeFunctions.WEAPON_PICKUP_UPDATE_WAIT_FOR_PICKUP)
        get, put, sell, buy = require(symbols,
            NativeFunctions.GADGET_PLAYER_HAS_GADGET,
            NativeFunctions.GADGET_SET_GADGET_OWNERSHIP_STATUS,
            NativeFunctions.GADGET_IS_SELLABLE,
            NativeFunctions.SCRNVENDOR_PROCESS_PURCHASE,
        )
        module, sellable_gate, purchase_grant, *purchase_tail, call = p.batch_read_int32([
            0x206328, sell + 12, buy + 0x1EC, buy + 0x1F4, buy + 0x1F8, buy + 0x338])
        check(sellable_gate == jump(get, True), "Sellable gate changed")
        check(purchase_grant == jump(put, True), "Purchase grant changed")
        check(purchase_tail == [0x8E430010, 0x24020026], "Purchase tail changed")
        check(call >> 26 == 3, "Vendor rebuild call changed")
        builder = (call & 0x3FFFFFF) << 2
        body = words(p.read_bytes(builder, 0x800))
        check(body[0] == 0x27BDFF70, "Vendor builder changed")
        sites = [builder + i * 4 for i, w in enumerate(body) if w == jump(get, True)
                 and next((body[j] for j in range(i - 1, max(-1, i - 7), -1)
                           if body[j] >> 26 == 3), None) == jump(sell, True)]
        check(len(sites) == 4, f"Unexpected base-offer gates: {len(sites)}")
        reported = set(checked)
        plan_locations = {"vendor": dict(locations)} if locations else {}
        arena = buy + 0x1FC
        tables = {"vendor": arena + 16} if locations else {}
        # Hide weapons without a vendor check, regardless of AP ownership.
        flags = bytearray([4] * 40)
        for slot, name in locations.items():
            if not 0 <= slot < 40:
                raise ValueError("Invalid gadget id")
            flags[slot] = 2 if name in reported else 1
        data = bytearray(MARKER)
        if locations:
            data.extend(flags)
            getter = arena + len(data)
            data.extend(GameFlags(p).prepare(
                address=getter, table=arena + 16, fallback=get, record=False).replacement)
            setter = arena + len(data)
            data.extend(GameFlags(p).prepare(
                address=setter, table=arena + 16, fallback=put, record=True).replacement)
        init_edits = []
        entitlement_table = base = None
        if entitlements is not None:
            base, init, load, restart = require(symbols,
                "GADGET_g_GadgetList", NativeFunctions.MOBY_INIT_MOBYS, NativeFunctions.LEVEL_LOAD_LEVEL, NativeFunctions.LEVEL_RESTART,
            )
            entitlement_table = arena + len(data)
            snapshot = bytearray(44)
            for slot, value in entitlements.items():
                snapshot[slot] = 2 if value else 1
            data.extend(snapshot)
            routine = arena + len(data)
            data.extend(Entitlements(p).prepare(
                address=routine, table=entitlement_table, gadget_base=base,
                fallback=init).replacement)
            sites_words = p.batch_read_int32([load + 0x2F0, load + 0x2F4, restart + 0x12C, restart + 0x130])
            check(sites_words == [jump(init, True), 0] * 2, "Object init call changed")
            init_edits = [(site, packed([jump(routine, True)])) for site in (load + 0x2F0, restart + 0x12C)]
        check(arena + len(data) <= buy + 0x338, "Vendor hooks exceed the purchase tail")
        edits = [(buy + 0x1F4, packed([branch(buy + 0x1F4, buy + 0x338), 0])),
                 (arena, bytes(data))]
        if locations:
            edits.extend(((buy + 0x1EC, packed([jump(setter, True)])),
                          (sell + 12, packed([jump(getter, True)]))))
            edits.extend((site, packed([jump(getter, True)])) for site in sites)
        edits.extend(init_edits)
        plan = PatchPlan(
            patches=capture(p, edits), locations=plan_locations, tables=tables, reported=reported,
            marker_address=arena, module=module, entitlement_table=entitlement_table, gadget_base=base,
        )
        self.patches = plan.patches
        self.plan = plan
        return plan
