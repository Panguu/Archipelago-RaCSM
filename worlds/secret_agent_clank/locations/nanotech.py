"""Per-operative health progression checks, with stable IDs across NG modes."""
from BaseClasses import Region

from ..constants import SACOperatives
from ..constants.nanotech import (nanotech_levels, nanotech_location_name,
                                  ratchet_nanotech_levels, ratchet_nanotech_location_name)
from ..entities import SACLocation as Location
from ..rules.nanotech import nanotech_access_rule, ratchet_nanotech_access_rule
from .model import SACLocation, SACLocationType

NANOTECH_LOCATIONS = {
    nanotech_location_name(level): SACLocation(
        nanotech_location_name(level), SACLocationType.NANOTECH,
    ) for level in nanotech_levels(True)
}


def create_nanotech_locations(world, menu_region):
    if not world.options.nanotech_checks or SACOperatives.CLANK not in world.options.operatives.value:
        return
    region = Region("Clank Nanotech", world.player, world.multiworld)
    for level in nanotech_levels(world.options.ng_plus.value):
        definition = NANOTECH_LOCATIONS[nanotech_location_name(level)]
        location = Location(world.player, definition.name, world.location_name_to_id[definition.name], region)
        world.set_rule(location, nanotech_access_rule(world, level))
        region.locations.append(location)
    menu_region.connect(region)
    world.multiworld.regions.append(region)

RATCHET_NANOTECH_LOCATIONS = {
    ratchet_nanotech_location_name(level): SACLocation(
        ratchet_nanotech_location_name(level), SACLocationType.NANOTECH,
    ) for level in ratchet_nanotech_levels(True)
}


def create_ratchet_nanotech_locations(world, menu_region):
    if not world.options.ratchet_nanotech_checks or SACOperatives.RATCHET not in world.options.operatives.value:
        return
    region = Region("Ratchet Nanotech", world.player, world.multiworld)
    for level in ratchet_nanotech_levels(world.options.ng_plus.value):
        name = ratchet_nanotech_location_name(level)
        location = Location(world.player, name, world.location_name_to_id[name], region)
        world.set_rule(location, ratchet_nanotech_access_rule(world, level))
        region.locations.append(location)
    menu_region.connect(region)
    world.multiworld.regions.append(region)
