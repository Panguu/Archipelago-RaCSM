"""Choose the seed's eligible skill points once, and preserve that set for UT."""
from Options import OptionError


def select_skill_points(world):
    from . import SKILL_POINT_LOCATIONS

    eligible = sorted(name for name, definition in SKILL_POINT_LOCATIONS.items()
                      if definition.available(world.options))
    if world.using_ut and "selected_skill_points" in world.passthrough:
        return frozenset(world.passthrough["selected_skill_points"])
    if not world.options.skill_points or not world.options.random_skill_points:
        return frozenset(eligible)
    count = world.options.skill_point_count.value
    if count > len(eligible):
        raise OptionError(
            f"{world.multiworld.player_name[world.player]}: Random Skill Points requests {count}, "
            f"but only {len(eligible)} are available with difficulty "
            f"{world.options.skill_points.current_key} and the enabled operatives. "
            "Lower Random Skill Point Count, raise the difficulty, or enable more operatives."
        )
    return frozenset(world.random.sample(eligible, count))
