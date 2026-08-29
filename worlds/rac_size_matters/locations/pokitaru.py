"""Pokitaru's slice of the shared location registry (locations/shared.py), by category.

Also carries the weapon-level/nanotech-level/armour-set-check locations —
those are anchored to Pokitaru's region because the AP region graph needs
*some* planet, not because they're really Pokitaru-specific (see shared.py).
"""
from ..constants import Rac5Planets
from . import shared

_PLANET = Rac5Planets.POKITARU

TITANIUM_BOLT_LOCATIONS = shared.for_planet(_PLANET, shared.TITANIUM_BOLT_LOCATIONS)
ARMOUR_PICKUP_LOCATIONS = shared.for_planet(_PLANET, shared.ARMOUR_PICKUP_LOCATIONS)
VENDOR_LOCATIONS = shared.for_planet(
    _PLANET,
    shared.WEAPON_VENDOR_LOCATIONS, shared.GADGET_VENDOR_LOCATIONS,
    shared.WEAPON_MOD_VENDOR_LOCATIONS, shared.WEAPON_TITAN_VENDOR_LOCATIONS,
)
STORY_MISSION_LOCATIONS = shared.for_planet(_PLANET, shared.STORY_MISSION_LOCATIONS)
CUTSCENE_LOCATIONS = shared.for_planet(_PLANET, shared.CUTSCENE_LOCATIONS)
SKILL_POINT_LOCATIONS = shared.for_planet(_PLANET, shared.SKILL_POINT_LOCATIONS)
GADGET_PICKUP_LOCATIONS = shared.for_planet(_PLANET, shared.GADGET_PICKUP_LOCATIONS)
SKYBOARD_LOCATIONS = shared.for_planet(_PLANET, shared.SKYBOARD_ITEM_LOCATIONS, shared.EXTRA_SKYBOARD_LOCATIONS)
SHRINK_RAY_SKIP_LOCATIONS = shared.for_planet(_PLANET, shared.SHRINK_RAY_SKIP_LOCATIONS)
CHALLENGE_LOCATIONS = shared.for_planet(_PLANET, shared.CHALLENGE_LOCATIONS, shared.ALL_CLANK_LOCATIONS)
BOSS_LOCATIONS = shared.for_planet(_PLANET, shared.BOSS_LOCATIONS)
WEAPON_LEVEL_LOCATIONS = shared.WEAPON_LEVEL_LOCATIONS
NANOTECH_LEVEL_LOCATIONS = shared.NANOTECH_LEVEL_LOCATIONS
ARMOUR_SET_CHECK_LOCATIONS = shared.ARMOUR_SET_CHECK_LOCATIONS

LOCATIONS: dict[str, shared.RACLocationData] = {
    **TITANIUM_BOLT_LOCATIONS, **ARMOUR_PICKUP_LOCATIONS, **VENDOR_LOCATIONS,
    **STORY_MISSION_LOCATIONS, **CUTSCENE_LOCATIONS, **SKILL_POINT_LOCATIONS,
    **GADGET_PICKUP_LOCATIONS, **SKYBOARD_LOCATIONS, **SHRINK_RAY_SKIP_LOCATIONS,
    **CHALLENGE_LOCATIONS, **BOSS_LOCATIONS,
    **WEAPON_LEVEL_LOCATIONS, **NANOTECH_LEVEL_LOCATIONS, **ARMOUR_SET_CHECK_LOCATIONS,
}
