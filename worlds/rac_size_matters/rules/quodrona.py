from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import RACSMITEM, RACSMSKILLPOINT, RACSMTBOLT, RACSMVENDORLOCATION, RacSMCutsceneLocations
from ._helpers import has_weapon

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_quodrona_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _checks = lambda state: (state.has(RACSMITEM.SHRINK_RAY, player)
                             and state.has(RACSMITEM.HYPERSHOT, player))

    # ── Skill Points ──────────────────────────────────────────────────────────
    if world.options.skill_points.value >= 2:
        mw.get_location(RACSMSKILLPOINT.QUODRONA_ELITE,  player).access_rule = _checks
        mw.get_location(RACSMSKILLPOINT.QUODRONA_STORM,  player).access_rule = _checks

    # ── Missions ──────────────────────────────────────────────────────────────
    if world.options.all_cutscenes:
        mw.get_location(RacSMCutsceneLocations.QUODRONA_CLONE, player).access_rule = _checks
        mw.get_location(RacSMCutsceneLocations.QUODRONA_CHASE, player).access_rule = _checks
        mw.get_location(RacSMCutsceneLocations.QUODRONA_MECHA, player).access_rule = _checks
    if world.options.all_missions:
        mw.get_location(RacSMCutsceneLocations.QUODRONA_FIND,  player).access_rule = _checks

    # ── Titanium Bolts ────────────────────────────────────────────────────────
    mw.get_location(RACSMTBOLT.QUODRONA_DUMMIES, player).access_rule = _checks

    # ── Boss ──────────────────────────────────────────────────────────────────
    mw.get_location(RacSMCutsceneLocations.QUODRONA_GOAL, player).access_rule = _checks

    # ── Vendors ───────────────────────────────────────────────────────────────
    mw.get_location(RACSMVENDORLOCATION.QUODRONA_LASER, player).access_rule = lambda _: True

    # ── Weapon Mod Vendor ─────────────────────────────────────────────────────
    mw.get_location(RACSMVENDORLOCATION.QUODRONA_AGENTS_LAUNCHER,  player).access_rule = \
        lambda state: has_weapon(state, player, RACSMITEM.AGENTS_OF_DOOM)
    mw.get_location(RACSMVENDORLOCATION.QUODRONA_SCORCHER_SPITFIRE, player).access_rule = \
        lambda state: has_weapon(state, player, RACSMITEM.SCORCHER)
    mw.get_location(RACSMVENDORLOCATION.QUODRONA_SNIPER_SPLIT,     player).access_rule = \
        lambda state: has_weapon(state, player, RACSMITEM.SNIPER_MINE)
    mw.get_location(RACSMVENDORLOCATION.QUODRONA_SHOCK_LOCK,       player).access_rule = \
        lambda state: has_weapon(state, player, RACSMITEM.SHOCK_ROCKET)
    mw.get_location(RACSMVENDORLOCATION.QUODRONA_SHOCK_AFTER,      player).access_rule = \
        lambda state: has_weapon(state, player, RACSMITEM.SHOCK_ROCKET)
