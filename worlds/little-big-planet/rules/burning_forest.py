"""Burning Forest (g26698): the Stylised Antelope sticker switch releases the Crazy
Eyes prize, and the Cat Head sticker switch (Cat Head is obtained in a later level)
releases the Scary Ornament and Buffalo Emitter prizes. A separate 2-player Co-Op
area (button-and-door puzzle past the crocodiles) releases Prize Bubbles 3, 14 and 17
(Tiger Nose, Mahogany Wood, Antlers)."""
if __package__ and '.' in __package__:
    from ..constants.levels.base.burning_forest import LOCATION_KEYS as BUBBLE_KEYS
else:
    from constants.levels.base.burning_forest import LOCATION_KEYS as BUBBLE_KEYS


def requires_stylised_antelope(world, state):
    return state.has('Stylised Antelope', world.player)


def requires_cat_head(world, state):
    return state.has('Cat Head', world.player)


def requires_two_players(world, state):
    return world.options.players.value >= 2


def requires_all_prizes(world, state):
    return (requires_stylised_antelope(world, state) and requires_cat_head(world, state)
            and requires_two_players(world, state))


_CO_OP_PRIZE_BUBBLES = (3, 14, 17)

RULES = {
    BUBBLE_KEYS['PRIZE_BUBBLE_7']: requires_stylised_antelope,
    BUBBLE_KEYS['PRIZE_BUBBLE_11']: requires_cat_head,
    BUBBLE_KEYS['PRIZE_BUBBLE_8']: requires_cat_head,
}
RULES.update({BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_two_players for n in _CO_OP_PRIZE_BUBBLES})
RULES[BUBBLE_KEYS['ALL_PRIZES']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_1']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_2']] = requires_all_prizes
