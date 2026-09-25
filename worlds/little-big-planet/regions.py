from BaseClasses import ItemClassification, Region
from rule_builder.rules import Has

from .content_packs import PACKS, PACK_LOCATIONS, UNLOCK_NAMES
from .items import LBPItem
from .levels import LEVELS
from .locations import LBPLocation

MENU = 'Menu'


def level_region_name(guid):
    return f'{LEVELS[guid]["name"]} [{guid}]'


def victory_name(world, guid):
    if len(world.goal_guids) == 1:
        return 'LittleBigPlanet Victory'
    return f'LittleBigPlanet Victory: {LEVELS[guid]["name"]}'


def create_regions(world):
    player, multiworld = world.player, world.multiworld
    menu = Region(MENU, player, multiworld)
    regions = {guid: Region(level_region_name(guid), player, multiworld) for guid in world.levels}
    for data in world.enabled:
        location = LBPLocation(player, data.name, data.code, regions[data.level])
        location.data = data
        regions[data.level].locations.append(location)
    for region in regions.values():
        menu.connect(region)

    packs = []
    for slot in sorted(world.costume_packs):
        region = Region(f'My Content: {PACKS[slot]["name"]}', player, multiworld)
        pack = PACK_LOCATIONS[slot]
        region.locations.append(LBPLocation(player, pack['name'], pack['id'], region))
        world.create_entrance(menu, region, Has(UNLOCK_NAMES[slot]))
        packs.append(region)

    for guid in sorted(world.goal_guids):
        victory = LBPLocation(player, victory_name(world, guid), None, regions[guid])
        victory.place_locked_item(LBPItem('Victory', ItemClassification.progression, None, player))
        regions[guid].locations.append(victory)

    multiworld.regions += [menu, *regions.values(), *packs]
