from typing import TYPE_CHECKING

from rule_builder.rules import Has, HasAll, True_

from ..constants import (
    Rac5CutsceneLocations,
    Rac5Gadgets,
    Rac5Infobots,
    Rac5ModVendorLocations,
    Rac5ShrinkRayGrindrail,
    Rac5SkillPoints,
    Rac5TBolts,
    Rac5TitanVendorLocations,
    Rac5VendorLocations,
)
from ._helpers import HasInfobot

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_quodrona_rules(world: "RACSizeMatterWorld") -> None:
    player = world.player
    mw = world.multiworld

    _checks = HasAll(Rac5Gadgets.SHRINK_RAY, Rac5Gadgets.HYPERSHOT)

    if world.options.skill_points.value >= 2:
        world.set_rule(mw.get_location(Rac5SkillPoints.QUODRONA_ELITE, player), _checks)
        world.set_rule(mw.get_location(Rac5SkillPoints.QUODRONA_STORM, player), _checks)

    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.QUODRONA_CLONE, player), _checks)
        world.set_rule(mw.get_location(Rac5CutsceneLocations.QUODRONA_CHASE, player), _checks)
        world.set_rule(mw.get_location(Rac5CutsceneLocations.QUODRONA_MECHA, player), _checks)
    if world.options.all_missions:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.QUODRONA_FIND, player), _checks)

    world.set_rule(mw.get_location(Rac5TBolts.QUODRONA_DUMMIES, player), _checks)

    # Boss
    world.set_rule(mw.get_location(Rac5CutsceneLocations.QUODRONA_GOAL, player), _checks)

    # Go Mode / victory condition — beating Otto Destruct needs the same
    # Hypershot + Shrink Ray as the boss fight itself, plus actually having
    # reached Quodrona in the first place.
    world.set_rule(
        mw.get_location("Quodrona Completed", player),
        _checks & HasInfobot(Rac5Infobots.QUODRONA),
    )

    world.set_rule(mw.get_location(Rac5VendorLocations.QUODRONA_LASER, player), True_())

    # Weapon Mod Vendor — purchasable without owning the weapon (mod_unlock_N
    # is gated purely on this vendor's planet being accessible; see
    # VendorUnlockState.mod_vendor_unlock_weapons).
    world.set_rule(mw.get_location(Rac5ModVendorLocations.QUODRONA_AGENTS_LAUNCHER, player), True_())
    world.set_rule(mw.get_location(Rac5ModVendorLocations.QUODRONA_SCORCHER_SPITFIRE, player), True_())
    world.set_rule(mw.get_location(Rac5ModVendorLocations.QUODRONA_SNIPER_SPLIT, player), True_())
    world.set_rule(mw.get_location(Rac5ModVendorLocations.QUODRONA_SHOCK_LOCK, player), True_())
    world.set_rule(mw.get_location(Rac5ModVendorLocations.QUODRONA_SHOCK_AFTER, player), True_())

    if world.options.shrink_ray_locations:
        world.set_rule(mw.get_location(Rac5ShrinkRayGrindrail.QUODRONA_ENTRANCE, player), Has(Rac5Gadgets.SHRINK_RAY))
        world.set_rule(mw.get_location(Rac5ShrinkRayGrindrail.QUODRONA_CLONE_TRAINING_ROOM, player), Has(Rac5Gadgets.SHRINK_RAY))

    # Challenge Mode — NG+ Items only controls the item pool, not location
    # existence (see regions.py, which both tables must agree with on
    # which of these locations actually exist).
    if world.options.challenge_mode.value >= 1:
        # Titan variant available once the base weapon is purchasable at
        # its own vendor — buying it there is what actually unlocks the
        # Titan re-purchase in-game now (see core/vendor.py), matching
        # QUODRONA_LASER's own rule above.
        world.set_rule(mw.get_location(Rac5TitanVendorLocations.QUODRONA_LASER_TITAN, player), True_())
        world.set_rule(mw.get_location(Rac5ModVendorLocations.QUODRONA_STATIC_MIRAGE, player), True_())
        world.set_rule(mw.get_location(Rac5ModVendorLocations.QUODRONA_LASER_RICOCHET, player), True_())
