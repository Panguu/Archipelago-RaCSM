"""Location tables linked to generated AP display-name constants."""
if __package__:
    from .constants.data.levels import DATA
    from .constants.levels import LEVEL_LOCATIONS
else:
    from constants.data.levels import DATA
    from constants.levels import LEVEL_LOCATIONS

LEVELS = {level['guid']:level for level in DATA['levels']}
LOCATIONS = {location['key']:dict(location,level_guid=level['guid'])
             for level in LEVELS.values() for location in level['locations']}

LOCATION_NAME_TO_ID = {}
for guid, (cls, keys) in LEVEL_LOCATIONS.items():
    for constant, key in keys.items():
        name = getattr(cls, constant)
        if LOCATIONS[key]['name'] != name or name in LOCATION_NAME_TO_ID:
            raise ValueError(f'Stale or duplicate location constant: {guid}.{constant}')
        LOCATION_NAME_TO_ID[name] = LOCATIONS[key]['id']
if len(LOCATION_NAME_TO_ID) != len(LOCATIONS):
    raise ValueError('Regenerate constants: not every location has a constant')


def locations_for_level(name_or_guid, kind=None):
    """Use LevelName.FIRST_STEPS or 'g26374'; optional kind 'score'/'prize'/etc."""
    matching = [l for l in LEVELS.values() if name_or_guid in (l['guid'],l['name'])]
    if len(matching) != 1:
        raise ValueError('Unknown or ambiguous level; use its GUID')
    return tuple(l for l in matching[0]['locations'] if kind is None or l['kind']==kind)
