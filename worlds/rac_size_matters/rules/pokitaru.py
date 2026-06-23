from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import Rac5SkillPoints, Rac5TBolts, Rac5VendorLocations, Rac5CutsceneLocations, Rac5Weapons
from ._helpers import has_projectile_weapon, has_weapon

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_pokitaru_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    # â”€â”€ Skill Points â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if world.options.skill_points.value >= 1:
        mw.get_location(Rac5SkillPoints.POKITARU_TRAIN, player).access_rule = \
            lambda state: has_projectile_weapon(state, player)
        mw.get_location(Rac5SkillPoints.POKITARU_BOAT, player).access_rule = lambda _: True
        mw.get_location(Rac5SkillPoints.POKITARU_COWS, player).access_rule = \
            lambda state: has_weapon(state, player, Rac5Weapons.MOOTATOR)

    # â”€â”€ Missions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if world.options.all_missions:
        mw.get_location(Rac5CutsceneLocations.POKITARU_FIGHT, player).access_rule = lambda _: True

    # â”€â”€ Titanium Bolts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    mw.get_location(Rac5TBolts.POKITARU_ZIPLINE, player).access_rule = lambda _: True
    mw.get_location(Rac5TBolts.POKITARU_HUT,     player).access_rule = lambda _: True

    # â”€â”€ Vendors â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Weapons and gadgets freely accessible on arrival.
    mw.get_location(Rac5VendorLocations.POKITARU_LACERATOR,  player).access_rule = lambda _: True
    mw.get_location(Rac5VendorLocations.POKITARU_ACID,       player).access_rule = lambda _: True
    mw.get_location(Rac5VendorLocations.POKITARU_CONCUSSION, player).access_rule = lambda _: True
    mw.get_location(Rac5VendorLocations.POKITARU_HYPERSHOT,  player).access_rule = lambda _: True
