import os
from typing import Any, ClassVar

from BaseClasses import CollectionState, Tutorial
from Options import OptionError
from rule_builder.rules import Has
from worlds.AutoWorld import WebWorld, World

from .constants import (
    ALL_CASES,
    ALL_FILLER,
    CASES_BY_PLANET,
    CASE_NAME_TO_INFOBOT,
    EQUIPMENT_DISPLAY_TO_INTERNAL,
    GADGETS_FROM_WEAPON_TABLE,
    LEVELLED_INTERNALS,
    NG_PLUS_VENDOR_ITEMS,
    PLANET_NAMES,
    PROGRESSIVE_CHALLENGE_MODE,
    PROGRESSIVE_PLANET_ITEM_NAME,
    PROGRESSIVE_TO_INTERNAL,
    PROGRESSIVE_TO_UNLOCK,
    PROGRESSIVE_WRENCH,
    RATCHET_WEAPONS,
    UNLOCK_TO_PROGRESSIVE,
    InfobotsOptions,
    ProgressiveWeaponsOptions,
    SACCases,
    SACFiller,
    SACOperatives,
    WeaponMod,
    enabled_challenge_mods,
    max_level,
)
from .entities import SACItem, SACProgressiveItem
from .items import (
    ALL_ITEMS,
    CASE_GADGET_ITEM_TABLE,
    ITEM_NAME_GROUPS,
    KEYCARD_ITEM_TABLE,
    RATCHET_WEAPON_ITEM_TABLE,
    RATCHET_PACK_ITEM_TABLE,
    TRAP_ITEM_TABLE,
    EQUIPMENT_ITEM_TABLE,
)
from .locations import CASE_REGIONS, LOCATIONS, LOCATION_NAME_TO_ID, stealth_case_counts
from .patcher import SACPatch, add_release_patch
from .options import SLOT_DATA_OPTIONS, SecretAgentClankOptions, enabled_operatives, sac_option_groups
from .regions import create_regions
from .rules import VENDOR_ONLY_ITEM_NAMES, region_names, set_entrance_rules
from .universal_tracker import setup_options_from_slot_data
from .settings import SecretAgentClankSettings
from .vendor_logic import export_vendor_rules

try:
    from worlds.dynamicpine import DynamicPineGame
    _DYNAMIC_PINE_SPEC = DynamicPineGame(
        game_ids="SCUS-97623",
        client_component="Secret Agent Clank Client",
        launcher_options="simple",
    )
except ImportError:
    _DYNAMIC_PINE_SPEC = None


MIN_START_ROOM = 4


class SACWeb(WebWorld):
    theme = "ocean"
    tutorials = [
        Tutorial(
            "Multiworld Setup Guide",
            "A guide to setting up Secret Agent Clank for Archipelago.",
            "English",
            "setup_en.md",
            "setup/en",
            ["Archipelago Community"],
        )
    ]
    option_groups = sac_option_groups


class SecretAgentClankWorld(World):
    """Secret Agent Clank is a 2008 PS2 action-platformer spin-off following Ratchet, Clank, Qwark, and the Gadgetbots on an undercover mission across the galaxy."""

    game = "Secret Agent Clank"
    web = SACWeb()
    options_dataclass = SecretAgentClankOptions
    options: SecretAgentClankOptions
    settings: ClassVar[SecretAgentClankSettings]
    settings_key = "secret_agent_clank_options"  # the default would be "secret_agent_clank.world_options"

    item_name_to_id: dict[str, int] = {name: data.code for name, data in ALL_ITEMS.items()}
    item_name_groups = ITEM_NAME_GROUPS
    location_name_to_id: dict[str, int] = LOCATION_NAME_TO_ID
    dynamic_pine = _DYNAMIC_PINE_SPEC

    using_ut: bool = False
    passthrough: dict[str, Any]
    ut_can_gen_without_yaml: bool = True

    has_vendor: bool
    weapon_mod_catalog: tuple[WeaponMod, ...]
    starting_case: str
    second_starting_case: str

    def create_item(self, name: str) -> SACItem:
        data = ALL_ITEMS[name]
        stages = self.progressive_stages(name)
        if stages is not None:
            return SACProgressiveItem(name, data.classification, data.code, self.player, stages)
        return SACItem(name, data.classification, data.code, self.player)

    def progressive_stages(self, name: str) -> list[str] | None:
        """What each copy of a progressive item unlocks, in order. None if `name` isn't progressive."""
        if name in PROGRESSIVE_TO_UNLOCK:
            weapon = PROGRESSIVE_TO_UNLOCK[name]
            levels = max_level(PROGRESSIVE_TO_INTERNAL[name], self.options.ng_plus.value)
            return [weapon] + [f"{weapon} V{level}" for level in range(2, levels + 1)]
        for planet, item in PROGRESSIVE_PLANET_ITEM_NAME.items():
            if name == item:
                return self.planet_cases.get(planet, [])  # shuffled per seed
        if name == PROGRESSIVE_WRENCH:
            return [f"Wrench Level {level}" for level in range(1, 6)]
        if name == PROGRESSIVE_CHALLENGE_MODE:
            return [f"Challenge Mode {level}" for level in range(1, self.options.ng_plus.value + 1)]
        return None

    def collect(self, state, item):
        changed = super().collect(state, item)
        if changed and item.name in PROGRESSIVE_TO_UNLOCK:
            state.add_item(PROGRESSIVE_TO_UNLOCK[item.name], self.player)
        return changed

    def remove(self, state, item):
        changed = super().remove(state, item)
        if changed and item.name in PROGRESSIVE_TO_UNLOCK:
            state.remove_item(PROGRESSIVE_TO_UNLOCK[item.name], self.player)
        return changed

    def generate_early(self) -> None:
        setup_options_from_slot_data(self)

    def create_regions(self) -> None:
        create_regions(self)

    @property
    def planet_cases(self) -> dict[str, list[str]]:
        if self.using_ut:
            return {planet: list(cases) for planet, cases in self.passthrough["planet_cases"].items()}
        regions = region_names(self)
        cases = {planet: [case.name for case in CASES_BY_PLANET[planet] if case.name in regions]
                 for planet in PLANET_NAMES}
        return {planet: names for planet, names in cases.items() if names}

    def set_rules(self) -> None:
        self.set_completion_rule(Has("Victory"))
        set_entrance_rules(self)
        locations = {location.name: location for location in self.multiworld.get_locations(self.player)}
        for definition in LOCATIONS:
            location = locations.get(definition.name)
            rule = definition.resolve_rule(self) if location is not None else None
            if rule is not None:
                self.set_rule(location, rule)

    def generate_basic(self) -> None:
        if self.using_ut:
            return
        state = CollectionState(self.multiworld)
        if any(location.item is None for location in self.multiworld.get_reachable_locations(state, self.player)):
            return
        if any(location.item is None for location in self.multiworld.get_reachable_locations(state)):
            return
        player_name = self.multiworld.get_player_name(self.player)
        raise OptionError(
            f"{player_name}'s Secret Agent Clank has no locations reachable from the starting inventory "
            f"(starting case: {self.starting_case}), so items cannot be placed. Enable more operatives or cases, "
            "raise starting_weapons / starting_gadgets, or turn on more location checks "
            "(such as Missions: All, All Cutscenes, Skill Points, Keycards, Alien Codes, "
            "Weapon Level Checks, Clank Nanotech Locations or Ratchet Nanotech Locations)."
        )

    def _start_room(self, case) -> int:
        """Locations inside `case` reachable from the precollected inventory and its Case File."""
        state = CollectionState(self.multiworld)
        for name in self._starting_items((case,)):
            state.collect(self.create_item(name), prevent_sweep=True)
        existing = {location.name for location in self.multiworld.get_region(case.name, self.player).locations}
        room = 0
        for definition in CASE_REGIONS[case.name].locations:
            if definition.name not in existing:
                continue
            rule = definition.resolve_rule(self)
            if rule is None or rule.resolve(self)(state):
                room += 1
        return room

    def _starting_items(self, cases) -> list[str]:
        if self.options.infobots == InfobotsOptions.PROGRESSIVE_PLANET:
            planet_cases = self.planet_cases
            counts: dict[str, int] = {}
            for case in cases:
                order = planet_cases[case.planet]
                counts[case.planet] = max(counts.get(case.planet, 0), order.index(case.name) + 1)
            return [PROGRESSIVE_PLANET_ITEM_NAME[planet] for planet, count in counts.items() for _ in range(count)]
        return [CASE_NAME_TO_INFOBOT[case.name] for case in cases]

    def _choose_starting_cases(self, candidates):
        """Two random distinct starting cases, at least one Clank's, preferring pairs that open
        at least MIN_START_ROOM locations between them before any item is received."""
        # Region reachability decides some rules (vendors need enemy access), so the
        # case entrances need their rules before the starts are scored.
        set_entrance_rules(self)
        if self.options.infobots == InfobotsOptions.PROGRESSIVE_PLANET:
            # A later case would also open every case before it on its planet,
            # so start on cases that are first in their planet's unlock order.
            planet_cases = self.planet_cases
            firsts = [case for case in candidates if planet_cases[case.planet][0] == case.name]
            if len(firsts) > 1 and any(case.operative == SACOperatives.CLANK for case in firsts):
                candidates = firsts
        room = {case.name: self._start_room(case) for case in candidates}
        pairs = [(first, second) for first in candidates for second in candidates
                 if first is not second and SACOperatives.CLANK in (first.operative, second.operative)]
        roomy = [pair for pair in pairs if all(room[case.name] for case in pair)
                 and sum(room[case.name] for case in pair) >= MIN_START_ROOM]
        if not roomy:
            best = max(sum(room[case.name] for case in pair) for pair in pairs)
            roomy = [pair for pair in pairs if sum(room[case.name] for case in pair) == best]
        return self.random.choice(roomy)

    def create_items(self) -> None:
        existing = region_names(self)
        active_cases = [case for case in ALL_CASES if case.name in existing]
        candidates = [case for case in active_cases
                      if case.operative in enabled_operatives(self.options)
                      and case.name != SACCases.KLUNKS_LAIR]
        if not candidates:
            raise OptionError("Secret Agent Clank requires at least one enabled operative")
        pool: list[str] = []
        if self.options.keycard_hunt:
            pool += list(KEYCARD_ITEM_TABLE)
        if self.options.progressive_challenge_mode:
            pool += [PROGRESSIVE_CHALLENGE_MODE] * self.options.ng_plus.value
        pool += [mod.name for mod in self.weapon_mod_catalog]
        pool += [mod.name for mod in enabled_challenge_mods(enabled_operatives(self.options))]
        ratchet_enabled = SACOperatives.RATCHET in enabled_operatives(self.options)
        if ratchet_enabled and self.options.progressive_wrench:
            pool += [PROGRESSIVE_WRENCH] * 5

        for name in EQUIPMENT_ITEM_TABLE:
            if name in RATCHET_WEAPON_ITEM_TABLE and not ratchet_enabled:
                continue
            if name in NG_PLUS_VENDOR_ITEMS and not self.options.ng_plus.value:
                continue
            if not self.has_vendor and name in VENDOR_ONLY_ITEM_NAMES:
                continue
            if self.options.progressive_weapons and name in UNLOCK_TO_PROGRESSIVE:
                progressive = UNLOCK_TO_PROGRESSIVE[name]
                pool += [progressive] * max_level(PROGRESSIVE_TO_INTERNAL[progressive], self.options.ng_plus.value)
            else:
                pool.append(name)
        pool += list(CASE_GADGET_ITEM_TABLE)
        if ratchet_enabled:
            pool += list(RATCHET_PACK_ITEM_TABLE)

        starting_groups = (
            (SACOperatives.RATCHET, self.options.starting_weapons.value,
             [name for name in RATCHET_WEAPONS
              if EQUIPMENT_DISPLAY_TO_INTERNAL[name] in LEVELLED_INTERNALS or EQUIPMENT_DISPLAY_TO_INTERNAL[name] == "hypnowatch"]),
            (SACOperatives.CLANK, self.options.starting_gadgets.value,
             list(dict.fromkeys([*GADGETS_FROM_WEAPON_TABLE, *CASE_GADGET_ITEM_TABLE]))),
        )
        for character, count, eligible in starting_groups:
            if character not in enabled_operatives(self.options):
                continue
            eligible = [UNLOCK_TO_PROGRESSIVE.get(name, name)
                        if self.options.progressive_weapons else name for name in eligible]
            eligible = [name for name in eligible if name in pool]
            if count > len(eligible):
                raise OptionError(f"Not enough eligible {character} starting items for {count} selections")
            for name in self.random.sample(eligible, count):
                pool.remove(name)
                self.multiworld.push_precollected(self.create_item(name))

        if self.using_ut:
            names = (self.passthrough["starting_case"], self.passthrough["second_starting_case"])
            starting_case, second_starting_case = (
                next(case for case in candidates if case.name == name) for name in names)
        else:
            starting_case, second_starting_case = self._choose_starting_cases(candidates)
        self.starting_case = starting_case.name
        self.second_starting_case = second_starting_case.name
        starting_items = self._starting_items((starting_case, second_starting_case))
        for name in starting_items:
            self.multiworld.push_precollected(self.create_item(name))
        starting_cases = {self.starting_case, self.second_starting_case}

        if self.options.infobots == InfobotsOptions.PROGRESSIVE_PLANET:
            for planet, cases in self.planet_cases.items():
                item = PROGRESSIVE_PLANET_ITEM_NAME[planet]
                pool += [item] * (len(cases) - starting_items.count(item))
        else:
            pool += [
                CASE_NAME_TO_INFOBOT[case.name] for case in active_cases
                if case.name not in starting_cases
            ]

        unfilled = len(self.multiworld.get_unfilled_locations(self.player))
        if len(pool) > unfilled:
            raise OptionError(
                f"Secret Agent Clank needs {len(pool)} item locations, but only {unfilled} are enabled. "
                f"Enable at least {len(pool) - unfilled} more optional locations (such as Missions: All, "
                "All Cutscenes, Skill Points, Keycards or Alien Codes)."
                + (" Progressive Weapons can also increase the required pool size."
                   if self.options.progressive_weapons else "")
            )
        filler_count = max(0, unfilled - len(pool))
        pool += [self.get_filler_item_name() for _ in range(filler_count)]

        for name in pool:
            self.multiworld.itempool.append(self.create_item(name))

    def fill_slot_data(self) -> dict[str, Any]:
        return {
            "iso_patch_abi": 1,
            "vendor_rules": export_vendor_rules(self),
            "planet_cases": self.planet_cases,
            "starting_case": self.starting_case,
            "second_starting_case": self.second_starting_case,
            "weapon_mod_ids": [mod.mod_id for mod in self.weapon_mod_catalog],
            "operatives": dict.fromkeys(sorted(enabled_operatives(self.options)), 1),
            "selected_skill_points": sorted(self.selected_skill_points),
            "stealth_cases": stealth_case_counts(self),
            **self.options.as_dict(*SLOT_DATA_OPTIONS, toggles_as_bools=True),
        }

    @staticmethod
    def interpret_slot_data(slot_data: dict[str, Any]) -> dict[str, Any]:
        return slot_data

    def generate_output(self, output_directory: str) -> None:
        patch = SACPatch(player=self.player, player_name=self.player_name)
        add_release_patch(patch)
        file_name = self.multiworld.get_out_file_name_base(self.player) + patch.patch_file_ending
        patch.write(os.path.join(output_directory, file_name))

    def get_filler_item_name(self) -> str:
        trap_chance = self.options.trap_chance.value
        if trap_chance and self.random.randint(1, 100) <= trap_chance:
            weights = self.options.trap_weight.value
            names = [name for name in TRAP_ITEM_TABLE if weights.get(name, 0) > 0]
            if names:
                return self.random.choices(names, weights=[weights[name] for name in names])[0]
        filler = list(ALL_FILLER)
        if self.options.progressive_weapons == ProgressiveWeaponsOptions.AUTOMATIC:
            filler.remove(SACFiller.WEAPON_XP)  # weapons only level up from Progressive Weapons
        return self.random.choice(filler)
