"""The Darkness (g26421): the Pixel Skull sticker switches gate Brown Leather and
Bunny. Two separate co-op sections (a gong/skull-bungee swing across spikes, and a
button-and-spring launch) need a second player and gate the three pinata motifs
(Red, Green, Blue), Flower Frame/Cyclops Eye/Pink Star Sunglasses, and Sugar
Bone/Torn Cloth respectively. All are optional detours, so Ace is not gated."""
if __package__ and '.' in __package__:
    from ..constants.levels.base.the_darkness import LOCATION_KEYS as BUBBLE_KEYS
else:
    from constants.levels.base.the_darkness import LOCATION_KEYS as BUBBLE_KEYS


def requires_pixel_skull(world, state):
    return state.has('Pixel Skull', world.player)


def requires_two_players(world, state):
    return world.options.players.value >= 2


_PIXEL_SKULL_PRIZE_BUBBLES = (27, 28)
_CO_OP_PRIZE_BUBBLES = (12, 15, 16, 17, 18, 25, 26, 33, 38)

def requires_all_prizes(world, state):
    return requires_pixel_skull(world, state) and requires_two_players(world, state)


RULES = {BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_pixel_skull for n in _PIXEL_SKULL_PRIZE_BUBBLES}
RULES.update({BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_two_players for n in _CO_OP_PRIZE_BUBBLES})
RULES[BUBBLE_KEYS['ALL_PRIZES']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_1']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_2']] = requires_all_prizes
