from __future__ import annotations

from typing import Any, ClassVar

from BaseClasses import Item, ItemClassification, Location, Tutorial

from Options import OptionError
from worlds.AutoWorld import WebWorld, World

from .constants import RACSMITEM
from .core.weapons import WEAPON_MOD_COUNTS
from .items import (
    ALL_ITEMS,
    ARMOUR_ITEM_TABLE,
    ARMOUR_PROGRESSIVE_ITEM_TABLE,
    ARMOUR_SETS,
    GADGET_ITEM_TABLE,
    INFOBOT_ITEM_TABLE,
    PROGRESSIVE_ARMOUR_NAME,
    PROGRESSIVE_MOD_NAME,
    PROGRESSIVE_WEAPON_NAME,
    TRAP_ITEM_TABLE,
    WEAPON_DISPLAY_TO_INTERNAL,
    WEAPON_ITEM_TABLE,
    WEAPON_MOD_ITEM_TABLE,
    WEAPON_PROGRESSIVE_ITEM_TABLE,
    WEAPON_PROGRESSIVE_STEPS,
)
from .locations import ALL_LOCATIONS
from .options import (
    AllCutscenes,
    AllMissions,
    ArmourSetChecks,
    ClankChallenges,
    EnableClankChallengeSkillPoints,
    EnableSkyboardChallengeSkillPoints,
    ProgressiveWeapons,
    RACSizeMatterOptions,
    SkillPoints,
    SkyboardChallenges,
    racsm_option_groups,
)
from .regions import create_regions
from .rules import set_rules
from .universal_tracker import setup_options_from_slot_data, tracker_world


class RACItem(Item):
    game: str = "Ratchet & Clank: Size Matters"


class RACLocation(Location):
    game: str = "Ratchet & Clank: Size Matters"


class RACWeb(WebWorld):
    theme = "ocean"
    tutorials = [
        Tutorial(
            "Multiworld Setup Guide",
            "A guide to setting up Ratchet & Clank: Size Matters for Archipelago.",
            "English",
            "setup_en.md",
            "setup/en",
            ["Archipelago Community"],
        )
    ]
    option_groups = racsm_option_groups


class RACSizeMatterWorld(World):
    """Ratchet & Clank: Size Matters is a 2007 PSP/PS2 action platformer following
    Ratchet and Clank as they unravel the mystery of the Technomites across ten planets.
    Weapons, gadgets, and armour pieces are shuffled across all locations.
    Defeat Otto Destruct on Quodrona to complete your goal."""

    game = "Ratchet & Clank: Size Matters"
    web = RACWeb()
    options_dataclass = RACSizeMatterOptions
    options: RACSizeMatterOptions

    item_name_to_id: dict[str, int] = {name: data.code for name, data in ALL_ITEMS.items()}
    location_name_to_id: dict[str, int] = {name: data.code for name, data in ALL_LOCATIONS.items()}

    using_ut: bool = False
    passthrough: dict[str, Any]
    ut_can_gen_without_yaml: bool = True
    disable_ut: bool = False
    tracker_world: ClassVar = tracker_world

    def create_item(self, name: str) -> RACItem:
        data = ALL_ITEMS[name]
        classification = data.classification
        # Armour pieces gate armour set check locations, so they must be tracked
        # as progression items for AP's reachability sweep to work correctly.
        if (classification == ItemClassification.useful
                and self.options.armour_set_checks
                and (name in ARMOUR_ITEM_TABLE or name in ARMOUR_PROGRESSIVE_ITEM_TABLE)):
            classification = ItemClassification.progression_skip_balancing
        return RACItem(name, classification, data.code, self.player)

    def create_event(self, name: str) -> RACItem:
        return RACItem(name, ItemClassification.progression, None, self.player)

    def generate_early(self) -> None:
        setup_options_from_slot_data(self)

    def create_regions(self) -> None:
        create_regions(self)

    def set_rules(self) -> None:
        set_rules(self)

    def create_items(self) -> None:
        pool: list[str] = []
        if self.options.progressive_weapons:
            ryno_progressive = self.options.skill_points.value >= SkillPoints.option_hard
            mootator_progressive = self.options.skill_points.value >= SkillPoints.option_easy
            for display, steps in WEAPON_PROGRESSIVE_STEPS.items():
                if display == RACSMITEM.RYNO and not ryno_progressive:
                    pool.append(display)
                elif display == RACSMITEM.MOOTATOR and not mootator_progressive:
                    pool.append(display)
                else:
                    pool += [PROGRESSIVE_WEAPON_NAME[display]] * steps
        else:
            pool += list(WEAPON_ITEM_TABLE)

        if self.options.progressive_mods:
            for display in PROGRESSIVE_MOD_NAME:
                internal = WEAPON_DISPLAY_TO_INTERNAL[display]
                pool += [PROGRESSIVE_MOD_NAME[display]] * WEAPON_MOD_COUNTS.get(internal, 0)
        else:
            pool += list(WEAPON_MOD_ITEM_TABLE)

        pool += list(GADGET_ITEM_TABLE)
        pool += list(INFOBOT_ITEM_TABLE)

        if self.options.progressive_armour:
            for display, _ in ARMOUR_SETS:
                pool += [PROGRESSIVE_ARMOUR_NAME[display]] * 4
        else:
            pool += list(ARMOUR_ITEM_TABLE)

        # Fill any remaining slots
        unfilled = len(self.multiworld.get_unfilled_locations(self.player))
        deficit = len(pool) - unfilled
        if deficit > 0:
            self.handle_not_enough_locations(deficit)
        pool += [self.get_filler_item_name() for _ in range(-deficit)]

        for name in pool:
            self.multiworld.itempool.append(self.create_item(name))

    def get_excluded_count(self) -> int:
        return len(self.options.exclude_locations.value)

    def handle_not_enough_locations(self, count: int) -> None:
        """Check the available location and item counts, raise OptionError to warn the player of too few locations."""
        excluded_count = self.get_excluded_count()
        option_list: list[str] = []
        if not self.options.all_missions:
            option_list.append(AllMissions.display_name)
        if not self.options.all_cutscenes:
            option_list.append(AllCutscenes.display_name)
        if self.options.skill_points.value < SkillPoints.option_hard:
            option_list.append(SkillPoints.display_name)
        if not self.options.enable_clank_challenge_skill_points:
            option_list.append(EnableClankChallengeSkillPoints.display_name)
        if not self.options.enable_skyboard_challenge_skill_points:
            option_list.append(EnableSkyboardChallengeSkillPoints.display_name)
        if not self.options.armour_set_checks:
            option_list.append(ArmourSetChecks.display_name)
        if self.options.clank_challenges.value < ClankChallenges.option_all:
            option_list.append(ClankChallenges.display_name)
        if self.options.skyboard_challenges.value < SkyboardChallenges.option_all:
            option_list.append(SkyboardChallenges.display_name)
        if excluded_count > 10:
            option_list.append("Exclude Locations")
        if not option_list:
            option_list = ["dunno"]  # ¯\_(ツ)_/¯

        message = f"Not enough location options enabled! {count} items have nowhere to be placed."
        if count >= 20:
            message += (f"\nThis large of a difference requires {ProgressiveWeapons.display_name} to be disabled, "
                        f"{ClankChallenges.display_name} set to All, or {SkyboardChallenges.display_name} set to All.")
        if count <= 10 and sum(self.options.start_inventory_from_pool.value.values()) <= 10:
            message += "Consider adding some items to your starting_items_from_pool or "
        else:
            message += "Consider "
        message += f"adjusting some of the following options: {option_list}"
        raise OptionError(message)

    def _precollect(self, name: str) -> None:
        """Precollect an item and replace its copy in the pool with Bolts filler."""
        self.multiworld.push_precollected(self.create_item(name))
        for item in self.multiworld.itempool:
            if item.player == self.player and item.name == name:
                self.multiworld.itempool.remove(item)
                self.multiworld.itempool.append(self.create_item("Bolts"))
                break

    def generate_basic(self) -> None:
        # Pokitaru and Ryllus are always the starting planets.
        self._precollect(RACSMITEM.POKITARU)
        self._precollect(RACSMITEM.RYLLUS)

        if self.options.starting_bolts.value > 0:
            self.multiworld.push_precollected(self.create_item("Bolts"))

        weapon_count = self.options.starting_weapons.value
        if weapon_count > 0:
            if self.options.progressive_weapons:
                pool = list(WEAPON_PROGRESSIVE_ITEM_TABLE.keys())
            else:
                pool = list(WEAPON_ITEM_TABLE.keys())
            for name in self.random.sample(pool, min(weapon_count, len(pool))):
                self._precollect(name)

        gadget_count = self.options.starting_gadgets.value
        if gadget_count > 0:
            pool = list(GADGET_ITEM_TABLE.keys())
            for name in self.random.sample(pool, min(gadget_count, len(pool))):
                self._precollect(name)

    def fill_slot_data(self) -> dict[str, Any]:
        return {
            "death_link": bool(self.options.death_link.value),
            "all_missions": bool(self.options.all_missions.value),
            "all_cutscenes": bool(self.options.all_cutscenes.value),
            "clank_challenges": self.options.clank_challenges.value,
            "skyboard_challenges": self.options.skyboard_challenges.value,

            "skill_points": self.options.skill_points.value,
            "enable_clank_challenge_skill_points": bool(self.options.enable_clank_challenge_skill_points.value),
            "enable_skyboard_challenge_skill_points": bool(self.options.enable_skyboard_challenge_skill_points.value),
            "armour_set_checks": bool(self.options.armour_set_checks.value),
            "starting_bolts": self.options.starting_bolts.value,
            "death_amnesty": self.options.death_amnesty.value,
            "progressive_weapons": self.options.progressive_weapons.value,
            "progressive_mods": self.options.progressive_mods.value,
            "progressive_armour": self.options.progressive_armour.value,
            "starting_weapons": self.options.starting_weapons.value,
            "starting_gadgets": self.options.starting_gadgets.value,
            "starting_skin": self.options.starting_skin.value,
        }

    @staticmethod
    def interpret_slot_data(slot_data: dict[str, Any]) -> dict[str, Any]:
        return slot_data

    def get_filler_item_name(self) -> str:
        trap_chance = self.options.trap_chance.value
        if trap_chance and self.random.randint(1, 100) <= trap_chance:
            return self.random.choice(list(TRAP_ITEM_TABLE))
        return "Bolts"
