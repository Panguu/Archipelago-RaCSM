"""Deterministic level-unlock item definitions for the future Archipelago world."""
from locations import LEVELS

def slot_state(slot):
    kind, number = slot['slot'][7:-1].split(', ')
    if kind not in ('DEVELOPER','DLC_LEVEL'): return None
    return {'slot_type':{'DEVELOPER':0,'DLC_LEVEL':8}[kind], 'slot_number':int(number),
            'discovered_offset':0x20,'unlocked_offset':0x21,'unlocked_value':1}

# Separate project-local range; coordinate the range before upstream registration.
LEVEL_UNLOCK_ITEMS = {
    1_241_000_000 + int(guid[1:]): {
        'name': f'Unlock {level["name"]}', 'level_guid':guid,
        'slots':sorted({state['slot_number'] for s in level['slots'] if (state:=slot_state(s))}),
        'unlock_states':[state for s in level['slots'] if (state:=slot_state(s))],
    }
    for guid,level in LEVELS.items()
}


def slots_for_received_items(item_ids):
    """Replay the server's received-item list after reconnect; grants are idempotent."""
    return sorted({slot for item_id in item_ids if item_id in LEVEL_UNLOCK_ITEMS
                   for slot in LEVEL_UNLOCK_ITEMS[item_id]['slots']})
