from __future__ import annotations

from typing import TYPE_CHECKING


from ..constants import (
    Rac5Locations,
    Rac5SkillPoints,
    Rac5TBolts,
    Rac5VendorLocations,
    Rac5CutsceneLocations,
    Rac5Gadgets
)
from rule_builder.rules import HasAll, True_

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_inside_clank_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _base = HasAll(Rac5Gadgets.HYPERSHOT, Rac5Gadgets.POLARIZER, Rac5Gadgets.SHRINK_RAY)
    if world.options.skill_points.value >= 2:
        world.set_rule(mw.get_location(Rac5SkillPoints.INSIDE_CLANK_SHOCK, player), _base)
        world.set_rule(mw.get_location(Rac5SkillPoints.INSIDE_CLANK_RATCHET, player), _base)

    if world.options.all_missions:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.INSIDE_CLANK_ESCAPE, player), _base)
        world.set_rule(mw.get_location(Rac5CutsceneLocations.INSIDE_CLANK_TECHNOMITES, player), _base)

    world.set_rule(mw.get_location(Rac5TBolts.INSIDE_CLANK_LADDER, player), True_())
    world.set_rule(mw.get_location(Rac5TBolts.INSIDE_CLANK_WALL, player), True_())

    world.set_rule(mw.get_location(Rac5Locations.INSIDE_CLANK_CHESTPLATE, player), _base)

    # Static Barrier vendor — freely accessible on arrival.
    world.set_rule(mw.get_location(Rac5VendorLocations.INSIDE_CLANK_STATIC, player), _base)
