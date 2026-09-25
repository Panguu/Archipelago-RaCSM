from rule_builder.rules import And

from .base import LOCATIONS as BASE_LOCATIONS
from .dlc import LOCATIONS as DLC_LOCATIONS
from .model import Kind, LBPLocation, LBPLocationData


def _add_all_prizes_rules(locations):
    """All Prizes (and its rewards) needs every prize bubble in the level, so it inherits their requirements."""
    prizes = {}
    for location in locations:
        if location.kind == Kind.PRIZE:
            prizes.setdefault(location.level, []).append(location)
    for location in locations:
        if location.kind == Kind.ALL_PRIZES or location.condition == Kind.ALL_PRIZES:
            level_prizes = prizes.get(location.level, [])
            rules = [prize.rule for prize in level_prizes if prize.rule is not None]
            location.players = max([location.players, *(prize.players for prize in level_prizes)])
            location.rule = And(*rules) if rules else None


LOCATIONS = BASE_LOCATIONS + DLC_LOCATIONS
_add_all_prizes_rules(LOCATIONS)
LOCATION_NAME_TO_ID = {location.name: location.code for location in LOCATIONS}
LOCATIONS_BY_LEVEL: dict[str, list[LBPLocationData]] = {}
for _location in LOCATIONS:
    LOCATIONS_BY_LEVEL.setdefault(_location.level, []).append(_location)

if len(LOCATION_NAME_TO_ID) != len(LOCATIONS):
    raise ValueError('Duplicate location names')

__all__ = ['Kind', 'LBPLocation', 'LBPLocationData', 'LOCATIONS', 'LOCATION_NAME_TO_ID', 'LOCATIONS_BY_LEVEL']
