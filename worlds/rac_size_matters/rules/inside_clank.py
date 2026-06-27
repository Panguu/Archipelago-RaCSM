from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import (
    Rac5Locations,
    Rac5SkillPoints,
    Rac5TBolts,
    Rac5VendorLocations,
    Rac5CutsceneLocations,
)
from rule_builder.rules import True_

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_inside_clank_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    # Skill Points
    if world.options.skill_points.value >= 2:
        world.set_rule(mw.get_location(Rac5SkillPoints.INSIDE_CLANK_SHOCK, player), True_())
        world.set_rule(mw.get_location(Rac5SkillPoints.INSIDE_CLANK_RATCHET, player), True_())

    # Missions
    if world.options.all_missions:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.INSIDE_CLANK_ESCAPE, player), True_())
        world.set_rule(mw.get_location(Rac5CutsceneLocations.INSIDE_CLANK_TECHNOMITES, player), True_())

    # Titanium Bolts
    world.set_rule(mw.get_location(Rac5TBolts.INSIDE_CLANK_LADDER, player), True_())
    world.set_rule(mw.get_location(Rac5TBolts.INSIDE_CLANK_WALL, player), True_())

    # Armour
    world.set_rule(mw.get_location(Rac5Locations.INSIDE_CLANK_CHESTPLATE, player), True_())

    # Vendors
    # Static Barrier vendor — freely accessible on arrival.
    world.set_rule(mw.get_location(Rac5VendorLocations.INSIDE_CLANK_STATIC, player), True_())
