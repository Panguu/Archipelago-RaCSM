"""The Wedding Reception (g26606): the Huge Eye sticker switch (stuck on the
skeleton's eye) gates Fuzzy Scribble. The Skeleton Hat sticker switch gates Plastic
Moustache and Lower Teeth. A co-op platform/skeleton-decoration puzzle needs a second
player and gates 'Volver a Comenzar', Straw and Farmers Cap. All are optional
detours, so Ace is not gated."""
if __package__ and '.' in __package__:
    from ..constants.levels.base.the_wedding_reception import LOCATION_KEYS as BUBBLE_KEYS
else:
    from constants.levels.base.the_wedding_reception import LOCATION_KEYS as BUBBLE_KEYS


def requires_huge_eye(world, state):
    return state.has('Huge Eye', world.player)


def requires_skeleton_hat(world, state):
    return state.has('Skeleton Hat', world.player)


def requires_two_players(world, state):
    return world.options.players.value >= 2


_HUGE_EYE_PRIZE_BUBBLES = (49,)
_SKELETON_HAT_PRIZE_BUBBLES = (53, 54)
_CO_OP_PRIZE_BUBBLES = (8, 47, 48)

def requires_all_prizes(world, state):
    return (requires_huge_eye(world, state) and requires_skeleton_hat(world, state)
            and requires_two_players(world, state))


RULES = {BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_huge_eye for n in _HUGE_EYE_PRIZE_BUBBLES}
RULES.update({BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_skeleton_hat for n in _SKELETON_HAT_PRIZE_BUBBLES})
RULES.update({BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_two_players for n in _CO_OP_PRIZE_BUBBLES})
RULES[BUBBLE_KEYS['ALL_PRIZES']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_1']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_2']] = requires_all_prizes
