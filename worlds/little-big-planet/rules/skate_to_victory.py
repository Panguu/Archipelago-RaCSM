"""Skate to Victory (g26376): a co-op button section needs a second player physically
present to release the Vince Meat Pie, Yellow Danke and Funny Face Glasses prizes (the
nearby Sketch Bricks prize is reachable solo and is not gated). A detour off the main
path, not required for Ace."""
if __package__ and '.' in __package__:
    from ..constants.levels.base.skate_to_victory import LOCATION_KEYS as BUBBLE_KEYS
else:
    from constants.levels.base.skate_to_victory import LOCATION_KEYS as BUBBLE_KEYS


def requires_two_players(world, state):
    return world.options.players.value >= 2


RULES = {
    BUBBLE_KEYS['PRIZE_BUBBLE_17']: requires_two_players,
    BUBBLE_KEYS['PRIZE_BUBBLE_19']: requires_two_players,
    BUBBLE_KEYS['PRIZE_BUBBLE_56']: requires_two_players,
    BUBBLE_KEYS['ALL_PRIZES']: requires_two_players,
    BUBBLE_KEYS['ALL_PRIZES_REWARD_1']: requires_two_players,
    BUBBLE_KEYS['ALL_PRIZES_REWARD_2']: requires_two_players,
}
