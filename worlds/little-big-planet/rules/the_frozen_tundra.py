"""The Frozen Tundra (g20366): Prize Bubbles 38 and 39 sit behind the Gear Graphic
sticker switch and are unreachable without it. Near the end, a strict 4-player Co-Op
area (dial-matching puzzle then a springy platform all four players must bounce in
time) releases Prize Bubbles 40, 41, 42, 46 and 47 (Red Devil, Red Horns, Devil Tail,
Red Dress, Devil Trousers) -- both walkthrough sources describe it as needing four,
with no "fewer works" caveat unlike this level's other Co-Op areas."""
if __package__ and '.' in __package__:
    from ..constants.levels.base.the_frozen_tundra import LOCATION_KEYS as BUBBLE_KEYS
else:
    from constants.levels.base.the_frozen_tundra import LOCATION_KEYS as BUBBLE_KEYS


def requires_gear_graphic(world, state):
    return state.has('Gear Graphic', world.player)


def requires_four_players(world, state):
    return world.options.players.value >= 4


def requires_all_prizes(world, state):
    return requires_gear_graphic(world, state) and requires_four_players(world, state)


_FOUR_PLAYER_PRIZE_BUBBLES = (40, 41, 42, 46, 47)

RULES = {
    BUBBLE_KEYS['PRIZE_BUBBLE_38']: requires_gear_graphic,
    BUBBLE_KEYS['PRIZE_BUBBLE_39']: requires_gear_graphic,
}
RULES.update({BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_four_players for n in _FOUR_PLAYER_PRIZE_BUBBLES})
RULES[BUBBLE_KEYS['ALL_PRIZES']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_1']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_2']] = requires_all_prizes
