"""Boom Town (g26417): the five Orange Bird sticker switches gate six prize bubbles
(Cactus Body, Angry Skull, Weathered Wood, 'Cornman', Border Bit, Window Semi Circle).
Two separate co-op detours (mine-cart ramp puzzle and a foam/explosives puzzle) each
gate a cluster of prize bubbles behind a second player. Both are optional bonus
detours off the hub's main path, not required to reach Level Complete, so Ace is not
gated."""
if __package__ and '.' in __package__:
    from ..constants.levels.base.boom_town import LOCATION_KEYS as BUBBLE_KEYS
else:
    from constants.levels.base.boom_town import LOCATION_KEYS as BUBBLE_KEYS


def requires_orange_bird(world, state):
    return state.has('Orange Bird', world.player)


def requires_two_players(world, state):
    return world.options.players.value >= 2


_ORANGE_BIRD_PRIZE_BUBBLES = (11, 39, 50, 61, 67, 81)
_CO_OP_MINE_CART_PRIZE_BUBBLES = (8, 9, 22, 23, 43, 57, 58, 62, 66, 72, 73)
_CO_OP_FOAM_PRIZE_BUBBLES = (42, 51, 54, 55, 64)

def requires_all_prizes(world, state):
    return requires_orange_bird(world, state) and requires_two_players(world, state)


RULES = {BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_orange_bird for n in _ORANGE_BIRD_PRIZE_BUBBLES}
RULES.update({BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_two_players for n in _CO_OP_MINE_CART_PRIZE_BUBBLES})
RULES.update({BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_two_players for n in _CO_OP_FOAM_PRIZE_BUBBLES})
RULES[BUBBLE_KEYS['ALL_PRIZES']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_1']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_2']] = requires_all_prizes
