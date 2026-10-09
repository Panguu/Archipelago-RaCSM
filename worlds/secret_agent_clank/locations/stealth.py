"""Per-case cumulative successful Clank stealth takedown checks."""
from BaseClasses import Region

from ..constants import SACOperatives
from ..constants.stealth import STEALTH_CASES, STEALTH_MAX_PER_CASE, stealth_check_count, stealth_location_name
from ..entities import SACLocation as Location
from ..rules.rule_helpers import region_names
from ..rules.stealth import stealth_access_rule
from .model import SACLocation, SACLocationType

STEALTH_TAKEDOWN_LOCATIONS = {
    stealth_location_name(case, count): SACLocation(
        stealth_location_name(case, count), SACLocationType.STEALTH_TAKEDOWN,
    ) for case in STEALTH_CASES for count in range(1, STEALTH_MAX_PER_CASE + 1)
}


def stealth_case_counts(world):
    """Case -> stealth checks it gets in this world (only existing cases with at least one)."""
    if SACOperatives.CLANK not in world.options.operatives.value:
        return {}
    if world.using_ut:
        # The tracker follows the seed's table, not this apworld's.
        return dict(world.passthrough.get("stealth_cases", {}))
    existing = region_names(world)
    counts = {case: stealth_check_count(case, world.options.stealth_takedown_checks.value)
              for case in STEALTH_CASES if case in existing}
    return {case: count for case, count in counts.items() if count}


def create_stealth_locations(world, menu_region):
    counts = stealth_case_counts(world)
    if not counts:
        return
    region = Region("Clank Stealth Takedowns", world.player, world.multiworld)
    for case, count in counts.items():
        rule = stealth_access_rule(world, case)
        for takedown in range(1, count + 1):
            name = stealth_location_name(case, takedown)
            location = Location(world.player, name, world.location_name_to_id[name], region)
            world.set_rule(location, rule)
            region.locations.append(location)
    menu_region.connect(region)
    world.multiworld.regions.append(region)
