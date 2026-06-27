from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import Rac5Gadgets, Rac5Items
from ._helpers import HasInfobot, HasProjectileWeapon
from rule_builder.rules import HasAll

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_entrance_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    world.set_rule(mw.get_entrance("To Kalidon", player), HasInfobot(Rac5Items.KALIDON))
    world.set_rule(mw.get_entrance("To Metalis", player), HasInfobot(Rac5Items.METALIS))
    world.set_rule(
        mw.get_entrance("To Dreamtime", player),
        HasAll(Rac5Items.OUTPOST_OMEGA, Rac5Gadgets.HYPERSHOT, Rac5Gadgets.SPROUT_O_MATIC),
    )
    world.set_rule(mw.get_entrance("To Outpost Omega", player), HasInfobot(Rac5Items.OUTPOST_OMEGA))
    world.set_rule(
        mw.get_entrance("To Challax", player),
        HasAll(Rac5Items.CHALLAX, Rac5Gadgets.SHRINK_RAY, Rac5Gadgets.POLARIZER),
    )
    world.set_rule(mw.get_entrance("To Dayni Moon", player), HasInfobot(Rac5Items.DAYNI_MOON))
    world.set_rule(
        mw.get_entrance("To Inside Clank", player),
        HasAll(
            Rac5Items.DAYNI_MOON, Rac5Gadgets.SPROUT_O_MATIC, Rac5Gadgets.SHRINK_RAY,
            Rac5Gadgets.HYPERSHOT, Rac5Gadgets.POLARIZER,
        ) & HasProjectileWeapon(),
    )
    world.set_rule(mw.get_entrance("To Quodrona", player), HasInfobot(Rac5Items.QUODRONA))
