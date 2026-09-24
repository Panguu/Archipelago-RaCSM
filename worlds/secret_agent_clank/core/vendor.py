"""Native vendor rows and the pause-screen selector."""
import struct
from collections.abc import Sequence
from typing import TYPE_CHECKING, NamedTuple

from .address_maps.ps2 import (
    _ITEM_OFFSET_ACTIVE,
    _ITEM_OFFSET_ICON,
    _ITEM_OFFSET_MOD_ID,
    _ITEM_OFFSET_NODE_TYPE,
    _ITEM_OFFSET_WEAPON_ID,
    VENDOR_ITEM_MAX_COUNT,
    VENDOR_ITEM_STRIDE,
)
from .inventories.weapons import WEAPON_ORDER

if TYPE_CHECKING:
    from ..pypine import Pine

# Node type for a base-weapon-for-sale offer, per FUN_003d2b28's other call
# sites (0=weapon, 2=ammo bundle, 3=mod [CONFIRMED live, see write_item()'s
# default], 4=titan weapon) -- 0's own icon/field conventions are NOT yet
# live-verified (see module docstring point 3), this is a best-effort
# placeholder pending confirmation.
WEAPON_OFFER_NODE_TYPE = 0
# Icon value for a forced weapon-for-sale row -- reuses write_item()'s
# existing default (the one CONFIRMED icon value, seen on node_type=3 mod
# rows) since node_type=0's real icon convention is unknown. Cosmetic only
# (doesn't affect the purchase mechanism itself) -- update once a real
# node_type=0 row has been captured live.
DEFAULT_WEAPON_ICON = 51


class VendorOffer(NamedTuple):
    """One entry in a force_roster() call -- weapon_name must be a WEAPON_ORDER name (== a constants/weapons.py RATCHET_WEAPONS entry)."""
    weapon_name: str
    mod_id: int = 0
    node_type: int = WEAPON_OFFER_NODE_TYPE
    icon: int = DEFAULT_WEAPON_ICON


class VendorItem(NamedTuple):
    """One live row read out of the vendor's real item array (see read_items() below)."""
    index: int
    node_type: int
    icon: int
    weapon_id: int
    weapon_name: str | None
    mod_id: int


class VendorSnapshot(NamedTuple):
    rows: tuple[VendorItem, ...]
    selected_index: int
    price: int
    bolts: int
    purchase_flag: int


def purchased_base_item(before: VendorSnapshot, after: VendorSnapshot) -> str | None:
    """Require a paid, disappearing base-item offer; inventory is not evidence."""
    row = next((r for r in before.rows if r.index == before.selected_index), None)
    if row is None or row.node_type != 0 or row.weapon_name is None:
        return None
    if before.price <= 0 or before.bolts - after.bolts != before.price or after.purchase_flag != 1:
        return None
    if any(r.node_type == 0 and r.weapon_id == row.weapon_id for r in after.rows):
        return None
    return row.weapon_name


class VendorState:

    def __init__(self, pine: "Pine") -> None:
        self.pine = pine
        self.menu_addr: int | None = None
        self.items_addr: int | None = None
        self.header_addr: int | None = None
        self.price_addr: int | None = None
        self.purchase_flag_addr: int | None = None
        self._previous_snapshot: VendorSnapshot | None = None

    def set_addr(self, menu_addr: int | None, items_addr: int | None = None) -> None:
        """Rebind to the current case's derived addresses (CaseAddresses.menu and .vendor_items) -- called from core/planets.py's CaseInventory.set_case() the same way every other per-case accessor is rebound."""
        self.menu_addr = menu_addr
        self.items_addr = items_addr
        self.header_addr = self.price_addr = self.purchase_flag_addr = None
        self._previous_snapshot = None

    def poll_purchases(self) -> list[str]:
        """Read the native transaction before Core applies AP entitlements."""
        if not self.active or self.header_addr is None or self.price_addr is None or self.purchase_flag_addr is None:
            self._previous_snapshot = None
            return []
        header = self._native_header()
        if header is None:
            return []
        rows = tuple(self.read_items())
        if len(rows) != header[1]:
            return []
        snapshot = VendorSnapshot(rows, header[2], self.pine.read_int32(self.price_addr),
                                  self.pine.read_int32(0x2075C8), self.pine.read_int8(self.purchase_flag_addr))
        if self._native_header() != header:
            return []  # Menu changed during the read; retain the earlier baseline.
        previous = self._previous_snapshot
        self._previous_snapshot = snapshot
        if previous is None:
            return []
        name = purchased_base_item(previous, snapshot)
        return [name] if name is not None else []

    def bind_runtime(self, symbols) -> bool:
        """Resolve native vendor globals from a signature-checked purchase prologue."""
        pause = symbols.get("g_PauseModeData")
        self.set_addr(pause + 12 if pause else None)
        function = symbols.get("SCRNVENDOR_ProcessPurchase__Fv")
        if function is None:
            return False
        words = struct.unpack("<27I", self.pine.read_bytes(function, 108))
        pairs = ((8, 24, 0x3C100000, 0x26100000),
                 (72, 88, 0x3C070000, 0x8CE30000),
                 (76, 104, 0x3C080000, 0xA1050000))
        addresses = []
        for upper_offset, lower_offset, upper_opcode, lower_opcode in pairs:
            upper, lower = words[upper_offset // 4], words[lower_offset // 4]
            if upper & 0xFFFF0000 != upper_opcode or lower & 0xFFFF0000 != lower_opcode:
                return False
            immediate = lower & 0xFFFF
            if immediate & 0x8000:
                immediate -= 0x10000
            address = ((upper & 0xFFFF) << 16) + immediate
            if not 0x100000 <= address < 0x2000000 - 16:
                return False
            addresses.append(address)
        self.header_addr, self.price_addr, self.purchase_flag_addr = addresses
        return True

    def _native_header(self) -> tuple[int, int, int] | None:
        if self.header_addr is None or not self.active:
            return None
        pointer, count, _columns, selected = struct.unpack(
            "<4I", self.pine.read_bytes(self.header_addr, 16))
        if count == 0:
            return pointer, count, selected
        if not (0 < count <= VENDOR_ITEM_MAX_COUNT and selected < count
                and 0x100000 <= pointer < 0x2000000 - count * VENDOR_ITEM_STRIDE
                and pointer % 4 == 0):
            return None
        return pointer, count, selected

    def selected_item(self) -> VendorItem | None:
        header = self._native_header()
        if header is None:
            return None
        return next((row for row in self.read_items() if row.index == header[2]), None)

    @property
    def state(self) -> int:
        """32-bit native pause-screen enum; zero when unbound."""
        if self.menu_addr is None:
            return 0
        return self.pine.read_int32(self.menu_addr)

    @property
    def active(self) -> bool:
        """Whether the native weapon vendor is the active pause screen."""
        return self.state in (8, 16)

    # Field order used to lay out both the batched read in read_items() and
    # the batched write in write_item() -- keep these in sync with each
    # other (index math below assumes this exact order/length).
    _FIELDS = (
        _ITEM_OFFSET_ACTIVE, _ITEM_OFFSET_ICON, _ITEM_OFFSET_NODE_TYPE,
        _ITEM_OFFSET_WEAPON_ID, _ITEM_OFFSET_MOD_ID,
    )

    def read_items(self) -> list[VendorItem]:
        """Read only populated native rows while the bound vendor is open."""
        count = VENDOR_ITEM_MAX_COUNT
        if self.header_addr is not None:
            header = self._native_header()
            if header is None:
                return []
            self.items_addr, count, _selected = header
            if count == 0:
                return []
        if self.items_addr is None:
            return []
        addrs = [
            self.items_addr + i * VENDOR_ITEM_STRIDE + field_offset
            for i in range(count)
            for field_offset in self._FIELDS
        ]
        values = self.pine.batch_read_int32(addrs)
        n = len(self._FIELDS)
        items: list[VendorItem] = []
        for i in range(count):
            active, icon, node_type, weapon_id, mod_id = values[i * n:(i + 1) * n]
            if not active:
                break
            weapon_name = (
                WEAPON_ORDER[weapon_id]
                if 0 <= weapon_id < len(WEAPON_ORDER) else None
            )
            items.append(VendorItem(
                index=i, node_type=node_type, icon=icon,
                weapon_id=weapon_id, weapon_name=weapon_name, mod_id=mod_id,
            ))
        return items

    def write_item(
        self,
        index: int,
        weapon_id: int,
        mod_id: int = 0,
        node_type: int = 3,
        icon: int = 51,
        active: bool = True,
    ) -> None:
        if self.header_addr is not None:
            header = self._native_header()
            if header is None:
                return
            self.items_addr, count, _selected = header
            if not 0 <= index < count:
                raise ValueError("Native vendor capacity is unverified; only existing rows may be edited")
        if self.items_addr is None:
            return
        if not (0 <= index < VENDOR_ITEM_MAX_COUNT):
            raise ValueError(f"index must be 0-{VENDOR_ITEM_MAX_COUNT - 1}, got {index}")
        base = self.items_addr + index * VENDOR_ITEM_STRIDE
        values = (1 if active else 0, icon, node_type, weapon_id, mod_id)
        self.pine.batch_write_int32(list(zip(
            (base + off for off in self._FIELDS), values,
        )))

    def force_roster(self, offers: Sequence["VendorOffer"]) -> None:
        if self.items_addr is None or not offers:
            return
        current = self.read_items()
        existing_ids = {item.weapon_id for item in current}
        index = len(current)
        for offer in offers:
            if index >= VENDOR_ITEM_MAX_COUNT:
                break
            if offer.weapon_name not in WEAPON_ORDER:
                continue
            weapon_id = WEAPON_ORDER.index(offer.weapon_name)
            if weapon_id in existing_ids:
                continue
            self.write_item(
                index, weapon_id, mod_id=offer.mod_id,
                node_type=offer.node_type, icon=offer.icon,
            )
            existing_ids.add(weapon_id)
            index += 1

    def __repr__(self) -> str:
        return (
            f"VendorState(menu_addr={self.menu_addr!r}, items_addr={self.items_addr!r}, "
            f"state={self.state}, active={self.active})"
        )
