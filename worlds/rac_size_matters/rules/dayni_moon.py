from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import (
    Rac5ClankChallenges as RACSMCLANK,
    Rac5Gadgets,
    Rac5Locations,
    Rac5SkillPoints,
    Rac5TBolts,
    Rac5VendorLocations,
    Rac5CutsceneLocations,
)
from ._helpers import HasProjectileWeapon
from rule_builder.rules import Has, True_

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_dayni_moon_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _base       = Has(Rac5Gadgets.SPROUT_O_MATIC) & HasProjectileWeapon()
    _shrink_ray = _base & Has(Rac5Gadgets.SHRINK_RAY)

    # Skill Points
    if world.options.skill_points.value >= 1:
        world.set_rule(mw.get_location(Rac5SkillPoints.DAYNI_MOON_BOUNCY, player), _base)
    if world.options.skill_points.value >= 2:
        world.set_rule(mw.get_location(Rac5SkillPoints.DAYNI_MOON_WOOL_PROTEST, player), _base)
    if world.options.enable_clank_challenge_skill_points:
        world.set_rule(mw.get_location(Rac5SkillPoints.DAYNI_MOON_GLADIATOR, player), True_())

    # Missions
    if world.options.all_missions:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.DAYNI_MOON, player), _shrink_ray)
        world.set_rule(mw.get_location(Rac5CutsceneLocations.DAYNI_MOON_LUNA, player), _shrink_ray)
    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.DAYNI_MOON_FIGHT1, player), _shrink_ray)
        world.set_rule(mw.get_location(Rac5CutsceneLocations.DAYNI_MOON_FIGHT2, player), _shrink_ray)

    # Titanium Bolts
    world.set_rule(mw.get_location(Rac5TBolts.DAYNI_MOON_BARN, player), _base)
    world.set_rule(mw.get_location(Rac5TBolts.DAYNI_MOON_MIMIC, player), _shrink_ray)

    # Armour
    world.set_rule(mw.get_location(Rac5Locations.DAYNI_MOON_HELMET, player), _base)

    # Clank Challenges — item rewards (clank_challenges >= 1)
    if world.options.clank_challenges.value >= 1:
        world.set_rule(mw.get_location(RACSMCLANK.DAYNI_MOON_SHOWDOWN, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.DAYNI_MOON_INFINITE, player), True_())

    # Clank Challenges — individual completions (clank_challenges >= 2)
    if world.options.clank_challenges.value >= 2:
        world.set_rule(mw.get_location(RACSMCLANK.DAYNI_MOON_CROWD, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.DAYNI_MOON_REVERSE, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.DAYNI_MOON_BRIDGE, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.DAYNI_MOON_LEAP, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.DAYNI_MOON_WELCOME, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.DAYNI_MOON_ROUND, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.DAYNI_MOON_VARIETY, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.DAYNI_MOON_SAWYER, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.DAYNI_MOON_SMASHER, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.DAYNI_MOON_TOURNAMENT, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.DAYNI_MOON_AROUND, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.DAYNI_MOON_LINE, player), True_())
        world.set_rule(mw.get_location(RACSMCLANK.DAYNI_MOON_HAY, player), True_())

    # Vendors
    world.set_rule(mw.get_location(Rac5VendorLocations.DAYNI_MOON_SHOCK, player), True_())
    world.set_rule(mw.get_location(Rac5VendorLocations.DAYNI_MOON_MAP, player), True_())
