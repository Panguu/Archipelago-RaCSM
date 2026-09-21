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
    Rac5Weapons,
)
from ..items import GLITCHES_ITEM_NAME
from ..options import ShrinkRayOptions
from ._helpers import HasChallengeMode, HasShrinkRayDoorAccess, weapon_enabled

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_kalidon_rules(world: "RACSizeMatterWorld") -> None:
    player = world.player
    mw = world.multiworld

    _inside = Has(Rac5Gadgets.HYPERSHOT) & HasShrinkRayDoorAccess(world)

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
        if world.options.skyboard_challenges.value >= 1:
            world.set_rule(mw.get_location(Rac5CutsceneLocations.KALIDON_WIN, player), True_())

    world.set_rule(mw.get_location(Rac5TBolts.KALIDON_SHIP, player), True_())
    world.set_rule(
        mw.get_location(Rac5TBolts.KALIDON_FACTORY, player), Has(Rac5Gadgets.HYPERSHOT) | HasAll(GLITCHES_ITEM_NAME, Rac5Gadgets.SHRINK_RAY)
    )
    world.set_rule(mw.get_location(Rac5TBolts.KALIDON_RAMP, player), _inside)

    world.set_rule(mw.get_location(Rac5Locations.KALIDON_CHESTPLATE, player), _inside)
    world.set_rule(mw.get_location(Rac5Locations.KALIDON_BOOTS, player), _inside | (HasShrinkRayDoorAccess(world) & Has(GLITCHES_ITEM_NAME)))

    if world.options.skyboard_challenges.value >= 1:
        world.set_rule(mw.get_location(Rac5SkyboardChallenges.KALIDON_LEARNER, player), True_())
        world.set_rule(mw.get_location(Rac5SkyboardChallenges.KALIDON_MASTER, player), True_())
        world.set_rule(mw.get_location(Rac5SkyboardChallenges.KALIDON_TICKET, player), True_())
        world.set_rule(mw.get_location(Rac5SkyboardChallenges.KALIDON_TRICKY, player), True_())

    if weapon_enabled(world, Rac5Weapons.SCORCHER):
        world.set_rule(mw.get_location(Rac5VendorLocations.KALIDON_SCORCHER, player), True_())

    if weapon_enabled(world, Rac5Weapons.LACERATOR):
        world.set_rule(mw.get_location(Rac5ModVendorLocations.KALIDON_LACERATOR_LOCK, player), True_())
    if weapon_enabled(world, Rac5Weapons.CONCUSSION_GUN):
        world.set_rule(mw.get_location(Rac5ModVendorLocations.KALIDON_CONCUSSION_SPLIT, player), True_())

    if world.options.shrink_ray_options.value == ShrinkRayOptions.option_locations:
        world.set_rule(
            mw.get_location(Rac5ShrinkRayGrindrail.KALIDON_ENTER_FACTORY, player), Has(Rac5Gadgets.SHRINK_RAY)
        )
        world.set_rule(mw.get_location(Rac5ShrinkRayGrindrail.KALIDON_INSIDE_FACTORY, player), _inside)

    if world.options.challenge_mode.value >= 1:
        tier1 = HasChallengeMode(world, 1)
        if weapon_enabled(world, Rac5Weapons.SCORCHER):
            world.set_rule(mw.get_location(Rac5TitanVendorLocations.KALIDON_SCORCHER_TITAN, player), tier1)
            world.set_rule(mw.get_location(Rac5ModVendorLocations.KALIDON_SCORCHER_SUNFLARE, player), tier1)
        if weapon_enabled(world, Rac5Weapons.AGENTS_OF_DOOM):
            world.set_rule(mw.get_location(Rac5ModVendorLocations.KALIDON_AGENTS_EXPLOSIVE, player), tier1)
        if weapon_enabled(world, Rac5Weapons.SUCK_CANNON):
            world.set_rule(mw.get_location(Rac5ModVendorLocations.KALIDON_SUCK_CANNON_BOUNCE, player), tier1)
        if weapon_enabled(world, Rac5Weapons.BEE_MINE_GLOVE):
            world.set_rule(mw.get_location(Rac5ModVendorLocations.KALIDON_BEE_HIVE_BOMB, player), tier1)
        if weapon_enabled(world, Rac5Weapons.STATIC_BARRIER):
            world.set_rule(mw.get_location(Rac5ModVendorLocations.KALIDON_STATIC_REFLECTION, player), tier1)
    if world.options.challenge_mode.value >= 2:
        world.set_rule(
            mw.get_location(Rac5Locations.KALIDON_CHAMELEON_CHESTPLATE, player), _inside & HasChallengeMode(world, 2)
        )
