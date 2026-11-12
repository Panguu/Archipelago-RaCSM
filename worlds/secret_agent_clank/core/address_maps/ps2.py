"""Fixed EE addresses. Anything that moves between levels comes from runtime exports instead."""
from dataclasses import dataclass, field

from ...constants import CASE_ID_TO_CASE

CURRENT_CASE_ADDRESS = 0x206328
FORCE_CASE_ADDRESS = 0x206324
CASE_IDLE_VALUE = 0x00
BOLTS_ADDRESS = 0x2075C8
QUICK_SELECT_ADDRESS = 0x220010
QUICK_SELECT_SLOT_COUNT = 8


@dataclass(frozen=True)
class CaseAddresses:
    case_id: int
    ratchet_state:  int | None = None
    ratchet_health: int | None = None
    clank_state:    int | None = None
    clank_health:   int | None = None
    qwark_state:    int | None = None
    qwark_health:   int | None = None
    menu:                     int | None = None
    vendor_items:             int | None = None
    mission:                  int | None = None
    controller_pause_select:  int | None = None
    weapon_array:         int | None = None
    clank_gadget_addrs:   dict[str, int] = field(default_factory=dict)


WEAPON_ARRAY_BASE_BY_CASE: dict[int, int] = {
    1: 0x0057AAF8,
    2: 0x00521378,
    4: 0x00598678,
    10: 0x0057C578,
    11: 0x005935F8,
    12: 0x005935F8,
    18: 0x00523478,
    23: 0x0051BBF8,
    27: 0x0051AC78,
    8: 0x004FF6F8,
    15: 0x00568778,
    17: 0x005097F8,
    24: 0x00530BF8,
    26: 0x00512E78,
    7: 0x0056A2F8,
    13: 0x0056DAF8,
    16: 0x00585478,
    19: 0x00586978,
    29: 0x0058D3F8,
    22: 0x0058B578,
    30: 0x0056C4F8,
    3: 0x005A4078,
    9: 0x005A2378,
    14: 0x005A4278,
    21: 0x0059C978,
    25: 0x005A8F78,
    20: 0x00515F78,
    28: 0x005142F8,
    5: 0x00512878,
}

VENDOR_SCREEN_STATE_OFFSET = 0xB470
VENDOR_SLOT_ARRAY_OFFSET   = 0xB9C8
VENDOR_SLOT_COUNT          = 6

VENDOR_ITEM_ARRAY_OFFSET = 0x13F38
VENDOR_ITEM_STRIDE       = 0x1C
VENDOR_ITEM_MAX_COUNT    = 64
_ITEM_OFFSET_ACTIVE    = 0x00
_ITEM_OFFSET_ICON      = 0x04
_ITEM_OFFSET_NODE_TYPE = 0x0C
_ITEM_OFFSET_WEAPON_ID = 0x10
_ITEM_OFFSET_MOD_ID    = 0x14

CASE_ADDRESSES: dict[int, CaseAddresses] = {
    case_id: CaseAddresses(
        case_id=case_id,
        weapon_array=WEAPON_ARRAY_BASE_BY_CASE.get(case_id),
        vendor_items=(
            WEAPON_ARRAY_BASE_BY_CASE[case_id] + VENDOR_ITEM_ARRAY_OFFSET
            if case_id in WEAPON_ARRAY_BASE_BY_CASE else None
        ),
    )
    for case_id in CASE_ID_TO_CASE
}
