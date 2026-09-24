"""Generated item definitions with stable IDs and explicit game-state mappings."""
if __package__:
    from .constants.data.items import DATA
    from .constants.item_names import ItemName, ITEM_KEYS
else:
    from constants.data.items import DATA
    from constants.item_names import ItemName, ITEM_KEYS

ITEM_ID_TO_DATA = {item['id']:item for item in DATA['items']}

ITEM_KEY_TO_DATA = {item['key']: item for item in DATA['items']}
ITEM_NAME_TO_ID = {}
for constant, key in ITEM_KEYS.items():
    name = getattr(ItemName, constant)
    item = ITEM_KEY_TO_DATA[key]
    if name != item['name'] or name in ITEM_NAME_TO_ID:
        raise ValueError(f'Stale or duplicate item constant: {constant}')
    ITEM_NAME_TO_ID[name] = item['id']
if len(ITEM_NAME_TO_ID) != len(DATA['items']):
    raise ValueError('Regenerate item constants: missing inventory definitions')
PRIZE_PLAN_TO_ITEM_ID = {item['state']['plan_guid']:item['id'] for item in DATA['items']
                       if item['state']['kind']=='inventory_plan'}
LEVEL_GUID_TO_ITEM_ID = {item['level_guid']:item['id'] for item in DATA['items']
                       if item['state']['kind']=='level_unlock'}
ITEM_GROUPS = {category:tuple(item['id'] for item in DATA['items'] if item['category']==category)
               for category in {item['category'] for item in DATA['items']}}
ITEM_NAME_GROUPS = {category: {ITEM_ID_TO_DATA[item_id]['name'] for item_id in ids}
                    for category, ids in ITEM_GROUPS.items()}

if __package__:
    from .dlc import DLC_KITS, DLC_UNLOCK_NAMES, LEVEL_DLC
    from .locations import LOCATIONS
else:
    from dlc import DLC_KITS, DLC_UNLOCK_NAMES, LEVEL_DLC
    from locations import LOCATIONS

DLC_ITEM_IDS = {}
for kit, (pack_name, _, item_id) in DLC_KITS.items():
    name = DLC_UNLOCK_NAMES[kit]
    if item_id in ITEM_ID_TO_DATA or name in ITEM_NAME_TO_ID:
        raise ValueError(f'DLC unlock identity collision: {kit}')
    definition = dict(id=item_id, key=f'dlc/{kit}', name=name, category='dlc',
                      state=dict(kind='dlc_unlock', kit=kit), grant_support='pine_runtime_access_table')
    ITEM_ID_TO_DATA[item_id] = definition
    ITEM_KEY_TO_DATA[definition['key']] = definition
    ITEM_NAME_TO_ID[name] = item_id
    guids = {g for g,k in LEVEL_DLC.items() if k == kit}
    plans = {int(loc['plan'][1:]) for loc in LOCATIONS.values()
             if loc['level_guid'] in guids and (loc.get('plan') or '').startswith('g')}
    DLC_ITEM_IDS[kit] = ({item_id} | {LEVEL_GUID_TO_ITEM_ID[g] for g in guids}
                         | {PRIZE_PLAN_TO_ITEM_ID[p] for p in plans})
    ITEM_NAME_GROUPS[pack_name] = {ITEM_ID_TO_DATA[i]['name'] for i in DLC_ITEM_IDS[kit]}
ITEM_NAME_GROUPS['DLC Unlocks'] = set(DLC_UNLOCK_NAMES.values())

if __package__:
    from .content_packs import PACKS, UNLOCK_NAMES
else:
    from content_packs import PACKS, UNLOCK_NAMES
for slot, pack in PACKS.items():
    item_id, name = pack['item_id'], UNLOCK_NAMES[slot]
    if item_id in ITEM_ID_TO_DATA or name in ITEM_NAME_TO_ID:
        raise ValueError(f'My Content item collision: {name}')
    item = dict(id=item_id, key=f'content_pack/{slot}', name=name, category='dlc',
                state=dict(kind='content_pack_unlock', slot_number=slot),
                grant_support='pine_runtime_access_table')
    ITEM_ID_TO_DATA[item_id] = item
    ITEM_KEY_TO_DATA[item['key']] = item
    ITEM_NAME_TO_ID[name] = item_id
ITEM_NAME_GROUPS['Costume Pack Unlocks'] = set(UNLOCK_NAMES.values())

if __package__:
    from .chapters import STORY_CHAPTERS
else:
    from chapters import STORY_CHAPTERS
PROGRESSIVE_ITEM_IDS = {chapter:1249900000+i for i,chapter in enumerate(STORY_CHAPTERS)}
for chapter,item_id in PROGRESSIVE_ITEM_IDS.items():
    name=f'Progressive {chapter}'
    ITEM_ID_TO_DATA[item_id]=dict(id=item_id,key=f'chapter/{chapter}',name=name,category='level',
                                state=dict(kind='progressive_chapter',chapter=chapter))
    ITEM_NAME_TO_ID[name]=item_id
ITEM_NAME_GROUPS['Progressive Levels']={f'Progressive {c}' for c in STORY_CHAPTERS}


def state_for_item(item_id):
    """Level items -> slot flags. Collectible items -> plan identity, not a fake flag."""
    return ITEM_ID_TO_DATA[item_id]['state']


if __package__:
    from .constants.traps import TrapItems, RANDOM_COSTUME_TRAP_ID, GAMEPLAY_EFFECTS
else:
    from constants.traps import TrapItems, RANDOM_COSTUME_TRAP_ID, GAMEPLAY_EFFECTS
ITEM_ID_TO_DATA[RANDOM_COSTUME_TRAP_ID] = dict(
    id=RANDOM_COSTUME_TRAP_ID, key='trap/random_costume',
    name=TrapItems.RANDOM_COSTUME_TRAP, category='trap',
    state=dict(kind='random_costume_trap'))
ITEM_NAME_TO_ID[TrapItems.RANDOM_COSTUME_TRAP] = RANDOM_COSTUME_TRAP_ID
ITEM_NAME_GROUPS['Traps'] = {TrapItems.RANDOM_COSTUME_TRAP}
ITEM_NAME_GROUPS['Help Items'] = set()
for kind, (effect_id, name, category, opcode) in GAMEPLAY_EFFECTS.items():
    ITEM_ID_TO_DATA[effect_id] = dict(id=effect_id, key=f'effect/{kind}', name=name,
                                    category=category, state=dict(kind=kind))
    ITEM_NAME_TO_ID[name] = effect_id
    ITEM_NAME_GROUPS['Traps' if category == 'trap' else 'Help Items'].add(name)



def split_received_items(item_ids):
    """Separate level flag writes from plans queued for native inventory delivery."""
    level_slots, inventory_plans, unknown = set(),set(),set()
    for item_id in item_ids:
        item = ITEM_ID_TO_DATA.get(item_id)
        if not item: unknown.add(item_id); continue
        state=item['state']
        if state['kind']=='level_unlock':
            level_slots.update((s['slot_type'],s['slot_number']) for s in state['slots'])
        elif state['kind']=='inventory_plan': inventory_plans.add(state['plan_guid'])
    return {'level_slots':sorted(level_slots),'pending_inventory_plans':sorted(inventory_plans),'unknown_items':sorted(unknown)}
