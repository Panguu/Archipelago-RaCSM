from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import Rac5Gadgets, Rac5SkillPoints, Rac5TBolts, Rac5VendorLocations, Rac5CutsceneLocations
from rule_builder.rules import HasAll, True_

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_quodrona_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _checks = HasAll(Rac5Gadgets.SHRINK_RAY, Rac5Gadgets.HYPERSHOT)

    # Skill Points
    if world.options.skill_points.value >= 2:
        world.set_rule(mw.get_location(Rac5SkillPoints.QUODRONA_ELITE, player), _checks)
        world.set_rule(mw.get_location(Rac5SkillPoints.QUODRONA_STORM, player), _checks)

    # Missions
    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.QUODRONA_CLONE, player), _checks)
        world.set_rule(mw.get_location(Rac5CutsceneLocations.QUODRONA_CHASE, player), _checks)
        world.set_rule(mw.get_location(Rac5CutsceneLocations.QUODRONA_MECHA, player), _checks)
    if world.options.all_missions:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.QUODRONA_FIND, player), _checks)

    # Titanium Bolts
    world.set_rule(mw.get_location(Rac5TBolts.QUODRONA_DUMMIES, player), _checks)

    # Boss
    world.set_rule(mw.get_location(Rac5CutsceneLocations.QUODRONA_GOAL, player), _checks)

    # Vendors
    world.set_rule(mw.get_location(Rac5VendorLocations.QUODRONA_LASER, player), True_())

    # Weapon Mod Vendor — purchasable without owning the weapon (mod_unlock_N
    # is gated purely on this vendor's planet being accessible; see
    # VendorUnlockState.mod_vendor_unlock_weapons).
    world.set_rule(mw.get_location(Rac5VendorLocations.QUODRONA_AGENTS_LAUNCHER, player), True_())
    world.set_rule(mw.get_location(Rac5VendorLocations.QUODRONA_SCORCHER_SPITFIRE, player), True_())
    world.set_rule(mw.get_location(Rac5VendorLocations.QUODRONA_SNIPER_SPLIT, player), True_())
    world.set_rule(mw.get_location(Rac5VendorLocations.QUODRONA_SHOCK_LOCK, player), True_())
    world.set_rule(mw.get_location(Rac5VendorLocations.QUODRONA_SHOCK_AFTER, player), True_())
