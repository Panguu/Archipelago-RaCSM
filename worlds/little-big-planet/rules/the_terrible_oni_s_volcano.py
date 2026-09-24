"""The Terrible Oni's Volcano (g20359): the Sakura Flower sticker switch (sticker found
on Sensei's Lost Castle) reveals Prize Bubbles 29 and 30 (Rainbow Tree, Pretty Leaf).
The Bouncy Cloud sticker switch reveals Prize Bubbles 31 and 32 (Fairy Star Wand, Wind
Charm). The Pink Warrior Mask sticker switch (sticker found on Sensei's Lost Castle)
reveals Prize Bubbles 20 and 21 (Dark Wooden Button, Bonsai Pot). A separate 2-player
Co-Op area (button-and-cart puzzle over falling rocks) releases Prize Bubbles 7, 16
and 17 (Japanese Coin, White Wood, Cream Marble Button)."""
if __package__ and '.' in __package__:
    from ..constants.levels.base.the_terrible_oni_s_volcano import LOCATION_KEYS as BUBBLE_KEYS
else:
    from constants.levels.base.the_terrible_oni_s_volcano import LOCATION_KEYS as BUBBLE_KEYS


def requires_sakura_flower(world, state):
    return state.has('Sakura Flower', world.player)


def requires_bouncy_cloud(world, state):
    return state.has('Bouncy Cloud', world.player)


def requires_pink_warrior_mask(world, state):
    return state.has('Pink Warrior Mask', world.player)


def requires_two_players(world, state):
    return world.options.players.value >= 2


def requires_all_prizes(world, state):
    return (requires_sakura_flower(world, state) and requires_bouncy_cloud(world, state)
            and requires_pink_warrior_mask(world, state) and requires_two_players(world, state))


_CO_OP_PRIZE_BUBBLES = (7, 16, 17)

RULES = {
    BUBBLE_KEYS['PRIZE_BUBBLE_29']: requires_sakura_flower,
    BUBBLE_KEYS['PRIZE_BUBBLE_30']: requires_sakura_flower,
    BUBBLE_KEYS['PRIZE_BUBBLE_31']: requires_bouncy_cloud,
    BUBBLE_KEYS['PRIZE_BUBBLE_32']: requires_bouncy_cloud,
    BUBBLE_KEYS['PRIZE_BUBBLE_20']: requires_pink_warrior_mask,
    BUBBLE_KEYS['PRIZE_BUBBLE_21']: requires_pink_warrior_mask,
}
RULES.update({BUBBLE_KEYS[f'PRIZE_BUBBLE_{n}']: requires_two_players for n in _CO_OP_PRIZE_BUBBLES})
RULES[BUBBLE_KEYS['ALL_PRIZES']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_1']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_2']] = requires_all_prizes
RULES[BUBBLE_KEYS['ALL_PRIZES_REWARD_3']] = requires_all_prizes
