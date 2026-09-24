"""Authored sticker-switch and key checks; independent optional sanity pools."""
if __package__:
    from .constants.data.interactions import DATA
    from .constants.interactions import INTERACTION_LEVEL_LOCATIONS
else:
    from constants.data.interactions import DATA
    from constants.interactions import INTERACTION_LEVEL_LOCATIONS

INTERACTION_LOCATIONS = {loc['key']:loc for loc in DATA['locations']}
INTERACTION_NAME_TO_ID = {loc['name']:loc['id'] for loc in DATA['locations']}

for _guid, (_cls, _keys) in INTERACTION_LEVEL_LOCATIONS.items():
    for _constant, _key in _keys.items():
        _name = getattr(_cls, _constant)
        if INTERACTION_LOCATIONS[_key]['name'] != _name or INTERACTION_NAME_TO_ID.get(_name) != INTERACTION_LOCATIONS[_key]['id']:
            raise ValueError(f'Stale or duplicate interaction location constant: {_guid}.{_constant}')
if sum(len(keys) for _, keys in INTERACTION_LEVEL_LOCATIONS.values()) != len(INTERACTION_LOCATIONS):
    raise ValueError('Regenerate interaction constants: not every interaction location has a constant')


def required_sticker_plans(locations):
    return {int(loc['sticker_plan'][1:]) for loc in locations
            if loc['kind']=='sticker_switch' and loc['sticker_plan'].startswith('g')}
