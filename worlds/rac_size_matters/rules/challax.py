from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import Rac5Gadgets, Rac5Items, Rac5Locations, Rac5SkillPoints, Rac5TBolts, Rac5VendorLocations, Rac5Weapons
from ._helpers import HasWeapon
from rule_builder.rules import Has, HasAll, True_

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_challax_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _base   = HasAll(Rac5Gadgets.SHRINK_RAY, Rac5Gadgets.POLARIZER)
    _sprout = HasAll(Rac5Gadgets.SHRINK_RAY, Rac5Gadgets.POLARIZER, Rac5Gadgets.SPROUT_O_MATIC)

    # â”€â”€ Skill Points â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if world.options.skill_points.value >= 1:
        world.set_rule(mw.get_location(Rac5SkillPoints.CHALLAX_VARMINTS, player), _sprout)
    if world.options.skill_points.value >= 2:
        world.set_rule(mw.get_location(Rac5SkillPoints.CHALLAX_MASTER, player), _sprout)

    # â”€â”€ Missions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Giant Clank disabled/unreachable â€” METALIS_CLANK and CHALLAX_CLANK are
    # commented out of the location pool in locations.py, so no rule is set here.

    # â”€â”€ Titanium Bolts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    world.set_rule(mw.get_location(Rac5TBolts.CHALLAX_MECH_PAD, player), True_())
    world.set_rule(mw.get_location(Rac5TBolts.CHALLAX_ROOM, player), _base)
    world.set_rule(mw.get_location(Rac5TBolts.CHALLAX_PLANT, player), _sprout)

    # â”€â”€ Armour â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    world.set_rule(
        mw.get_location(Rac5Locations.CHALLAX_HELMET, player),
        _base | Has(Rac5Items.DAYNI_MOON),
    )

    # â”€â”€ Vendors â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _shrink_ray = Has(Rac5Gadgets.SHRINK_RAY)
    world.set_rule(mw.get_location(Rac5VendorLocations.CHALLAX_SNIPER, player), _shrink_ray)
    world.set_rule(mw.get_location(Rac5VendorLocations.CHALLAX_PDA, player), _shrink_ray)

    # â”€â”€ Weapon Mod Vendor â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    world.set_rule(
        mw.get_location(Rac5VendorLocations.CHALLAX_LACERATOR_DOUBLE, player),
        _base & HasWeapon(Rac5Weapons.LACERATOR),
    )
    world.set_rule(
        mw.get_location(Rac5VendorLocations.CHALLAX_ACID_BURN, player),
        _base & HasWeapon(Rac5Weapons.ACID_BOMB_GLOVE),
    )
    world.set_rule(
        mw.get_location(Rac5VendorLocations.CHALLAX_ACID_EPOXY, player),
        _base & HasWeapon(Rac5Weapons.ACID_BOMB_GLOVE),
    )
    world.set_rule(
        mw.get_location(Rac5VendorLocations.CHALLAX_CONCUSSION_LOCK, player),
        _base & HasWeapon(Rac5Weapons.CONCUSSION_GUN),
    )
    world.set_rule(
        mw.get_location(Rac5VendorLocations.CHALLAX_CONCUSSION_CHARGE, player),
        _base & HasWeapon(Rac5Weapons.CONCUSSION_GUN),
    )
    world.set_rule(
        mw.get_location(Rac5VendorLocations.CHALLAX_BEE_WORKER, player),
        _base & HasWeapon(Rac5Weapons.BEE_MINE_GLOVE),
    )
