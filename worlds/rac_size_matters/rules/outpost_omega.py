from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import (
    Rac5Gadgets,
    Rac5SkillPoints,
    Rac5SkyboardChallenges as RACSMSKY,
    Rac5TBolts,
    Rac5VendorLocations,
    Rac5CutsceneLocations,
)

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_outpost_omega_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _facility = lambda state: (state.has(Rac5Gadgets.SHRINK_RAY, player)
                               and state.has(Rac5Gadgets.HYPERSHOT, player)
                               and state.has(Rac5Gadgets.SPROUT_O_MATIC, player))

    # â”€â”€ Skill Points â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if world.options.enable_skyboard_challenge_skill_points:
        mw.get_location(Rac5SkillPoints.OUTPOST_OMEGA_AWESOME, player).access_rule = lambda _: True

    # â”€â”€ Missions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if world.options.all_cutscenes:
        mw.get_location(Rac5CutsceneLocations.OUTPOST_OMEGA,        player).access_rule = _facility
    if world.options.all_missions:
        mw.get_location(Rac5CutsceneLocations.OUTPOST_OMEGA_ESCAPE,  player).access_rule = _facility
        mw.get_location(Rac5CutsceneLocations.OUTPOST_OMEGA_REMATCH, player).access_rule = lambda _: True

    # â”€â”€ Titanium Bolts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    mw.get_location(Rac5TBolts.OUTPOST_OMEGA_DREAM, player).access_rule = lambda _: True

    # â”€â”€ Skyboard Challenges (skyboard_challenges >= 1) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if world.options.skyboard_challenges.value >= 1:
        mw.get_location(RACSMSKY.OUTPOST_OMEGA_VERTIGO,  player).access_rule = lambda _: True
        mw.get_location(RACSMSKY.OUTPOST_OMEGA_INTERIOR, player).access_rule = lambda _: True
        mw.get_location(RACSMSKY.OUTPOST_OMEGA_DANGER,   player).access_rule = lambda _: True
        mw.get_location(RACSMSKY.OUTPOST_OMEGA_VORTEX,   player).access_rule = lambda _: True

    # â”€â”€ Vendors â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    mw.get_location(Rac5VendorLocations.OUTPOST_OMEGA_BEE, player).access_rule = \
        lambda state: state.has(Rac5Gadgets.SHRINK_RAY, player)
