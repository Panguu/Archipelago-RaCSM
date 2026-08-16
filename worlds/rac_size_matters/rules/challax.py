from typing import TYPE_CHECKING

from rule_builder.rules import Has, HasAll, True_

from ..constants import (
    Rac5CutsceneLocations,
    Rac5Gadgets,
    Rac5Infobots,
    Rac5Locations,
    Rac5ModVendorLocations,
    Rac5ShrinkRayGrindrail,
    Rac5SkillPoints,
    Rac5TBolts,
    Rac5TitanVendorLocations,
    Rac5VendorLocations,
)
from ..options import ShrinkRayOptions

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_challax_rules(world: "RACSizeMatterWorld") -> None:
    player = world.player
    mw = world.multiworld

    _base   = HasAll(Rac5Gadgets.SHRINK_RAY, Rac5Gadgets.POLARIZER)
    _sprout = HasAll(Rac5Gadgets.SHRINK_RAY, Rac5Gadgets.POLARIZER, Rac5Gadgets.SPROUT_O_MATIC)

    if world.options.skill_points.value >= 2:
        world.set_rule(mw.get_location(Rac5SkillPoints.CHALLAX_MASTER, player), _sprout)

    if world.options.all_missions:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.CHALLAX_EXPLORE, player), _base)

    # Giant Clank Challax: locked out entirely by the Giant Clank option (see
    # regions.py/GIANT_CLANK_LOCATIONS and PlanetInventory.giant_clank_allowed)
    # — when on, completed by collecting the Electroshock Chestplate during
    # the sequence, no extra item needed beyond Challax itself being
    # reachable. METALIS_CLANK (the shared trigger bit, not a completion)
    # remains untracked regardless — see locations.py.
    if world.options.giant_clank:
        if world.options.skill_points.value >= 1:
            world.set_rule(mw.get_location(Rac5SkillPoints.CHALLAX_VARMINTS, player), True_())
        if world.options.all_missions:
            world.set_rule(mw.get_location(Rac5CutsceneLocations.CHALLAX_CLANK, player), True_())
        world.set_rule(mw.get_location(Rac5Locations.CHALLAX_CHESTPLATE, player), True_())

    world.set_rule(mw.get_location(Rac5TBolts.CHALLAX_MECH_PAD, player), True_())
    world.set_rule(mw.get_location(Rac5TBolts.CHALLAX_ROOM, player), _base)
    world.set_rule(mw.get_location(Rac5TBolts.CHALLAX_PLANT, player), _sprout)

    world.set_rule(
        mw.get_location(Rac5Locations.CHALLAX_HELMET, player),
        _sprout | Has(Rac5Infobots.DAYNI_MOON),
    )

    _shrink_ray = Has(Rac5Gadgets.SHRINK_RAY)
    world.set_rule(mw.get_location(Rac5VendorLocations.CHALLAX_SNIPER, player), _shrink_ray)
    world.set_rule(mw.get_location(Rac5VendorLocations.CHALLAX_PDA, player), _shrink_ray)

    # Weapon Mod Vendor — purchasable without owning the weapon (mod_unlock_N
    # is gated purely on this vendor's planet being accessible; see
    # VendorUnlockState.mod_vendor_unlock_weapons). _base (Shrink Ray +
    # Polarizer) still gates physically reaching the mod vendor area itself.
    world.set_rule(mw.get_location(Rac5ModVendorLocations.CHALLAX_LACERATOR_DOUBLE, player), _base)
    world.set_rule(mw.get_location(Rac5ModVendorLocations.CHALLAX_ACID_BURN, player), _base)
    world.set_rule(mw.get_location(Rac5ModVendorLocations.CHALLAX_ACID_EPOXY, player), _base)
    world.set_rule(mw.get_location(Rac5ModVendorLocations.CHALLAX_CONCUSSION_LOCK, player), _base)
    world.set_rule(mw.get_location(Rac5ModVendorLocations.CHALLAX_CONCUSSION_CHARGE, player), _base)
    world.set_rule(mw.get_location(Rac5ModVendorLocations.CHALLAX_BEE_WORKER, player), _base)

    if world.options.shrink_ray_options.value == ShrinkRayOptions.option_locations:
        world.set_rule(mw.get_location(Rac5ShrinkRayGrindrail.CHALLAX_GRINDRAIL, player), _shrink_ray)

    # Challenge Mode — NG+ Items only controls the item pool, not location
    # existence (see regions.py, which both tables must agree with on
    # which of these locations actually exist).
    if world.options.challenge_mode.value >= 1:
        world.set_rule(mw.get_location(Rac5Locations.CHALLAX_HYPERBOREAN_HELMET, player), _base)
        # Titan variant available once the base weapon is purchasable at
        # its own vendor — buying it there is what actually unlocks the
        # Titan re-purchase in-game now (see core/vendor.py), matching
        # CHALLAX_SNIPER's own rule above.
        world.set_rule(mw.get_location(Rac5TitanVendorLocations.CHALLAX_SNIPER_TITAN, player), _shrink_ray)
        world.set_rule(mw.get_location(Rac5ModVendorLocations.CHALLAX_SNIPER_SMART_REFLECTOR, player), _base)
        world.set_rule(mw.get_location(Rac5ModVendorLocations.CHALLAX_SHOCK_MULTI_LAUNCHER, player), _base)
        world.set_rule(mw.get_location(Rac5ModVendorLocations.CHALLAX_LASER_PIERCE, player), _base)

