from typing import TYPE_CHECKING

from rule_builder.rules import Has, HasAll, True_

from ..constants import (
    Rac5CutsceneLocations,
    Rac5Gadgets,
    Rac5Locations,
    Rac5SkillPoints,
    Rac5SkyboardChallenges,
    Rac5TBolts,
    Rac5TitanVendorLocations,
    Rac5VendorLocations,
)

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_outpost_omega_rules(world: "RACSizeMatterWorld") -> None:
    player = world.player
    mw = world.multiworld

    _facility = HasAll(Rac5Gadgets.HYPERSHOT, Rac5Gadgets.SPROUT_O_MATIC)

    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.OUTPOST_OMEGA_ENTER, player), _facility)
        world.set_rule(mw.get_location(Rac5CutsceneLocations.OUTPOST_OMEGA, player), _facility)
    if world.options.all_missions:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.OUTPOST_OMEGA_ESCAPE, player), _facility)

    # Challenge Mode — NG+ Items only controls the item pool, not location
    # existence (see regions.py, which both tables must agree with on
    # which of these locations actually exist).
    if world.options.challenge_mode.value >= 1:
        # Titan variant available once the base weapon is purchasable at
        # its own vendor — buying it there is what actually unlocks the
        # Titan re-purchase in-game now (see core/vendor.py), matching
        # OUTPOST_OMEGA_BEE's own rule in set_outpost_omega_two_rules()
        # below.
        world.set_rule(mw.get_location(Rac5TitanVendorLocations.OUTPOST_OMEGA_BEE_TITAN, player), True_())
    if world.options.challenge_mode.value >= 2:
        world.set_rule(mw.get_location(Rac5Locations.OUTPOST_OMEGA_CHAMELEON_GLOVES, player), True_())


def set_outpost_omega_two_rules(world: "RACSizeMatterWorld") -> None:
    player = world.player
    mw = world.multiworld

    world.set_rule(mw.get_location(Rac5VendorLocations.OUTPOST_OMEGA_BEE, player), True_())
    if world.options.enable_skyboard_challenge_skill_points:
        world.set_rule(mw.get_location(Rac5SkillPoints.OUTPOST_OMEGA_AWESOME, player), True_())

    if world.options.all_missions:
        rematch_rule = True_() if world.options.skyboard_challenges.value >= 1 else Has(Rac5Gadgets.POLARIZER)
        world.set_rule(mw.get_location(Rac5CutsceneLocations.OUTPOST_OMEGA_REMATCH, player), rematch_rule)

    world.set_rule(mw.get_location(Rac5TBolts.OUTPOST_OMEGA_DREAM, player), True_())

    if world.options.skyboard_challenges.value >= 1:
        world.set_rule(mw.get_location(Rac5SkyboardChallenges.OUTPOST_OMEGA_VERTIGO, player), True_())
        world.set_rule(mw.get_location(Rac5SkyboardChallenges.OUTPOST_OMEGA_INTERIOR, player), True_())
        world.set_rule(mw.get_location(Rac5SkyboardChallenges.OUTPOST_OMEGA_DANGER, player), True_())
        world.set_rule(mw.get_location(Rac5SkyboardChallenges.OUTPOST_OMEGA_VORTEX, player), True_())
