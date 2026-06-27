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
from rule_builder.rules import Has, HasAll, True_

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_ryllus_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _full = HasAll(Rac5Gadgets.HYPERSHOT, Rac5Gadgets.SPROUT_O_MATIC)

    # Skill Points
    if world.options.skill_points.value >= 1:
        world.set_rule(mw.get_location(Rac5SkillPoints.RYLLUS_CAMERA, player), True_())
        world.set_rule(mw.get_location(Rac5SkillPoints.RYLLUS_SHIP_IT, player), _full)
    if world.options.skill_points.value >= 2:
        world.set_rule(mw.get_location(Rac5SkillPoints.RYLLUS_BURY, player), _full)

    # Missions
    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.RYLLUS_BUZZING, player), True_())
    if world.options.all_missions:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.RYLLUS_ARTIFACT, player), _full)
        world.set_rule(mw.get_location(Rac5CutsceneLocations.RYLLUS_TEMPLE, player), _full)

    # Titanium Bolts
    world.set_rule(mw.get_location(Rac5TBolts.RYLLUS_CLIFF, player), True_())
    world.set_rule(mw.get_location(Rac5TBolts.RYLLUS_WALL, player), _full)
    world.set_rule(mw.get_location(Rac5Locations.RYLLUS_HELMET, player), _full)
    world.set_rule(mw.get_location(Rac5Locations.RYLLUS_BOOTS, player), Has(Rac5Gadgets.SPROUT_O_MATIC))

    # Vendors
    world.set_rule(mw.get_location(Rac5VendorLocations.RYLLUS_AGENTS, player), True_())
