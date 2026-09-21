"""Native patch plan for modules with a vendor but no WeaponPickup code (e.g."""
from ...constants.native_functions import NativeFunctions
from ..symbols import forbid, require
from .asm import MARKER, Patch, branch, jump, packed, words
from .entitlements import Entitlements
from .gameFlags import GameFlags
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
        assert p.read_int32(sell + 12) == jump(get, True)
        assert p.read_int32(buy + 0x1EC) == jump(put, True)
        assert words(p.read_bytes(buy + 0x1F4, 8)) == [0x8E430010, 0x24020026]
        call = p.read_int32(buy + 0x338)
        assert call >> 26 == 3
        builder = (call & 0x3FFFFFF) << 2
        assert p.read_int32(builder) == 0x27BDFF70
        body = words(p.read_bytes(builder, 0x800))
        sites = [builder + i * 4 for i, w in enumerate(body) if w == jump(get, True)
                 and next((body[j] for j in range(i - 1, max(-1, i - 7), -1)
                           if body[j] >> 26 == 3), None) == jump(sell, True)]
        assert len(sites) == 4
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
        entitlement_table = None
        if entitlements is not None:
            base, init, load, restart = require(symbols,
                "GADGET_g_GadgetList", NativeFunctions.MOBY_INIT_MOBYS, NativeFunctions.LEVEL_LOAD_LEVEL, NativeFunctions.LEVEL_RESTART,
            )
            entitlement_table = arena + len(data)
            snapshot = bytearray(44)
            for slot, value in entitlements.items():
                if not 0 <= slot < 40 or type(value) is not bool:
                    raise ValueError("Invalid AP entitlement")
                snapshot[slot] = 2 if value else 1
            data.extend(snapshot)
            routine = arena + len(data)
            data.extend(Entitlements(p).prepare(
                address=routine, table=entitlement_table, gadget_base=base,
                fallback=init).replacement)
            for site in (load + 0x2F0, restart + 0x12C):
                assert words(p.read_bytes(site, 8)) == [jump(init, True), 0]
                init_edits.append((site, packed([jump(routine, True)])))
        assert arena + len(data) <= buy + 0x338
        edits = [(buy + 0x1F4, packed([branch(buy + 0x1F4, buy + 0x338), 0])),
                 (arena, bytes(data))]
        if locations:
            edits.extend(((buy + 0x1EC, packed([jump(setter, True)])),
                          (sell + 12, packed([jump(getter, True)]))))
            edits.extend((site, packed([jump(getter, True)])) for site in sites)
        edits.extend(init_edits)
        patches = [Patch(a, p.read_bytes(a, len(b)), b) for a, b in edits]
        plan = PatchPlan(
            patches=patches, locations=plan_locations, tables=tables, reported=reported,
            marker_address=arena, module=p.read_int32(0x206328), entitlement_table=entitlement_table,
        )
        self.patches = plan.patches
        self.plan = plan
        return plan
