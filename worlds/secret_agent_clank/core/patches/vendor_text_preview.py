"""Reversible selected-offer text preview using native vendor font windows."""
import struct

from ..notifications import ItemNotifications
from ..symbols import require
from ..vendor import VendorState
from . import mips as m
from .asm import Patch, jump, packed
from .gain_storage import GainStorage
from .patch import PatchSet


class VendorTextPreview(PatchSet):
    TITLE_CALLS = (0x3FC, 0x464, 0x4CC)
    DESCRIPTION_CALL = 0x5FC
    TITLE_OFFSET = 8
    DESCRIPTION_OFFSET = 104

    def __init__(self, pine):
        super().__init__(pine)
        self.vendor = VendorState(pine)
        self.module = None
        self.installed = False

    @staticmethod
    def _text(value, capacity, color=None):
        clean = "".join(c if 32 <= ord(c) < 127 or c == "\n" else "?" for c in value)
        prefix = bytes((0x90, color)) if color is not None else b""
        suffix = b"\x90\x01" if color is not None else b""
        content = clean.encode("ascii")[:capacity-len(prefix)-len(suffix)-1]
        return (prefix + content + suffix).ljust(capacity, b"\0")

    @staticmethod
    def _routine(mailbox, offset, target, encoded_flag=None):
        enable = []
        if encoded_flag is not None:
            high = (encoded_flag + 0x8000) >> 16
            enable = [m.lui(m.T2, high), m.addiu(m.T1, m.ZERO, 1),
                      m.sb(m.T1, encoded_flag & 0xFFFF, m.T2)]
        return packed([
            *m.li32(m.T0, mailbox), m.lw(m.T1, 0, m.T0),
            m.bne(m.T1, m.S5, 2 + len(enable)), m.addiu(m.T0, m.T0, offset),
            m.sw(m.T0, 0x14, m.A0), *enable, jump(target), m.NOP])

    def prepare(self, symbols, *, title, description, progression=False):
        if self.installed:
            raise RuntimeError("Restore the existing text preview first")
        self.patches = []
        if not self.vendor.bind_runtime(symbols) or not self.vendor.active:
            raise RuntimeError("Open a vendor with the SAC client closed")
        if self.pine.get_game_id() != "SCUS-97623":
            raise RuntimeError("Unsupported game")
        self.module = self.pine.read_int32(0x206328)
        header = self.vendor._native_header()
        if header is None or not header[1]:
            raise RuntimeError("No selected vendor offer")
        selected = self.vendor.selected_item()
        if selected.node_type not in (0, 3, 4):
            raise RuntimeError("Select a weapon, mod or Titan check")
        notifications = ItemNotifications(self.pine)
        if not notifications.bind(symbols):
            raise RuntimeError("Native text buffer signature changed")
        mailbox, timer, cooldown, *_ = notifications.binding
        if self.pine.read_int32(timer):
            raise RuntimeError("Wait for native HUD notifications to finish")
        render, title_draw, description_draw = require(
            symbols, "SCRNVENDOR_Render__Fv",
            "HUD_FontPrintWindowAreaScaledXY__FP20tFontPrintWindowDataff",
            "HUD_FontPrintWindowArea__FP20tFontPrintWindowData")
        set_encoded = require(symbols, "HUD_SetUseEncodedTextColorTo__Fb")
        words = struct.unpack("<3I", self.pine.read_bytes(set_encoded, 12))
        if (words[0] & 0xFFFF0000 != 0x3C020000 or words[1] != 0x03E00008
                or words[2] & 0xFFFF0000 != 0xA0440000):
            raise RuntimeError("Native encoded text switch changed")
        low = words[2] & 0xFFFF
        encoded_flag = ((words[0] & 0xFFFF) << 16) + (low-65536 if low & 32768 else low)
        guards, ranges = GainStorage(self.pine).prepare(symbols)
        routines = []
        calls = []
        for offsets, offset, target, region in (
                (self.TITLE_CALLS, self.TITLE_OFFSET, title_draw, ranges[1]),
                ((self.DESCRIPTION_CALL,), self.DESCRIPTION_OFFSET, description_draw, ranges[0])):
            code = self._routine(mailbox, offset, target,
                                 encoded_flag if offset == self.TITLE_OFFSET else None)
            if len(code) > region[1] - region[0]:
                raise RuntimeError("Insufficient verified text hook storage")
            routines.append(Patch(region[0], self.pine.read_bytes(region[0], len(code)), code))
            for site_offset in offsets:
                site = render + site_offset
                if self.pine.read_int32(site) != jump(target, True):
                    raise RuntimeError("Vendor text call changed")
                calls.append(Patch(site, packed([jump(target, True)]),
                                   packed([jump(region[0], True)])))
        pointer, count, selected_index = header
        payload = struct.pack("<2I", pointer + selected_index * 0x1C, 0)
        payload += self._text(title, 96, color=2 if progression else 1) + self._text(description, 152)
        self.patches = guards + routines + [
            Patch(mailbox, self.pine.read_bytes(mailbox, 256), payload)] + calls
        return self.patches

    def _check_context(self):
        if (self.pine.get_game_id() != "SCUS-97623"
                or self.pine.read_int32(0x206328) != self.module
                or self.pine.read_int32(0x206324) != 0xFFFFFFFF
                or not self.vendor.active):
            raise RuntimeError("Vendor text preview context changed")

    def apply(self):
        self._check_context()
        if self.installed:
            raise RuntimeError("Text preview already installed")
        super().apply()
        self.installed = True

    def restore(self):
        if not self.installed:
            return
        self._check_context()
        for patch in self.patches:
            if self.pine.read_bytes(patch.address, len(patch.replacement)) != patch.replacement:
                raise RuntimeError("Text preview was changed; refusing stale restoration")
        for patch in reversed(self.patches):
            self.pine.write_bytes(patch.address, patch.original)
            if self.pine.read_bytes(patch.address, len(patch.original)) != patch.original:
                raise RuntimeError("Text preview restoration failed")
        self.installed = False
