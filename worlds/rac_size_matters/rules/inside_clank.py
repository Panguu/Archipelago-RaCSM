from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import (
    Rac5Locations,
    Rac5SkillPoints,
    Rac5TBolts,
    Rac5VendorLocations,
    Rac5CutsceneLocations,
)

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_inside_clank_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    # Skill Points
    if world.options.skill_points.value >= 2:
        mw.get_location(Rac5SkillPoints.INSIDE_CLANK_SHOCK,   player).access_rule = lambda _: True
        mw.get_location(Rac5SkillPoints.INSIDE_CLANK_RATCHET, player).access_rule = lambda _: True

    # Missions
    if world.options.all_missions:
        mw.get_location(Rac5CutsceneLocations.INSIDE_CLANK_ESCAPE,      player).access_rule = lambda _: True
        mw.get_location(Rac5CutsceneLocations.INSIDE_CLANK_TECHNOMITES, player).access_rule = lambda _: True

    # Titanium Bolts
    mw.get_location(Rac5TBolts.INSIDE_CLANK_LADDER, player).access_rule = lambda _: True
    mw.get_location(Rac5TBolts.INSIDE_CLANK_WALL,   player).access_rule = lambda _: True

    # Armour
    mw.get_location(Rac5Locations.INSIDE_CLANK_CHESTPLATE, player).access_rule = lambda _: True

    # Vendors
    # Static Barrier vendor — freely accessible on arrival.
    mw.get_location(Rac5VendorLocations.INSIDE_CLANK_STATIC, player).access_rule = lambda _: True
