from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.weapons import WEAPON_DATA
from ..items import PROGRESSIVE_WEAPON_NAME, WEAPON_DISPLAY_TO_INTERNAL
from ..locations import WEAPON_LEVEL_LOOKUP, WEAPON_MAX_LEVEL_LOCATIONS, WEAPON_SUB_MAX_LEVEL_LOCATIONS
from ._helpers import HasWeapon
from rule_builder.rules import Has

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_weapon_level_rules(world: RACSizeMatterWorld) -> None:
    """Weapon Level Checks option: the rule differs by ProgressiveWeapons mode.
    manual/automatic gate leveling entirely behind received Progressive Weapon
    copies (see core/weapons.py's apply_progressive_leveling()), so the
    location needs that many copies to ever be reachable. off mode has no such
    gate — leveling is free once the weapon is owned — so the location just
    needs the weapon itself.
    """
    tier = world.options.weapon_level_checks.value
    if tier < 1:
        return

    created = set(WEAPON_MAX_LEVEL_LOCATIONS)
    if tier >= 2:
        created |= set(WEAPON_SUB_MAX_LEVEL_LOCATIONS)

    player = world.player
    mw = world.multiworld
    progressive = bool(world.options.progressive_weapons.value)

    for display, internal in WEAPON_DISPLAY_TO_INTERNAL.items():
        for level in range(1, WEAPON_DATA[internal].max_level + 1):
            loc_name = WEAPON_LEVEL_LOOKUP[(internal, level)]
            if loc_name not in created:
                continue
            rule = Has(PROGRESSIVE_WEAPON_NAME[display], level) if progressive else HasWeapon(display)
            world.set_rule(mw.get_location(loc_name, player), rule)
