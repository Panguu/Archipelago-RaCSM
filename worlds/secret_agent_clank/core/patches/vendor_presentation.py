"""Vendor reward text hooks installed with the other native patches."""
import struct
import hashlib

from ..notifications import ItemNotifications
from ..symbols import require
from . import mips as m
from .asm import Patch, jump, packed
from .patch import PatchSet
from .vendor_text_preview import VendorTextPreview


def triangle_storage(pine, symbols):
    # Retail DrawTriangle only transforms local stack vertices and sets a
    # local color; it never submits geometry. Guard its complete body,
    # including every instruction except relocated JAL destinations.
    storage = require(symbols, "DEBUGDRAW_DrawTriangle__FPC4VEC3N20UiPC7MATRIX4")
    storage_original = pine.read_bytes(storage, 352)
    words = struct.unpack("<88I", storage_original)
    normalized = packed([0x0C000000 if word >> 26 == 3 else word for word in words])
    if hashlib.sha256(normalized).hexdigest() != "572b00ad8dd163d5fb2c33d751223e56928bf4186bf2960640ae82a88e1bc37f":
        raise RuntimeError("Vendor debug storage layout changed")
    if not (words[14] == words[18] == words[22] and words[49] == words[78]):
        raise RuntimeError("Vendor debug storage calls changed")
    return storage, storage_original


class VendorPresentation(PatchSet):
    def __init__(self, pine):
        super().__init__(pine)
        self.mailbox = self.timer = None

    @staticmethod
    def routine(mailbox, encoded):
        # T3 is the original draw target, T4 the text offset, supplied by
        # the two tiny entry stubs. Both share the identity validation.
        code = [*m.li32(m.T0, mailbox)]
        branches = []
        for i, native_offset in enumerate((None, 0x0C, 0x10, 0x14)):
            code.append(m.lw(m.T1, i * 4, m.T0))
            if native_offset is not None:
                code.append(m.lw(m.T2, native_offset, m.S5))
            branches.append(len(code))
            code += [0, m.NOP]
        code += [m.addu(m.T0, m.T0, m.T4), m.sw(m.T0, 0x14, m.A0),
                 m.lui(m.T2, (encoded + 0x8000) >> 16), m.addiu(m.T1, m.ZERO, 1),
                 m.sb(m.T1, encoded & 65535, m.T2)]
        fallback = len(code)
        code += [m.jr(m.T3), m.NOP]
        for index, site in enumerate(branches):
            code[site] = m.bne(m.T1, m.S5 if index == 0 else m.T2, fallback - site - 1)
        return packed(code)

    def prepare(self, symbols, hooks):
        self.patches = []
        self.mailbox = self.timer = None
        notifications = ItemNotifications(self.pine)
        if not notifications.bind(symbols):
            raise RuntimeError("Vendor notification buffer layout changed")
        mailbox, timer, *_ = notifications.binding
        render, title, description, encoded = require(symbols, "SCRNVENDOR_Render__Fv",
            "HUD_FontPrintWindowAreaScaledXY__FP20tFontPrintWindowDataff",
            "HUD_FontPrintWindowArea__FP20tFontPrintWindowData", "HUD_SetUseEncodedTextColorTo__Fb")
        w = struct.unpack("<3I", self.pine.read_bytes(encoded, 12))
        if w[0] & 0xFFFF0000 != 0x3C020000 or w[1] != 0x03E00008 or w[2] & 0xFFFF0000 != 0xA0440000:
            raise RuntimeError("Vendor encoded color switch changed")
        low = w[2] & 65535
        encoded = ((w[0] & 65535) << 16) + (low - 65536 if low & 32768 else low)
        storage, storage_original = triangle_storage(self.pine, symbols)
        if any(storage < patch.address + len(patch.replacement) and patch.address < storage + 352
               for patch in hooks.patches):
            raise RuntimeError("Vendor debug storage is already occupied")
        body = bytearray(packed([m.jr(m.RA), m.NOP]))
        common = storage + len(body)
        body.extend(self.routine(mailbox, encoded))
        def reserve(code):
            address = storage + len(body)
            body.extend(code)
            return address
        for sites, offset, target in ((VendorTextPreview.TITLE_CALLS, 16, title),
                                     ((VendorTextPreview.DESCRIPTION_CALL,), 104, description)):
            address = reserve(packed([*m.li32(m.T3, target), jump(common), m.addiu(m.T4, m.ZERO, offset)]))
            for site in sites:
                original = packed([jump(target, True)])
                if self.pine.read_bytes(render + site, 4) != original:
                    raise RuntimeError("Vendor text draw call changed")
                self.patches.append(Patch(render + site, original, packed([jump(address, True)])))
        if len(body) > 352:
            raise RuntimeError("Vendor text exceeds verified storage")
        self.patches.insert(0, Patch(storage, storage_original[:len(body)], bytes(body)))
        self.mailbox, self.timer = mailbox, timer
        return self.patches

    def publish(self, pointer, row, reward):
        if self.mailbox is None or self.pine.read_int32(self.timer):
            return
        # Withdraw first; native render can only see the new payload after commit.
        self.pine.write_int32(self.mailbox, 0)
        if reward is None:
            return
        text = VendorTextPreview._text(reward.item_name, 88, 2 if reward.progression else 1)
        text += VendorTextPreview._text("For " + reward.recipient_name + "\nArchipelago reward", 152)
        self.pine.write_bytes(self.mailbox + 4, struct.pack("<3I", row.node_type, row.weapon_id, row.mod_id) + text)
        self.pine.write_int32(self.mailbox, pointer)
