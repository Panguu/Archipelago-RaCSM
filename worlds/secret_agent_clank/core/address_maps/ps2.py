# 2026-09-11 audit: runtime exports now supply GadgetData and pause state.
# Historical case-unlock anchors below overlap mission state fields and MUST
# NOT be applied by the normal client. See docs/address_research.md.
"""Secret Agent Clank PS2 (SCUS-97623) RAM addresses."""
from dataclasses import dataclass, field

from ...constants.planets import ALL_CASES, CASE_ID_TO_CASE, SACCases

CURRENT_CASE_ADDRESS = 0x206328  # read: the case currently loaded
FORCE_CASE_ADDRESS    = 0x206324  # write: forces a transition to the given case id

CASE_IDLE_VALUE: int = 0x00


TITANIUM_BOLT_ADDRESS = 0x206C17

QUICK_SELECT_ADDRESS = 0x220010
QUICK_SELECT_SLOT_COUNT = 8

CHALLENGE_MODE_ADDRESS = 0x2075D4  # NG+ / NG++ tier
BOLTS_ADDRESS          = 0x2075C8  # bolt currency count
CHEATS_ADDRESS         = 0x206FE0

CUTSCENE_ADDRESSES: dict[str, int] = {}

CASE_UNLOCK_BASE_ADDRESSES: dict[str, int] = {
    SACCases.BOLTAIRE_MUSEUM:            0x57632C,
    SACCases.BOLTAIRE_GEM_WING:          0x51CC00,
    SACCases.MAX_SECURITY_CELLS:         0x59F9E0,
    SACCases.ROOFTOP_DEATHTRAP:          0x594100,
    SACCases.LARGER_THAN_LIFE:           0x50E360,
    SACCases.COUNTESS_VILLA:             0x5941C0,
    SACCases.ASYANICA_ROOFTOPS:          0x565EA0,
    SACCases.GLACIARA_SKI_SLOPES:        0x4FB360,
    SACCases.THE_MESS_HALL:              0x59E0E0,
    SACCases.AZCOTAL_ALLEY:              0x5783A0,
    SACCases.GONDOLA_ASCENT:             0x58F480,
    SACCases.SUCK_AND_JIVE:              0x594580,
    SACCases.HIGH_ROLLERS_CASINO:        0x569AC0,
    SACCases.THE_EXERCISE_YARD:          0x5A02A0,
    SACCases.HIGH_STAKES_ROOM:           0x564800,
    SACCases.VENANTONIO_LABS:            0x581560,
    SACCases.VENANTONIO_CANALS:          0x5059A0,
    SACCases.MADAM_BUTTERQWARK:          0x51F6E0,
    SACCases.GALACTIC_BOLT_RESERVE:      0x582C80,
    SACCases.INSIDE_THE_A_EYE:           0x512360,
    SACCases.THE_SHOWERS:                0x598E20,
    SACCases.SPACESHIP_GRAVEYARD:        0x587AE0,
    SACCases.SAINT_QWARK:                0x5181C0,
    SACCases.THE_QUASAR_FIELDS:          0x52D220,
    SACCases.PRISON_BREAKOUT:            0x5A5600,
    SACCases.DAMS_EDGE_HYDRANO:          0x50F5C0,
    SACCases.A_FICTION_FULL_OF_DOLLARS:  0x5174E0,
    SACCases.BULKHEAD_LOCK:              0x510BC0,
    SACCases.UNDERWATER_BUNKER:          0x589DE0,
    SACCases.KLUNKS_LAIR:                0x568EE0,
}

CASE_UNLOCK_TABLE_OFFSETS: tuple[int, ...] = (
    -0xC0, 0x000, 0x060, 0x140, 0x260, 0x2C0, 0x320, 0x380, 0x440, 0x540,
    0x600, 0x660, 0x6E0, 0x7A0, 0x800, 0x860, 0x8C0, 0x980, 0xA40, 0xAE0,
    0xBC0, 0xC80, 0xD40, 0xDA0, 0xE00, 0xE60, 0xF20, 0x1040, 0x10A0, 0x11C0,
    0x1220,
)

CASE_UNLOCK_TABLE_SLOT_TO_CASE: dict[int, str] = {
    case.case_id + 1: case.name for case in ALL_CASES
}
CASE_NAME_TO_UNLOCK_SLOT: dict[str, int] = {
    name: slot for slot, name in CASE_UNLOCK_TABLE_SLOT_TO_CASE.items()
}

# --- Gadgetbot Challenges (per-case unlock gate) ----------------------------
GADGETBOT_UNLOCK_ADDRESSES: dict[str, int] = {
    SACCases.INSIDE_THE_A_EYE: 0x206C77,
    SACCases.BULKHEAD_LOCK:    0x206C79,
}

# --- Special Challenges (per-case unlock gate) ------------------------------
SPECIAL_CHALLENGE_UNLOCK_ADDRESSES: dict[str, int] = {
    SACCases.VENANTONIO_CANALS:   0x206C99,
    SACCases.DAMS_EDGE_HYDRANO:   0x206C9A,
    SACCases.GLACIARA_SKI_SLOPES: 0x206C98,
}


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
    1: 0x0057AAF8,   # Boltaire Museum
    2: 0x00521378,   # Boltaire Gem Wing
    4: 0x00598678,   # Rooftop Deathtrap
    10: 0x0057C578,  # Azcotal Alley
    11: 0x005935F8,  # Gondola Ascent
    12: 0x005935F8,  # Suck and Jive -- ALIASED to Gondola Ascent's base (shares its case_id/data at the engine level, not a separate discovery)
    18: 0x00523478,  # Madam Butterqwark
    23: 0x0051BBF8,  # Saint Qwark
    27: 0x0051AC78,  # A Fiction Full Of Dollars
    8: 0x004FF6F8,   # Glaciara Ski Slopes
    15: 0x00568778,  # High Stakes Room
    17: 0x005097F8,  # Venantonio Canals
    24: 0x00530BF8,  # The Quasar Fields
    26: 0x00512E78,  # Dam's Edge, Hydrano
    7: 0x0056A2F8,   # Asyanica Rooftops
    13: 0x0056DAF8,  # High-Rollers Casino
    16: 0x00585478,  # Venantonio Labs
    19: 0x00586978,  # Galactic Bolt Reserve
    29: 0x0058D3F8,  # Underwater Bunker
    22: 0x0058B578,  # Spaceship Graveyard
    30: 0x0056C4F8,  # Klunk's Lair
    3: 0x005A4078,   # Max-Security Cells
    9: 0x005A2378,   # The Mess Hall
    14: 0x005A4278,  # The Exercise Yard
    21: 0x0059C978,  # The Showers
    25: 0x005A8F78,  # Prison Breakout!
    20: 0x00515F78,  # Inside the A-Eye
    28: 0x005142F8,  # Bulkhead Lock
    5: 0x00512878,   # Larger Than Life
}

VENDOR_SCREEN_STATE_OFFSET = 0xB470
VENDOR_SLOT_ARRAY_OFFSET   = 0xB9C8
VENDOR_SLOT_COUNT          = 6

VENDOR_ITEM_ARRAY_OFFSET = 0x13F38
VENDOR_ITEM_STRIDE       = 0x1C
VENDOR_ITEM_MAX_COUNT    = 32
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
