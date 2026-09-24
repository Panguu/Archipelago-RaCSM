"""Sensei's Lost Castle (g20358): a room needs both the Blue Mountain sticker and the
Japanese Wave sticker placed on its sticker boards to reveal Prize Bubbles 12, 13, 14
and 15 -- Little Doll, Green Bamboo Stick, Pink Warrior Mask and Big Cute Eye. A
separate 2-player Co-Op area (fabric wheel + spike-pit traversal) releases Prize
Bubbles 9, 10, 16, 21, 24, 33, 34, 35 and 41 (Brushcloud, Red Wicker, Sakura, Dragon
Scale, Thin Ninja, 'Tricky Business', Flip Flops, Metallic Tunic, Daruma San)."""
if __package__ and '.' in __package__:
    from ..constants.levels.base.sensei_s_lost_castle import LOCATION_KEYS as BUBBLE_KEYS
else:
    from constants.levels.base.sensei_s_lost_castle import LOCATION_KEYS as BUBBLE_KEYS


def requires_mountain_and_wave(world, state):
    return state.has_all({'Blue Mountain', 'Japanese Wave'}, world.player)


def requires_two_players(world, state):
    return world.options.players.value >= 2


def requires_all_prizes(world, state):
    return requires_mountain_and_wave(world, state) and requires_two_players(world, state)


_CO_OP_PRIZE_BUBBLES = (9, 10, 16, 21, 24, 33, 34, 35, 41)

RULES = {
    BUBBLE_KEYS['PRIZE_BUBBLE_12']: requires_mountain_and_wave,
    BUBBLE_KEYS['PRIZE_BUBBLE_13']: requires_mountain_and_wave,
    BUBBLE_KEYS['PRIZE_BUBBLE_14']: requires_mountain_and_wave,
    BUBBLE_KEYS['PRIZE_BUBBLE_15']: requires_mountain_and_wave,
}
RULES.update({BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_two_players for n in _CO_OP_PRIZE_BUBBLES})
RULES[BUBBLE_KEYS['ALL_PRIZES']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_1']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_2']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_3']] = requires_all_prizes
