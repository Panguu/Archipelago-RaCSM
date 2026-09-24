"""The Bunker (g20367): the Power Fist sticker switch, usable only after collecting
Power Fist from The Collector's Lair (the next level), reveals Prize Bubbles 3, 41 and
42 -- Russian Border, Spiral Doodle and Faces in Circles. A separate 4-wheel Co-Op
puzzle (lower-right and lower-left wheels each need one player, then "hopefully 2 of
them" fill the upper-right wheel; portforward's walkthrough calls 3 players the
minimum) releases Prize Bubbles 5, 10, 11, 12, 32, 33, 34 and 38 (Decayed Metal Plate,
Mellow Sun, Grey Camo, Dog Tag, Collar and Tie, Soldier's Helmet, Cardboard Hat, Egg
Carton Side)."""
if __package__ and '.' in __package__:
    from ..constants.levels.base.the_bunker import LOCATION_KEYS as BUBBLE_KEYS
else:
    from constants.levels.base.the_bunker import LOCATION_KEYS as BUBBLE_KEYS


def requires_power_fist(world, state):
    return state.has('Power Fist', world.player)


def requires_three_players(world, state):
    return world.options.players.value >= 3


def requires_all_prizes(world, state):
    return requires_power_fist(world, state) and requires_three_players(world, state)


_CO_OP_PRIZE_BUBBLES = (5, 10, 11, 12, 32, 33, 34, 38)

RULES = {
    BUBBLE_KEYS['PRIZE_BUBBLE_3']: requires_power_fist,
    BUBBLE_KEYS['PRIZE_BUBBLE_41']: requires_power_fist,
    BUBBLE_KEYS['PRIZE_BUBBLE_42']: requires_power_fist,
}
RULES.update({BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_three_players for n in _CO_OP_PRIZE_BUBBLES})
RULES[BUBBLE_KEYS['ALL_PRIZES']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_1']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_2']] = requires_all_prizes
