from .entrances import set_entrance_rules
from rule_builder.rules import Has

from ..items import CLANK_PACK_NAME


# Until individual routes have been verified without the backpack, field checks
# conservatively require it. Shops provide places to find the unlock; their
# existing weapon/gadget/challenge-mode requirements still apply.
_PACK_FREE_CATEGORIES = frozenset((
    "weapon_vendor", "gadget_vendor", "weapon_mod_vendor", "weapon_titan_vendor",
    "armour_set_check", "challenge", "all_clank", "clank_challenge_skill_point",
))

# Set completions need all four pieces, so progression placed there lets fill
# lock a missing piece behind its own set and dead-end the seed.
_NO_PROGRESSION_CATEGORIES = frozenset(("armour_set_check",))


def set_rules(world) -> None:
    from ..locations import LOCATIONS

    pack_free_locations = {
        definition.name for definition in LOCATIONS
        if definition.categories & _PACK_FREE_CATEGORIES
    }
    no_progression_locations = {
        definition.name for definition in LOCATIONS
        if definition.categories & _NO_PROGRESSION_CATEGORIES
    }
    world.multiworld.completion_condition[world.player] = lambda state: state.has("Victory", world.player)
    set_entrance_rules(world)
    for location in world.multiworld.get_locations(world.player):
        rule = location.rule_factory(world)
        if world.options.clank_pack and location.name not in pack_free_locations:
            rule = rule & Has(CLANK_PACK_NAME)
        world.set_rule(location, rule)
        if location.name in no_progression_locations:
            location.item_rule = lambda item: not item.advancement
