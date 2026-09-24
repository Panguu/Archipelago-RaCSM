"""Get a Grip (g26375): the Tea Pot sticker switch (live-tested, see
INTERACTION_CHECKS.md) releases the Golf Club Bottom and Noughts & Crosses prizes.
A detour off the main path, not required for Ace."""
if __package__ and '.' in __package__:
    from ..constants.levels.base.get_a_grip import LOCATION_KEYS as BUBBLE_KEYS
else:
    from constants.levels.base.get_a_grip import LOCATION_KEYS as BUBBLE_KEYS


def requires_tea_pot(world, state):
    return state.has('Tea Pot', world.player)


RULES = {
    BUBBLE_KEYS['PRIZE_BUBBLE_19']: requires_tea_pot,
    BUBBLE_KEYS['PRIZE_BUBBLE_20']: requires_tea_pot,
    BUBBLE_KEYS['ALL_PRIZES']: requires_tea_pot,
    BUBBLE_KEYS['ALL_PRIZES_REWARD_1']: requires_tea_pot,
    BUBBLE_KEYS['ALL_PRIZES_REWARD_2']: requires_tea_pot,
}
