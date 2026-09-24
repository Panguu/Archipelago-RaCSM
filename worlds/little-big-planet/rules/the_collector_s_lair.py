"""The Collector's Lair (g20368): the Wirey Tree sticker switch (sticker found on The
Bunker, the previous level) reveals Prize Bubbles 54 and 55, Scale Swimsuit and
Mermaid Tail. Later, a separate 4-player Co-Op button-stack area -- portforward's
walkthrough is explicit "you only really need three players to complete it" -- releases
Prize Bubbles 50, 51, 52, 53, 56 and 63 (Head Dress, Chinese Dragon Mask, Danger
Platform, Metal Vent, 'Rainbow Warrior', Blue Camo)."""
if __package__ and '.' in __package__:
    from ..constants.levels.base.the_collector_s_lair import LOCATION_KEYS as BUBBLE_KEYS
else:
    from constants.levels.base.the_collector_s_lair import LOCATION_KEYS as BUBBLE_KEYS


def requires_wirey_tree(world, state):
    return state.has('Wirey Tree', world.player)


def requires_three_players(world, state):
    return world.options.players.value >= 3


def requires_all_prizes(world, state):
    return requires_wirey_tree(world, state) and requires_three_players(world, state)


_CO_OP_PRIZE_BUBBLES = (50, 51, 52, 53, 56, 63)

RULES = {
    BUBBLE_KEYS['PRIZE_BUBBLE_54']: requires_wirey_tree,
    BUBBLE_KEYS['PRIZE_BUBBLE_55']: requires_wirey_tree,
}
RULES.update({BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_three_players for n in _CO_OP_PRIZE_BUBBLES})
RULES[BUBBLE_KEYS['ALL_PRIZES']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_1']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_2']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_3']] = requires_all_prizes
