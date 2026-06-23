from __future__ import annotations

from typing import TYPE_CHECKING

from .armour_sets import set_armour_set_rules
from .challax import set_challax_rules
from .dayni_moon import set_dayni_moon_rules
from .dreamtime import set_dreamtime_rules
from .entrances import set_entrance_rules
from .inside_clank import set_inside_clank_rules
from .kalidon import set_kalidon_rules
from .metalis import set_metalis_rules
from .outpost_omega import set_outpost_omega_rules
from .pokitaru import set_pokitaru_rules
from .quodrona import set_quodrona_rules
from .ryllus import set_ryllus_rules

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_rules(world: RACSizeMatterWorld) -> None:
    world.multiworld.completion_condition[world.player] = \
        lambda state: state.has("Victory", world.player)

    set_entrance_rules(world)
    set_pokitaru_rules(world)
    set_ryllus_rules(world)
    set_kalidon_rules(world)
    set_metalis_rules(world)
    set_dreamtime_rules(world)
    set_outpost_omega_rules(world)
    set_challax_rules(world)
    set_dayni_moon_rules(world)
    set_inside_clank_rules(world)
    set_quodrona_rules(world)
    set_armour_set_rules(world)
