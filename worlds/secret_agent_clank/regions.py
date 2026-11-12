from typing import TYPE_CHECKING

from BaseClasses import Region
from Options import OptionError
from rule_builder.rules import And, CanReachLocation, CanReachRegion, False_, Has, HasAll

from .constants import (
    ALL_CASES,
    CASES_BY_OPERATIVE,
    CASE_NAME_TO_CASE,
    EQUIPMENT_INTERNAL_TO_DISPLAY,
    KEYCARD_ITEMS,
    TITAN_LOCATIONS,
    VENDOR_CASES,
    VENDOR_WEAPONS,
    GoalOptions,
    SACCases,
    SACClankGadgets,
    SACOperatives,
    enabled_mods,
    vendor_location_name,
)
from .entities import SACItem, SACLocation
from .locations import (
    ALIEN_CODE_LOCATIONS,
    ALL_ALIEN_CODES_EVENT,
    BASE_VENDOR_LOCATIONS,
    CASE_REGIONS,
    KEYCARD_LOCATIONS,
    RATCHET_CHALLENGE_LOCATIONS,
    SKILL_POINT_LOCATIONS,
    create_nanotech_locations,
    create_ratchet_nanotech_locations,
    create_stealth_locations,
    create_weapon_level_locations,
)
from .options import Goal, enabled_operatives
from .rules import VENDOR_REQUIREMENTS, CaseAccessRule, disabled_operatives

if TYPE_CHECKING:
    from .world import SecretAgentClankWorld

def select_skill_points(world):
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


def create_regions(world: "SecretAgentClankWorld") -> None:
    player = world.player
    multiworld = world.multiworld
    disabled = disabled_operatives(world)
    world.selected_skill_points = select_skill_points(world)

    menu_region = Region("Menu", player, multiworld)
    has_vendor = any(
        case.operative not in disabled and
        not isinstance(VENDOR_REQUIREMENTS.get(case.name, False_()), False_)
        for case in ALL_CASES
    )
    world.has_vendor = has_vendor
    def available_stock(name):
        return CASE_NAME_TO_CASE[VENDOR_CASES[name]].operative not in disabled

    world.weapon_mod_catalog = (
        tuple(mod for mod in enabled_mods(enabled_operatives(world.options), world.options.ng_plus.value)
              if available_stock(mod.location)) if has_vendor else ()
    )
    if world.using_ut:
        saved_ids = world.passthrough["weapon_mod_ids"]
        world.weapon_mod_catalog = tuple(mod for mod in enabled_mods(
            enabled_operatives(world.options), world.options.ng_plus.value) if mod.mod_id in saved_ids)
    vendor_stock: set[str] = set()
    if has_vendor:
        def enabled_item(name):
            return (SACOperatives.CLANK if name.endswith("(Clank)")
                    else SACOperatives.RATCHET) not in disabled
        vendor_stock.update(vendor_location_name(item) for item in VENDOR_WEAPONS
                            if enabled_item(item)
                            and BASE_VENDOR_LOCATIONS[vendor_location_name(item)].available(world.options)
                            and available_stock(vendor_location_name(item)))
        vendor_stock.update(mod.location for mod in world.weapon_mod_catalog)
        if world.options.ng_plus.value:
            vendor_stock.update(name for internal, name in TITAN_LOCATIONS.items()
                                if enabled_item(EQUIPMENT_INTERNAL_TO_DISPLAY[internal]) and available_stock(name))

    def enabled(definition) -> bool:
        if definition.name in SKILL_POINT_LOCATIONS:
            return definition.name in world.selected_skill_points
        if definition.name in VENDOR_CASES:
            return definition.name in vendor_stock
        return definition.available(world.options)

    case_regions: dict[str, Region] = {
        case.name: Region(case.name, player, multiworld)
        for case in ALL_CASES if case.operative not in disabled
    }

    for case_name, region in case_regions.items():
        definitions = sorted(CASE_REGIONS[case_name].locations, key=lambda location: location.region_order)
        region.add_locations({
            definition.name: world.location_name_to_id[definition.name] for definition in definitions
            if enabled(definition)
        }, SACLocation)

    multiworld.regions += [menu_region, *case_regions.values()]
    _create_treehouse_event(world, menu_region)
    _create_victory(world, case_regions, disabled)

    for case_name, region in case_regions.items():
        menu_region.connect(region, f"To {case_name}")

    create_weapon_level_locations(world, menu_region)
    create_nanotech_locations(world, menu_region)
    create_ratchet_nanotech_locations(world, menu_region)
    create_stealth_locations(world, menu_region)


def _create_treehouse_event(world, menu_region):
    """The native Case Files menu opens High Impact Treehouse once all 27 Alien Codes are scanned."""
    reach = [CanReachLocation(location.name) if world.options.alien_code_checks_enabled
             else CanReachRegion(location.case) for location in ALIEN_CODE_LOCATIONS.values()]
    menu_region.add_event(ALL_ALIEN_CODES_EVENT, SACCases.HIGH_TREEHOUSE,
                          Has(SACClankGadgets.THERM_OPTIC_SHADES) & And(*reach),
                          location_type=SACLocation, item_type=SACItem)


def _create_victory(world, case_regions, disabled_operatives):
    def add_victory(name, region, rule):
        region.add_event(name, "Victory", rule, location_type=SACLocation, item_type=SACItem)

    if world.options.goal != GoalOptions.PICK_AND_MIX:
        _create_goal_conditions(world, case_regions, disabled_operatives,
                                world.options.goal.value, add_victory)
        return
    selected = world.options.pick_and_mix_goals.value
    if not selected:
        raise OptionError(f"{world.multiworld.get_player_name(world.player)}: "
                          "Pick and Mix requires at least one selected goal.")
    conditions = []
    for name in sorted(selected):
        _create_goal_conditions(world, case_regions, disabled_operatives,
                                Goal.from_any(name).value,
                                lambda title, region, rule: conditions.append((region, rule)))
    rule = And(*(CanReachRegion(region.name) & condition for region, condition in conditions))
    add_victory("Victory: Pick and Mix", conditions[0][0], rule)


INDIVIDUAL_GOALS: tuple[int, ...] = (
    GoalOptions.DEFEAT_KLUNK, GoalOptions.QWARK_OPERA, GoalOptions.ALL_GADGETBOTS,
    GoalOptions.RATCHET_PRISON_ESCAPE, GoalOptions.THESE_ARE_THE_REAL_ADVENTURES_OF_CAPTAIN_QWARK,
    GoalOptions.ALIEN_CODES, GoalOptions.CHALICE_OF_POWER,
)
GOAL_TITLES: dict[int, str] = {
    GoalOptions.DEFEAT_KLUNK: "Defeat Klunk",
    GoalOptions.QWARK_OPERA: "Qwark Opera",
    GoalOptions.ALL_GADGETBOTS: "All Gadgetbots",
    GoalOptions.RATCHET_PRISON_ESCAPE: "Ratchet Prison Escape",
    GoalOptions.THESE_ARE_THE_REAL_ADVENTURES_OF_CAPTAIN_QWARK: "These Are the Real Adventures of Captain Qwark",
    GoalOptions.ALIEN_CODES: "All Alien Codes",
    GoalOptions.CHALICE_OF_POWER: "Collect the Chalice of Power",
}
_GOAL_OPERATIVES: dict[int, str] = {
    GoalOptions.QWARK_OPERA: SACOperatives.QWARK,
    GoalOptions.ALL_GADGETBOTS: SACOperatives.GADGETBOTS,
    GoalOptions.RATCHET_PRISON_ESCAPE: SACOperatives.RATCHET,
    GoalOptions.THESE_ARE_THE_REAL_ADVENTURES_OF_CAPTAIN_QWARK: SACOperatives.QWARK,
}


def _collectibles(goal: int, keycard_hunt=False) -> tuple:
    """Physical keycards the Chalice needs inside the Treehouse, unless they are shuffled."""
    if goal == GoalOptions.CHALICE_OF_POWER and not keycard_hunt:
        return tuple(KEYCARD_LOCATIONS.values())
    return ()


def _goal_unavailable(goal: int, case_regions: dict[str, Region], disabled_operatives: set[str], keycard_hunt=False) -> str | None:
    """Why `goal` cannot be completed with these options, or None when it can."""
    operative = _GOAL_OPERATIVES.get(goal)
    if operative in disabled_operatives:
        return f"requires {operative}, but {operative} is disabled via the Operatives option"
    if goal in (GoalOptions.ALIEN_CODES, GoalOptions.CHALICE_OF_POWER):
        for location in _collectibles(goal, keycard_hunt):
            if location.case not in case_regions:
                return f"requires disabled case {location.case}"
    return None


def _create_goal_conditions(
    world: "SecretAgentClankWorld", case_regions: dict[str, Region], disabled_operatives: set[str],
    goal: int, add_victory,
) -> None:
    player_name = world.multiworld.get_player_name(world.player)
    if goal == GoalOptions.ANY:
        goals = [g for g in INDIVIDUAL_GOALS if _goal_unavailable(g, case_regions, disabled_operatives, bool(world.options.keycard_hunt)) is None]
        if not goals:
            raise OptionError(f"{player_name}'s Secret Agent Clank: Goal is Any, but no goal can be "
                              "completed with the enabled operatives.")
        for g in goals:
            _add_goal_victory(world, case_regions, g, add_victory)
        return
    reason = _goal_unavailable(goal, case_regions, disabled_operatives, bool(world.options.keycard_hunt))
    if reason is not None:
        raise OptionError(f"{player_name}'s Secret Agent Clank: Goal is {GOAL_TITLES[goal]}, which {reason}.")
    _add_goal_victory(world, case_regions, goal, add_victory)


def _add_goal_victory(world: "SecretAgentClankWorld", case_regions: dict[str, Region], goal: int, add_victory) -> None:
    title = f"Victory: {GOAL_TITLES[goal]}"
    if goal in (GoalOptions.ALIEN_CODES, GoalOptions.CHALICE_OF_POWER):
        rule = Has(SACCases.HIGH_TREEHOUSE)
        if goal == GoalOptions.CHALICE_OF_POWER:
            if world.options.keycard_hunt:
                rule = rule & HasAll(*KEYCARD_ITEMS)
            else:
                rule = rule & And(*(CanReachLocation(location.name) if world.options.keycard_checks_enabled
                                    else CanReachRegion(location.case)
                                    for location in _collectibles(goal)))
        region = case_regions[next(iter(ALIEN_CODE_LOCATIONS.values())).case]
        add_victory(title, region, rule)
    elif goal == GoalOptions.RATCHET_PRISON_ESCAPE:
        rule = And(*(CanReachLocation(name) for name in RATCHET_CHALLENGE_LOCATIONS))
        add_victory(title, case_regions[SACCases.PRISON_BREAKOUT], rule)
    else:
        cases = {
            GoalOptions.DEFEAT_KLUNK: (CASE_NAME_TO_CASE[SACCases.KLUNKS_LAIR],),
            GoalOptions.QWARK_OPERA: (CASE_NAME_TO_CASE[SACCases.MADAM_BUTTERQWARK],),
            GoalOptions.ALL_GADGETBOTS: CASES_BY_OPERATIVE[SACOperatives.GADGETBOTS],
            GoalOptions.THESE_ARE_THE_REAL_ADVENTURES_OF_CAPTAIN_QWARK: CASES_BY_OPERATIVE[SACOperatives.QWARK],
        }[goal]
        rule = And(*(CaseAccessRule(case.name) for case in cases))
        add_victory(title, case_regions[cases[0].name], rule)
