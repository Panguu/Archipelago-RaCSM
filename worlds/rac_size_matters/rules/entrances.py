from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import RACSMITEM
from ._helpers import has_projectile_weapon, infobot

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_entrance_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    mw.get_entrance("To Kalidon",       player).access_rule = infobot(RACSMITEM.KALIDON, player)
    mw.get_entrance("To Metalis",       player).access_rule = infobot(RACSMITEM.METALIS, player)
    mw.get_entrance("To Dreamtime",     player).access_rule = \
        lambda state: (state.has(RACSMITEM.OUTPOST_OMEGA, player)
                       and state.has(RACSMITEM.HYPERSHOT, player)
                       and state.has(RACSMITEM.SPROUT_O_MATIC, player))
    mw.get_entrance("To Outpost Omega", player).access_rule = infobot(RACSMITEM.OUTPOST_OMEGA, player)
    mw.get_entrance("To Challax",       player).access_rule = \
        lambda state: (state.has(RACSMITEM.CHALLAX, player)
                       and state.has(RACSMITEM.SHRINK_RAY, player)
                       and state.has(RACSMITEM.POLARIZER, player))
    mw.get_entrance("To Dayni Moon",    player).access_rule = infobot(RACSMITEM.DAYNI_MOON, player)
    mw.get_entrance("To Inside Clank",  player).access_rule = \
        lambda state: (state.has(RACSMITEM.DAYNI_MOON, player)
                       and state.has(RACSMITEM.SPROUT_O_MATIC, player)
                       and state.has(RACSMITEM.SHRINK_RAY, player)
                       and has_projectile_weapon(state, player)
                       and state.has(RACSMITEM.HYPERSHOT, player)
                       and state.has(RACSMITEM.POLARIZER, player))
    mw.get_entrance("To Quodrona",      player).access_rule = infobot(RACSMITEM.QUODRONA, player)
