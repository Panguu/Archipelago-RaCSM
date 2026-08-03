from __future__ import annotations

from typing import Any, ClassVar

from BaseClasses import Item, ItemClassification, Location, Tutorial

from Options import OptionError
from worlds.AutoWorld import WebWorld, World

from .constants import Rac5Infobots
from .core.weapons import WEAPON_MOD_COUNTS
from .items import (
    ALL_ITEMS,
    ARMOUR_DISPLAY_TO_INTERNAL,
    ARMOUR_ITEM_TABLE,
    ARMOUR_PROGRESSIVE_ITEM_TABLE,
    ARMOUR_SETS,
    GADGET_ITEM_TABLE,
    INFOBOT_ITEM_TABLE,
    NG_PLUS_ARMOUR_SETS,
    NG_PLUS_WEAPONS,
    PROGRESSIVE_ARMOUR_NAME,
    PROGRESSIVE_MOD_NAME,
    PROGRESSIVE_WEAPON_NAME,
    TRAP_ITEM_TABLE,
    WEAPON_DISPLAY_TO_INTERNAL,
    WEAPON_ITEM_TABLE,
    WEAPON_MOD_ITEM_TABLE,
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
    WeaponLevelChecks,
    racsm_option_groups,
)
from .regions import create_regions
from .rules import set_rules
from .universal_tracker import setup_options_from_slot_data, tracker_world


class RACItem(Item):
    game: str = "Ratchet & Clank: Size Matters PSP"


class RACLocation(Location):
    game: str = "Ratchet & Clank: Size Matters PSP"


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

    game = "Ratchet & Clank: Size Matters PSP"
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
        # Static Barrier/Suck Cannon are the only "useful" weapons, but Weapon
        # Level Checks gates their own level locations behind owning them
        # (HasWeapon rule), so they must be progression too when that option
        # is on — otherwise the fill algorithm can place them somewhere that
        # never becomes reachable, same issue armour pieces had above.
        if (classification == ItemClassification.useful
                and self.options.weapon_level_checks
                and name in WEAPON_ITEM_TABLE):
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
        ng_plus = bool(self.options.ng_plus_items)
        if self.options.progressive_weapons:
            for display, steps in WEAPON_PROGRESSIVE_STEPS.items():
                if not ng_plus and display in NG_PLUS_WEAPONS:
                    continue
                pool += [PROGRESSIVE_WEAPON_NAME[display]] * steps
        else:
            pool += [name for name in WEAPON_ITEM_TABLE if ng_plus or name not in NG_PLUS_WEAPONS]

        if self.options.progressive_mods:
            for display in PROGRESSIVE_MOD_NAME:
                internal = WEAPON_DISPLAY_TO_INTERNAL[display]
                pool += [PROGRESSIVE_MOD_NAME[display]] * WEAPON_MOD_COUNTS.get(internal, 0)
        else:
            pool += list(WEAPON_MOD_ITEM_TABLE)

        pool += list(GADGET_ITEM_TABLE)
        pool += list(INFOBOT_ITEM_TABLE)

        if self.options.progressive_armour:
            for display, internal in ARMOUR_SETS:
                if not ng_plus and internal in NG_PLUS_ARMOUR_SETS:
                    continue
                pool += [PROGRESSIVE_ARMOUR_NAME[display]] * 4
        else:
            pool += [
                name for name in ARMOUR_ITEM_TABLE
                if ng_plus or ARMOUR_DISPLAY_TO_INTERNAL[name][0] not in NG_PLUS_ARMOUR_SETS
            ]

        # Fill any remaining slots
        unfilled = len(self.multiworld.get_unfilled_locations(self.player))
        deficit = len(pool) - unfilled
        filler_count = -deficit

        # exclude_locations locations must end up filler-only (never
        # progression/useful) — if there are more of them than the filler
        # we're about to generate, the excluded locations alone can't all be
        # covered by real filler once fill runs. Solo-only for the same
        # reason as the check below: a multiworld's other players still
        # supply enough of their own filler overall, this player's exclusions
        # don't shrink the global filler supply. Matches rac3's own
        # players == 1 gate on the equivalent check (world.py's create_items).
        excluded_count = self.get_excluded_count()
        if excluded_count > filler_count and self.multiworld.players == 1:
            self.handle_not_enough_locations(excluded_count - filler_count)

        # Unlike the excluded-locations check above, rac3 does NOT gate this
        # one on players == 1 — a deficit here means this world generated
        # more progression/useful items than it has locations of its own,
        # which rac3 always treats as fatal regardless of multiworld size
        # (see the unconditional `else: self.handle_not_enough_locations(...)`
        # branch in rac3's world.py create_items). Mirrored here as-is.
        if deficit > 0:
            self.handle_not_enough_locations(deficit)
        pool += [self.get_filler_item_name() for _ in range(max(0, filler_count))]

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
        if self.options.weapon_level_checks.value < WeaponLevelChecks.option_all:
            option_list.append(WeaponLevelChecks.display_name)
        if self.options.clank_challenges.value < ClankChallenges.option_all:
            option_list.append(ClankChallenges.display_name)
        if self.options.skyboard_challenges.value < SkyboardChallenges.option_all:
            option_list.append(SkyboardChallenges.display_name)
        if excluded_count > 10:
            option_list.append("Exclude Locations")
        if not option_list:
            option_list = ["dunno"]  # Â¯\_(ãƒ„)_/Â¯

        player_name = self.multiworld.get_player_name(self.player)
        message = (
            f"{player_name}'s RAC Size Matters: Not enough location options enabled! "
            f"{count} items have nowhere to be placed."
        )
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
        self._precollect(Rac5Infobots.POKITARU)
        self._precollect(Rac5Infobots.RYLLUS)

        if self.options.starting_bolts.value > 0:
            self.multiworld.push_precollected(self.create_item("Bolts"))

        ng_plus = bool(self.options.ng_plus_items)
        weapon_count = self.options.starting_weapons.value
        if weapon_count > 0:
            # Sampled straight from the static item tables, not the actual
            # itempool — so an NG+-locked weapon (e.g. RYNO) has to be
            # excluded here too, or a fresh (non-NG+) seed could still roll
            # it as a starting weapon despite never placing it in the pool.
            if self.options.progressive_weapons:
                pool = [
                    PROGRESSIVE_WEAPON_NAME[display] for display in WEAPON_PROGRESSIVE_STEPS
                    if ng_plus or display not in NG_PLUS_WEAPONS
                ]
            else:
                pool = [name for name in WEAPON_ITEM_TABLE if ng_plus or name not in NG_PLUS_WEAPONS]
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
            "ng_plus_items": bool(self.options.ng_plus_items.value),
            "starting_bolts": self.options.starting_bolts.value,
            "death_amnesty": self.options.death_amnesty.value,
            "progressive_weapons": self.options.progressive_weapons.value,
            "progressive_mods": self.options.progressive_mods.value,
            "progressive_armour": self.options.progressive_armour.value,
            "starting_weapons": self.options.starting_weapons.value,
            "starting_gadgets": self.options.starting_gadgets.value,
            "starting_skin": self.options.starting_skin.value,
            "weapon_experience_multiplier": self.options.weapon_experience_multiplier.value,
            "bolt_multiplier": self.options.bolt_multiplier.value,
            "weapon_level_checks": self.options.weapon_level_checks.value,
            "trap_duration": dict(self.options.trap_duration.value),
        }

    @staticmethod
    def interpret_slot_data(slot_data: dict[str, Any]) -> dict[str, Any]:
        return slot_data

    def get_filler_item_name(self) -> str:
        trap_chance = self.options.trap_chance.value
        if trap_chance and self.random.randint(1, 100) <= trap_chance:
            weights = self.options.trap_weight.value
            names = [name for name in TRAP_ITEM_TABLE if weights.get(name, 0) > 0]
            if names:
                return self.random.choices(names, weights=[weights[name] for name in names])[0]
        return "Bolts"
