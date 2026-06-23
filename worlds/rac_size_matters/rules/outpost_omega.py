from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import (
    RACSMITEM,
    RACSMSKILLPOINT,
    RACSMSKYBOARDCHALLENGE as RACSMSKY,
    RACSMTBOLT,
    RACSMVENDORLOCATION,
    RacSMCutsceneLocations,
)

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_outpost_omega_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _facility = lambda state: (state.has(RACSMITEM.SHRINK_RAY, player)
                               and state.has(RACSMITEM.HYPERSHOT, player)
                               and state.has(RACSMITEM.SPROUT_O_MATIC, player))

    # ── Skill Points ──────────────────────────────────────────────────────────
    if world.options.enable_skyboard_challenge_skill_points:
        mw.get_location(RACSMSKILLPOINT.OUTPOST_OMEGA_AWESOME, player).access_rule = lambda _: True

    # ── Missions ──────────────────────────────────────────────────────────────
    if world.options.all_cutscenes:
        mw.get_location(RacSMCutsceneLocations.OUTPOST_OMEGA,        player).access_rule = _facility
    if world.options.all_missions:
        mw.get_location(RacSMCutsceneLocations.OUTPOST_OMEGA_ESCAPE,  player).access_rule = _facility
        mw.get_location(RacSMCutsceneLocations.OUTPOST_OMEGA_REMATCH, player).access_rule = lambda _: True

    # ── Titanium Bolts ────────────────────────────────────────────────────────
    mw.get_location(RACSMTBOLT.OUTPOST_OMEGA_DREAM, player).access_rule = lambda _: True

    # ── Skyboard Challenges (skyboard_challenges >= 1) ────────────────────────
    if world.options.skyboard_challenges.value >= 1:
        mw.get_location(RACSMSKY.OUTPOST_OMEGA_VERTIGO,  player).access_rule = lambda _: True
        mw.get_location(RACSMSKY.OUTPOST_OMEGA_INTERIOR, player).access_rule = lambda _: True
        mw.get_location(RACSMSKY.OUTPOST_OMEGA_DANGER,   player).access_rule = lambda _: True
        mw.get_location(RACSMSKY.OUTPOST_OMEGA_VORTEX,   player).access_rule = lambda _: True

    # ── Vendors ───────────────────────────────────────────────────────────────
    mw.get_location(RACSMVENDORLOCATION.OUTPOST_OMEGA_BEE, player).access_rule = \
        lambda state: state.has(RACSMITEM.SHRINK_RAY, player)
