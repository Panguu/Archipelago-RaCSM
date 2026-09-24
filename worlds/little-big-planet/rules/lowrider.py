"""Lowrider (g31204): a co-op section needs a second player physically present.
Covers the tail of the level (Score Bubbles 76-90), the Prize Bubbles only reachable
from that section, All Prize Bubbles and its rewards (depend on those prizes), and
both of the level's sticker switches."""
if __package__ and '.' in __package__:
    from ..constants.levels.base.lowrider import LOCATION_KEYS as BUBBLE_KEYS
    from ..constants.interactions.base.lowrider import LOCATION_KEYS as STICKER_KEYS
else:
    from constants.levels.base.lowrider import LOCATION_KEYS as BUBBLE_KEYS
    from constants.interactions.base.lowrider import LOCATION_KEYS as STICKER_KEYS


def requires_two_players(world, state):
    return world.options.players.value >= 2


_TWO_PLAYER_PRIZE_BUBBLES = (3, 14, 19, 32, 36, 39, 41, 42, 43, 45, 69)
_TWO_PLAYER_SCORE_BUBBLES = range(76, 91)

RULES = {BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_two_players for n in _TWO_PLAYER_PRIZE_BUBBLES}
RULES.update({BUBBLE_KEYS[f'SCORE_BUBBLE_{n}']: requires_two_players for n in _TWO_PLAYER_SCORE_BUBBLES})
RULES[BUBBLE_KEYS['ALL_PRIZES']] = requires_two_players
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_1']] = requires_two_players
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_2']] = requires_two_players
RULES[STICKER_KEYS['STICKER_SWITCH_2']] = requires_two_players
RULES[STICKER_KEYS['STICKER_SWITCH_3']] = requires_two_players
