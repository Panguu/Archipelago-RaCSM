from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import RACSMITEM, RACSMLOCATION, RACSMSKILLPOINT, RACSMTBOLT, RACSMVENDORLOCATION
from ._helpers import HasWeapon
from rule_builder.rules import Has, HasAll, True_

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_challax_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _base   = HasAll(RACSMITEM.SHRINK_RAY, RACSMITEM.POLARIZER)
    _sprout = HasAll(RACSMITEM.SHRINK_RAY, RACSMITEM.POLARIZER, RACSMITEM.SPROUT_O_MATIC)

    # ── Skill Points ──────────────────────────────────────────────────────────
    if world.options.skill_points.value >= 1:
        world.set_rule(mw.get_location(RACSMSKILLPOINT.CHALLAX_VARMINTS, player), _sprout)
    if world.options.skill_points.value >= 2:
        world.set_rule(mw.get_location(RACSMSKILLPOINT.CHALLAX_MASTER, player), _sprout)

    # ── Missions ──────────────────────────────────────────────────────────────
    # Giant Clank disabled/unreachable — METALIS_CLANK and CHALLAX_CLANK are
    # commented out of the location pool in locations.py, so no rule is set here.

    # ── Titanium Bolts ────────────────────────────────────────────────────────
    world.set_rule(mw.get_location(RACSMTBOLT.CHALLAX_MECH_PAD, player), True_())
    world.set_rule(mw.get_location(RACSMTBOLT.CHALLAX_ROOM, player), _base)
    world.set_rule(mw.get_location(RACSMTBOLT.CHALLAX_PLANT, player), _sprout)

    # ── Armour ────────────────────────────────────────────────────────────────
    world.set_rule(
        mw.get_location(RACSMLOCATION.CHALLAX_HELMET, player),
        _base | Has(RACSMITEM.DAYNI_MOON),
    )

    # ── Vendors ───────────────────────────────────────────────────────────────
    _shrink_ray = Has(RACSMITEM.SHRINK_RAY)
    world.set_rule(mw.get_location(RACSMVENDORLOCATION.CHALLAX_SNIPER, player), _shrink_ray)
    world.set_rule(mw.get_location(RACSMVENDORLOCATION.CHALLAX_PDA, player), _shrink_ray)

    # ── Weapon Mod Vendor ─────────────────────────────────────────────────────
    world.set_rule(
        mw.get_location(RACSMVENDORLOCATION.CHALLAX_LACERATOR_DOUBLE, player),
        _base & HasWeapon(RACSMITEM.LACERATOR),
    )
    world.set_rule(
        mw.get_location(RACSMVENDORLOCATION.CHALLAX_ACID_BURN, player),
        _base & HasWeapon(RACSMITEM.ACID_BOMB_GLOVE),
    )
    world.set_rule(
        mw.get_location(RACSMVENDORLOCATION.CHALLAX_ACID_EPOXY, player),
        _base & HasWeapon(RACSMITEM.ACID_BOMB_GLOVE),
    )
    world.set_rule(
        mw.get_location(RACSMVENDORLOCATION.CHALLAX_CONCUSSION_LOCK, player),
        _base & HasWeapon(RACSMITEM.CONCUSSION_GUN),
    )
    world.set_rule(
        mw.get_location(RACSMVENDORLOCATION.CHALLAX_CONCUSSION_CHARGE, player),
        _base & HasWeapon(RACSMITEM.CONCUSSION_GUN),
    )
    world.set_rule(
        mw.get_location(RACSMVENDORLOCATION.CHALLAX_BEE_WORKER, player),
        _base & HasWeapon(RACSMITEM.BEE_MINE_GLOVE),
    )
