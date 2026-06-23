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

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_ryllus_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _full = lambda state: (state.has(Rac5Gadgets.HYPERSHOT, player)
                           and state.has(Rac5Gadgets.SPROUT_O_MATIC, player))

    # â”€â”€ Skill Points â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if world.options.skill_points.value >= 1:
        mw.get_location(Rac5SkillPoints.RYLLUS_CAMERA,  player).access_rule = lambda _: True
        mw.get_location(Rac5SkillPoints.RYLLUS_SHIP_IT, player).access_rule = _full
    if world.options.skill_points.value >= 2:
        mw.get_location(Rac5SkillPoints.RYLLUS_BURY, player).access_rule = _full

    # â”€â”€ Missions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if world.options.all_cutscenes:
        mw.get_location(Rac5CutsceneLocations.RYLLUS_BUZZING,  player).access_rule = lambda _: True
    if world.options.all_missions:
        mw.get_location(Rac5CutsceneLocations.RYLLUS_ARTIFACT, player).access_rule = _full
        mw.get_location(Rac5CutsceneLocations.RYLLUS_TEMPLE,   player).access_rule = _full

    # â”€â”€ Titanium Bolts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    mw.get_location(Rac5TBolts.RYLLUS_CLIFF,  player).access_rule = lambda _: True
    mw.get_location(Rac5TBolts.RYLLUS_WALL,   player).access_rule = _full
    mw.get_location(Rac5Locations.RYLLUS_HELMET, player).access_rule = _full
    mw.get_location(Rac5Locations.RYLLUS_BOOTS,  player).access_rule = \
        lambda state: state.has(Rac5Gadgets.SPROUT_O_MATIC, player)

    # â”€â”€ Vendors â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    mw.get_location(Rac5VendorLocations.RYLLUS_AGENTS, player).access_rule = lambda _: True
