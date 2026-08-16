from __future__ import annotations

from typing import TYPE_CHECKING

from rule_builder.rules import Has

from ..constants import Rac5Weapons
from ..core.weapons import WEAPON_DATA
from ..items import PROGRESSIVE_WEAPON_NAME, WEAPON_DISPLAY_TO_INTERNAL
from ..locations import (
    CHALLENGE_MODE_MAX_LEVEL_LOCATIONS,
    CHALLENGE_MODE_SUB_MAX_LEVEL_LOCATIONS,
    NG_PLUS_WEAPON_LEVEL_LOCATIONS,
    WEAPON_LEVEL_LOOKUP,
    WEAPON_MAX_LEVEL_LOCATIONS,
    WEAPON_SUB_MAX_LEVEL_LOCATIONS,
)
from ..options import WeaponLevelChecks
from ._helpers import HasGoodExpPlanet, HasWeapon

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld

# These three weapons only gain experience at a meaningful rate on specific
# planets/gadget combos (see HasGoodExpPlanet) — every other weapon levels
# fine anywhere, so this extra requirement is scoped to just these.
_NEEDS_GOOD_EXP_PLANET: frozenset[str] = frozenset({
    Rac5Weapons.RYNO, Rac5Weapons.LASER_TRACER, Rac5Weapons.STATIC_BARRIER,
})


def set_weapon_level_rules(world: RACSizeMatterWorld) -> None:
    """Weapon Level Checks option: rule differs by ProgressiveWeapons mode.
    manual/automatic gate leveling behind received Progressive Weapon copies,
    so the location needs that many copies; off mode just needs the weapon.
    RYNO/Laser Tracer/Static Barrier also need HasGoodExpPlanet().
    """
    tier = world.options.weapon_level_checks.value
    if tier == WeaponLevelChecks.option_off:
        return

    wants_level_4 = tier in (
        WeaponLevelChecks.option_level_4, WeaponLevelChecks.option_level_4_and_8, WeaponLevelChecks.option_all,
    )
    wants_level_8 = tier in (
        WeaponLevelChecks.option_level_8, WeaponLevelChecks.option_level_4_and_8, WeaponLevelChecks.option_all,
    )
    wants_sub_levels = tier == WeaponLevelChecks.option_all

    created: set[str] = set()
    if wants_level_4:
        created |= set(WEAPON_MAX_LEVEL_LOCATIONS)
    if wants_sub_levels:
        created |= set(WEAPON_SUB_MAX_LEVEL_LOCATIONS)
    if not world.options.ng_plus_items:
        # RYNO's own levels never got created (regions.py excludes them the
        # same way) — must match here too, or set_rule() below targets a
        # Location that was never actually built.
        created -= NG_PLUS_WEAPON_LEVEL_LOCATIONS
    if world.options.challenge_mode.value >= 1:
        # Levels 5-8 (Challenge Mode Titan variant) — same gating as
        # regions.py uses to create them.
        if wants_level_8:
            created |= set(CHALLENGE_MODE_MAX_LEVEL_LOCATIONS)
        if wants_sub_levels:
            created |= set(CHALLENGE_MODE_SUB_MAX_LEVEL_LOCATIONS)

    player = world.player
    mw = world.multiworld
    progressive = bool(world.options.progressive_weapons.value)

    for display, internal in WEAPON_DISPLAY_TO_INTERNAL.items():
        for level in range(2, WEAPON_DATA[internal].max_level + 1):
            loc_name = WEAPON_LEVEL_LOOKUP[(internal, level)]
            if loc_name not in created:
                continue
            rule = Has(PROGRESSIVE_WEAPON_NAME[display], level) if progressive else HasWeapon(display)
            if display in _NEEDS_GOOD_EXP_PLANET:
                rule = rule & HasGoodExpPlanet()
            world.set_rule(mw.get_location(loc_name, player), rule)
