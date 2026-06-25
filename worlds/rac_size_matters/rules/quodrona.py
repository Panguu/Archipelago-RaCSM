from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import Rac5Gadgets, Rac5SkillPoints, Rac5TBolts, Rac5VendorLocations, Rac5CutsceneLocations, Rac5Weapons
from ._helpers import has_weapon

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_quodrona_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _checks = lambda state: (state.has(Rac5Gadgets.SHRINK_RAY, player)
                             and state.has(Rac5Gadgets.HYPERSHOT, player))

    # Skill Points
    if world.options.skill_points.value >= 2:
        mw.get_location(Rac5SkillPoints.QUODRONA_ELITE,  player).access_rule = _checks
        mw.get_location(Rac5SkillPoints.QUODRONA_STORM,  player).access_rule = _checks

    # Missions
    if world.options.all_cutscenes:
        mw.get_location(Rac5CutsceneLocations.QUODRONA_CLONE, player).access_rule = _checks
        mw.get_location(Rac5CutsceneLocations.QUODRONA_CHASE, player).access_rule = _checks
        mw.get_location(Rac5CutsceneLocations.QUODRONA_MECHA, player).access_rule = _checks
    if world.options.all_missions:
        mw.get_location(Rac5CutsceneLocations.QUODRONA_FIND,  player).access_rule = _checks

    # Titanium Bolts
    mw.get_location(Rac5TBolts.QUODRONA_DUMMIES, player).access_rule = _checks

    # Boss
    mw.get_location(Rac5CutsceneLocations.QUODRONA_GOAL, player).access_rule = _checks

    # Vendors
    mw.get_location(Rac5VendorLocations.QUODRONA_LASER, player).access_rule = lambda _: True

    # Weapon Mod Vendor
    mw.get_location(Rac5VendorLocations.QUODRONA_AGENTS_LAUNCHER,  player).access_rule = \
        lambda state: has_weapon(state, player, Rac5Weapons.AGENTS_OF_DOOM)
    mw.get_location(Rac5VendorLocations.QUODRONA_SCORCHER_SPITFIRE, player).access_rule = \
        lambda state: has_weapon(state, player, Rac5Weapons.SCORCHER)
    mw.get_location(Rac5VendorLocations.QUODRONA_SNIPER_SPLIT,     player).access_rule = \
        lambda state: has_weapon(state, player, Rac5Weapons.SNIPER_MINE)
    mw.get_location(Rac5VendorLocations.QUODRONA_SHOCK_LOCK,       player).access_rule = \
        lambda state: has_weapon(state, player, Rac5Weapons.SHOCK_ROCKET)
    mw.get_location(Rac5VendorLocations.QUODRONA_SHOCK_AFTER,      player).access_rule = \
        lambda state: has_weapon(state, player, Rac5Weapons.SHOCK_ROCKET)
