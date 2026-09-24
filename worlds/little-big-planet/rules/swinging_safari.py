"""Swinging Safari (g26699): a 2-player Co-Op area (alternating pressure-plate
platform past a large drum) releases Prize Bubbles 9, 10, 37, 38, 40 and 43 (Voodoo
Face, Real Brown Leaf, Mean Piranha Fish, Orange Boar Fish, Big Crab Claw, Cork
Hat)."""
if __package__ and '.' in __package__:
    from ..constants.levels.base.swinging_safari import LOCATION_KEYS as BUBBLE_KEYS
else:
    from constants.levels.base.swinging_safari import LOCATION_KEYS as BUBBLE_KEYS


def requires_two_players(world, state):
    return world.options.players.value >= 2


_CO_OP_PRIZE_BUBBLES = (9, 10, 37, 38, 40, 43)

RULES = {BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_two_players for n in _CO_OP_PRIZE_BUBBLES}
RULES[BUBBLE_KEYS['ALL_PRIZES']] = requires_two_players
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_1']] = requires_two_players
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_2']] = requires_two_players
