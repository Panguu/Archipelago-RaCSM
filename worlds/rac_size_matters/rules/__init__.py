from rule_builder.rules import Has

# Set completions need all four pieces, so progression placed there lets fill
# lock a missing piece behind its own set and dead-end the seed.
_NO_PROGRESSION_CATEGORIES = frozenset(("armour_set_check",))


def set_rules(world) -> None:
    from ..locations import ALL_LOCATIONS

    world.set_completion_rule(Has("Victory"))
    for location in world.get_locations():
        definition = ALL_LOCATIONS.get(location.name)
        if definition is None:
            continue
        world.set_rule(location, definition.rule(world))
        if definition.categories & _NO_PROGRESSION_CATEGORIES:
            location.item_rule = lambda item: not item.advancement
