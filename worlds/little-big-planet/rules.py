from rule_builder.rules import Has, HasAll, HasAny, NestedRule

from .regions import victory_name


def rule_items(rule):
    """Every item name a rule can ask for."""
    if isinstance(rule, Has):
        return {rule.item_name}
    if isinstance(rule, (HasAll, HasAny)):
        return set(rule.item_names)
    if isinstance(rule, NestedRule):
        return set().union(*(rule_items(child) for child in rule.children))
    return set()


def set_rules(world):
    for location in world.get_locations():
        if location.data is not None:
            world.set_rule(location, location.data.access_rule(world))
    for guid in world.goal_guids:
        world.set_rule(world.get_location(victory_name(world, guid)), world.level_rule(guid))
    world.set_completion_rule(Has('Victory', len(world.goal_guids)))
