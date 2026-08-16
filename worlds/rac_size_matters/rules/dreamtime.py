from typing import TYPE_CHECKING

from rule_builder.rules import HasAll

from ..constants import (
    Rac5CutsceneLocations,
    Rac5Gadgets,
    Rac5Locations,
    Rac5SkillPoints,
    Rac5TBolts,
    Rac5TitanVendorLocations,
    Rac5VendorLocations,
)
from ._helpers import HasProjectileWeapon

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_dreamtime_rules(world: "RACSizeMatterWorld") -> None:
    player = world.player
    mw = world.multiworld

    # Entrance already requires Hypershot + Sprout-O-Matic.
    _base = HasAll(Rac5Gadgets.HYPERSHOT, Rac5Gadgets.SPROUT_O_MATIC)

    if world.options.skill_points.value >= 2:
        world.set_rule(mw.get_location(Rac5SkillPoints.DREAMTIME_FRIENDS, player), _base)
        world.set_rule(mw.get_location(Rac5SkillPoints.DREAMTIME_NIGHT_TERRORS, player), _base)

    if world.options.all_missions:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.DREAMTIME_COMPLETE, player), _base)
    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.DREAMTIME_SLEEPING_RATCHET, player), _base)

    world.set_rule(mw.get_location(Rac5TBolts.DREAMTIME_HAT, player), _base)
    world.set_rule(mw.get_location(Rac5TBolts.DREAMTIME_GARAGE, player), _base)
    world.set_rule(mw.get_location(Rac5TBolts.DREAMTIME_CRAB, player), _base & HasProjectileWeapon())

    world.set_rule(mw.get_location(Rac5Locations.DREAMTIME_CHESTPLATE, player), _base)

    world.set_rule(mw.get_location(Rac5VendorLocations.DREAMTIME_SUCK, player), _base)

    # Challenge Mode — NG+ Items only controls the item pool, not location
    # existence (see regions.py, which both tables must agree with on
    # which of these locations actually exist).
    if world.options.challenge_mode.value >= 1:
        world.set_rule(mw.get_location(Rac5Locations.DREAMTIME_HYPERBOREAN_CHESTPLATE, player), _base)
        # Titan variant available once the base weapon is purchasable at
        # its own vendor — buying it there is what actually unlocks the
        # Titan re-purchase in-game now (see core/vendor.py), matching
        # DREAMTIME_SUCK's own rule above.
        world.set_rule(mw.get_location(Rac5TitanVendorLocations.DREAMTIME_SUCK_TITAN, player), _base)
