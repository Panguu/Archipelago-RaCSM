from __future__ import annotations

from typing import TYPE_CHECKING

from rule_builder.rules import HasAll

from ..constants import Rac5Gadgets, Rac5Infobots
from ._helpers import HasInfobot, HasProjectileWeapon

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_entrance_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    world.set_rule(mw.get_entrance("To Pokitaru", player), HasInfobot(Rac5Infobots.POKITARU))
    world.set_rule(mw.get_entrance("To Ryllus", player), HasInfobot(Rac5Infobots.POKITARU))
    world.set_rule(mw.get_entrance("To Kalidon", player), HasInfobot(Rac5Infobots.KALIDON))
    world.set_rule(mw.get_entrance("To Metalis", player), HasInfobot(Rac5Infobots.METALIS))
    world.set_rule(
        mw.get_entrance("To Dreamtime", player),
        HasAll(Rac5Infobots.OUTPOST_OMEGA, Rac5Gadgets.HYPERSHOT, Rac5Gadgets.SPROUT_O_MATIC),
    )
    world.set_rule(mw.get_entrance("To Outpost Omega", player), HasInfobot(Rac5Infobots.OUTPOST_OMEGA))
    world.set_rule(
        mw.get_entrance("To Challax", player),
        HasAll(Rac5Infobots.CHALLAX),
    )
    world.set_rule(mw.get_entrance("To Dayni Moon", player), HasInfobot(Rac5Infobots.DAYNI_MOON))
    world.set_rule(
        mw.get_entrance("To Inside Clank", player),
        HasAll(
            Rac5Infobots.DAYNI_MOON, Rac5Gadgets.SPROUT_O_MATIC, Rac5Gadgets.SHRINK_RAY,
            Rac5Gadgets.HYPERSHOT,
        ) & HasProjectileWeapon(),
    )
    world.set_rule(mw.get_entrance("To Quodrona", player), HasInfobot(Rac5Infobots.QUODRONA))
