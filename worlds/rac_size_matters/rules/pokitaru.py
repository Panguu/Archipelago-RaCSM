from typing import TYPE_CHECKING

from rule_builder.rules import Has, True_

from ..constants import (
    Rac5CutsceneLocations,
    Rac5Locations,
    Rac5SkillPoints,
    Rac5TBolts,
    Rac5TitanVendorLocations,
    Rac5VendorLocations,
    Rac5Weapons,
)
from ..items import GLITCHES_ITEM_NAME
from ._helpers import HasChallengeMode, HasProjectileWeapon, HasWeapon, weapon_enabled

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld

_GLITCH = Has(GLITCHES_ITEM_NAME)


def set_pokitaru_rules(world: "RACSizeMatterWorld") -> None:
    player = world.player
    mw = world.multiworld

    if world.options.skill_points.value >= 1:
        world.set_rule(mw.get_location(Rac5SkillPoints.POKITARU_TRAIN, player), HasProjectileWeapon() | _GLITCH)
        world.set_rule(mw.get_location(Rac5SkillPoints.POKITARU_BOAT, player), HasProjectileWeapon() | _GLITCH)
    if world.options.skill_points.value >= 2:
        world.set_rule(mw.get_location(Rac5SkillPoints.POKITARU_COWS, player), HasWeapon(Rac5Weapons.MOOTATOR))

    if world.options.all_missions:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.POKITARU_RESCUE, player), HasProjectileWeapon() | _GLITCH)
        world.set_rule(mw.get_location(Rac5CutsceneLocations.POKITARU_FIGHT, player), HasProjectileWeapon() | _GLITCH)

    world.set_rule(mw.get_location(Rac5TBolts.POKITARU_ZIPLINE, player), HasProjectileWeapon() | _GLITCH)
    world.set_rule(mw.get_location(Rac5TBolts.POKITARU_HUT, player), HasProjectileWeapon() | _GLITCH)

    world.set_rule(mw.get_location(Rac5Locations.POKITARU_CHESTPLATE, player), HasProjectileWeapon() | _GLITCH)
    world.set_rule(mw.get_location(Rac5Locations.POKITARU_GLOVES, player), HasProjectileWeapon() | _GLITCH)

    if weapon_enabled(world, Rac5Weapons.LACERATOR):
        world.set_rule(mw.get_location(Rac5VendorLocations.POKITARU_LACERATOR, player), True_())
    if weapon_enabled(world, Rac5Weapons.ACID_BOMB_GLOVE):
        world.set_rule(mw.get_location(Rac5VendorLocations.POKITARU_ACID, player), True_())
    if weapon_enabled(world, Rac5Weapons.CONCUSSION_GUN):
        world.set_rule(mw.get_location(Rac5VendorLocations.POKITARU_CONCUSSION, player), True_())
    world.set_rule(mw.get_location(Rac5VendorLocations.POKITARU_HYPERSHOT, player), True_())

    if world.options.challenge_mode.value >= 1:
        tier1 = HasChallengeMode(world, 1)
        world.set_rule(
            mw.get_location(Rac5Locations.POKITARU_HYPERBOREAN_GLOVES, player),
            (HasProjectileWeapon() | _GLITCH) & tier1,
        )
        if weapon_enabled(world, Rac5Weapons.RYNO):
            world.set_rule(mw.get_location(Rac5VendorLocations.POKITARU_RYNO, player), tier1)
        if weapon_enabled(world, Rac5Weapons.LACERATOR):
            world.set_rule(mw.get_location(Rac5TitanVendorLocations.POKITARU_LACERATOR_TITAN, player), tier1)
        if weapon_enabled(world, Rac5Weapons.ACID_BOMB_GLOVE):
            world.set_rule(mw.get_location(Rac5TitanVendorLocations.POKITARU_ACID_TITAN, player), tier1)
        if weapon_enabled(world, Rac5Weapons.CONCUSSION_GUN):
            world.set_rule(mw.get_location(Rac5TitanVendorLocations.POKITARU_CONCUSSION_TITAN, player), tier1)
    if world.options.challenge_mode.value >= 2:
        world.set_rule(mw.get_location(Rac5Locations.POKITARU_CHAMELEON_BOOTS, player), HasChallengeMode(world, 2))
