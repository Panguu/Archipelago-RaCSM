"""Stable DLC identities shared by generation, constants and runtime access."""
if __package__:
    from .chapters import LEVEL_CHAPTER
else:
    from chapters import LEVEL_CHAPTER

# Explicit IDs must not change when packs are reordered or new DLC is added.
DLC_KITS = {
    'creator_pack': ('Creator Pack 1', 'LBPCreatorPack', 1249800000),
    'history_kit': ('History Level Kit', 'LBPHistoryKit', 1249800001),
    'incredibles_kit': ('The Incredibles Level Kit', 'LBPIncrediblesKit', 1249800002),
    'metal_gear_solid_kit': ('Metal Gear Solid Premium Level Kit', 'LBPMetalGearSolidKit', 1249800003),
    'monster_kit': ('Monsters Level Kit', 'LBPMonsterKit', 1249800004),
    'pirates_of_the_caribbean_kit': ('Pirates of the Caribbean Premium Level Kit', 'LBPPiratesOfTheCaribbeanKit', 1249800005),
    'marvel_kit': ('Marvel Level Kit', 'LBPMarvelKit', 1249800007),
    'goty_bonus': ('GOTY Edition Community Levels', 'LBPGOTYBonus', 1249800006),
}
PACK_TO_KEY = {name:key for key,(name,_,_) in DLC_KITS.items()}
LEVEL_DLC = {guid:PACK_TO_KEY[chapter] for guid,chapter in LEVEL_CHAPTER.items() if chapter in PACK_TO_KEY}
DLC_UNLOCK_NAMES = {key:f'Unlock {name}' for key,(name,_,_) in DLC_KITS.items()}
DLC_UNLOCK_IDS = {key:item_id for key,(_,_,item_id) in DLC_KITS.items()}

# Asset families in the extracted catalogue. These are not ownership detection
# or a claim to enumerate every separately sold PlayStation Store SKU.
ADDON_PACKS = {
    'animals2': 'Animals 2', 'assassinscreed': "Assassin's Creed II",
    'beta': 'Beta Rewards', 'birthday': 'Birthday', 'ghostbusters': 'Ghostbusters',
    'goty': 'Launch T-Shirts', 'heavyrain': 'Heavy Rain', 'history': 'History Costumes',
    'ico': 'ICO and Shadow of the Colossus', 'incredibles': 'The Incredibles Costumes',
    'independenceday': 'Independence Day', 'infamous': 'inFAMOUS',
    'marvel': 'Marvel Costumes',
    'machinima': 'Machinima', 'modnation': 'ModNation Stickers',
    'modnation_racers': 'ModNation Racers Costumes', 'monsters': 'Monsters Costumes',
    'music_pack_01': 'Music Pack 1', 'mythology': 'Mythology', 'pirates': 'Pirates Background',
    'potc': 'Pirates of the Caribbean Costumes', 'qore': 'Qore', 'ragdoll': 'Rag Doll Kung Fu',
    'solstice': 'Solstice', 'sonic': 'Sonic', 'verabee': 'Vera Bee', 'watchmen': 'Watchmen',
}


def addon_for_item(item):
    parts = item.get('resource_path', '').split('/')
    if len(parts) > 5 and parts[:4] == ['gamedata','plans','palettes','dlc']:
        return parts[4]
    return None


def owned_kit_keys(item_ids):
    received = set(item_ids)
    return {key for key,item_id in DLC_UNLOCK_IDS.items() if item_id in received}


def accessible_levels(levels, received_levels, starting_level, item_ids, required_kits):
    """Apply the same kit AND level rule as the AP world. Empty mapping is legacy."""
    received = set(received_levels) | {starting_level}
    owned = owned_kit_keys(item_ids)
    return {guid for guid in levels if guid in received
            and (guid not in required_kits or required_kits[guid] in owned)}
