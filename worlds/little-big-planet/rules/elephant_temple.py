"""Elephant Temple (g20355): the Monkey sticker switch reveals Prize Bubbles 24, 25
and 26 (LBP Wiki walkthrough). The Blue Elephant sticker switch, usable only after
collecting Blue Elephant from Great Magician's Palace, lowers a platform with Prize
Bubbles 14, 16 and 17 (LBP Wiki walkthrough). A separate 2-player Co-Op area (lever
puzzle raising/lowering blocks) releases Prize Bubbles 11, 12, 13, 27 and 28 (Emerald
Jewel, Ruby Jewel, Green Fabric Star, Mini Sackboy, Short Sleeved Shirt)."""
if __package__ and '.' in __package__:
    from ..constants.levels.base.elephant_temple import LOCATION_KEYS as BUBBLE_KEYS
else:
    from constants.levels.base.elephant_temple import LOCATION_KEYS as BUBBLE_KEYS


def requires_monkey(world, state):
    return state.has('Monkey', world.player)


def requires_blue_elephant(world, state):
    return state.has('Blue Elephant', world.player)


def requires_two_players(world, state):
    return world.options.players.value >= 2


def requires_all_prizes(world, state):
    return (requires_monkey(world, state) and requires_blue_elephant(world, state)
            and requires_two_players(world, state))


_CO_OP_PRIZE_BUBBLES = (11, 12, 13, 27, 28)

RULES = {
    BUBBLE_KEYS['PRIZE_BUBBLE_24']: requires_monkey,
    BUBBLE_KEYS['PRIZE_BUBBLE_25']: requires_monkey,
    BUBBLE_KEYS['PRIZE_BUBBLE_26']: requires_monkey,
    BUBBLE_KEYS['PRIZE_BUBBLE_14']: requires_blue_elephant,
    BUBBLE_KEYS['PRIZE_BUBBLE_16']: requires_blue_elephant,
    BUBBLE_KEYS['PRIZE_BUBBLE_17']: requires_blue_elephant,
}
RULES.update({BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_two_players for n in _CO_OP_PRIZE_BUBBLES})
RULES[BUBBLE_KEYS['ALL_PRIZES']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_1']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_2']] = requires_all_prizes
