"""Reversible native-row insertion probe; purchases are disabled during preview."""
import struct

from ...constants.native_functions import NativeFunctions
from ..symbols import require
from ..vendor import VendorState
from .asm import Patch, branch, packed
from .patch import PatchSet
from .vendor_only import VendorOnly
from .weapon_pickup import WeaponPickup


class VendorOfferPreview(PatchSet):
    ROW_SIZE = 0x1C
    HEADER_SIZE = 0x68
    STORAGE_START = 0x60
    STORAGE_END = 0x278
    RETURN = packed([0x03E00008, 0])
    PURCHASE_PROLOGUE = packed([0x27BDFFC0, 0xFFB00000])

    def __init__(self, pine):
        super().__init__(pine)
        self.vendor = VendorState(pine)
        self.module = None
        self.installed = False
        self.header = self.buffer = None
        self.count = 0

    def prepare(self, symbols, *, source_index):
        """Clone one valid offer into bounded, signature-verified shadow storage."""
        if self.installed:
            raise RuntimeError("Restore the existing preview first")
        self.patches = []
        if self.pine.get_game_id() != "SCUS-97623":
            raise RuntimeError("Unsupported game")
        if not self.vendor.bind_runtime(symbols) or not self.vendor.active:
            raise RuntimeError("Open a native weapon vendor with the SAC client closed")
        module = self.pine.read_int32(0x206328)
        if self.pine.read_int32(0x206324) != 0xFFFFFFFF:
            raise RuntimeError("Cannot preview during level travel")
        header = self.vendor._native_header()
        if header is None:
            raise RuntimeError("Invalid vendor header")
        pointer, count, selected = header
        if type(source_index) is not int or not 0 <= source_index < count:
            raise ValueError("Choose an existing vendor row")
        give = symbols.get(NativeFunctions.WEAPON_PICKUP_GIVE_WEAPON)
        buy = require(symbols, NativeFunctions.SCRNVENDOR_PROCESS_PURCHASE)
        bypass = []
        if give is not None:
            WeaponPickup(self.pine).prepare(
                symbols, give, pickup_locations={}, vendor_locations={},
                checked=(), entitlements=None)
            buffer, storage_end = give + self.STORAGE_START, give + self.STORAGE_END
            bypass.append(Patch(give + 0x58, self.pine.read_bytes(give + 0x58, 8),
                                packed([branch(give + 0x58, storage_end), 0])))
        else:
            VendorOnly(self.pine).prepare(symbols, {}, (), None)
            # Purchase returns at its entry for the entire preview. Its internal
            # mod/Titan/base grant blocks cannot run while used as shadow rows.
            buffer, storage_end = buy + 0x10C, buy + 0x338
        if self.pine.read_bytes(buy, 8) != self.PURCHASE_PROLOGUE:
            raise RuntimeError("Vendor purchase entry changed; close the SAC client")
        capacity = (storage_end - buffer) // self.ROW_SIZE
        if count + 1 > capacity:
            raise RuntimeError(f"Preview storage holds {capacity} rows; vendor already has {count}")
        rows = self.pine.read_bytes(pointer, count * self.ROW_SIZE)
        if len(rows) != count * self.ROW_SIZE:
            raise RuntimeError("Incomplete vendor row read")
        for i in range(count):
            active, _, _, kind, weapon, _mod, _extra = struct.unpack_from(
                "<7I", rows, i * self.ROW_SIZE)
            if active != 1 or kind not in (0, 1, 2, 3, 4):
                raise RuntimeError("Vendor contains an unverified row type")
        payload = rows + rows[source_index * self.ROW_SIZE:(source_index + 1) * self.ROW_SIZE]
        if self.vendor._native_header() != header:
            raise RuntimeError("Vendor changed during preparation")
        self.module, self.header = module, self.vendor.header_addr
        self.buffer, self.count = buffer, count + 1
        self.patches = [
            Patch(buy, self.PURCHASE_PROLOGUE, self.RETURN),
            *bypass,
            Patch(self.buffer, self.pine.read_bytes(self.buffer, len(payload)), payload),
            Patch(self.header, struct.pack("<2I", pointer, count),
                  struct.pack("<2I", self.buffer, self.count)),
        ]
        return self.patches

    def _check_context(self):
        if (self.pine.get_game_id() != "SCUS-97623"
                or self.pine.read_int32(0x206328) != self.module
                or self.pine.read_int32(0x206324) != 0xFFFFFFFF
                or not self.vendor.active):
            raise RuntimeError("Preview context changed; refusing stale vendor writes")

    def apply(self):
        self._check_context()
        if self.installed:
            raise RuntimeError("Preview already installed")
        super().apply()
        self.installed = True

    def read(self):
        """Read preview rows; does not report purchases or AP checks."""
        self._check_context()
        return self.vendor.read_items()

    def restore(self):
        """Remove the shadow list before restoring its storage and purchase entry."""
        if not self.installed:
            return
        self._check_context()
        for patch in self.patches:
            if self.pine.read_bytes(patch.address, len(patch.replacement)) != patch.replacement:
                raise RuntimeError("Preview was replaced; refusing to overwrite changed memory")
        # Restore selection before shrinking the count if the new row was selected.
        original_count = struct.unpack("<2I", self.patches[-1].original)[1]
        selected = self.pine.read_int32(self.header + 12)
        if selected >= original_count:
            self.pine.write_bytes(self.header + 12, struct.pack("<I", original_count - 1))
        for patch in reversed(self.patches):
            self.pine.write_bytes(patch.address, patch.original)
            if self.pine.read_bytes(patch.address, len(patch.original)) != patch.original:
                raise RuntimeError("Preview restoration readback failed")
        self.installed = False
