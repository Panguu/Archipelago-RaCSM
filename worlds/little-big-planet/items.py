from BaseClasses import Item

from .chapters import STORY_CHAPTERS
from .constants.data.items import DATA
from .constants.item_names import ItemName, ITEM_KEYS
from .constants.traps import TrapItems, RANDOM_COSTUME_TRAP_ID, GAMEPLAY_EFFECTS
from .content_packs import PACKS, UNLOCK_NAMES
from .dlc import DLC_KITS, DLC_UNLOCK_NAMES, LEVEL_DLC
from .locations import LOCATIONS, Kind

FILLER_NAME = 'Nothing'
FILLER_ID = 1_249_999_999


class LBPItem(Item):
    game = 'LittleBigPlanet'


ITEM_ID_TO_DATA = {item['id']: item for item in DATA['items']}
_ITEM_BY_KEY = {item['key']: item for item in DATA['items']}
ITEM_NAME_TO_ID = {}
for constant, key in ITEM_KEYS.items():
    name = getattr(ItemName, constant)
    if name != _ITEM_BY_KEY[key]['name'] or name in ITEM_NAME_TO_ID:
        raise ValueError(f'Stale or duplicate item constant: {constant}')
    ITEM_NAME_TO_ID[name] = _ITEM_BY_KEY[key]['id']
if len(ITEM_NAME_TO_ID) != len(DATA['items']):
    raise ValueError('Regenerate item constants: missing inventory definitions')

PRIZE_PLAN_TO_ITEM_ID = {item['state']['plan_guid']: item['id'] for item in DATA['items']
                         if item['state']['kind'] == 'inventory_plan'}
LEVEL_GUID_TO_ITEM_ID = {item['level_guid']: item['id'] for item in DATA['items']
                         if item['state']['kind'] == 'level_unlock'}
ITEM_NAME_GROUPS = {}
for _item in DATA['items']:
    ITEM_NAME_GROUPS.setdefault(_item['category'], set()).add(_item['name'])


def _add(item_id, name, category, state, key):
    if item_id in ITEM_ID_TO_DATA or name in ITEM_NAME_TO_ID:
        raise ValueError(f'Item identity collision: {name}')
    ITEM_ID_TO_DATA[item_id] = dict(id=item_id, key=key, name=name, category=category, state=state)
    ITEM_NAME_TO_ID[name] = item_id


_REWARD_PLANS = {}
for _location in LOCATIONS:
    if _location.kind in (Kind.PRIZE, Kind.REWARD) and (_location.plan or '').startswith('g'):
        _REWARD_PLANS.setdefault(_location.level, set()).add(int(_location.plan[1:]))

for kit, (pack_name, _, item_id) in DLC_KITS.items():
    _add(item_id, DLC_UNLOCK_NAMES[kit], 'dlc', dict(kind='dlc_unlock', kit=kit), f'dlc/{kit}')
    levels = {guid for guid, level_kit in LEVEL_DLC.items() if level_kit == kit}
    plans = set().union(*(_REWARD_PLANS.get(guid, set()) for guid in levels))
    ids = {item_id} | {LEVEL_GUID_TO_ITEM_ID[guid] for guid in levels} | {PRIZE_PLAN_TO_ITEM_ID[p] for p in plans}
    ITEM_NAME_GROUPS[pack_name] = {ITEM_ID_TO_DATA[i]['name'] for i in ids}
ITEM_NAME_GROUPS['DLC Unlocks'] = set(DLC_UNLOCK_NAMES.values())

for slot, pack in PACKS.items():
    _add(pack['item_id'], UNLOCK_NAMES[slot], 'dlc', dict(kind='content_pack_unlock', slot_number=slot),
         f'content_pack/{slot}')
ITEM_NAME_GROUPS['Costume Pack Unlocks'] = set(UNLOCK_NAMES.values())

PROGRESSIVE_ITEM_IDS = {chapter: 1_249_900_000 + i for i, chapter in enumerate(STORY_CHAPTERS)}
for chapter, item_id in PROGRESSIVE_ITEM_IDS.items():
    _add(item_id, f'Progressive {chapter}', 'level', dict(kind='progressive_chapter', chapter=chapter),
         f'chapter/{chapter}')
ITEM_NAME_GROUPS['Progressive Levels'] = {f'Progressive {chapter}' for chapter in STORY_CHAPTERS}

_add(RANDOM_COSTUME_TRAP_ID, TrapItems.RANDOM_COSTUME_TRAP, 'trap', dict(kind='random_costume_trap'),
     'trap/random_costume')
ITEM_NAME_GROUPS['Traps'] = {TrapItems.RANDOM_COSTUME_TRAP}
ITEM_NAME_GROUPS['Help Items'] = set()
for kind, (effect_id, name, category, _) in GAMEPLAY_EFFECTS.items():
    _add(effect_id, name, category, dict(kind=kind), f'effect/{kind}')
    ITEM_NAME_GROUPS['Traps' if category == 'trap' else 'Help Items'].add(name)
