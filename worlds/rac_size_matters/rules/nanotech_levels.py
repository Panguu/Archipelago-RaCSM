from __future__ import annotations

from typing import TYPE_CHECKING

from ..locations import NANOTECH_LEVEL_LOOKUP, nanotech_level_locations_for
from ._helpers import HasGoodExpPlanet

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld

_GOOD_EXP_PLANET_THRESHOLD: int = 20


def set_nanotech_level_rules(world: RACSizeMatterWorld) -> None:
    created = nanotech_level_locations_for(
        world.options.nanotech_level_interval.value, world.options.nanotech_level_max.value,
    )
    if not created:
        return
    if world.options.nanotech_experience_multiplier.value > 1:
        return

    player = world.player
    mw = world.multiworld

    for level, loc_name in NANOTECH_LEVEL_LOOKUP.items():
        if loc_name not in created:
            continue
        if level > _GOOD_EXP_PLANET_THRESHOLD:
            world.set_rule(mw.get_location(loc_name, player), HasGoodExpPlanet())
