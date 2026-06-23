from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import (
    RACSMITEM,
    RACSMLOCATION,
    RACSMSKILLPOINT,
    RACSMTBOLT,
    RACSMVENDORLOCATION,
    RacSMCutsceneLocations,
)

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_ryllus_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _full = lambda state: (state.has(RACSMITEM.HYPERSHOT, player)
                           and state.has(RACSMITEM.SPROUT_O_MATIC, player))

    # ── Skill Points ──────────────────────────────────────────────────────────
    if world.options.skill_points.value >= 1:
        mw.get_location(RACSMSKILLPOINT.RYLLUS_CAMERA,  player).access_rule = lambda _: True
        mw.get_location(RACSMSKILLPOINT.RYLLUS_SHIP_IT, player).access_rule = _full
    if world.options.skill_points.value >= 2:
        mw.get_location(RACSMSKILLPOINT.RYLLUS_BURY, player).access_rule = _full

    # ── Missions ──────────────────────────────────────────────────────────────
    if world.options.all_cutscenes:
        mw.get_location(RacSMCutsceneLocations.RYLLUS_BUZZING,  player).access_rule = lambda _: True
    if world.options.all_missions:
        mw.get_location(RacSMCutsceneLocations.RYLLUS_ARTIFACT, player).access_rule = _full
        mw.get_location(RacSMCutsceneLocations.RYLLUS_TEMPLE,   player).access_rule = _full

    # ── Titanium Bolts ────────────────────────────────────────────────────────
    mw.get_location(RACSMTBOLT.RYLLUS_CLIFF,  player).access_rule = lambda _: True
    mw.get_location(RACSMTBOLT.RYLLUS_WALL,   player).access_rule = _full
    mw.get_location(RACSMLOCATION.RYLLUS_HELMET, player).access_rule = _full
    mw.get_location(RACSMLOCATION.RYLLUS_BOOTS,  player).access_rule = \
        lambda state: state.has(RACSMITEM.SPROUT_O_MATIC, player)

    # ── Vendors ───────────────────────────────────────────────────────────────
    mw.get_location(RACSMVENDORLOCATION.RYLLUS_AGENTS, player).access_rule = lambda _: True
