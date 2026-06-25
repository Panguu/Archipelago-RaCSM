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
    Rac5Weapons,
)
from ._helpers import has_weapon

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_kalidon_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _inside = lambda state: (state.has(Rac5Gadgets.HYPERSHOT, player)
                             and state.has(Rac5Gadgets.SHRINK_RAY, player))

    # Skill Points
    if world.options.skill_points.value >= 1:
        mw.get_location(Rac5SkillPoints.KALIDON_EXPLOSIVE,    player).access_rule = _inside
    if world.options.skill_points.value >= 2:
        mw.get_location(Rac5SkillPoints.KALIDON_SUPER_LOMBAX, player).access_rule = _inside
    if world.options.enable_skyboard_challenge_skill_points:
        mw.get_location(Rac5SkillPoints.KALIDON_SKYBOARDER, player).access_rule = lambda _: True

    # Missions
    if world.options.all_cutscenes:
        mw.get_location(Rac5CutsceneLocations.KALIDON_EXPLORE, player).access_rule = _inside
    if world.options.all_missions:
        mw.get_location(Rac5CutsceneLocations.KALIDON_WIN,     player).access_rule = lambda _: True

    # Titanium Bolts
    mw.get_location(Rac5TBolts.KALIDON_SHIP,    player).access_rule = lambda _: True
    mw.get_location(Rac5TBolts.KALIDON_FACTORY, player).access_rule = \
        lambda state: state.has(Rac5Gadgets.HYPERSHOT, player)
    mw.get_location(Rac5TBolts.KALIDON_RAMP,    player).access_rule = _inside

    # Armour
    mw.get_location(Rac5Locations.KALIDON_CHESTPLATE, player).access_rule = _inside
    mw.get_location(Rac5Locations.KALIDON_BOOTS,      player).access_rule = _inside

    # Skyboard Challenges (skyboard_challenges >= 1)
    if world.options.skyboard_challenges.value >= 1:
        mw.get_location(RACSMSKY.KALIDON_LEARNER, player).access_rule = lambda _: True
        mw.get_location(RACSMSKY.KALIDON_MASTER,  player).access_rule = lambda _: True
        mw.get_location(RACSMSKY.KALIDON_TICKET,  player).access_rule = lambda _: True
        mw.get_location(RACSMSKY.KALIDON_TRICKY,  player).access_rule = lambda _: True

    # Vendors
    mw.get_location(Rac5VendorLocations.KALIDON_SCORCHER, player).access_rule = lambda _: True

    # Weapon Mod Vendor
    mw.get_location(Rac5VendorLocations.KALIDON_LACERATOR_LOCK,   player).access_rule = \
        lambda state: has_weapon(state, player, Rac5Weapons.LACERATOR)
    mw.get_location(Rac5VendorLocations.KALIDON_CONCUSSION_SPLIT, player).access_rule = \
        lambda state: has_weapon(state, player, Rac5Weapons.CONCUSSION_GUN)
