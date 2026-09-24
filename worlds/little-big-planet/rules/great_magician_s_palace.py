"""Great Magician's Palace (g20356): a sticker puzzle needs all three cobra stickers
(Straight Cobra Body on two switches, Cobra Head, Cobra Tail) placed to reveal Prize
Bubbles 33, 34 and 38 -- Green Felt, Brown Felt and Temples IntMusic. A separate
2-player Co-Op area (button/block-raising puzzle) releases Prize Bubbles 9, 30, 31,
32, 35 and 37 (Gold Coin Chain, Cardboard Mask, Grey Side Parting Wig, Cartoon Eyes,
Trainers, 'New Delhi Dawn')."""
if __package__ and '.' in __package__:
    from ..constants.levels.base.great_magician_s_palace import LOCATION_KEYS as BUBBLE_KEYS
else:
    from constants.levels.base.great_magician_s_palace import LOCATION_KEYS as BUBBLE_KEYS


def requires_cobra_stickers(world, state):
    return state.has_all({'Straight Cobra Body', 'Cobra Head', 'Cobra Tail'}, world.player)


def requires_two_players(world, state):
    return world.options.players.value >= 2


def requires_all_prizes(world, state):
    return requires_cobra_stickers(world, state) and requires_two_players(world, state)


_CO_OP_PRIZE_BUBBLES = (9, 30, 31, 32, 35, 37)

RULES = {
    BUBBLE_KEYS['PRIZE_BUBBLE_33']: requires_cobra_stickers,
    BUBBLE_KEYS['PRIZE_BUBBLE_34']: requires_cobra_stickers,
    BUBBLE_KEYS['PRIZE_BUBBLE_38']: requires_cobra_stickers,
}
RULES.update({BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_two_players for n in _CO_OP_PRIZE_BUBBLES})
RULES[BUBBLE_KEYS['ALL_PRIZES']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_1']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_2']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_3']] = requires_all_prizes
