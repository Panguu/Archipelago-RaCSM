from typing import Any

from BaseClasses import ItemClassification, Tutorial
from Options import OptionError
from worlds.AutoWorld import WebWorld, World

from .constants import (
    CASE_NAME_TO_INFOBOT,
    CASES_BY_OPERATIVE,
    CHARACTER_ITEM_NAME,
    GADGETS_FROM_WEAPON_TABLE,
    PLANET_NAMES,
    PROGRESSIVE_CHARACTER_ITEM_NAME,
    SACCases,
    SACOperatives,
)
from .constants.planets import ALL_CASES, PLANET_ACCESS_ITEM_NAME
from .constants.weapon_progression import (
    LEVELLED_INTERNALS,
    PROGRESSIVE_TO_INTERNAL,
    UNLOCK_TO_PROGRESSIVE,
    max_level,
)
from .constants.weapons import GADGET_DISPLAY_TO_INTERNAL, RATCHET_WEAPON_DISPLAY_TO_INTERNAL
from .entities import SACItem
from .items import (
    ALL_ITEMS,
    FILLER_ITEM_NAME,
    GADGET_ITEM_TABLE,
    PROGRESSIVE_PLANET_ITEM_NAME,
    RATCHET_PACK_ITEM_TABLE,
    TRAP_ITEM_TABLE,
    WEAPON_ITEM_TABLE,
)
from .locations import ALL_LOCATIONS
from .options import Infobots, SecretAgentClankOptions, sac_option_groups
from .regions import create_regions
from .rules import set_rules
from .rules.vendor_access import VENDOR_ONLY_ITEM_NAMES
from .universal_tracker import setup_options_from_slot_data

try:
    from worlds.dynamicpine import DynamicPineGame
    _DYNAMIC_PINE_SPEC = DynamicPineGame(
        game_ids="SCUS-97623",
        client_component="Secret Agent Clank Client",
        launcher_options="simple",
    )
except ImportError:
    _DYNAMIC_PINE_SPEC = None


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

    item_name_to_id: dict[str, int] = {name: data.code for name, data in ALL_ITEMS.items()}
    location_name_to_id: dict[str, int] = {name: data.code for name, data in ALL_LOCATIONS.items()}
    dynamic_pine = _DYNAMIC_PINE_SPEC

    # Universal Tracker integration (see universal_tracker.py) -- using_ut/
    # passthrough are read by UT itself once set; ut_can_gen_without_yaml
    # tells UT this world can regenerate purely from a finished multiworld's
    # slot_data, without needing the player's original YAML.
    using_ut: bool = False
    passthrough: dict[str, Any]
    ut_can_gen_without_yaml: bool = True

    def create_item(self, name: str) -> SACItem:
        data = ALL_ITEMS[name]
        return SACItem(name, data.classification, data.code, self.player)

    def create_event(self, name: str) -> SACItem:
        return SACItem(name, ItemClassification.progression, None, self.player)

    def generate_early(self) -> None:
        setup_options_from_slot_data(self)

    def create_regions(self) -> None:
        create_regions(self)

    @property
    def progressive_planets(self) -> list[str]:
        if self.using_ut:
            return list(self.passthrough.get("progressive_planets", PLANET_NAMES[1:]))
        regions = {region.name for region in self.multiworld.get_regions(self.player)}
        active = {case.planet for case in ALL_CASES if case.name in regions}
        return [planet for planet in PLANET_NAMES if planet in active]

    def set_rules(self) -> None:
        set_rules(self)

    def create_items(self) -> None:
        region_names = {r.name for r in self.multiworld.get_regions(self.player)}
        active_cases = [case for case in ALL_CASES if case.name in region_names]
        candidates = [case for case in active_cases
                      if self.options.operatives.value.get(case.operative, 0)]
        if not candidates:
            raise OptionError("Secret Agent Clank requires at least one enabled operative")
        if self.using_ut:
            name = self.passthrough.get("starting_case", SACCases.BOLTAIRE_MUSEUM)
            starting_case = next((case for case in active_cases if case.name == name), None)
            if starting_case is None:
                raise OptionError(f"Invalid starting case in slot data: {name}")
        else:
            starting_case = self.random.choice(candidates)
        self.starting_case = starting_case.name
        # A real AP starting item opens this exact case in every access mode.
        self.multiworld.push_precollected(
            self.create_item(CASE_NAME_TO_INFOBOT[starting_case.name])
        )

        # Infobots=cases has no planet/progressive fallback access tier --
        # a lone starting Case File can leave the player with only that
        # one case's own locations to find the rest from, so give a second
        # one too. Only meaningful with >1 enabled candidate; otherwise
        # there's nothing else to grant.
        second_starting_case = None
        if self.options.infobots == Infobots.option_cases:
            second_candidates = [case for case in candidates if case.name != starting_case.name]
            if second_candidates:
                if self.using_ut:
                    name = self.passthrough.get("second_starting_case")
                    second_starting_case = next(
                        (case for case in second_candidates if case.name == name), None,
                    )
                else:
                    second_starting_case = self.random.choice(second_candidates)
                if second_starting_case is not None:
                    self.multiworld.push_precollected(
                        self.create_item(CASE_NAME_TO_INFOBOT[second_starting_case.name])
                    )
        self.second_starting_case = second_starting_case.name if second_starting_case else None

        pool: list[str] = []
        pool += [mod.name for mod in self.weapon_mod_catalog]
        ratchet_enabled = SACOperatives.RATCHET in self.options.operatives.value
        clank_enabled = SACOperatives.CLANK in self.options.operatives.value
        if ratchet_enabled and self.options.progressive_wrench:
            pool += ["Progressive Wrench"] * 5

        # WEAPON_ITEM_TABLE mixes Ratchet's own weapons with the WEAPON_ORDER-
        # struct half of Clank's gadgets (see items/__init__.py's docstring) --
        # a disabled character's entries are excluded from the pool entirely,
        # same as their cases/locations already are (see regions.py's
        # disabled_operatives()), so their weapons/gadgets can never be
        # received or function in-game.
        for name in WEAPON_ITEM_TABLE:
            owned_by_clank = name in GADGETS_FROM_WEAPON_TABLE
            if owned_by_clank and not clank_enabled:
                continue
            if not owned_by_clank and not ratchet_enabled:
                continue
            if not self.has_vendor and name in VENDOR_ONLY_ITEM_NAMES:
                continue
            if self.options.progressive_weapons and name in UNLOCK_TO_PROGRESSIVE:
                progressive = UNLOCK_TO_PROGRESSIVE[name]
                pool += [progressive] * max_level(PROGRESSIVE_TO_INTERNAL[progressive], self.options.ng_plus.value)
            else:
                pool.append(name)
        if clank_enabled:
            pool += list(GADGET_ITEM_TABLE)

        # Planet access -- mutually exclusive tiers, see rules.py's
        # HasPlanet/HasCase docstring.
        if self.options.infobots == Infobots.option_progressive_planet:
            planets = self.progressive_planets
            starting_count = planets.index(starting_case.planet) + 1 if starting_case.planet in planets else 0
            for _ in range(starting_count):
                self.multiworld.push_precollected(self.create_item(PROGRESSIVE_PLANET_ITEM_NAME))
            pool += [PROGRESSIVE_PLANET_ITEM_NAME] * (len(planets) - starting_count)
        elif self.options.infobots == Infobots.option_cases:
            pool += [
                CASE_NAME_TO_INFOBOT[case.name] for case in active_cases
                if case.name != starting_case.name and case.name != self.second_starting_case
            ]
        elif self.options.infobots == Infobots.option_planets:
            active_planets = {case.planet for case in active_cases}
            pool += [item for planet, item in PLANET_ACCESS_ITEM_NAME.items() if planet in active_planets]

        # Character unlocks -- only for characters actually enabled (see
        # options.py's Operatives); a disabled operative has no cases
        # generated at all (see regions.py), so it'd be a wasted item.
        # ItemDict culls 0-valued entries in its own __init__, so a
        # disabled operative is simply absent from .value -- see
        # regions.py's disabled_operatives for the same check.
        if self.options.infobots == Infobots.option_character_unlocks:
            for character, item_name in CHARACTER_ITEM_NAME.items():
                if character in self.options.operatives.value:
                    pool.append(item_name)
            for character, item_name in PROGRESSIVE_CHARACTER_ITEM_NAME.items():
                if character in self.options.operatives.value:
                    pool += [item_name] * len(CASES_BY_OPERATIVE.get(character, ()))

        if ratchet_enabled:
            pool += list(RATCHET_PACK_ITEM_TABLE)

        # Choose once during generation so AP logic and every client agree.
        # Remove one pooled copy (also for progressive weapons) rather than
        # duplicating it; filler below replaces the freed location slot.
        starting_groups = (
            (SACOperatives.RATCHET, self.options.starting_weapons.value,
             [name for name, internal in RATCHET_WEAPON_DISPLAY_TO_INTERNAL.items()
              if internal in LEVELLED_INTERNALS or internal == "hypnowatch"]),
            (SACOperatives.CLANK, self.options.starting_gadgets.value,
             list(dict.fromkeys([*GADGET_DISPLAY_TO_INTERNAL, *GADGET_ITEM_TABLE]))),
        )
        for character, count, candidates in starting_groups:
            if character not in self.options.operatives.value:
                continue
            candidates = [UNLOCK_TO_PROGRESSIVE.get(name, name)
                          if self.options.progressive_weapons else name for name in candidates]
            candidates = [name for name in candidates if name in pool]
            if count > len(candidates):
                raise OptionError(f"Not enough eligible {character} starting items for {count} selections")
            for name in self.random.sample(candidates, count):
                pool.remove(name)
                self.multiworld.push_precollected(self.create_item(name))

        unfilled = len(self.multiworld.get_unfilled_locations(self.player))
        if len(pool) > unfilled:
            raise OptionError(
                f"Secret Agent Clank needs {len(pool)} item locations, but only {unfilled} are enabled. "
                f"Enable at least {len(pool) - unfilled} more optional locations (such as Missions: All, "
                "All Cutscenes, Skill Points, Keycards or Alien Codes)."
                + (" Progressive Weapons can also increase the required pool size."
                   if self.options.progressive_weapons and (ratchet_enabled or clank_enabled) else "")
            )
        filler_count = max(0, unfilled - len(pool))
        pool += [self.get_filler_item_name() for _ in range(filler_count)]

        for name in pool:
            self.multiworld.itempool.append(self.create_item(name))

    def fill_slot_data(self) -> dict[str, Any]:
        return {
            "progressive_planets": self.progressive_planets,
            "starting_case": self.starting_case,
            "second_starting_case": self.second_starting_case,
            "infobots": self.options.infobots.value,
            "weapon_mods": self.passthrough.get("weapon_mods", False) if self.using_ut else True,
            "weapon_mod_ids": [mod.mod_id for mod in self.weapon_mod_catalog],
            # Which operatives are enabled (see options.py's Operatives) --
            # determines which cases/locations exist and which weapons/
            # gadgets are pooled at all (see create_items() above). Required
            # for Universal Tracker's regenerated world to match the real
            # one (see universal_tracker.py).
            "operatives": dict(self.options.operatives.value),
            "death_link": bool(self.options.death_link.value),
            "death_amnesty": self.options.death_amnesty.value,
            # Missions.option_level_completion (0) or .option_all (1) --
            # tells the client which per-case location set it should be
            # sending completions for (see client/context.py).
            "all_missions": self.options.all_missions.value,
            "all_cutscenes": bool(self.options.all_cutscenes.value),
            "skill_points": bool(self.options.skill_points.value),
            "all_keycards": bool(self.options.all_keycards.value),
            "all_alien_codes": bool(self.options.all_alien_codes.value),
            "send_scouted_locations": bool(self.options.send_scouted_locations.value),
            "goal": self.options.goal.value,
            "progressive_wrench": bool(self.options.progressive_wrench.value),
            "progressive_weapons": bool(self.options.progressive_weapons.value),
            "weapon_xp_multiplier": self.options.weapon_xp_multiplier.value,
            "health_xp_multiplier": self.options.health_xp_multiplier.value,
            "bolt_multiplier": self.options.bolt_multiplier.value,
            "ng_plus": self.options.ng_plus.value,
            "starting_weapons": self.options.starting_weapons.value,
            "starting_gadgets": self.options.starting_gadgets.value,
            "starting_bolts": self.options.starting_bolts.value,
            "trap_chance": self.options.trap_chance.value,
            "trap_weight": dict(self.options.trap_weight.value),
            "trap_duration": dict(self.options.trap_duration.value),
        }

    def get_filler_item_name(self) -> str:
        trap_chance = self.options.trap_chance.value
        if trap_chance and self.random.randint(1, 100) <= trap_chance:
            weights = self.options.trap_weight.value
            names = [name for name in TRAP_ITEM_TABLE if weights.get(name, 0) > 0]
            if names:
                return self.random.choices(names, weights=[weights[name] for name in names])[0]
        return FILLER_ITEM_NAME
