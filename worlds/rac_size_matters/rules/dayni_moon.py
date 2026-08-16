from typing import TYPE_CHECKING

from rule_builder.rules import And, Has, HasAll, True_

from ..constants import (
    Rac5ClankChallenges,
    Rac5CutsceneLocations,
    Rac5Gadgets,
    Rac5Locations,
    Rac5ShrinkRayGrindrail,
    Rac5SkillPoints,
    Rac5TBolts,
    Rac5TitanVendorLocations,
    Rac5VendorLocations,
    Rac5Weapons,
)
from ._helpers import HasProjectileWeapon, HasTitanPrereq

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_dayni_moon_rules(world: "RACSizeMatterWorld") -> None:
    player = world.player
    mw = world.multiworld

    _base       = Has(Rac5Gadgets.SPROUT_O_MATIC) & HasProjectileWeapon()
    _shrink_ray = _base & Has(Rac5Gadgets.SHRINK_RAY)

    if world.options.skill_points.value >= 1:
        world.set_rule(mw.get_location(Rac5SkillPoints.DAYNI_MOON_BOUNCY, player), _base)
    if world.options.skill_points.value >= 2:
        world.set_rule(mw.get_location(Rac5SkillPoints.DAYNI_MOON_WOOL_PROTEST, player), _base)
    if world.options.enable_clank_challenge_skill_points:
        world.set_rule(mw.get_location(Rac5SkillPoints.DAYNI_MOON_GLADIATOR, player), True_())

    if world.options.all_missions:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.DAYNI_MOON, player), _base)
        world.set_rule(mw.get_location(Rac5CutsceneLocations.DAYNI_MOON_LUNA, player), _base)
    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.DAYNI_MOON_FIGHT1, player), _base)
        world.set_rule(mw.get_location(Rac5CutsceneLocations.DAYNI_MOON_FIGHT2, player), _base)

    world.set_rule(mw.get_location(Rac5TBolts.DAYNI_MOON_BARN, player), _base)
    world.set_rule(mw.get_location(Rac5TBolts.DAYNI_MOON_MIMIC, player), _shrink_ray)

    world.set_rule(mw.get_location(Rac5Locations.DAYNI_MOON_HELMET, player), _base)

    # Clank Challenges — item rewards (clank_challenges >= 1)
    if world.options.clank_challenges.value >= 1:
        world.set_rule(mw.get_location(Rac5ClankChallenges.DAYNI_MOON_SHOWDOWN, player), True_())
        world.set_rule(mw.get_location(Rac5ClankChallenges.DAYNI_MOON_INFINITE, player), True_())

    # Clank Challenges — individual completions (clank_challenges >= 2)
    if world.options.clank_challenges.value >= 2:
        world.set_rule(mw.get_location(Rac5ClankChallenges.DAYNI_MOON_CROWD, player), True_())
        world.set_rule(mw.get_location(Rac5ClankChallenges.DAYNI_MOON_REVERSE, player), True_())
        world.set_rule(mw.get_location(Rac5ClankChallenges.DAYNI_MOON_BRIDGE, player), True_())
        world.set_rule(mw.get_location(Rac5ClankChallenges.DAYNI_MOON_LEAP, player), True_())
        world.set_rule(mw.get_location(Rac5ClankChallenges.DAYNI_MOON_WELCOME, player), True_())
        world.set_rule(mw.get_location(Rac5ClankChallenges.DAYNI_MOON_ROUND, player), True_())
        world.set_rule(mw.get_location(Rac5ClankChallenges.DAYNI_MOON_VARIETY, player), True_())
        world.set_rule(mw.get_location(Rac5ClankChallenges.DAYNI_MOON_SAWYER, player), True_())
        world.set_rule(mw.get_location(Rac5ClankChallenges.DAYNI_MOON_SMASHER, player), True_())
        world.set_rule(mw.get_location(Rac5ClankChallenges.DAYNI_MOON_TOURNAMENT, player), True_())
        world.set_rule(mw.get_location(Rac5ClankChallenges.DAYNI_MOON_AROUND, player), True_())
        world.set_rule(mw.get_location(Rac5ClankChallenges.DAYNI_MOON_LINE, player), True_())
        world.set_rule(mw.get_location(Rac5ClankChallenges.DAYNI_MOON_HAY, player), True_())

    world.set_rule(mw.get_location(Rac5VendorLocations.DAYNI_MOON_SHOCK, player), True_())
    world.set_rule(mw.get_location(Rac5VendorLocations.DAYNI_MOON_MAP, player), True_())

    if world.options.shrink_ray_locations:
        world.set_rule(
            mw.get_location(
                Rac5ShrinkRayGrindrail.DAYNI_MOON_TITANIUM_BOLT_ENTRANCE, player),
                And(
                    HasAll(Rac5Gadgets.SHRINK_RAY, Rac5Gadgets.SPROUT_O_MATIC, Rac5Gadgets.SPROUT_O_MATIC),
                    HasProjectileWeapon(),
                    ),
        )

    # Challenge Mode — NG+ Items only controls the item pool, not location
    # existence (see regions.py, which both tables must agree with on
    # which of these locations actually exist).
    if world.options.challenge_mode.value >= 1:
        # Mootator has no base vendor listing at all — unlike every other
        # Titan-eligible weapon, its Titan purchase can't piggyback on a
        # base-purchase rule, so it still needs real progression (see
        # core/vendor.py's _is_titan_pending()/_purchasable_names()).
        world.set_rule(
            mw.get_location(Rac5TitanVendorLocations.DAYNI_MOON_MOOTATOR_TITAN, player),
            HasTitanPrereq(world, Rac5Weapons.MOOTATOR),
        )
        # Shock Rocket's Titan variant available once the base weapon is
        # purchasable at its own vendor — buying it there is what actually
        # unlocks the Titan re-purchase in-game now, matching
        # DAYNI_MOON_SHOCK's own rule above.
        world.set_rule(mw.get_location(Rac5TitanVendorLocations.DAYNI_MOON_SHOCK_TITAN, player), True_())
