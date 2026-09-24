"""Level groupings derived from data/levels.json.

LBP1's eight story chapters, named per the LittleBigPlanet wiki, plus its six DLC
level kits and the GOTY edition's bundled community levels. Chapter order (and each
chapter's finale/boss level) is derived from the game's own SlotID primary_link
chain rather than guessed: developer levels on the main story path link forward to
the next main-path level (even across chapter/world boundaries, since the path is
one continuous chain from Introduction to The Collector); side/bonus levels link to
nothing. For each chapter, the longest chain of its own members is that chapter's
main path, and its last level is the chapter's finale.
"""
import re
from collections import defaultdict
if __package__:
    from .locations import LEVELS
else:
    from locations import LEVELS

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


def _chapter_for(level):
    parts = level['path'].split('/')
    folder, sub = parts[2], (parts[3] if len(parts) > 3 else None)
    if folder == '00_developer_levels_episode_1':
        return _FOLDER_CHAPTER[sub]
    if folder == 'goty_levels':
        return GOTY_BONUS
    return _FOLDER_DLC_PACK[sub]


LEVEL_CHAPTER = {guid: _chapter_for(level) for guid, level in LEVELS.items()}


def _primary_link(level):
    for slot in level['slots']:
        match = re.fullmatch(r'SlotID\{(?:DEVELOPER|DLC_LEVEL), (\d+)\}', slot.get('primary_link') or '')
        if match and match[1] != '0' and f'g{match[1]}' in LEVELS:
            return f'g{match[1]}'
    return None


_NEXT = {guid: _primary_link(level) for guid, level in LEVELS.items()}


def _order_chapter(members):
    """Longest intra-chapter link chain first (the main path), then any other
    chains, then fully isolated levels; returns (ordered_guids, finale_guid)."""
    members = set(members)
    intra_next = {guid: _NEXT[guid] for guid in members if _NEXT.get(guid) in members}
    has_incoming = set(intra_next.values())
    chains, used = [], set()
    for start in [g for g in members if g not in has_incoming]:
        chain, guid = [], start
        while guid and guid not in used:
            chain.append(guid); used.add(guid)
            guid = intra_next.get(guid)
        chains.append(chain)
    chains.sort(key=len, reverse=True)
    leftover = sorted(members - used, key=lambda g: int(g[1:]))
    ordered = [guid for chain in chains for guid in chain] + leftover
    finale = chains[0][-1] if chains and chains[0] else ordered[-1]
    return tuple(ordered), finale


_MEMBERS = defaultdict(list)
for _guid, _chapter in LEVEL_CHAPTER.items():
    _MEMBERS[_chapter].append(_guid)

CHAPTER_LEVELS = {}
CHAPTER_FINALE = {}
for _chapter, _members in _MEMBERS.items():
    CHAPTER_LEVELS[_chapter], CHAPTER_FINALE[_chapter] = _order_chapter(_members)
