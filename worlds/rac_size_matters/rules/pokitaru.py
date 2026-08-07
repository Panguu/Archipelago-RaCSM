from __future__ import annotations

from typing import TYPE_CHECKING

from rule_builder.rules import True_

from ..constants import (
    Rac5CutsceneLocations,
    Rac5Locations,
    Rac5SkillPoints,
    Rac5TBolts,
    Rac5VendorLocations,
    Rac5Weapons,
)
from ._helpers import HasProjectileWeapon, HasWeapon

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_pokitaru_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    if world.options.skill_points.value >= 1:
        world.set_rule(mw.get_location(Rac5SkillPoints.POKITARU_TRAIN, player), HasProjectileWeapon())
        world.set_rule(mw.get_location(Rac5SkillPoints.POKITARU_BOAT, player), True_())
        world.set_rule(mw.get_location(Rac5SkillPoints.POKITARU_COWS, player), HasWeapon(Rac5Weapons.MOOTATOR))

    if world.options.all_missions:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.POKITARU_RESCUE, player), True_())
        world.set_rule(mw.get_location(Rac5CutsceneLocations.POKITARU_FIGHT, player), True_())

    world.set_rule(mw.get_location(Rac5TBolts.POKITARU_ZIPLINE, player), True_())
    world.set_rule(mw.get_location(Rac5TBolts.POKITARU_HUT, player), True_())

    world.set_rule(mw.get_location(Rac5Locations.POKITARU_CHESTPLATE, player), HasProjectileWeapon())
    world.set_rule(mw.get_location(Rac5Locations.POKITARU_GLOVES, player), HasProjectileWeapon())

    # Weapons and gadgets freely accessible on arrival.
    world.set_rule(mw.get_location(Rac5VendorLocations.POKITARU_LACERATOR, player), True_())
    world.set_rule(mw.get_location(Rac5VendorLocations.POKITARU_ACID, player), True_())
    world.set_rule(mw.get_location(Rac5VendorLocations.POKITARU_CONCUSSION, player), True_())
    world.set_rule(mw.get_location(Rac5VendorLocations.POKITARU_HYPERSHOT, player), True_())
