from __future__ import annotations

from typing import TYPE_CHECKING

from ..locations import NANOTECH_LEVEL_LOOKUP
from ._helpers import HasGoodExpPlanet

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld

# Nanotech Levels above this need access to a good EXP planet — mirrors
# rules/weapon_levels.py's HasGoodExpPlanet gating.
_GOOD_EXP_PLANET_THRESHOLD: int = 20


def set_nanotech_level_rules(world: RACSizeMatterWorld) -> None:
    """Nanotech Level Checks option: levels above 20 need HasGoodExpPlanet(),
    levels 6-20 are otherwise unrestricted."""
    if not world.options.nanotech_level_checks:
        return

    player = world.player
    mw = world.multiworld

    for level, loc_name in NANOTECH_LEVEL_LOOKUP.items():
        if level > _GOOD_EXP_PLANET_THRESHOLD:
            world.set_rule(mw.get_location(loc_name, player), HasGoodExpPlanet())
