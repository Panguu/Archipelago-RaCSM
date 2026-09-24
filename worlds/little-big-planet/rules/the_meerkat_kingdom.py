"""The Meerkat Kingdom (g26370): the Fluffy Tree sticker switch collapses a wall to
release the Baby Meerkats prize, and the Voodoo Face sticker switch releases the
Meerkat Popup prize. Two separate 2-player Co-Op sections (a zebra-block platform
puzzle, then a meerkat head/belly launch used twice) release Prize Bubbles 3, 9, 17,
21 and 41 (Black Animal Nose, Wooden Planks, Big-Belly Meerkat, Orange Block, Red
Roman Cape)."""
if __package__ and '.' in __package__:
    from ..constants.levels.base.the_meerkat_kingdom import LOCATION_KEYS as BUBBLE_KEYS
else:
    from constants.levels.base.the_meerkat_kingdom import LOCATION_KEYS as BUBBLE_KEYS


def requires_fluffy_tree(world, state):
    return state.has('Fluffy Tree', world.player)


def requires_voodoo_face(world, state):
    return state.has('Voodoo Face', world.player)


def requires_two_players(world, state):
    return world.options.players.value >= 2


def requires_all_prizes(world, state):
    return (requires_fluffy_tree(world, state) and requires_voodoo_face(world, state)
            and requires_two_players(world, state))


_CO_OP_PRIZE_BUBBLES = (3, 9, 17, 21, 41)

RULES = {
    BUBBLE_KEYS['PRIZE_BUBBLE_16']: requires_fluffy_tree,
    BUBBLE_KEYS['PRIZE_BUBBLE_10']: requires_voodoo_face,
}
RULES.update({BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_two_players for n in _CO_OP_PRIZE_BUBBLES})
RULES[BUBBLE_KEYS['ALL_PRIZES']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_1']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_2']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_3']] = requires_all_prizes
