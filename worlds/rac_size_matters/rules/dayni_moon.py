from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import (
    Rac5ClankChallenges as RACSMCLANK,
    Rac5Gadgets,
    Rac5Locations,
    Rac5SkillPoints,
    Rac5TBolts,
    Rac5VendorLocations,
    Rac5CutsceneLocations,
)
from ._helpers import has_projectile_weapon

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_dayni_moon_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _base       = lambda state: (state.has(Rac5Gadgets.SPROUT_O_MATIC, player)
                                 and has_projectile_weapon(state, player))
    _shrink_ray = lambda state: (_base(state) and state.has(Rac5Gadgets.SHRINK_RAY, player))

    # â”€â”€ Skill Points â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if world.options.skill_points.value >= 1:
        mw.get_location(Rac5SkillPoints.DAYNI_MOON_BOUNCY, player).access_rule = _base
    if world.options.skill_points.value >= 2:
        mw.get_location(Rac5SkillPoints.DAYNI_MOON_WOOL_PROTEST, player).access_rule = _base
    if world.options.enable_clank_challenge_skill_points:
        mw.get_location(Rac5SkillPoints.DAYNI_MOON_GLADIATOR, player).access_rule = lambda _: True

    # â”€â”€ Missions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if world.options.all_missions:
        mw.get_location(Rac5CutsceneLocations.DAYNI_MOON,      player).access_rule = _shrink_ray
        mw.get_location(Rac5CutsceneLocations.DAYNI_MOON_LUNA, player).access_rule = _shrink_ray
    if world.options.all_cutscenes:
        mw.get_location(Rac5CutsceneLocations.DAYNI_MOON_FIGHT1, player).access_rule = _shrink_ray
        mw.get_location(Rac5CutsceneLocations.DAYNI_MOON_FIGHT2, player).access_rule = _shrink_ray

    # â”€â”€ Titanium Bolts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    mw.get_location(Rac5TBolts.DAYNI_MOON_BARN,  player).access_rule = _base
    mw.get_location(Rac5TBolts.DAYNI_MOON_MIMIC, player).access_rule = _shrink_ray

    # â”€â”€ Armour â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    mw.get_location(Rac5Locations.DAYNI_MOON_HELMET, player).access_rule = _base

    # â”€â”€ Clank Challenges â€” item rewards (clank_challenges >= 1) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if world.options.clank_challenges.value >= 1:
        mw.get_location(RACSMCLANK.DAYNI_MOON_SHOWDOWN,  player).access_rule = lambda _: True
        mw.get_location(RACSMCLANK.DAYNI_MOON_INFINITE,  player).access_rule = lambda _: True

    # â”€â”€ Clank Challenges â€” individual completions (clank_challenges >= 2) â”€â”€â”€â”€â”€
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

    # â”€â”€ Vendors â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    mw.get_location(Rac5VendorLocations.DAYNI_MOON_SHOCK, player).access_rule = lambda _: True
    mw.get_location(Rac5VendorLocations.DAYNI_MOON_MAP,   player).access_rule = lambda _: True
