"""Endurance Dojo (g20357): the Geisha sticker switch reveals Prize Bubbles 7, 41 and
43 (Short Fence, Pink Sundae, Black Japanese Text). The Japanese Samurai sticker
switch, usable only after collecting Japanese Samurai from Sensei's Lost Castle,
reveals Prize Bubbles 8, 15 and 37 (Clockwork Box, Long Fence, Wavy Beige Motif). A
separate 2-player Co-Op area (chain-platform/hamster-wheel puzzle) releases Prize
Bubbles 5, 12, 33, 34, 35 and 39 (Piñata Cloth, Salmon Sushi Monster, Pink Umbrella
Top, Wooden Cane, Fried Egg, Pink Microchip Motif)."""
if __package__ and '.' in __package__:
    from ..constants.levels.base.endurance_dojo import LOCATION_KEYS as BUBBLE_KEYS
else:
    from constants.levels.base.endurance_dojo import LOCATION_KEYS as BUBBLE_KEYS


def requires_geisha(world, state):
    return state.has('Geisha', world.player)


def requires_japanese_samurai(world, state):
    return state.has('Japanese Samurai', world.player)


def requires_two_players(world, state):
    return world.options.players.value >= 2


def requires_all_prizes(world, state):
    return (requires_geisha(world, state) and requires_japanese_samurai(world, state)
            and requires_two_players(world, state))


_CO_OP_PRIZE_BUBBLES = (5, 12, 33, 34, 35, 39)

RULES = {
    BUBBLE_KEYS['PRIZE_BUBBLE_7']: requires_geisha,
    BUBBLE_KEYS['PRIZE_BUBBLE_41']: requires_geisha,
    BUBBLE_KEYS['PRIZE_BUBBLE_43']: requires_geisha,
    BUBBLE_KEYS['PRIZE_BUBBLE_8']: requires_japanese_samurai,
    BUBBLE_KEYS['PRIZE_BUBBLE_15']: requires_japanese_samurai,
    BUBBLE_KEYS['PRIZE_BUBBLE_37']: requires_japanese_samurai,
}
RULES.update({BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_two_players for n in _CO_OP_PRIZE_BUBBLES})
RULES[BUBBLE_KEYS['ALL_PRIZES']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_1']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_2']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_3']] = requires_all_prizes
