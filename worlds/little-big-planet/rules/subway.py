"""Subway (g31203): two sticker switches gate prize bubbles, and a two-player
vent/cart maze gates two more. Sticker Switch 1 needs Yellow Fries (drops
Prize Bubbles 9 and 41). Sticker Switch 2 needs Intense Blue Graffiti, found
in The Construction Site (drops Prize Bubbles 15, 19, 33). The co-op vent/cart
section (Prize Bubbles 42 and 43) needs a second player physically present."""
if __package__ and '.' in __package__:
    from ..constants.levels.base.subway import LOCATION_KEYS as BUBBLE_KEYS
else:
    from constants.levels.base.subway import LOCATION_KEYS as BUBBLE_KEYS


def requires_yellow_fries(world, state):
    return state.has('Yellow Fries', world.player)


def requires_intense_blue_graffiti(world, state):
    return state.has('Intense Blue Graffiti', world.player)


def requires_two_players(world, state):
    return world.options.players.value >= 2


def requires_all_prizes(world, state):
    return (requires_yellow_fries(world, state) and requires_intense_blue_graffiti(world, state)
            and requires_two_players(world, state))


RULES = {
    BUBBLE_KEYS['PRIZE_BUBBLE_9']: requires_yellow_fries,
    BUBBLE_KEYS['PRIZE_BUBBLE_41']: requires_yellow_fries,
    BUBBLE_KEYS['PRIZE_BUBBLE_15']: requires_intense_blue_graffiti,
    BUBBLE_KEYS['PRIZE_BUBBLE_19']: requires_intense_blue_graffiti,
    BUBBLE_KEYS['PRIZE_BUBBLE_33']: requires_intense_blue_graffiti,
    BUBBLE_KEYS['PRIZE_BUBBLE_42']: requires_two_players,
    BUBBLE_KEYS['PRIZE_BUBBLE_43']: requires_two_players,
    BUBBLE_KEYS['ALL_PRIZES']: requires_all_prizes,
    BUBBLE_KEYS['ALL_PRIZES_REWARD_1']: requires_all_prizes,
    BUBBLE_KEYS['ALL_PRIZES_REWARD_2']: requires_all_prizes,
    BUBBLE_KEYS['ALL_PRIZES_REWARD_3']: requires_all_prizes,
}
