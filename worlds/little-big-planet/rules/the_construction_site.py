"""The Construction Site (g31205): a 2-player Co-Op area (one player rides a crane
beam, the other rides a warning block up to the crane top) releases Prize Bubbles 3,
15, 16, 17, 38, 39 and 44 (Big Crane, Boxing Glove Front, Boxing Glove Back, Red
Stiletto, Yellow Builder Cap, Dungarees Top, 'Atlas')."""
if __package__ and '.' in __package__:
    from ..constants.levels.base.the_construction_site import LOCATION_KEYS as BUBBLE_KEYS
else:
    from constants.levels.base.the_construction_site import LOCATION_KEYS as BUBBLE_KEYS


def requires_two_players(world, state):
    return world.options.players.value >= 2


_CO_OP_PRIZE_BUBBLES = (3, 15, 16, 17, 38, 39, 44)

RULES = {BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_two_players for n in _CO_OP_PRIZE_BUBBLES}
RULES[BUBBLE_KEYS['ALL_PRIZES']] = requires_two_players
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_1']] = requires_two_players
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_2']] = requires_two_players
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_3']] = requires_two_players
