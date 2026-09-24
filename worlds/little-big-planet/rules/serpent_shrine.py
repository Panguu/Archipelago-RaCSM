"""Serpent Shrine (g26614): the Aztec Face sticker switch gates Strong Man Logo, Gold
Motif and Mexican Dollar. The Green Gecko sticker switch lowers a block bridge gating
Orange Motif, Jade Track Emitter and Clown. A co-op fabric-ball puzzle needs a second
player and gates Man Stone, Orange Mexican Pattern and Zombie Brain. All are optional
detours off the main path, so Ace is not gated."""
if __package__ and '.' in __package__:
    from ..constants.levels.base.serpent_shrine import LOCATION_KEYS as BUBBLE_KEYS
else:
    from constants.levels.base.serpent_shrine import LOCATION_KEYS as BUBBLE_KEYS


def requires_aztec_face(world, state):
    return state.has('Aztec Face', world.player)


def requires_green_gecko(world, state):
    return state.has('Green Gecko', world.player)


def requires_two_players(world, state):
    return world.options.players.value >= 2


_AZTEC_FACE_PRIZE_BUBBLES = (10, 11, 19)
_GREEN_GECKO_PRIZE_BUBBLES = (12, 23, 25)
_CO_OP_PRIZE_BUBBLES = (6, 7, 26)

def requires_all_prizes(world, state):
    return (requires_aztec_face(world, state) and requires_green_gecko(world, state)
            and requires_two_players(world, state))


RULES = {BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_aztec_face for n in _AZTEC_FACE_PRIZE_BUBBLES}
RULES.update({BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_green_gecko for n in _GREEN_GECKO_PRIZE_BUBBLES})
RULES.update({BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_two_players for n in _CO_OP_PRIZE_BUBBLES})
RULES[BUBBLE_KEYS['ALL_PRIZES']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_1']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_2']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_3']] = requires_all_prizes
