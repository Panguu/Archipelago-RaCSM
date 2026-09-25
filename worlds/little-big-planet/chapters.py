"""Story chapters, DLC packs and each chapter's level order, from the game's own primary_link chain."""
from .levels import LEVELS, parse_slot

_FOLDER_CHAPTER = {
    'introduction': 'Introduction',
    'england_garden': 'The Gardens',
    'africa': 'The Savannah',
    'mexico_graveyard': 'The Wedding',
    'mexico_desert': 'The Canyons',
    'usa_new_york': 'The Metropolis',
    'japan_zen_garden': 'The Islands',
    'india': 'The Temples',
    'russia_snow_wilderness': 'The Wilderness',
}
STORY_CHAPTERS = tuple(name for name in _FOLDER_CHAPTER.values() if name != 'Introduction')

_FOLDER_DLC_PACK = {
    'creators_pack_01': 'Creator Pack 1',
    'history_pack': 'History Level Kit',
    'incredibles_pack': 'The Incredibles Level Kit',
    'marvel_pack': 'Marvel Level Kit',
    'mgs_levels': 'Metal Gear Solid Premium Level Kit',
    'monster_pack': 'Monsters Level Kit',
    'potc_levels': 'Pirates of the Caribbean Premium Level Kit',
}
GOTY_BONUS = 'GOTY Edition Community Levels'
DLC_PACKS = tuple(_FOLDER_DLC_PACK.values()) + (GOTY_BONUS,)


def _chapter(level):
    parts = level['path'].split('/')
    folder, sub = parts[2], (parts[3] if len(parts) > 3 else None)
    if folder == '00_developer_levels_episode_1':
        return _FOLDER_CHAPTER[sub]
    if folder == 'goty_levels':
        return GOTY_BONUS
    return _FOLDER_DLC_PACK[sub]


def _next_level(level):
    for slot in level['slots']:
        link = parse_slot(slot.get('primary_link'))
        if link and f'g{link[1]}' in LEVELS:
            return f'g{link[1]}'
    return None


def _order(members):
    """Longest linked chain first (the main path, whose last level is the finale), then the rest."""
    members = set(members)
    links = {guid: NEXT_LEVEL[guid] for guid in members if NEXT_LEVEL.get(guid) in members}
    chains, used = [], set()
    for start in sorted(members - set(links.values()), key=lambda g: int(g[1:])):
        chain, guid = [], start
        while guid and guid not in used:
            chain.append(guid)
            used.add(guid)
            guid = links.get(guid)
        chains.append(chain)
    chains.sort(key=len, reverse=True)
    ordered = [guid for chain in chains for guid in chain] + sorted(members - used, key=lambda g: int(g[1:]))
    finale = chains[0][-1] if chains and chains[0] else ordered[-1]
    return tuple(ordered), finale


LEVEL_CHAPTER = {guid: _chapter(level) for guid, level in LEVELS.items()}
NEXT_LEVEL = {guid: _next_level(level) for guid, level in LEVELS.items()}
CHAPTER_LEVELS = {}
CHAPTER_FINALE = {}
for _chapter_name in dict.fromkeys(LEVEL_CHAPTER.values()):
    CHAPTER_LEVELS[_chapter_name], CHAPTER_FINALE[_chapter_name] = _order(
        guid for guid, chapter in LEVEL_CHAPTER.items() if chapter == _chapter_name)
