from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import (
    Rac5Gadgets,
    Rac5Locations,
    Rac5SkillPoints,
    Rac5SkyboardChallenges as RACSMSKY,
    Rac5TBolts,
    Rac5VendorLocations,
    Rac5CutsceneLocations,
)
from rule_builder.rules import Has, HasAll, True_

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_kalidon_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _inside = HasAll(Rac5Gadgets.HYPERSHOT, Rac5Gadgets.SHRINK_RAY)

    # Skill Points
    if world.options.skill_points.value >= 1:
        world.set_rule(mw.get_location(Rac5SkillPoints.KALIDON_EXPLOSIVE, player), _inside)
    if world.options.skill_points.value >= 2:
        world.set_rule(mw.get_location(Rac5SkillPoints.KALIDON_SUPER_LOMBAX, player), _inside)
    if world.options.enable_skyboard_challenge_skill_points:
        world.set_rule(mw.get_location(Rac5SkillPoints.KALIDON_SKYBOARDER, player), True_())

    # Missions
    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.KALIDON_EXPLORE, player), _inside)
    if world.options.all_missions:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.KALIDON_WIN, player), True_())

    # Titanium Bolts
    world.set_rule(mw.get_location(Rac5TBolts.KALIDON_SHIP, player), True_())
    world.set_rule(mw.get_location(Rac5TBolts.KALIDON_FACTORY, player), Has(Rac5Gadgets.HYPERSHOT))
    world.set_rule(mw.get_location(Rac5TBolts.KALIDON_RAMP, player), _inside)

    # Armour
    world.set_rule(mw.get_location(Rac5Locations.KALIDON_CHESTPLATE, player), _inside)
    world.set_rule(mw.get_location(Rac5Locations.KALIDON_BOOTS, player), _inside)

    # Skyboard Challenges (skyboard_challenges >= 1)
    if world.options.skyboard_challenges.value >= 1:
        world.set_rule(mw.get_location(RACSMSKY.KALIDON_LEARNER, player), True_())
        world.set_rule(mw.get_location(RACSMSKY.KALIDON_MASTER, player), True_())
        world.set_rule(mw.get_location(RACSMSKY.KALIDON_TICKET, player), True_())
        world.set_rule(mw.get_location(RACSMSKY.KALIDON_TRICKY, player), True_())

    # Vendors
    world.set_rule(mw.get_location(Rac5VendorLocations.KALIDON_SCORCHER, player), True_())

    # Weapon Mod Vendor — purchasable without owning the weapon (mod_unlock_N
    # is gated purely on this vendor's planet being accessible; see
    # VendorUnlockState.mod_vendor_unlock_weapons).
    world.set_rule(mw.get_location(Rac5VendorLocations.KALIDON_LACERATOR_LOCK, player), True_())
    world.set_rule(mw.get_location(Rac5VendorLocations.KALIDON_CONCUSSION_SPLIT, player), True_())
