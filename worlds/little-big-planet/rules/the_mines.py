"""The Mines (g27483): three sticker switches each gate a small cluster of prize
bubbles (Angry Skull -> Sardine Can/Mexican Symbol/Red Explosives; the Red Explosives
sticker just unlocked then gates Big Mouth Teeth/Big Platform Booster/Plain Natural;
Mexican Scary Mask -> Pink Wrestler Face/Leather Struts/Sardine Label). A separate
co-op wheel/ramp puzzle needs a second player and gates Powered Chain Platform, Red
Motif, Rotten Teeth, Single Sponge Rotator and Dungarees Bottom. All are optional
detours, not required to finish the level, so Ace is not gated."""
if __package__ and '.' in __package__:
    from ..constants.levels.base.the_mines import LOCATION_KEYS as BUBBLE_KEYS
else:
    from constants.levels.base.the_mines import LOCATION_KEYS as BUBBLE_KEYS


def requires_angry_skull(world, state):
    return state.has('Angry Skull [plan/g31825]', world.player)


def requires_red_explosives(world, state):
    return state.has('Red Explosives', world.player)


def requires_mexican_scary_mask(world, state):
    return state.has('Mexican Scary Mask', world.player)


def requires_two_players(world, state):
    return world.options.players.value >= 2


_ANGRY_SKULL_PRIZE_BUBBLES = (4, 5, 41)
_RED_EXPLOSIVES_PRIZE_BUBBLES = (3, 24, 29)
_MEXICAN_SCARY_MASK_PRIZE_BUBBLES = (11, 16, 25)
_CO_OP_PRIZE_BUBBLES = (21, 22, 23, 31, 33)

def requires_all_prizes(world, state):
    return (requires_angry_skull(world, state) and requires_red_explosives(world, state)
            and requires_mexican_scary_mask(world, state) and requires_two_players(world, state))


RULES = {BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_angry_skull for n in _ANGRY_SKULL_PRIZE_BUBBLES}
RULES.update({BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_red_explosives for n in _RED_EXPLOSIVES_PRIZE_BUBBLES})
RULES.update({BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_mexican_scary_mask for n in _MEXICAN_SCARY_MASK_PRIZE_BUBBLES})
RULES.update({BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_two_players for n in _CO_OP_PRIZE_BUBBLES})
RULES[BUBBLE_KEYS['ALL_PRIZES']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_1']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_2']] = requires_all_prizes
