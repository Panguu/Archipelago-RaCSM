from __future__ import annotations

from dataclasses import dataclass

ARMOUR_BASE                = 0x088C1334  
ARMOUR_SET_COLLECTED_ADDR  = 0x088C1402  
TITANIUM_BOLT_BASE         = 0x088C1404  
SKILL_POINTS_BASE          = 0x088C13F7  
CLANK_CHALLENGE_BASE       = 0x088C139B  
CLANK_CHALLENGE_SIZE       = 42          
SKYBOARD_BASE              = 0x088C13C7  
CHEATS                     = 0x088C2400  
CURRENT_PLANET_ADDRESS     = 0x088C272C 
PLAYER_BOLT_COUNT          = 0x088C2728  
BOLT_PICKUP_MASK           = 0x000000FFFFFFFFFF  
CONTROLLER_PAUSE_SELECT_ADDRESS = 0x094A679C  
CONTROLLER_BUTTONS_ADDRESS      = 0x094A679D  

WEAPON_VENDOR_SLOTS        = 0x088C0BC4 
WEAPON_VENDOR_ITEMS        = 0x088C0B60 

PLAYER_STATE  = 0x09473338 
PLAYER_HEALTH = 0x09473BA4 

# Planet unlock progress: each value must reach 3 to unlock the next planet.
# All ten computed in-range from PLAYER_BOLT_COUNT's offset — good candidates, not yet live-verified.
# CONFIRMED live — writing INFOBOT_UNLOCK_VALUE (3) to each address (and each
# +PLANET_STATE_OFFSET) made all 10 planets appear unlocked on the ship menu.
PLANET_UNLOCK_ADDRESSES: dict[str, int] = {
    "POKITARU":      0x088C2621,  
    "RYLLUS":        0x088C2622,  
    "KALIDON":       0x088C2623,  
    "METALIS":       0x088C2624,  
    "DREAMTIME":     0x088C2625,  
    "OUTPOST_OMEGA": 0x088C2626,  
    "CHALLAX":       0x088C2627,  
    "DAYNI_MOON":    0x088C2628,  
    "INSIDE_CLANK":  0x088C2629,  
    "QUODRONA":      0x088C262A,
}



PLANET_STATE_OFFSET: int = 0x11  


@dataclass(frozen=True)
class PlanetAddresses:
    name:          str
    player_state:  int
    player_health: int
    menu:             int | None = None
    weapon_array:     int | None = None
    mission:          int | None = None
    clank_challenge_base: int | None = None
    skyboard_base:        int | None = None
    controller_pause_select_v2: int | None = None
    weapon_cycler_apply:   int | None = None   # write a weapon id here to hand it straight to the player
    weapon_cycler_state:   int | None = None   # WeaponCycleState — 0x0C while a pickup animation plays (PS2 value; unconfirmed on PSP)
    weapon_cycler_current: int | None = None   # currently-equipped weapon id
    weapon_cycler_stored:  int | None = None   # weapon id waiting to be cycled in
        # Same fixed offset from player_health PS2 used (current = health+0x34,
        # stored = health+0x40, apply = health+0x54, cycle_state = health+0x58)
        # — CONFIRMED live on Pokitaru (see PLANET_ADDRESSES below), so this
        # offset carries over from PS2 to PSP exactly. Every other planet
        # below is derived from that same offset, not independently verified
        # yet (see worlds/rac_size_matters_psp/core/weapon_cycler.py).




PLANET_ADDRESSES: dict[int, PlanetAddresses] = {
    0x01: PlanetAddresses("Pokitaru",        0x09473338, 0x09473BA4, menu=0x09597B24, weapon_array=0x093E677B, mission=0x088C1384, controller_pause_select_v2=0x094A679C, weapon_cycler_apply=0x09473BF8, weapon_cycler_state=0x09473BFC, weapon_cycler_current=0x09473BD8, weapon_cycler_stored=0x09473BE4),  # movement/health/menu/weapon_array/mission/controller_pause_select_v2 CONFIRMED live; weapon_cycler_* CONFIRMED live too — same player_health+{0x34,0x40,0x54,0x58} offset PS2 used, carries over exactly
    0x02: PlanetAddresses("Ryllus",          0x0948C038, 0x0948C8A4, menu=0x095B0864, weapon_array=0x0940F60F, mission=0x088C1386, controller_pause_select_v2=0x094BF4BC, weapon_cycler_apply=0x0948C8F8, weapon_cycler_state=0x0948C8FC, weapon_cycler_current=0x0948C8D8, weapon_cycler_stored=0x0948C8E4),  # ALL confirmed live (player_state re-derived: earlier 0x09DC9180 was a false positive, corrected hex-subtraction error); weapon_cycler_* derived from player_health+{0x34,0x40,0x54,0x58}, unverified
    0x03: PlanetAddresses("Kalidon",         0x094893F8, 0x09489C64, menu=0x095ADBE4, weapon_array=0x093FACFB, mission=0x088C1388, skyboard_base=0x088C13C7, controller_pause_select_v2=0x094BC85C, weapon_cycler_apply=0x09489CB8, weapon_cycler_state=0x09489CBC, weapon_cycler_current=0x09489C98, weapon_cycler_stored=0x09489CA4),  # ALL confirmed live (menu reads 3, not 0x09/0x0E from the PS2 comment — PSP vendor-open value differs; skyboard_base CONFIRMED live — see top-level SKYBOARD_BASE comment); weapon_cycler_* derived from player_health+{0x34,0x40,0x54,0x58}, unverified
    0x04: PlanetAddresses("Metalis",         0x094871B8, 0x09487A24, menu=0x095AB9A4, weapon_array=0x093F927B, mission=0x088C138A, clank_challenge_base=0x088C139B, controller_pause_select_v2=0x094BA62C, weapon_cycler_apply=0x09487A78, weapon_cycler_state=0x09487A7C, weapon_cycler_current=0x09487A58, weapon_cycler_stored=0x09487A64),  # ALL confirmed live, including clank_challenge_base — see top-level CLANK_CHALLENGE_BASE comment; weapon_cycler_* derived from player_health+{0x34,0x40,0x54,0x58}, unverified
    0x05: PlanetAddresses("Dreamtime",       0x094693F8, 0x09469C64, menu=0x0958DBE4, weapon_array=0x093D3D7B, mission=0x088C138C, controller_pause_select_v2=0x0949C85C, weapon_cycler_apply=0x09469CB8, weapon_cycler_state=0x09469CBC, weapon_cycler_current=0x09469C98, weapon_cycler_stored=0x09469CA4),  # ALL confirmed live; weapon_cycler_* derived from player_health+{0x34,0x40,0x54,0x58}, unverified
    0x06: PlanetAddresses("Outpost Omega",   0x09461538, 0x09461DA4, menu=0x09585D24, weapon_array=0x093D647B, mission=0x088C138E, skyboard_base=0x088C13C9, controller_pause_select_v2=0x0949499C, weapon_cycler_apply=0x09461DF8, weapon_cycler_state=0x09461DFC, weapon_cycler_current=0x09461DD8, weapon_cycler_stored=0x09461DE4),  # ALL CONFIRMED live. player_state/player_health: user gave 3 Cheat Engine candidates 4/2 bytes apart (host 0x35C61538/0x35C6153C/0x35C6153E), same pattern as Inside Clank's discovery — converted (base -> PSP 0x09461538), and the first two candidates' +0x86C offset both read a clean float (8.0) while the third was misaligned garbage; confirmed by writing 1.0 to the first candidate's health live and the user seeing the bar drop. Also lands in the normal 0x0946xxxx planet cluster, not the old 0x078Fxxxx family the previous guess used. weapon_array: user supplied two Cheat Engine candidates for Lacerator ammo (host 0x35BD64AC and 0x35BE8250); converted both and read 5 structs at each (base = ammo_addr - WEAPON_STRUCT's ammo offset 0x31) — 0x35BD64AC -> base 0x093D647B produced 5 clean weapon structs (valid icon pointers, level=7 on every slot, ammo=115 matching CE's live value exactly), while 0x35BE8250's base produced garbage (icon=0, level in the billions) and was ruled out. menu: user-supplied Cheat Engine address (host 0x35D85D24 -> 0x09585D24), CONFIRMED live. controller_pause_select_v2: user's first CE address (host 0x35C9499D -> 0x0949499D) was the buttons byte, offset +1 from the true base — same off-by-one seen on Inside Clank; user corrected to the true base 0x0949499C, CONFIRMED live for START/SELECT. skyboard_base: CONFIRMED live by user — same top-byte-fix pattern as Kalidon skyboard_base and Dayni Moon clank_challenge_base. weapon_cycler_* derived from player_health+{0x34,0x40,0x54,0x58}, unverified
    0x07: PlanetAddresses("Challax",         0x09483E38, 0x094846A4, menu=0x095A8624, weapon_array=0x093F60FB, mission=0x088C1390, controller_pause_select_v2=0x0948729C, weapon_cycler_apply=0x094846F8, weapon_cycler_state=0x094846FC, weapon_cycler_current=0x094846D8, weapon_cycler_stored=0x094846E4),  # ALL confirmed live; weapon_cycler_* derived from player_health+{0x34,0x40,0x54,0x58}, unverified
    0x08: PlanetAddresses("Dayni Moon",      0x094B8AFC, 0x094B9368, menu=0x095DD2E4, weapon_array=0x09424FFB, mission=0x088C1392, clank_challenge_base=0x088C13B3, controller_pause_select_v2=0x094EBF6C, weapon_cycler_apply=0x094B93BC, weapon_cycler_state=0x094B93C0, weapon_cycler_current=0x094B939C, weapon_cycler_stored=0x094B93A8),  # player_state/player_health/menu/controller_pause_select_v2/weapon_array/clank_challenge_base CONFIRMED live (state 0x094B8AFC read 0 idle -> 2 while running; health 0x094B9368 read 6.0 at the same +0x86C offset every other planet uses; menu/controller_pause_select_v2 found by projecting the same-offset pattern from confirmed planets then live-confirmed; weapon_array derived from Lacerator's live-confirmed ammo address 0x0942502C minus its known struct offset — slot 0 * WEAPON_STRUCT_SIZE (0x58) + ammo field offset (0x31) — writing 99 there read back as a clean 4-byte 99 in-game; clank_challenge_base found via user-supplied Cheat Engine address for the completed "Two's A Crowd" challenge (host 0x350C13C0, converted via memory.base 0x2C800000 -> PSP 0x088C13C0, minus its known +13 struct offset -> base 0x088C13B3) — live read matches the struct exactly: +2 Gadgetbot-unlock=0x01, +13 Two's-A-Crowd=0x01 completed, everything else 0). weapon_cycler_* derived from player_health+{0x34,0x40,0x54,0x58}, unverified
    0x09: PlanetAddresses("Inside Clank",    0x0945BD78, 0x0945C5E4, menu=0x09580564, weapon_array=0x093D0CFB, mission=0x088C1394, controller_pause_select_v2=0x0948F1DC, weapon_cycler_apply=0x0945C638, weapon_cycler_state=0x0945C63C, weapon_cycler_current=0x0945C618, weapon_cycler_stored=0x0945C624),  # ALL CONFIRMED live. player_state: user-supplied Cheat Engine address (host 0x35C5BD78, converted via memory.base 0x2C800000 -> PSP 0x0945BD78); state read 2 while running (matches the 0-idle/2-running pattern on every other confirmed planet), and player_health at the same +0x86C offset every other planet uses read a clean float (8.0) — confirmed by writing 1.0 there live and the user seeing the on-screen health bar drop. Lands in the normal 0x0945xxxx planet cluster, not the anomalous 0x078Fxxxx family the old guess (and Outpost Omega) used — the old guess was simply wrong, not evidence Inside Clank is structurally special. weapon_array: user supplied two Cheat Engine candidates for Lacerator ammo (host 0x35BD0D2C and 0x35BE2AF0); converted both and read 5 structs at each (base = ammo_addr - WEAPON_STRUCT's ammo offset 0x31) — 0x35BD0D2C -> base 0x093D0CFB produced 5 clean weapon structs (valid icon pointers, level=7 on every slot matching the level-7 grant done earlier this session, sane ammo/mods/unlocked), while 0x35BE2AF0's base produced garbage (icon=0, level in the billions, out-of-range unlocked byte) and was ruled out. menu: user-supplied Cheat Engine address (host 0x35D80564 -> 0x09580564), CONFIRMED live. controller_pause_select_v2: user's first CE address (host 0x35C8F1DD -> 0x0948F1DD) turned out to be the buttons byte (offset +1, matches GlobalButtonState's pause_sel/buttons layout); user corrected to the true base 0x0948F1DC, CONFIRMED live for START/SELECT. weapon_cycler_* derived from player_health+{0x34,0x40,0x54,0x58}, unverified
    0x0A: PlanetAddresses("Quodrona",        0x0947AB78, 0x0947B3E4, menu=0x0959F364, weapon_array=0x093EDFFB, mission=0x088C1396, controller_pause_select_v2=0x094ADFDC, weapon_cycler_apply=0x0947B438, weapon_cycler_state=0x0947B43C, weapon_cycler_current=0x0947B418, weapon_cycler_stored=0x0947B424),  # player_state/player_health/menu/controller_pause_select_v2/weapon_array CONFIRMED live (state 0x0947AB78 read 0 idle -> 2 while running; health 0x0947B3E4 read 6.0 at the same +0x86C offset every other planet uses; menu reads 0 closed-baseline; controller_pause_select_v2 reads 255 no-buttons-pressed baseline, same convention as Dayni Moon; weapon_array found via Cheat Engine value-scan on Lacerator's live ammo (host 0x35BEE02C, converted via memory.base 0x2C800000 -> PSP 0x093EE02C, minus known ammo offset 0x31 -> struct base 0x093EDFFB) — ammo read back exactly 97 matching CE, and 5 consecutive structs at the 0x58 stride all pass is_weapon_candidate()'s sanity checks; a second CE candidate at host 0x35BFFEE0 was ruled out as garbage (level/unlocked/mods all out of valid range)) — clank_challenge_base still the old computed OUT-OF-RANGE guess; unverified/likely wrong. weapon_cycler_* derived from player_health+{0x34,0x40,0x54,0x58}, unverified
    0x17: PlanetAddresses("Outpost Omega 2", 0x094419B8, 0x09442224, menu=0x095661A4, weapon_array=0x093B95FB, controller_pause_select_v2=0x09474E1C, weapon_cycler_apply=0x09442278, weapon_cycler_state=0x0944227C, weapon_cycler_current=0x09442258, weapon_cycler_stored=0x09442264),  # ALL confirmed live; weapon_cycler_* derived from player_health+{0x34,0x40,0x54,0x58}, unverified
}


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

# (apply, cycle_state, current_weapon, stored_weapon) — only present for a
# planet once all four addresses are known. Empty until PSP addresses are
# captured (see PlanetAddresses.weapon_cycler_*).
WEAPON_CYCLER_ADDRS_BY_PLANET: dict[int, tuple[int, int, int, int]] = {
    pid: (p.weapon_cycler_apply, p.weapon_cycler_state, p.weapon_cycler_current, p.weapon_cycler_stored)
    for pid, p in PLANET_ADDRESSES.items()
    if p.weapon_cycler_apply is not None and p.weapon_cycler_state is not None
    and p.weapon_cycler_current is not None and p.weapon_cycler_stored is not None
}
