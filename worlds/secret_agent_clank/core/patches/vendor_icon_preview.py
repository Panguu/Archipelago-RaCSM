"""Temporary replacement of the verified 32x32 Shock Rocket icon."""
import struct

from ..symbols import require
from ..vendor import VendorState
from .asm import Patch
from .patch import PatchSet


class VendorIconPreview(PatchSet):
    ICON_ID = 73
    IMAGE_SIZE = 1024
    PALETTE_SIZE = 1024

    def __init__(self, pine):
        super().__init__(pine)
        self.vendor = VendorState(pine)
        self.module = self.texture_slot = self.texture = self.cache = None
        self.installed = False

    def prepare(self, symbols, *, indices, palette, selected_only=True):
        if self.installed:
            raise RuntimeError("Restore the previous icon test first")
        self.patches = []
        if len(indices) != self.IMAGE_SIZE or len(palette) != self.PALETTE_SIZE:
            raise ValueError("Icon requires 1024 index bytes and 1024 palette bytes")
        if not self.vendor.bind_runtime(symbols) or not self.vendor.active:
            raise RuntimeError("Open a vendor with the SAC client closed")
        row = self.vendor.selected_item()
        if selected_only and (row is None or row.icon != self.ICON_ID):
            raise RuntimeError("Highlight Shock Rocket for the verified icon test")
        self.module = self.pine.read_int32(0x206328)
        lookup, invalidate = require(symbols, "GetIconTextureID__14DrawObjManagerUi",
                                     "aglPs2VramInvalidate__Fv")
        w = struct.unpack("<6I", self.pine.read_bytes(lookup, 24))
        if (w[0] & 0xFFFF0000 != 0x3C030000 or w[1] != 0x000420C0
                or w[2] & 0xFFFF0000 != 0x24630000
                or w[3:] != (0x00641821, 0x03E00008, 0x8C620004)):
            raise RuntimeError("Native icon lookup changed")
        low = w[2] & 65535
        table = ((w[0] & 65535) << 16) + (low-65536 if low & 32768 else low)
        self.texture_slot = table + self.ICON_ID*8 + 4
        self.texture = self.pine.read_int32(self.texture_slot)
        if not 0x100000 <= self.texture < 0x1FFFF00:
            raise RuntimeError("Invalid icon texture object")
        data = self.pine.read_bytes(self.texture, 0xA8)
        if (data[0x10:0x30].split(b"\0", 1)[0] != b"weapon_shockrocket.tga"
                or struct.unpack_from("<I", data, 0x34)[0] != 0x00200020
                or struct.unpack_from("<I", data, 0x64)[0] != 0x93010020
                or struct.unpack_from("<I", data, 0xA4)[0] != 0x80000010):
            raise RuntimeError("Shock Rocket texture format changed")
        image = struct.unpack_from("<I", data, 0x58)[0]
        clut = struct.unpack_from("<I", data, 0x98)[0]
        if not 0x100000 <= image < 0x1FFF800 or clut != image+1024:
            raise RuntimeError("Native icon pixel allocation changed")
        w = struct.unpack("<3I", self.pine.read_bytes(invalidate, 12))
        if w[0] & 0xFFFF0000 != 0x3C020000 or w[1] != 0x03E00008 or w[2] & 0xFFFF0000 != 0xAC400000:
            raise RuntimeError("VRAM invalidation routine changed")
        low = w[2] & 65535
        self.cache = ((w[0] & 65535) << 16) + (low-65536 if low & 32768 else low)
        self.patches = [Patch(image, self.pine.read_bytes(image,1024), bytes(indices)),
                        Patch(clut, self.pine.read_bytes(clut,1024), bytes(palette))]
        return self.patches

    def _check_context(self):
        if (self.pine.get_game_id() != "SCUS-97623"
                or self.pine.read_int32(0x206328) != self.module
                or self.pine.read_int32(0x206324) != 0xFFFFFFFF
                or self.pine.read_int32(self.texture_slot) != self.texture):
            raise RuntimeError("Icon preview context changed")

    def apply(self):
        self._check_context()
        if self.installed:
            raise RuntimeError("Icon preview already installed")
        super().apply()
        self.installed = True
        self.pine.write_int32(self.cache, 0)

    def restore(self):
        if not self.installed:
            return
        self._check_context()
        for patch in self.patches:
            if self.pine.read_bytes(patch.address,len(patch.replacement)) != patch.replacement:
                raise RuntimeError("Icon pixels changed; refusing stale restoration")
        for patch in reversed(self.patches):
            self.pine.write_bytes(patch.address,patch.original)
            if self.pine.read_bytes(patch.address,len(patch.original)) != patch.original:
                raise RuntimeError("Icon restoration failed")
        self.pine.write_int32(self.cache,0)
        self.installed = False
