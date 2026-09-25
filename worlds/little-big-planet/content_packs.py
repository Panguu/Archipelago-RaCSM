"""Actual My Content costume entries, with stable slot-derived AP identities."""
from .constants.data.my_content_packs import DATA

PACKS = {p['slot_number']: p for p in DATA['packs']}
PACK_BY_NAME = {p['name']: slot for slot, p in PACKS.items()}
UNLOCK_NAMES = {slot: f'Unlock {p["name"]}' for slot, p in PACKS.items()}
PACK_LOCATIONS = {slot: dict(id=p['location_id'], name=f'My Content: {p["name"]} Unlocked',
                           key=f'content_pack/{slot}', kind='content_pack', slot_number=slot)
                  for slot, p in PACKS.items()}


def access_rows(enabled, received):
    """A collection unlock opens its included characters as well as its own entry."""
    enabled, received = set(enabled), set(received)
    if enabled-set(PACKS) or received-set(PACKS):
        raise ValueError('Unknown My Content pack slot')
    owned = enabled & received
    accessible = set(owned)
    for slot in PACKS:
        parent, seen = slot, set()
        while parent in PACKS and parent not in seen:
            seen.add(parent)
            if parent in owned:
                accessible.add(slot)
                break
            parent = PACKS[parent]['parent_slot']
    return [(9, slot, int(slot in accessible)) for slot in sorted(PACKS)]
