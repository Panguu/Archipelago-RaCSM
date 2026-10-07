"""Native D-pad tabs, retaining the retail ammo builder and transaction paths."""
import hashlib

from ..symbols import require
from . import mips as m
from .asm import Patch, jump, packed, words
from .storage import storage_address


class VendorTabs:
    # These retail debug routines only calculate stack-local geometry/colors;
    # they never submit it. Keep their public entries as immediate returns.
    STORAGE = (
        ("DEBUGDRAW_DrawArrowFlat__FPC4VEC3T0fUiT0", 336,
         "25ca36ae2bf19eeaa01db26cd51632c721b84f2142764080363216d98399886c"),
        ("DEBUGDRAW_DrawTrigger__FPC7TriggerUi", 336,
         "82052e02601e8c1f0e5f248d6e99c648b9650570887839035fb4d8116f5f1ffe"),
        ("DEBUGDRAW_DrawCapsule__FPC4VEC3T0ffUi", 208,
         "569e75adbcc924d4026e983c89acaca56abb35aba277d6d1561316b56f0f2ea9"),
    )
    AMMO_RELOCATIONS = (0x7C, 0x84, 0x154, 0x168, 0x210, 0x23C,
                        0x248, 0x24C, 0x26C, 0x270, 0x280)
    STORAGE_CALLS = (
        ((0xFC, "__aml__5AVec3f"), (0x130, "SetARGB__7ApeRGBAUi")),
        ((0x24, "TRIGGER_GetAABB__FPC7TriggerP4VEC3T1"),
         (0x88, "TRIGGER_GetCenterPoint__FPC7TriggerP4VEC4"),
         (0xFC, "SetCenter__9ApeSphereRC5AVec3"), (0x108, "SetRadius__9ApeSpheref"),
         (0x114, "SetARGB__7ApeRGBAUi"), (0x128, "SetARGB__7ApeRGBAUi")),
        ((0x4C, "SetCenter__9ApeSphereRC5AVec3"), (0x58, "SetRadius__9ApeSpheref"),
         (0x64, "SetARGB__7ApeRGBAUi"), (0x90, "SetCenter__9ApeSphereRC5AVec3"),
         (0x9C, "SetRadius__9ApeSpheref"), (0xA8, "SetARGB__7ApeRGBAUi")),
    )
    UP, DOWN = 4, 8

    @staticmethod
    def initial_tab_routine(mode, descriptors, count, builder):
        # Use the catalog's live comparison bytes: checked, case-locked and
        # challenge-locked rows must not select an empty purchases tab.
        code = [*m.li32(m.T0, descriptors), *m.li32(m.T1, descriptors + count * 8),
                m.addiu(m.T2, m.ZERO, 1)]
        if count:
            loop = len(code)
            code += [m.lw(m.T3, 0, m.T0), m.lbu(m.T3, 0, m.T3),
                     m.lbu(m.V0, 7, m.T0)]
            found = len(code)
            code += [0, 0, m.addiu(m.T0, m.T0, 8)]
            code += [m.bne(m.T0, m.T1, loop - len(code) - 1), 0]
            done = len(code)
            code += [m.beq(m.ZERO, m.ZERO, 2), 0, m.addiu(m.T2, m.ZERO, 0)]
            code[found] = m.beq(m.T3, m.V0, done + 2 - found - 1)
        code += [*m.li32(m.T0, mode), m.sb(m.T2, 0, m.T0), jump(builder), 0]
        return packed(code)

    @staticmethod
    def split_initial_tab(code, first, second):
        instructions = words(code)
        def address(index):
            return first + index * 4 if index < 11 else second + (index - 11) * 4
        for index, word in enumerate(instructions):
            if word >> 26 in (4, 5):
                offset = word & 65535
                if offset & 32768:
                    offset -= 65536
                target = index + 1 + offset
                delta = (address(target) - address(index) - 4) // 4
                if not -32768 <= delta < 32768:
                    raise RuntimeError('Initial vendor tab branch exceeds MIPS range')
                instructions[index] = word & 0xFFFF0000 | delta & 65535
        return packed(instructions[:11] + [jump(second), 0]), packed(instructions[11:])

    @staticmethod
    def controller_address(pine, symbols):
        address = require(symbols, "CONTROLLER_GetButtonsDown__FUi")
        upper, ret, lower, nop = words(pine.read_bytes(address, 16))
        if (upper & 0xFFFF0000 != m.lui(m.V1, 0) or ret != m.jr(m.RA)
                or lower & 0xFFFF0000 != m.lw(m.V0, 0, m.V1) or nop):
            raise RuntimeError("Controller button-state getter changed")
        low = lower & 65535
        result = ((upper & 65535) << 16) + (low - 65536 if low & 32768 else low)
        if result % 4 or not 0x100000 <= result < 0x2000000 - 8:
            raise RuntimeError("Controller button-state address is invalid")
        return result

    @staticmethod
    def input_routine(mode, pressed, original, builder, dirty):
        # Read physical press edges, not analog directions or held buttons.
        # A changed tab consumes confirm for this frame, preventing a purchase
        # of the newly selected first row when Down and X arrive together.
        code = [m.addiu(m.SP, m.SP, -16), m.sd(m.RA, 0, m.SP),
                m.sw(m.A0, 8, m.SP), jump(pressed, True), 0,
                m.andi(m.V0, m.V0, 12), m.addiu(m.T1, m.ZERO, 4)]
        up = len(code)
        code += [0, m.addiu(m.T2, m.ZERO, 0), m.addiu(m.T1, m.ZERO, 8)]
        other = len(code)
        code += [0, m.addiu(m.T2, m.ZERO, 1)]
        check = len(code)
        code += [*m.li32(m.T0, mode), m.lbu(m.T1, 0, m.T0)]
        same = len(code)
        code += [0, 0, m.sb(m.T2, 0, m.T0), jump(builder, True), 0,
                 *m.li32(m.T0, dirty), m.addiu(m.T1, m.ZERO, 1),
                 m.sb(m.T1, 0, m.T0), m.ld(m.RA, 0, m.SP),
                 m.addiu(m.SP, m.SP, 16), m.jr(m.RA), m.addu(m.V0, m.ZERO, m.ZERO)]
        normal = len(code)
        code += [m.lw(m.A0, 8, m.SP), m.ld(m.RA, 0, m.SP),
                 jump(original), m.addiu(m.SP, m.SP, 16)]
        code[up] = m.beq(m.V0, m.T1, check - up - 1)
        code[other] = m.bne(m.V0, m.T1, normal - other - 1)
        code[same] = m.beq(m.T1, m.T2, normal - same - 1)
        return packed(code)

    @classmethod
    def relocate_ammo(cls, original, destinations, tail):
        # Split only between complete instructions AND their delay slots.
        # All retail JALs retain their original absolute targets. Relative
        # branches must be remapped even when they cross the two pieces.
        pieces = ((0x70, 0x178), (0x178, 0x284))
        normalized = words(original[0x70:0x284])
        for index, word in enumerate(normalized):
            if word >> 26 == 3:
                normalized[index] = 0x0C000000
            elif 0x70 + index * 4 in cls.AMMO_RELOCATIONS:
                normalized[index] &= 0xFFFF0000
        if hashlib.sha256(packed(normalized)).hexdigest() != (
                "65b3f0cbbcbf7c13089236225da7c825b9397a2e46cf48975cb1ede63b2afb0f"):
            raise RuntimeError("Native vendor ammo builder changed")

        def relocated(offset):
            if offset == 0x284:
                return destinations[1] + 0x284 - 0x178
            for (start, end), destination in zip(pieces, destinations):
                if start <= offset < end:
                    return destination + offset - start
            raise RuntimeError("Ammo branch leaves the verified builder")

        result = []
        for (start, end), destination in zip(pieces, destinations):
            code = words(original[start:end])
            for index, word in enumerate(code):
                op = word >> 26
                if op in (1, 4, 5, 6, 7, 20, 21, 22, 23) or (op == 17 and word >> 21 & 31 == 8):
                    immediate = word & 65535
                    signed = immediate - 65536 if immediate & 32768 else immediate
                    target = relocated(start + index * 4 + 4 + signed * 4)
                    delta = (target - (destination + index * 4 + 4)) // 4
                    if not -32768 <= delta < 32768:
                        raise RuntimeError("Relocated ammo branch exceeds MIPS range")
                    code[index] = word & 0xFFFF0000 | delta & 65535
            code += [jump(tail if end == 0x284 else relocated(end)), 0]
            result.append(packed(code))
        return result

    def prepare(self, pine, symbols, hooks, builder, original, catalog, descriptors=0, count=0):
        patches, ranges = [], []
        self.buttons_address = self.controller_address(pine, symbols)
        for offset, name in ((0x8C, "GADGET_IsGadgetOfChar__F8PLR_TYPE7eGADGET"),
                             (0x9C, "GADGET_PlayerHasGadget__FUi"),
                             (0xAC, "GADGET_PlayerHasButItIsHidden__FUi"),
                             (0xC4, "GADGET_GetData__FUi"), (0xD0, "GADGET_GetDataDef__FUi"),
                             (0x144, "PAUSEMODE_GetCurrentPauseScreen__Fv"),
                             (0x220, "ICONMENU_AddItem__FP9tICONMENUUiUiUiUiUiUi"),
                             (0x264, "ICONMENU_AddItem__FP9tICONMENUUiUiUiUiUiUi")):
            if words(original[offset:offset + 4]) != [jump(require(symbols, name), True)]:
                raise RuntimeError("Native vendor ammo call changed")
        if original[0x1B0:0x1B4] != original[0x1F8:0x1FC]:
            raise RuntimeError("Native vendor ammo conversion changed")
        for (name, size, digest), calls in zip(self.STORAGE, self.STORAGE_CALLS):
            address = require(symbols, name)
            native = pine.read_bytes(address, size)
            normalized = packed([0x0C000000 if w >> 26 == 3 else w for w in words(native)])
            if hashlib.sha256(normalized).hexdigest() != digest:
                raise RuntimeError(f"Vendor tab storage changed: {name}")
            if any(words(native[offset:offset + 4]) != [jump(require(symbols, target), True)]
                   for offset, target in calls):
                raise RuntimeError(f"Vendor tab storage calls changed: {name}")
            if any(address < p.address + len(p.replacement) and p.address < address + size
                   for p in hooks.patches):
                raise RuntimeError("Vendor tab storage is occupied")
            patches.append(Patch(address, native[:8], packed([m.jr(m.RA), 0])))
            ranges.append((address + 8, address + size))

        def reserve(address, code):
            patches.append(Patch(address, pine.read_bytes(address, len(code)), code))
            return address

        def allocate(code):
            address = storage_address(ranges, patches, len(code))
            if address is None:
                raise RuntimeError("Vendor tabs exceed verified storage")
            return reserve(address, code)

        ammo = (ranges[0][0], ranges[1][0])
        for address, code in zip(ammo, self.relocate_ammo(original, ammo, builder + 0x738)):
            reserve(address, code)
        self.mode_address = allocate(bytes(4))
        mode = self.mode_address
        dispatch = allocate(packed([*m.li32(m.T0, mode), m.lbu(m.T0, 0, m.T0),
                                   m.beq(m.T0, m.ZERO, 3), 0, jump(ammo[0]), 0,
                                   jump(catalog), 0]))
        browse, init, pressed, analog = require(symbols, "SCRNVENDOR_UpdateBrowseState__Fv",
            "SCRNVENDOR_Init__Fv", "CONTROLLER_GetButtonsPressed__FUi",
            "CONTROLLER_GetButtonsPressedWithAnalog__FUi")
        if (pine.read_bytes(browse + 0x18, 8) != packed([jump(analog, True), 0x240416C4])
                or pine.read_bytes(init + 0x5C, 8) != packed([jump(builder, True), 0])):
            raise RuntimeError("Vendor tab input/init call changed")
        upper, lower = pine.read_int32(init + 0x2C), pine.read_int32(init + 0x38)
        if upper & 0xFFFF0000 != m.lui(m.V1, 0) or lower & 0xFFFF0000 != m.sb(m.V0, 0, m.V1):
            raise RuntimeError("Vendor selection refresh flag changed")
        low = lower & 65535
        dirty = ((upper & 65535) << 16) + (low - 65536 if low & 32768 else low)
        self.input_address = allocate(self.input_routine(mode, pressed, analog, builder, dirty))
        initial = self.initial_tab_routine(mode, descriptors, count, builder)
        if count:
            # Fit around the two relocated ammo pieces without consuming the
            # catalog row buffer. Split after ADDIU, never in a delay slot.
            reset = allocate(bytes(52))
            continuation = allocate(bytes(len(initial) - 44))
            first, second = self.split_initial_tab(initial, reset, continuation)
            for address, body in ((reset, first), (continuation, second)):
                index = next(i for i, patch in enumerate(patches) if patch.address == address)
                patches[index] = Patch(address, patches[index].original, body)
        else:
            reset = allocate(initial)
        reserve(browse + 0x18, packed([jump(self.input_address, True)]))
        reserve(init + 0x5C, packed([jump(reset, True)]))
        hooks.extra_ranges.extend(ranges)
        return patches, packed([jump(dispatch), 0])
