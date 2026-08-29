from __future__ import annotations

from dataclasses import dataclass

from ...constants.shrink_ray import Rac5ShrinkRayGrindrail

ARMOUR_BASE                = 0x21F4B354
ARMOUR_SET_COLLECTED_ADDR  = 0x21F4B442  # byte 0: pure sets (bit N = ArmourSets(N+1) complete)
                                          # byte 1 (0x21F4B443): hybrid sets equipped (bitmask)
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
# Idle/sentinel value of NEW_PLANET_START_LOAD_ADDR when no forced load is pending.
# A forced load is encoded as plain planet_id written via little-endian write_int32.
PLANET_LOAD_IDLE_VALUE     = 0xFFFFFFFF
CONTROLLER_PAUSE_SELECT_ADDRESS = 0x20F7F414
CONTROLLER_BUTTONS_ADDRESS      = 0x20F7F415

QUICK_SELECT_BASE          = 0x21F4B364
SKIN_BASE                  = 0x21F4B45A
CHALLENGE_MODE_BASE        = 0x21F4C778  # single byte: New Game Plus tier, mirrored from slot_data on connect

# Rests at TRANSITION_GATE_IDLE (0x000000FF) — see structs/game.py's
# TransitionGateStruct/TRANSITION_GATE_IDLE/TRANSITION_GATE_ARRIVED for the
# state machine built on top of this address.
TRANSITION_GATE_ADDRESS    = 0x1EDDAD4
# Sits right beside the gate (+0x10) and holds the planet ID being loaded —
# see structs/game.py's LoadingPlanetStruct.
LOADING_PLANET_ADDRESS     = 0x1EDDAE4

CURRENT_WEAPON_IN_VENDOR   = 0x21F4AB8C
WEAPON_VENDOR_SLOTS        = 0x21F4ABE4
WEAPON_VENDOR_ITEMS        = 0x21F4AB80

POKITARU_RYLLUS_ALT_TRIGGER = 0x2F9CC6  # releases Ryllus when it changes from 0x00 to any value

PLAYER_STATE  = 0x20F805C0  # fallback when planet not in PLANET_ADDRESSES
PLAYER_HEALTH = 0x20F80E2C

@dataclass(frozen=True)
class GhostRatchetPlanetAddresses:
    """Per-planet addresses for the Ghost Ratchet feature (see core/ghost_ratchet.py).
    trigger arms the spawn and is a separate address from ghost_base, not an offset within it."""
    player_position: int
    ghost_base: int
    trigger: int


# Filled in as each planet is confirmed in-game. Kalidon Race (0x16) and both Giant
# Clank sub-modes (0x0F/0x15) have no clone struct at all and are deliberately absent.
GHOST_RATCHET_ADDRESSES: dict[int, GhostRatchetPlanetAddresses] = {
    0x01: GhostRatchetPlanetAddresses(  # Pokitaru
        player_position=0x202E62E0,
        ghost_base=0x202F4144,
        trigger=0x202CD554,
    ),
    0x02: GhostRatchetPlanetAddresses(  # Ryllus
        player_position=0x205BAB00,
        ghost_base=0x205C6E64,
        trigger=0x205A8D34,
    ),
    0x03: GhostRatchetPlanetAddresses(  # Kalidon
        player_position=0x2050E8A0,
        ghost_base=0x2051EC84,
        trigger=0x204F3934,
    ),
    0x04: GhostRatchetPlanetAddresses(  # Metalis
        player_position=0x201E65B0,
        ghost_base=0x201F3A94,
        trigger=0x201CFB8C,
    ),
    0x05: GhostRatchetPlanetAddresses(  # Dreamtime
        player_position=0x2020BFF0,
        ghost_base=0x202143D4,
        trigger=0x201F77E8,
    ),
    0x06: GhostRatchetPlanetAddresses(  # Outpost Omega
        player_position=0x20480E10,
        ghost_base=0x2048E0F4,
        trigger=0x2046E8EC,
    ),
    0x07: GhostRatchetPlanetAddresses(  # Challax
        player_position=0x20482010,
        ghost_base=0x2048D474,
        trigger=0x20471B04,
    ),
    0x08: GhostRatchetPlanetAddresses(  # Dayni Moon
        player_position=0x202FFB00,
        ghost_base=0x2032EB64,
        trigger=0x202F4964,
    ),
    0x09: GhostRatchetPlanetAddresses(  # Inside Clank
        player_position=0x203E4F30,
        ghost_base=0x203EF894,
        trigger=0x203CE028,
    ),
    0x0A: GhostRatchetPlanetAddresses(  # Quodrona
        player_position=0x203E0990,
        ghost_base=0x20404774,
        trigger=0x203D9A58,
    ),
    0x17: GhostRatchetPlanetAddresses(  # Outpost Omega 2
        player_position=0x2045F290,
        ghost_base=0x2047CBF4,
        trigger=0x2045A454,
    ),
}

# Global (non-per-planet) health EXP counter. Crossing a Nanotech Level
# threshold (see constants/nanotech_levels.py) is checked as an AP location.
PLAYER_HEALTH_EXP = 0x21F4C774

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
# Same 10-byte block as PLANET_UNLOCK_ADDRESSES, read/written as one contiguous
# struct by PlanetProgressStruct (see structs/game.py) instead of ten separate addresses.
PLANET_PROGRESS_BASE = PLANET_UNLOCK_ADDRESSES["POKITARU"]
BRIGHTNESS_ADDRESS = 0x21EF1056
DREAMTIME_EFFECT = 0x21EF1058

# Shrink Ray puzzle-gate bitmask (2 bytes), one bit per puzzle, OR'd together.
# For at least Kalidon Enter Factory the bitmask write alone doesn't unlock/bypass
# the puzzle in-game — see SHRINK_RAY_SKIP_ADDRESSES for the extra per-puzzle write.
SHRINK_RAY_GATE_ADDRESS: int = 0x21F4B40E

# Per-puzzle bypass addresses written 1 every tick IN ADDITION TO the
# SHRINK_RAY_GATE_ADDRESS bitmask write, for puzzles where the bitmask bit alone
# doesn't unlock/bypass it in-game. Puzzles not listed here rely on the bitmask alone.
SHRINK_RAY_SKIP_ADDRESSES: dict[str, int] = {
    Rac5ShrinkRayGrindrail.KALIDON_ENTER_FACTORY: 0x21F4B3EF,
}

# Static RAM buffer where custom notification-text strings are written before
# pointing a text box's message_str_pointer at them.
STATIC_TEXT_BUFFER: int = 0x21F649D0

# Parallel "state" byte at unlock_address + PLANET_STATE_OFFSET.
# e.g. OUTPOST_OMEGA state = 0x21F4C677; gates Outpost Omega 2 (0x17) access.
PLANET_STATE_OFFSET: int = 0x11


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
    controller_pause_select: int | None = None   # 0x20F7F414 on all planets
    controller_pause_select_v2: int | None = None   # candidate replacement: counts DOWN from 0xFF,
        # decremented by held PauseSelectButtons/ControllerButtons bit value (inverse of controller_pause_select).
        # buttons_v2 byte is always at +1. Captured per-planet as it's verified; not yet known for all planets.
    weapon_cycler_apply:   int | None = None   # write a weapon id here to hand it straight to the player
    weapon_cycler_state:   int | None = None   # WeaponCycleState — 0x0C while a pickup animation plays
    weapon_cycler_current: int | None = None   # currently-equipped weapon id
    weapon_cycler_stored:  int | None = None   # weapon id waiting to be cycled in
        # Fixed offsets from player_health, confirmed on Pokitaru and Ryllus; every other
        # planet is derived from that same offset, not independently verified yet.
    max_health: int | None = None   # float; max HP, rises with Nanotech level.
        # Fixed offset from player_health, confirmed on Pokitaru; every other planet
        # below is derived from that same offset, not independently verified yet.


PLANET_ADDRESSES: dict[int, PlanetAddresses] = {
    0x01: PlanetAddresses("Pokitaru",        0x20F805C0, 0x20F80E2C, menu=0x1073DC0, preload_menu=0xF4C8C0, weapon_array=0x20F3EA17, mission=0x21F4B3C4, vendor_prompt_id=0xBF48, small_text_box=0xF479E8, multi_line_text_box=0xF47B28, controller_pause_select=0xF80594, controller_pause_select_v2=0xF866C2, weapon_cycler_apply=0xF80E80, weapon_cycler_state=0xF80E84, weapon_cycler_current=0xF80E60, weapon_cycler_stored=0xF80E6C, max_health=0x20F80E30),
    0x02: PlanetAddresses("Ryllus",          0x20F7F2D0, 0x20F7FB3C, menu=0x1072AC0, preload_menu=0xF49080, weapon_array=0x20F3AE97, mission=0x21F4B3C6, vendor_prompt_id=0xBF35, small_text_box=0xF441A8, multi_line_text_box=0xF442E8, controller_pause_select=0xF7F2A4, controller_pause_select_v2=0xF853C2, weapon_cycler_apply=0xF7FB90, weapon_cycler_state=0xF7FB94, weapon_cycler_current=0xF7FB70, weapon_cycler_stored=0xF7FB7C, max_health=0x20F7FB40),
    0x03: PlanetAddresses("Kalidon",         0x20F7F440, 0x20F7FCAC, menu=0x1072C40, preload_menu=0xF48F40, weapon_array=0x20F3B097, mission=0x21F4B3C8, vendor_prompt_id=0x3F37, skyboard_base=0x1F4B407, small_text_box=0xF44068, multi_line_text_box=0xF441A8, controller_pause_select=0xF7F414, controller_pause_select_v2=0xF85542, weapon_cycler_apply=0xF7FD00, weapon_cycler_state=0xF7FD04, weapon_cycler_current=0xF7FCE0, weapon_cycler_stored=0xF7FCEC, max_health=0x20F7FCB0),
    0x04: PlanetAddresses("Metalis",         0x20F7EDD0, 0x20F7F63C, menu=0x10725C0, preload_menu=0xF49D80, weapon_array=0x20F3BB97, mission=0x21F4B3CA, vendor_prompt_id=0x3F30, clank_challenge_base=0x1F4B3DB, small_text_box=0xF44EA8, multi_line_text_box=0xF44FE8, controller_pause_select=0xF7EDA4, controller_pause_select_v2=0xF84EC2, weapon_cycler_apply=0xF7F690, weapon_cycler_state=0xF7F694, weapon_cycler_current=0xF7F670, weapon_cycler_stored=0xF7F67C, max_health=0x20F7F640),
    0x05: PlanetAddresses("Dreamtime",       0x20F762C0, 0x20F76B2C, menu=0x1069C80, preload_menu=0xF45C40, weapon_array=0x20F37D97, mission=0x21F4B3CC, vendor_prompt_id=0x7FA7, small_text_box=0xF40D68, multi_line_text_box=0xF40EA8, controller_pause_select=0xF76294, controller_pause_select_v2=0xF7C582, weapon_cycler_apply=0xF76B80, weapon_cycler_state=0xF76B84, weapon_cycler_current=0xF76B60, weapon_cycler_stored=0xF76B6C, max_health=0x20F76B30),
    0x06: PlanetAddresses("Outpost Omega",   0x20F81B40, 0x20F823AC, menu=0x1075340, preload_menu=0xF4D040, weapon_array=0x20F42117, mission=0x21F4B3CE, skyboard_base=0x1F4B409, controller_pause_select=0x20F7F414, controller_pause_select_v2=0xF87C42, weapon_cycler_apply=0xF82400, weapon_cycler_state=0xF82404, weapon_cycler_current=0xF823E0, weapon_cycler_stored=0xF823EC, max_health=0x20F823B0),
    0x07: PlanetAddresses("Challax",         0x20F806C0, 0x20F80F2C, menu=0x1073EC0, preload_menu=0xF4B3C0, weapon_array=0x20F3D517, mission=0x21F4B3D0, vendor_prompt_id=0xBF49, small_text_box=0xF464E8, multi_line_text_box=0xF46628, controller_pause_select=0xF80694, controller_pause_select_v2=0xF867C2, weapon_cycler_apply=0xF80F80, weapon_cycler_state=0xF80F84, weapon_cycler_current=0xF80F60, weapon_cycler_stored=0xF80F6C, max_health=0x20F80F30),
    0x08: PlanetAddresses("Dayni Moon",      0x20F79850, 0x20F7A0BC, menu=0x106D040, preload_menu=0xF3F780, weapon_array=0x20F31597, mission=0x21F4B3D2, vendor_prompt_id=0x3FDB, clank_challenge_base=0x1F4B3F3, small_text_box=0xF3A8A8, multi_line_text_box=0xF3A9E8, controller_pause_select=0xF79824, controller_pause_select_v2=0xF7F942, weapon_cycler_apply=0xF7A110, weapon_cycler_state=0xF7A114, weapon_cycler_current=0xF7A0F0, weapon_cycler_stored=0xF7A0FC, max_health=0x20F7A0C0),
    0x09: PlanetAddresses("Inside Clank",    0x20F82540, 0x20F82DAC, menu=0x1075D40, preload_menu=0xF50EC0, weapon_array=0x20F43017, mission=0x21F4B3D4, vendor_prompt_id=0x3F68, small_text_box=0xF4BFE8, multi_line_text_box=0xF4C128, controller_pause_select=0xF82514, controller_pause_select_v2=0xF88642, weapon_cycler_apply=0xF82E00, weapon_cycler_state=0xF82E04, weapon_cycler_current=0xF82DE0, weapon_cycler_stored=0xF82DEC, max_health=0x20F82DB0),
    0x0A: PlanetAddresses("Quodrona",        0x20F809C0, 0x20F8122C, menu=0x10741C0, preload_menu=0xF4C8C0, weapon_array=0x20F3EA17, mission=0x21F4B3D6, vendor_prompt_id=0xBF4C, small_text_box=0xF479E8, multi_line_text_box=0xF47B28, controller_pause_select=0xF80994, controller_pause_select_v2=0xF86AC2, weapon_cycler_apply=0xF81280, weapon_cycler_state=0xF81284, weapon_cycler_current=0xF81260, weapon_cycler_stored=0xF8126C, max_health=0x20F81230),
    0x17: PlanetAddresses("Outpost Omega 2", 0x20F82A40, 0x20F823AC, menu=0x107A200, preload_menu=0xF54CC0, weapon_array=0x20F46E17,                      vendor_prompt_id=0x3F37, small_text_box=0xF4FDE8, multi_line_text_box=0xF4FF28, controller_pause_select=0xF82A14, controller_pause_select_v2=0xF8CB42, max_health=0x20F823B0),
}
