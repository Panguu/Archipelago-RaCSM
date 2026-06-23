from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import (
    RACSMCLANKCHALLENGE as RACSMCLANK,
    RACSMITEM,
    RACSMLOCATION,
    RACSMSKILLPOINT,
    RACSMTBOLT,
    RACSMVENDORLOCATION,
    RacSMCutsceneLocations,
)
from ._helpers import has_projectile_weapon

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_dayni_moon_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _base       = lambda state: (state.has(RACSMITEM.SPROUT_O_MATIC, player)
                                 and has_projectile_weapon(state, player))
    _shrink_ray = lambda state: (_base(state) and state.has(RACSMITEM.SHRINK_RAY, player))

    # ── Skill Points ──────────────────────────────────────────────────────────
    if world.options.skill_points.value >= 1:
        mw.get_location(RACSMSKILLPOINT.DAYNI_MOON_BOUNCY, player).access_rule = _base
    if world.options.skill_points.value >= 2:
        mw.get_location(RACSMSKILLPOINT.DAYNI_MOON_WOOL_PROTEST, player).access_rule = _base
    if world.options.enable_clank_challenge_skill_points:
        mw.get_location(RACSMSKILLPOINT.DAYNI_MOON_GLADIATOR, player).access_rule = lambda _: True

    # ── Missions ──────────────────────────────────────────────────────────────
    if world.options.all_missions:
        mw.get_location(RacSMCutsceneLocations.DAYNI_MOON,      player).access_rule = _shrink_ray
        mw.get_location(RacSMCutsceneLocations.DAYNI_MOON_LUNA, player).access_rule = _shrink_ray
    if world.options.all_cutscenes:
        mw.get_location(RacSMCutsceneLocations.DAYNI_MOON_FIGHT1, player).access_rule = _shrink_ray
        mw.get_location(RacSMCutsceneLocations.DAYNI_MOON_FIGHT2, player).access_rule = _shrink_ray

    # ── Titanium Bolts ────────────────────────────────────────────────────────
    mw.get_location(RACSMTBOLT.DAYNI_MOON_BARN,  player).access_rule = _base
    mw.get_location(RACSMTBOLT.DAYNI_MOON_MIMIC, player).access_rule = _shrink_ray

    # ── Armour ────────────────────────────────────────────────────────────────
    mw.get_location(RACSMLOCATION.DAYNI_MOON_HELMET, player).access_rule = _base

    # ── Clank Challenges — item rewards (clank_challenges >= 1) ───────────────
    if world.options.clank_challenges.value >= 1:
        mw.get_location(RACSMCLANK.DAYNI_MOON_SHOWDOWN,  player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.DAYNI_MOON_INFINITE,  player).access_rule = lambda _: True

    # ── Clank Challenges — individual completions (clank_challenges >= 2) ─────
    if world.options.clank_challenges.value >= 2:
        mw.get_location(RACSMCLANK.DAYNI_MOON_CROWD,      player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.DAYNI_MOON_REVERSE,    player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.DAYNI_MOON_BRIDGE,     player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.DAYNI_MOON_LEAP,       player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.DAYNI_MOON_WELCOME,    player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.DAYNI_MOON_ROUND,      player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.DAYNI_MOON_VARIETY,    player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.DAYNI_MOON_SAWYER,     player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.DAYNI_MOON_SMASHER,    player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.DAYNI_MOON_TOURNAMENT, player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.DAYNI_MOON_AROUND,     player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.DAYNI_MOON_LINE,       player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.DAYNI_MOON_HAY,        player).access_rule = lambda _: True

    # ── Vendors ───────────────────────────────────────────────────────────────
    mw.get_location(RACSMVENDORLOCATION.DAYNI_MOON_SHOCK, player).access_rule = lambda _: True
    mw.get_location(RACSMVENDORLOCATION.DAYNI_MOON_MAP,   player).access_rule = lambda _: True
