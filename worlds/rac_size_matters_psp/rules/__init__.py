from .entrances import set_entrance_rules


def set_rules(world) -> None:
    world.multiworld.completion_condition[world.player] = lambda state: state.has("Victory", world.player)
    set_entrance_rules(world)
    for location in world.multiworld.get_locations(world.player):
        world.set_rule(location, location.rule_factory(world))
