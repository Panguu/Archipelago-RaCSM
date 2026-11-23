from .clank_gadgets import SACClankGadgets as G
from .clank_gadgets import SACClankWeapons as W
from .planets import SACCases as C
from .vendor import VENDOR_WEAPONS, vendor_location_name
from .weapon_mods import VENDOR_MODS
from .weapon_order import WEAPON_ORDER
from .weapon_progression import PROGRESSIVE_TO_UNLOCK, TITAN_LOCATIONS
from .weapons import EQUIPMENT_DISPLAY_TO_INTERNAL
from .weapons import SACRatchetWeapons as R

WEAPON_CASES = {
    "blaster": C.BOLTAIRE_MUSEUM, "shardgun": C.MAX_SECURITY_CELLS,
    "walloper": C.MAX_SECURITY_CELLS, "minelauncher": C.ASYANICA_ROOFTOPS,
    "beemineglove": C.AZCOTAL_ALLEY, "porkbomb": C.HIGH_ROLLERS_CASINO,
    "plasmawhip": C.VENANTONIO_LABS, "shockrocket": C.GALACTIC_BOLT_RESERVE,
    "ryno": C.BOLTAIRE_MUSEUM, "throwTie": C.BOLTAIRE_MUSEUM,
    "HoloKnuckles": C.BOLTAIRE_MUSEUM, "CuffLink": C.ASYANICA_ROOFTOPS,
    "TangleVine": C.AZCOTAL_ALLEY, "LightningUmbrella": C.VENANTONIO_LABS,
    "FlamethrowerPen": C.VENANTONIO_LABS,
}

MOD_CASES = {
    1: C.ASYANICA_ROOFTOPS, 2: C.ASYANICA_ROOFTOPS, 4: C.ASYANICA_ROOFTOPS,
    13: C.ASYANICA_ROOFTOPS, 22: C.AZCOTAL_ALLEY, 23: C.AZCOTAL_ALLEY,
    7: C.AZCOTAL_ALLEY, 8: C.HIGH_ROLLERS_CASINO, 19: C.THE_SHOWERS,
    20: C.SPACESHIP_GRAVEYARD, 17: C.SPACESHIP_GRAVEYARD,
    16: C.PRISON_BREAKOUT, 10: C.SPACESHIP_GRAVEYARD, 11: C.PRISON_BREAKOUT,
    25: C.VENANTONIO_LABS, 28: C.VENANTONIO_LABS, 29: C.VENANTONIO_LABS,
}

VENDOR_REQUIREMENT_ITEMS: dict[str, tuple[str, ...]] = {
    C.BOLTAIRE_MUSEUM: (G.BLACK_OUT_PEN,),
    C.MAX_SECURITY_CELLS: (R.RATCHETPDA,),
    C.ASYANICA_ROOFTOPS: (),
    C.COUNTESS_VILLA: (),
    C.THE_MESS_HALL: (R.RATCHETPDA,),
    C.AZCOTAL_ALLEY: (),
    C.GONDOLA_ASCENT: (),
    C.HIGH_ROLLERS_CASINO: (G.HOLOMONOCLE, W.CUFFLINK),
    C.THE_EXERCISE_YARD: (R.RATCHETPDA,),
    C.VENANTONIO_LABS: (),
    C.GALACTIC_BOLT_RESERVE: (),
    C.THE_SHOWERS: (R.RATCHETPDA,),
    C.SPACESHIP_GRAVEYARD: (),
    C.PRISON_BREAKOUT: (R.RATCHETPDA,),
    C.UNDERWATER_BUNKER: (),
    C.KLUNKS_LAIR: (),
}


def vendor_unlocked_cases(owned_cases, received_names) -> frozenset[str]:
    """Owned cases whose own vendor the player can reach with `received_names`."""
    received = set(received_names)
    # Match World.collect: the first progressive weapon grants its base unlock.
    received.update({PROGRESSIVE_TO_UNLOCK[name] for name in received
                     if name in PROGRESSIVE_TO_UNLOCK})
    return frozenset(case for case in owned_cases
                     if case in VENDOR_REQUIREMENT_ITEMS and received.issuperset(VENDOR_REQUIREMENT_ITEMS[case]))

VENDOR_CASES = {
    name: WEAPON_CASES[EQUIPMENT_DISPLAY_TO_INTERNAL[name]]
    for name in VENDOR_WEAPONS
    if EQUIPMENT_DISPLAY_TO_INTERNAL[name] in WEAPON_CASES
}
VENDOR_CASES.update({
    G.CLANKPDA: C.AZCOTAL_ALLEY, G.HYPNOWATCH: C.HIGH_ROLLERS_CASINO,
    G.BOLTGRABBER: C.GALACTIC_BOLT_RESERVE, W.SUPERKICK: C.BOLTAIRE_MUSEUM,
    W.KICKBLAST: C.VENANTONIO_LABS, W.KICKSPLOSION: C.BOLTAIRE_MUSEUM,
})
VENDOR_CASES = {vendor_location_name(name): case for name, case in VENDOR_CASES.items()}
VENDOR_CASES.update({mod.location: MOD_CASES[mod.mod_id] for mod in VENDOR_MODS})
VENDOR_CASES.update({name: WEAPON_CASES[internal] for internal, name in TITAN_LOCATIONS.items()})

VENDOR_ROW_CASES = {
    (0, WEAPON_ORDER.index(EQUIPMENT_DISPLAY_TO_INTERNAL[name])): VENDOR_CASES[vendor_location_name(name)]
    for name in VENDOR_WEAPONS
}
VENDOR_ROW_CASES.update({(3, mod.mod_id): MOD_CASES[mod.mod_id] for mod in VENDOR_MODS})
VENDOR_ROW_CASES.update({(4, WEAPON_ORDER.index(internal)): WEAPON_CASES[internal]
                         for internal in TITAN_LOCATIONS})
