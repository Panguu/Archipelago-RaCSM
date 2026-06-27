from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import (
    Rac5Gadgets,
    Rac5Locations,
    Rac5SkillPoints,
    Rac5TBolts,
    Rac5VendorLocations,
    Rac5CutsceneLocations,
)
from ._helpers import HasProjectileWeapon
from rule_builder.rules import HasAll

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_dreamtime_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    # Entrance already requires Hypershot + Sprout-O-Matic.
    _base = HasAll(Rac5Gadgets.HYPERSHOT, Rac5Gadgets.SPROUT_O_MATIC)

    # Skill Points
    if world.options.skill_points.value >= 2:
        world.set_rule(mw.get_location(Rac5SkillPoints.DREAMTIME_FRIENDS, player), _base)
        world.set_rule(mw.get_location(Rac5SkillPoints.DREAMTIME_NIGHT_TERRORS, player), _base)

    # Missions
    if world.options.all_missions:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.DREAMTIME_COMPLETE, player), _base)

    # Titanium Bolts
    world.set_rule(mw.get_location(Rac5TBolts.DREAMTIME_HAT, player), _base)
    world.set_rule(mw.get_location(Rac5TBolts.DREAMTIME_GARAGE, player), _base)
    world.set_rule(mw.get_location(Rac5TBolts.DREAMTIME_CRAB, player), _base & HasProjectileWeapon())

    # Armour
    world.set_rule(mw.get_location(Rac5Locations.DREAMTIME_CHESTPLATE, player), _base)

    # Vendors
    world.set_rule(mw.get_location(Rac5VendorLocations.DREAMTIME_SUCK, player), _base)
