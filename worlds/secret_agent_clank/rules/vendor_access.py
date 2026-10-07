from rule_builder.rules import CanReachRegion, False_, Has, True_

from ..constants import CHARACTER_ITEM_NAME, PROGRESSIVE_CHARACTER_ITEM_NAME
from ..constants.challenge_mode import CHALLENGE_VENDOR_LOCATIONS, PROGRESSIVE_CHALLENGE_MODE
from ..constants.clank_gadgets import SACClankGadgets, SACClankWeapons
from ..constants.weapons import SACRatchetWeapons
from ..constants.planets import CASE_NAME_TO_CASE, CASES_BY_OPERATIVE, PLANET_ACCESS_ITEM_NAME, SACCases
from ..constants.vendor_unlocks import VENDOR_CASES
from ..constants.weapons import EQUIPMENT_DISPLAY_TO_INTERNAL
from ..core.patches import VENDOR_LOCATIONS
from ..items import PROGRESSIVE_PLANET_ITEM_NAME
from ..options import Infobots
from .rule_helpers import region_names

VENDOR_ONLY_ITEM_NAMES: frozenset[str] = frozenset(
    name for name, internal in EQUIPMENT_DISPLAY_TO_INTERNAL.items()
    if internal in VENDOR_LOCATIONS.values()
)

VENDOR_REQUIREMENTS = {
    SACCases.BOLTAIRE_MUSEUM: Has(SACClankGadgets.BLACK_OUT_PEN),
    SACCases.BOLTAIRE_GEM_WING: False_(),
    SACCases.MAX_SECURITY_CELLS: Has(SACRatchetWeapons.RATCHETPDA),
    SACCases.ROOFTOP_DEATHTRAP: False_(),
    SACCases.ASYANICA_ROOFTOPS: True_(),
    SACCases.LARGER_THAN_LIFE: False_(),
    SACCases.COUNTESS_VILLA: True_(),
    SACCases.GLACIARA_SKI_SLOPES: False_(),
    SACCases.THE_MESS_HALL: Has(SACRatchetWeapons.RATCHETPDA),
    SACCases.AZCOTAL_ALLEY: True_(),
    SACCases.GONDOLA_ASCENT: True_(),
    SACCases.SUCK_AND_JIVE: False_(),
    SACCases.HIGH_ROLLERS_CASINO: Has(SACClankGadgets.HOLOMONOCLE) & Has(SACClankWeapons.CUFFLINK),
    SACCases.THE_EXERCISE_YARD: Has(SACRatchetWeapons.RATCHETPDA),
    SACCases.HIGH_STAKES_ROOM: False_(),
    SACCases.VENANTONIO_LABS: True_(),
    SACCases.VENANTONIO_CANALS: False_(),
    SACCases.MADAM_BUTTERQWARK: False_(),
    SACCases.GALACTIC_BOLT_RESERVE: True_(),
    SACCases.INSIDE_THE_A_EYE: False_(),
    SACCases.THE_SHOWERS: Has(SACRatchetWeapons.RATCHETPDA),
    SACCases.SPACESHIP_GRAVEYARD: True_(),
    SACCases.SAINT_QWARK: False_(),
    SACCases.THE_QUASAR_FIELDS: False_(),
    SACCases.PRISON_BREAKOUT: Has(SACRatchetWeapons.RATCHETPDA),
    SACCases.DAMS_EDGE_HYDRANO: False_(),
    SACCases.A_FICTION_FULL_OF_DOLLARS: False_(),
    SACCases.BULKHEAD_LOCK: False_(),
    SACCases.UNDERWATER_BUNKER: True_(),
    SACCases.KLUNKS_LAIR: True_(),
    SACCases.HIGH_TREEHOUSE: False_(),
}


def vendor_access_rule(world, case_name):
    if case_name not in region_names(world):
        return False_()
    return CanReachRegion(case_name) & VENDOR_REQUIREMENTS.get(case_name, False_())


def any_vendor_rule(world):
    rule = False_()
    for case_name in VENDOR_REQUIREMENTS:
        rule = rule | vendor_access_rule(world, case_name)
    return rule


def vendor_case_rule(world, case_name):
    """Match resolved AP case ownership, including alternative access modes."""
    rule = Has(case_name)
    case = CASE_NAME_TO_CASE[case_name]
    mode = world.options.infobots
    if mode == Infobots.option_character_unlocks:
        item = PROGRESSIVE_CHARACTER_ITEM_NAME.get(case.operative)
        if item:
            count = list(CASES_BY_OPERATIVE[case.operative]).index(case) + 1
            return rule | Has(item, count)
        return rule | Has(CHARACTER_ITEM_NAME[case.operative])
    if mode == Infobots.option_progressive_planet:
        if case.planet in world.progressive_planets:
            return rule | Has(PROGRESSIVE_PLANET_ITEM_NAME,
                              world.progressive_planets.index(case.planet) + 1)
    elif mode != Infobots.option_cases and case.planet in PLANET_ACCESS_ITEM_NAME:
        return rule | Has(PLANET_ACCESS_ITEM_NAME[case.planet])
    return rule


def set_vendor_rules(world):
    # Unlock the slot with its case, independently of the randomized reward.
    available_vendor = any_vendor_rule(world)
    for location in world.multiworld.get_locations(world.player):
        if location.parent_region.name == "Vendor":
            rule = available_vendor & vendor_case_rule(world, VENDOR_CASES[location.name])
            if world.options.progressive_challenge_mode and location.name in CHALLENGE_VENDOR_LOCATIONS:
                rule = rule & Has(PROGRESSIVE_CHALLENGE_MODE)
            world.set_rule(location, rule)
