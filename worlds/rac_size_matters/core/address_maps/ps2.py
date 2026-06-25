from __future__ import annotations

from dataclasses import dataclass

# Global memory addresses

ARMOUR_BASE                = 0x21F4B354
ARMOUR_SET_COLLECTED_ADDR  = 0x21F4B442  # byte 0: pure sets (bit N = ArmourSets(N+1) complete)
                                          # byte 1 (0x21F4B443): hybrid sets equipped —
                                          #   0x01=Shock Crystal  0x02=Wildburst  0x04=Triple Wave
                                          #   0x08=Ice II         0x10=Stalker
TITANIUM_BOLT_BASE         = 0x21F4B444
SKILL_POINTS_BASE          = 0x21F4B437
CLANK_CHALLENGE_BASE       = 0x1F4B3DB  # starts at Metalis unlock addr; Dayni Moon unlock at +0x18
CLANK_CHALLENGE_SIZE       = 42         # covers 0x1F4B3DB-0x1F4B404
SKYBOARD_BASE              = 0x1F4B407
CHEATS                     = 0x21F4C440
CURRENT_PLANET_ADDRESS     = 0x21F4C76C
PLAYER_BOLT_COUNT          = 0x21F4C768
BOLT_PICKUP_MASK           = 0x000000FFFFFFFFFF
PLANET_LOAD_ADDRESS        = 0x21F4C770
NEW_PLANET_START_LOAD_ADDR = 0x21F4A744
CONTROLLER_PAUSE_SELECT_ADDRESS = 0x20F7F414
CONTROLLER_BUTTONS_ADDRESS      = 0x20F7F415

CURRENT_WEAPON_IN_VENDOR   = 0x21F4AB8C
WEAPON_VENDOR_SLOTS        = 0x21F4ABE4
WEAPON_VENDOR_ITEMS        = 0x21F4AB80

POKITARU_RYLLUS_ALT_TRIGGER = 0x2F9CC6  # releases Ryllus when it changes from 0x00 to any value

PLAYER_STATE  = 0x20F805C0  # fallback when planet not in PLANET_ADDRESSES
PLAYER_HEALTH = 0x20F80E2C

# Planet unlock progress: each value must reach 3 to unlock the next planet.
PLANET_UNLOCK_ADDRESSES: dict[str, int] = {
    "POKITARU":      0x21F4C661,
    "RYLLUS":        0x21F4C662,
    "KALIDON":       0x21F4C663,
    "METALIS":       0x21F4C664,
    "DREAMTIME":     0x21F4C665,
    "OUTPOST_OMEGA": 0x21F4C666,
    "CHALLAX":       0x21F4C667,
    "DAYNI_MOON":    0x21F4C668,
    "INSIDE_CLANK":  0x21F4C669,
    "QUODRONA":      0x21F4C66A,
}
BRIGHTNESS_ADDRESS = 0x21EF1056
DREAMTIME_EFFECT = 0x21EF1058

# Static RAM buffer where custom notification-text strings are written before
# pointing a text box's message_str_pointer at them.
STATIC_TEXT_BUFFER: int = 0x21F649D0

# Parallel "state" byte at unlock_address + PLANET_STATE_OFFSET.
# e.g. OUTPOST_OMEGA state = 0x21F4C677; gates Outpost Omega 2 (0x17) access.
PLANET_STATE_OFFSET: int = 0x11


# Per-planet consolidated addresses

@dataclass(frozen=True)
class PlanetAddresses:
    name:          str
    player_state:  int
    player_health: int
    menu:             int | None = None   # vendor menu state addr (0x09=GadgetTron, 0x0E=Mod Vendor)
    preload_menu:     int | None = None   # goes to 0x13 when player can interact with vendor
    weapon_array:     int | None = None   # base of per-planet weapon struct array
    mission:          int | None = None   # 2-byte mission progress value
    vendor_prompt_id:     int | None = None   # message ID value in message_str_pointer when vendor dialog is open
    clank_challenge_base: int | None = None   # base address for clank challenge unlock/completion bytes
    skyboard_base:        int | None = None   # unlock addr; completed addr = skyboard_base + 1
    small_text_box:       int | None = None   # SmallTextBox base address
    multi_line_text_box:  int | None = None   # MultiLineTextBox base address


PLANET_ADDRESSES: dict[int, PlanetAddresses] = {
    0x01: PlanetAddresses("Pokitaru",        0x20F805C0, 0x20F80E2C, menu=0x1073DC0, preload_menu=0xF4C8C0, weapon_array=0x20F3EA17, mission=0x21F4B3C4, vendor_prompt_id=0xBF48, small_text_box=0xF479E8, multi_line_text_box=0xF47B28),
    0x02: PlanetAddresses("Ryllus",          0x20F7F2D0, 0x20F7FB3C, menu=0x1072AC0, preload_menu=0xF49080, weapon_array=0x20F3AE97, mission=0x21F4B3C6, vendor_prompt_id=0xBF35, small_text_box=0xF441A8, multi_line_text_box=0xF442E8),
    0x03: PlanetAddresses("Kalidon",         0x20F7F440, 0x20F7FCAC, menu=0x1072C40, preload_menu=0xF48F40, weapon_array=0x20F3B097, mission=0x21F4B3C8, vendor_prompt_id=0x3F37, skyboard_base=0x1F4B407, small_text_box=0xF44068, multi_line_text_box=0xF441A8),
    0x04: PlanetAddresses("Metalis",         0x20F7EDD0, 0x20F7F63C, menu=0x10725C0, preload_menu=0xF49D80, weapon_array=0x20F3BB97, mission=0x21F4B3CA, vendor_prompt_id=0x3F30, clank_challenge_base=0x1F4B3DB, small_text_box=0xF44EA8, multi_line_text_box=0xF44FE8),
    0x05: PlanetAddresses("Dreamtime",       0x20F762C0, 0x20F76B2C, menu=0x1069C80, preload_menu=0xF45C40, weapon_array=0x20F37D97, mission=0x21F4B3CC, vendor_prompt_id=0x7FA7, small_text_box=0xF40D68, multi_line_text_box=0xF40EA8),
    0x06: PlanetAddresses("Outpost Omega",   0x20F81B40, 0x20F823AC, menu=0x1075D40, preload_menu=0xF4D040, weapon_array=0x20F42117, mission=0x21F4B3CE, skyboard_base=0x1F4B409),
    0x07: PlanetAddresses("Challax",         0x20F806C0, 0x20F80F2C, menu=0x1073EC0, preload_menu=0xF4B3C0, weapon_array=0x20F3D517, mission=0x21F4B3D0, vendor_prompt_id=0xBF49, small_text_box=0xF464E8, multi_line_text_box=0xF46628),
    0x08: PlanetAddresses("Dayni Moon",      0x20F79850, 0x20F7A0BC, menu=0x106D040, preload_menu=0xF3F780, weapon_array=0x20F31597, mission=0x21F4B3D2, vendor_prompt_id=0x3FDB, clank_challenge_base=0x1F4B3F3, small_text_box=0xF3A8A8, multi_line_text_box=0xF3A9E8),
    0x09: PlanetAddresses("Inside Clank",    0x20F82540, 0x20F82DAC, menu=0x1075D40, preload_menu=0xF50EC0, weapon_array=0x20F43017, mission=0x21F4B3D4, vendor_prompt_id=0x3F68, small_text_box=0xF4BFE8, multi_line_text_box=0xF4C128),
    0x0A: PlanetAddresses("Quodrona",        0x20F809C0, 0x20F8122C, menu=0x10741C0, preload_menu=0xF4C8C0, weapon_array=0x20F3EA17, mission=0x21F4B3D6, vendor_prompt_id=0xBF4C, small_text_box=0xF479E8, multi_line_text_box=0xF47B28),
    0x17: PlanetAddresses("Outpost Omega 2", 0x20F82A40, 0x20F823AC, menu=0x107A200, preload_menu=0xF54CC0, weapon_array=0x20F46E17,                      vendor_prompt_id=0x3F37, small_text_box=0xF4FDE8, multi_line_text_box=0xF4FF28),
}


# Legacy dict views (derived from PLANET_ADDRESSES)

PLAYER_ADDRS: dict[int, tuple[int, int]] = {
    pid: (p.player_state, p.player_health) for pid, p in PLANET_ADDRESSES.items()
}

MENU_ADDR_BY_PLANET_ID: dict[int, int] = {
    pid: p.menu for pid, p in PLANET_ADDRESSES.items() if p.menu is not None
}

WEAPON_ARRAY_BASE_BY_PLANET: dict[int, int] = {
    pid: p.weapon_array for pid, p in PLANET_ADDRESSES.items() if p.weapon_array is not None
}

PLANET_MISSION_ADDRESSES: dict[str, int] = {
    p.name: p.mission for p in PLANET_ADDRESSES.values() if p.mission is not None
}

SMALL_TEXT_BOX_BY_PLANET: dict[int, int] = {
    pid: p.small_text_box for pid, p in PLANET_ADDRESSES.items() if p.small_text_box is not None
}

MULTI_LINE_TEXT_BOX_BY_PLANET: dict[int, int] = {
    pid: p.multi_line_text_box for pid, p in PLANET_ADDRESSES.items() if p.multi_line_text_box is not None
}
