from typing import TYPE_CHECKING

from ..constants import Rac5Infobots, Rac5Planets
from ..locations import (
    GADGET_PICKUP_LOCATIONS,
    GADGET_VENDOR_LOCATIONS,
    WEAPON_MOD_VENDOR_LOCATIONS,
    WEAPON_VENDOR_LOCATIONS,
)
from .planets import Planets

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld

# Planets a random start can land on: each is reachable with nothing but its
# own infobot (see rules/entrances.py), so precollecting it is always enough
# on its own. Dreamtime and Inside Clank need extra gadgets beyond their own
# infobot to enter, and Quodrona is the goal planet, so none of them are ever
# candidates. Ryllus isn't its own candidate either -- it shares Pokitaru's
# merged infobot, so it can't be independently rolled as one of the two picks.
STARTING_PLANET_CANDIDATES: tuple[str, ...] = (
    Rac5Planets.POKITARU,
    Rac5Planets.KALIDON,
    Rac5Planets.METALIS,
    Rac5Planets.OUTPOST_OMEGA,
    Rac5Planets.CHALLAX,
    Rac5Planets.DAYNI_MOON,
)

PLANET_TO_INFOBOT: dict[str, str] = {
    Rac5Planets.POKITARU:      Rac5Infobots.POKITARU,
    Rac5Planets.KALIDON:       Rac5Infobots.KALIDON,
    Rac5Planets.METALIS:       Rac5Infobots.METALIS,
    Rac5Planets.OUTPOST_OMEGA: Rac5Infobots.OUTPOST_OMEGA,
    Rac5Planets.CHALLAX:       Rac5Infobots.CHALLAX,
    Rac5Planets.DAYNI_MOON:    Rac5Infobots.DAYNI_MOON,
}

# The runtime planet id (see core/planets.py's Planets/NEW_PLANET_START_LOAD_ADDR)
# to force-load into on the very first boot-in, when that planet was chosen as
# a random start (see world.py's fill_slot_data()/generate_basic()). Outpost
# Omega 1 (0x06) isn't a real ship-selectable destination -- Outpost Omega 2
# is what a normal infobot-gated arrival lands on.
PLANET_TO_ID: dict[str, int] = {
    Rac5Planets.POKITARU:      Planets.POKITARU.planet_id,
    Rac5Planets.RYLLUS:        Planets.RYLLUS.planet_id,
    Rac5Planets.KALIDON:       Planets.KALIDON.planet_id,
    Rac5Planets.METALIS:       Planets.METALIS.planet_id,
    Rac5Planets.OUTPOST_OMEGA: Planets.OUTPOST_OMEGA_2.planet_id,
    Rac5Planets.CHALLAX:       Planets.CHALLAX.planet_id,
    Rac5Planets.DAYNI_MOON:    Planets.DAYNI_MOON.planet_id,
}

_WEAPON_LOCATION_NAMES = frozenset(WEAPON_VENDOR_LOCATIONS) | frozenset(WEAPON_MOD_VENDOR_LOCATIONS)
_GADGET_LOCATION_NAMES = frozenset(GADGET_PICKUP_LOCATIONS) | frozenset(GADGET_VENDOR_LOCATIONS)


def _planet_location_weight(world: "RACSizeMatterWorld", planet: str) -> int:
    """Locations available on `planet` under the current options. Always counts
    everything except weapon/gadget vendor (and gadget pickup) locations; those
    only count towards the weight when the player is also starting with random
    weapons/gadgets (Starting Weapons/Starting Gadgets > 0). Weapon level checks
    are excluded entirely -- they're all anchored to Pokitaru regardless of
    which weapon they belong to, so they say nothing about a given planet."""
    region = world.multiworld.get_region(planet, world.player)
    count_weapons = world.options.starting_weapons.value > 0
    count_gadgets = world.options.starting_gadgets.value > 0
    weight = 0
    for location in region.locations:
        if location.name in _WEAPON_LOCATION_NAMES:
            weight += count_weapons
        elif location.name in _GADGET_LOCATION_NAMES:
            weight += count_gadgets
        else:
            weight += 1
    return max(weight, 1)


def choose_starting_planets(world: "RACSizeMatterWorld", weighted: bool, count: int = 2) -> list[str]:
    """Pick `count` distinct planets from STARTING_PLANET_CANDIDATES.
    weighted=True (Logic): sampled without replacement, weighted by
    _planet_location_weight, so denser planets are more likely to be picked.
    weighted=False (No Logic): sampled uniformly at random."""
    candidates = list(STARTING_PLANET_CANDIDATES)
    count = min(count, len(candidates))
    if not weighted:
        return world.random.sample(candidates, count)

    weights = [_planet_location_weight(world, planet) for planet in candidates]
    chosen: list[str] = []
    for _ in range(count):
        [pick] = world.random.choices(candidates, weights=weights, k=1)
        idx = candidates.index(pick)
        chosen.append(candidates.pop(idx))
        weights.pop(idx)
    return chosen
