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
from rule_builder.rules import Has, HasAll, True_

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_outpost_omega_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _facility = HasAll(Rac5Gadgets.SHRINK_RAY, Rac5Gadgets.HYPERSHOT, Rac5Gadgets.SPROUT_O_MATIC)

    # Skill Points
    if world.options.enable_skyboard_challenge_skill_points:
        world.set_rule(mw.get_location(Rac5SkillPoints.OUTPOST_OMEGA_AWESOME, player), True_())

    # Missions
    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.OUTPOST_OMEGA, player), _facility)
    if world.options.all_missions:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.OUTPOST_OMEGA_ESCAPE, player), _facility)
        world.set_rule(mw.get_location(Rac5CutsceneLocations.OUTPOST_OMEGA_REMATCH, player), True_())

    # Titanium Bolts
    world.set_rule(mw.get_location(Rac5TBolts.OUTPOST_OMEGA_DREAM, player), True_())

    # Skyboard Challenges (skyboard_challenges >= 1)
    if world.options.skyboard_challenges.value >= 1:
        world.set_rule(mw.get_location(RACSMSKY.OUTPOST_OMEGA_VERTIGO, player), True_())
        world.set_rule(mw.get_location(RACSMSKY.OUTPOST_OMEGA_INTERIOR, player), True_())
        world.set_rule(mw.get_location(RACSMSKY.OUTPOST_OMEGA_DANGER, player), True_())
        world.set_rule(mw.get_location(RACSMSKY.OUTPOST_OMEGA_VORTEX, player), True_())

    # Vendors
    world.set_rule(mw.get_location(Rac5VendorLocations.OUTPOST_OMEGA_BEE, player), Has(Rac5Gadgets.SHRINK_RAY))
