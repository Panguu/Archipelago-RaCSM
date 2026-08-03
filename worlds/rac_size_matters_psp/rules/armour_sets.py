from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import Rac5ArmourSet
from ..locations import NG_PLUS_ARMOUR_SET_LOCATIONS
from ._helpers import HasArmourPiece
from rule_builder.rules import And

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def _full_set(set_display: str) -> list[tuple[str, str]]:
    """All 4 pieces of a single armour set, in piece-index order."""
    return [(set_display, piece) for piece in ("Chestplate", "Helmet", "Gloves", "Boots")]


_ARMOUR_SET_RULES: dict[str, list[tuple[str, str]]] = {
    Rac5ArmourSet.WILDFIRE: _full_set("Wildfire"),
    Rac5ArmourSet.WILDBURST: [
        ("Wildfire", "Chestplate"), ("Sludge Mk9", "Helmet"),
        ("Wildfire", "Gloves"), ("Wildfire", "Boots"),
    ],
    Rac5ArmourSet.SLUDGE_MK9: _full_set("Sludge Mk9"),
    Rac5ArmourSet.CRYSTALLIX: _full_set("Crystallix"),
    Rac5ArmourSet.TRIPLE_WAVE: [
        ("Wildfire", "Helmet"), ("Electroshock", "Chestplate"),
        ("Sludge Mk9", "Gloves"), ("Electroshock", "Boots"),
    ],
    Rac5ArmourSet.SHOCK_CRYSTAL: [
        ("Electroshock", "Helmet"), ("Crystallix", "Chestplate"),
        ("Crystallix", "Gloves"), ("Electroshock", "Boots"),
    ],
    Rac5ArmourSet.ELECTROSHOCK: _full_set("Electroshock"),
    Rac5ArmourSet.MEGA_BOMB: _full_set("Mega Bomb"),
    Rac5ArmourSet.FIRE_BOMB: [
        ("Mega Bomb", "Chestplate"), ("Mega Bomb", "Helmet"),
        ("Wildfire", "Gloves"), ("Mega Bomb", "Boots"),
    ],
    Rac5ArmourSet.HYPERBOREAN: _full_set("Hyperborean"),
    Rac5ArmourSet.ICE_II: [
        ("Hyperborean", "Chestplate"), ("Crystallix", "Helmet"),
        ("Hyperborean", "Gloves"), ("Hyperborean", "Boots"),
    ],
    Rac5ArmourSet.CHAMELEON: _full_set("Chameleon"),
    Rac5ArmourSet.STALKER: [
        ("Wildfire", "Helmet"), ("Chameleon", "Chestplate"),
        ("Sludge Mk9", "Gloves"), ("Chameleon", "Boots"),
    ],
}


def set_armour_set_rules(world: RACSizeMatterWorld) -> None:
    if not world.options.armour_set_checks:
        return

    player = world.player
    mw = world.multiworld
    ng_plus = bool(world.options.ng_plus_items)

    for loc_name, reqs in _ARMOUR_SET_RULES.items():
        # Chameleon/Hyperborean (and Stalker/Ice II, which each need one
        # piece from those two sets) were never created by regions.py when
        # NG+ Items is off — must match that same exclusion, or set_rule()
        # below targets a Location that doesn't exist.
        if not ng_plus and loc_name in NG_PLUS_ARMOUR_SET_LOCATIONS:
            continue
        rule = And(*(HasArmourPiece(sd, pn) for sd, pn in reqs))
        world.set_rule(mw.get_location(loc_name, player), rule)
