from __future__ import annotations

from typing import TYPE_CHECKING

from ..locations import NANOTECH_LEVEL_LOOKUP, nanotech_level_locations_for
from ._helpers import HasGoodExpPlanet

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld

# Nanotech Levels above this need access to a good EXP planet — mirrors
# rules/weapon_levels.py's HasGoodExpPlanet gating.
_GOOD_EXP_PLANET_THRESHOLD: int = 20


def set_nanotech_level_rules(world: RACSizeMatterWorld) -> None:
    """Nanotech Level Interval/Max options: levels above 20 need
    HasGoodExpPlanet(), levels 6-20 are otherwise unrestricted. Only sets a
    rule for levels regions.py actually created a location for (see
    nanotech_level_locations_for) — both must agree on the same set."""
    created = nanotech_level_locations_for(
        world.options.nanotech_level_interval.value, world.options.nanotech_level_max.value,
    )
    if not created:
        return

    player = world.player
    mw = world.multiworld

    for level, loc_name in NANOTECH_LEVEL_LOOKUP.items():
        if loc_name not in created:
            continue
        if level > _GOOD_EXP_PLANET_THRESHOLD:
            world.set_rule(mw.get_location(loc_name, player), HasGoodExpPlanet())
