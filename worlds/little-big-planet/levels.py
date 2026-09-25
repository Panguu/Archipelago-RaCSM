import re

from .constants.data.levels import LEVELS

SLOT_TYPES = {'DEVELOPER': 0, 'DLC_LEVEL': 8}


def parse_slot(slot_id):
    """'SlotID{DEVELOPER, 26374}' -> (0, 26374); None for slot types levels are not stored in."""
    match = re.fullmatch(r'SlotID\{(DEVELOPER|DLC_LEVEL), (\d+)\}', slot_id or '')
    return (SLOT_TYPES[match[1]], int(match[2])) if match else None


SLOT_LEVELS: dict[tuple[int, int], set[str]] = {}
for _guid, _level in LEVELS.items():
    for _slot in _level['slots']:
        if (_key := parse_slot(_slot['slot'])) is not None:
            SLOT_LEVELS.setdefault(_key, set()).add(_guid)
