"""One region per case, each entered from Menu through a "To <Case>" entrance gated by that case's access rule."""
from typing import TYPE_CHECKING

from BaseClasses import Region
from Options import OptionError
from rule_builder.rules import CanReachLocation, CanReachRegion, False_, Has, True_

from .constants import ALL_CASES, CASE_NAME_TO_CASE, CASES_BY_OPERATIVE, SACCases, SACOperatives
from .constants.clank_gadgets import SACClankGadgets
from .constants.weapon_mods import enabled_mods
from .constants.vendor_unlocks import VENDOR_CASES
from .constants.weapon_progression import TITAN_LOCATIONS
from .constants.weapons import EQUIPMENT_INTERNAL_TO_DISPLAY
from .entities import SACLocation
from .locations import (
    ALIEN_CODE_LOCATIONS,
    BASE_VENDOR_LOCATIONS,
    CASE_REGIONS,
    KEYCARD_LOCATIONS,
    RATCHET_CHALLENGE_LOCATIONS,
    SKILL_POINT_LOCATIONS,
)
from .locations.nanotech import create_nanotech_locations, create_ratchet_nanotech_locations
from .locations.stealth import create_stealth_locations
from .locations.skill_points import select_skill_points
from .locations.weapon_levels import create_weapon_level_locations
from .options import Goal
from .rules.rule_helpers import case_access_rule, disabled_operatives
from .rules.vendor_access import VENDOR_REQUIREMENTS

if TYPE_CHECKING:
    from .world import SecretAgentClankWorld

def create_regions(world: "SecretAgentClankWorld") -> None:
    player = world.player
    multiworld = world.multiworld
    disabled = disabled_operatives(world)
    world.selected_skill_points = select_skill_points(world)

    menu_region = Region("Menu", player, multiworld)
    # Clank's menu and Ratchet's PDA both provide vendor routes.
    has_vendor = any(
        case.operative not in disabled and
        not isinstance(VENDOR_REQUIREMENTS.get(case.name, False_()), False_)
        for case in ALL_CASES
    )
    world.has_vendor = has_vendor
    def available_stock(name):
        return CASE_NAME_TO_CASE[VENDOR_CASES[name]].operative not in disabled

    world.weapon_mod_catalog = (
        tuple(mod for mod in enabled_mods(world.options.operatives.value, world.options.ng_plus.value)
              if available_stock(mod.location)) if has_vendor else ()
    )
    if world.using_ut:
        saved_ids = world.passthrough.get("weapon_mod_ids", ())
        world.weapon_mod_catalog = tuple(mod for mod in enabled_mods(
            world.options.operatives.value, world.options.ng_plus.value) if mod.mod_id in saved_ids)
    if has_vendor:
        vendor_region = Region("Vendor", player, multiworld)
        def enabled_item(name):
            return (SACOperatives.CLANK if name.endswith("(Clank)")
                    else SACOperatives.RATCHET) not in disabled
        for definition in BASE_VENDOR_LOCATIONS.values():
            if enabled_item(definition.name) and definition.available(world.options) and available_stock(definition.name):
                vendor_region.locations.append(SACLocation(
                    player, definition.name, world.location_name_to_id[definition.name], vendor_region))
        for mod in world.weapon_mod_catalog:
            vendor_region.locations.append(SACLocation(
                player, mod.location, world.location_name_to_id[mod.location], vendor_region))
        if world.options.ng_plus.value:
            for internal, name in TITAN_LOCATIONS.items():
                if enabled_item(EQUIPMENT_INTERNAL_TO_DISPLAY[internal]) and available_stock(name):
                    vendor_region.locations.append(SACLocation(
                        player, name, world.location_name_to_id[name], vendor_region))
        menu_region.connect(vendor_region)
        multiworld.regions.append(vendor_region)
    case_regions: dict[str, Region] = {
        case.name: Region(case.name, player, multiworld)
        for case in ALL_CASES if case.operative not in disabled
    }

    for case_name, region in case_regions.items():
        # Stable sort: locations of one type keep their case file's order.
        for definition in sorted(CASE_REGIONS[case_name].locations, key=lambda location: location.region_order):
            if definition.name in SKILL_POINT_LOCATIONS:
                if definition.name in world.selected_skill_points:
                    region.locations.append(SACLocation(player, definition.name, world.location_name_to_id[definition.name], region))
                continue
            if definition.available(world.options):
                region.locations.append(SACLocation(player, definition.name, world.location_name_to_id[definition.name], region))

    _create_victory(world, case_regions, disabled)

    for case_name, region in case_regions.items():
        menu_region.connect(region, f"To {case_name}")

    multiworld.regions += [menu_region, *case_regions.values()]
    create_weapon_level_locations(world, menu_region)
    create_nanotech_locations(world, menu_region)
    create_ratchet_nanotech_locations(world, menu_region)
    create_stealth_locations(world, menu_region)


def _create_victory(world, case_regions, disabled_operatives):
    def add_victory(name, region, rule):
        loc = SACLocation(world.player, name, None, region)
        loc.place_locked_item(world.create_event("Victory"))
        world.set_rule(loc, rule)
        region.locations.append(loc)

    if world.options.goal != Goal.option_pick_and_mix:
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
    rule = True_()
    for region, condition in conditions:
        rule = rule & CanReachRegion(region.name) & condition
    add_victory("Victory: Pick and Mix", conditions[0][0], rule)


def _create_goal_conditions(
    world: "SecretAgentClankWorld", case_regions: dict[str, Region], disabled_operatives: set[str],
    goal: int, add_victory,
) -> None:
    """Validate one goal and pass its victory requirements to the caller."""
    player = world.player
    player_name = world.multiworld.get_player_name(player)
    clank_disabled = SACOperatives.CLANK in disabled_operatives
    qwark_disabled = SACOperatives.QWARK in disabled_operatives
    gadgetbots_disabled = SACOperatives.GADGETBOTS in disabled_operatives
    ratchet_disabled = SACOperatives.RATCHET in disabled_operatives

    if goal == Goal.option_defeat_klunk and clank_disabled:
        raise OptionError(
            f"{player_name}'s Secret Agent Clank: Goal is Defeat Klunk, which requires Clank, "
            "but Clank is disabled via the Operatives option."
        )
    if goal == Goal.option_qwark_opera and qwark_disabled:
        raise OptionError(
            f"{player_name}'s Secret Agent Clank: Goal is Qwark Opera, which requires Qwark, "
            "but Qwark is disabled via the Operatives option."
        )
    if goal == Goal.option_any and clank_disabled and qwark_disabled:
        raise OptionError(
            f"{player_name}'s Secret Agent Clank: Goal is Any, which requires Clank or Qwark, "
            "but both are disabled via the Operatives option."
        )
    if goal == Goal.option_all_gadgetbots and gadgetbots_disabled:
        raise OptionError(
            f"{player_name}'s Secret Agent Clank: Goal is All Gadgetbots, which requires Gadgetbots, "
            "but Gadgetbots is disabled via the Operatives option."
        )
    if goal == Goal.option_ratchet_prison_escape and ratchet_disabled:
        raise OptionError(
            f"{player_name}'s Secret Agent Clank: Goal is Ratchet Prison Escape, which requires Ratchet, "
            "but Ratchet is disabled via the Operatives option."
        )

    if goal in (Goal.option_alien_codes, Goal.option_chalice_of_power):
        alien_codes = goal == Goal.option_alien_codes
        collectibles = tuple((ALIEN_CODE_LOCATIONS if alien_codes else KEYCARD_LOCATIONS).values())
        locations_enabled = world.options.alien_code_checks_enabled if alien_codes else world.options.keycard_checks_enabled
        rule = True_()
        for location in collectibles:
            if location.case not in case_regions:
                raise OptionError(f"{player_name}: the selected goal requires disabled case {location.case}.")
            # Without AP reward checks, the native collectibles remain available in their case.
            rule = rule & (CanReachLocation(location.name) if locations_enabled else CanReachRegion(location.case))
        if alien_codes:
            rule = rule & Has(SACClankGadgets.THERM_OPTIC_SHADES)
        title = "All Alien Codes" if alien_codes else "Collect the Chalice of Power"
        add_victory(f"Victory: {title}", case_regions[collectibles[0].case], rule)

    if goal in (Goal.option_defeat_klunk, Goal.option_any) and not clank_disabled:
        case = CASE_NAME_TO_CASE[SACCases.KLUNKS_LAIR]
        add_victory("Victory: Defeat Klunk", case_regions[case.name], case_access_rule(world, case))

    if goal in (Goal.option_qwark_opera, Goal.option_any) and not qwark_disabled:
        qwark_cases = CASES_BY_OPERATIVE[SACOperatives.QWARK]
        rule = case_access_rule(world, qwark_cases[0])
        for case in qwark_cases[1:]:
            rule = rule & case_access_rule(world, case)
        add_victory("Victory: Qwark Opera", case_regions[qwark_cases[0].name], rule)

    if goal == Goal.option_all_gadgetbots and not gadgetbots_disabled:
        gadgetbot_cases = CASES_BY_OPERATIVE[SACOperatives.GADGETBOTS]
        rule = case_access_rule(world, gadgetbot_cases[0])
        for case in gadgetbot_cases[1:]:
            rule = rule & case_access_rule(world, case)
        add_victory("Victory: All Gadgetbots", case_regions[gadgetbot_cases[0].name], rule)

    if goal == Goal.option_ratchet_prison_escape and not ratchet_disabled:
        rule = True_()
        for name in RATCHET_CHALLENGE_LOCATIONS:
            rule = rule & CanReachLocation(name)
        add_victory("Victory: Ratchet Prison Escape", case_regions[SACCases.PRISON_BREAKOUT], rule)
