from typing import TYPE_CHECKING

from rule_builder.rules import Has, HasAll, True_

from ..constants import (
    Rac5CutsceneLocations,
    Rac5Gadgets,
    Rac5Locations,
    Rac5ModVendorLocations,
    Rac5ShrinkRayGrindrail,
    Rac5SkillPoints,
    Rac5SkyboardChallenges,
    Rac5TBolts,
    Rac5TitanVendorLocations,
    Rac5VendorLocations,
)
from ..items import GLITCHES_ITEM_NAME
from ..options import ShrinkRayOptions

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_kalidon_rules(world: "RACSizeMatterWorld") -> None:
    player = world.player
    mw = world.multiworld

    _inside = HasAll(Rac5Gadgets.HYPERSHOT, Rac5Gadgets.SHRINK_RAY)
    # Universal Tracker glitched-logic only (see world.glitches_item_name):
    # the titanium bolts here are reachable via glitches regardless of
    # gadgets — no separate infobot check needed since reaching this region
    # at all already requires the Kalidon infobot (see rules/entrances.py).
    # Never actually creatable during real generation, so this has no effect
    # there.

    if world.options.skill_points.value >= 1:
        world.set_rule(mw.get_location(Rac5SkillPoints.KALIDON_EXPLOSIVE, player), _inside)
    if world.options.skill_points.value >= 2:
        world.set_rule(mw.get_location(Rac5SkillPoints.KALIDON_SUPER_LOMBAX, player), _inside)
    if world.options.enable_skyboard_challenge_skill_points:
        world.set_rule(mw.get_location(Rac5SkillPoints.KALIDON_SKYBOARDER, player), True_())

    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.KALIDON_EXPLORE, player), _inside)
    if world.options.all_missions:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.KALIDON_SEARCH, player), _inside)
        # Skyboard racing is an alternate route around needing Shrink Ray
        # here — only required when that route isn't available.
        win_rule = True_() if world.options.skyboard_challenges.value >= 1 else Has(Rac5Gadgets.SHRINK_RAY)
        world.set_rule(mw.get_location(Rac5CutsceneLocations.KALIDON_WIN, player), win_rule)

    world.set_rule(mw.get_location(Rac5TBolts.KALIDON_SHIP, player), True_())
    world.set_rule(
        mw.get_location(Rac5TBolts.KALIDON_FACTORY, player), Has(Rac5Gadgets.HYPERSHOT) | Has(GLITCHES_ITEM_NAME)
    )
    world.set_rule(mw.get_location(Rac5TBolts.KALIDON_RAMP, player), _inside)

    world.set_rule(mw.get_location(Rac5Locations.KALIDON_CHESTPLATE, player), _inside)
    world.set_rule(mw.get_location(Rac5Locations.KALIDON_BOOTS, player), _inside)

    if world.options.skyboard_challenges.value >= 1:
        world.set_rule(mw.get_location(Rac5SkyboardChallenges.KALIDON_LEARNER, player), True_())
        world.set_rule(mw.get_location(Rac5SkyboardChallenges.KALIDON_MASTER, player), True_())
        world.set_rule(mw.get_location(Rac5SkyboardChallenges.KALIDON_TICKET, player), True_())
        world.set_rule(mw.get_location(Rac5SkyboardChallenges.KALIDON_TRICKY, player), True_())

    world.set_rule(mw.get_location(Rac5VendorLocations.KALIDON_SCORCHER, player), True_())

    # Weapon Mod Vendor — purchasable without owning the weapon (mod_unlock_N
    # is gated purely on this vendor's planet being accessible; see
    # VendorUnlockState.mod_vendor_unlock_weapons).
    world.set_rule(mw.get_location(Rac5ModVendorLocations.KALIDON_LACERATOR_LOCK, player), True_())
    world.set_rule(mw.get_location(Rac5ModVendorLocations.KALIDON_CONCUSSION_SPLIT, player), True_())

    if world.options.shrink_ray_options.value == ShrinkRayOptions.option_locations:
        world.set_rule(
            mw.get_location(Rac5ShrinkRayGrindrail.KALIDON_ENTER_FACTORY, player), Has(Rac5Gadgets.SHRINK_RAY)
        )
        world.set_rule(mw.get_location(Rac5ShrinkRayGrindrail.KALIDON_INSIDE_FACTORY, player), _inside)

    # Challenge Mode — NG+ Items only controls the item pool, not location
    # existence (see regions.py, which both tables must agree with on
    # which of these locations actually exist).
    if world.options.challenge_mode.value >= 1:
        # Titan variant available once the base weapon is purchasable at
        # its own vendor — buying it there is what actually unlocks the
        # Titan re-purchase in-game now (see core/vendor.py), matching
        # KALIDON_SCORCHER's own rule above.
        world.set_rule(mw.get_location(Rac5TitanVendorLocations.KALIDON_SCORCHER_TITAN, player), True_())
        world.set_rule(mw.get_location(Rac5ModVendorLocations.KALIDON_AGENTS_EXPLOSIVE, player), True_())
        world.set_rule(mw.get_location(Rac5ModVendorLocations.KALIDON_SCORCHER_SUNFLARE, player), True_())
        world.set_rule(mw.get_location(Rac5ModVendorLocations.KALIDON_SUCK_CANNON_BOUNCE, player), True_())
        world.set_rule(mw.get_location(Rac5ModVendorLocations.KALIDON_BEE_HIVE_BOMB, player), True_())
        world.set_rule(mw.get_location(Rac5ModVendorLocations.KALIDON_STATIC_REFLECTION, player), True_())
    if world.options.challenge_mode.value >= 2:
        world.set_rule(mw.get_location(Rac5Locations.KALIDON_CHAMELEON_CHESTPLATE, player), _inside)
