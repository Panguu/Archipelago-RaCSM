from typing import Any, ClassVar

from BaseClasses import ItemClassification, Tutorial

from Options import OptionError
from worlds.AutoWorld import WebWorld, World

from .constants import Rac5Infobots
from .constants.options import Rac5Options
from .core.starting_planet import PLANET_TO_ID, PLANET_TO_INFOBOT, choose_starting_planets
from .core.weapons import WEAPON_MOD_COUNTS
from .data.models import RACItem as RACItem, RACLocation as RACLocation
from .data.weapons import WEAPON_DATA
from .items import (
    ALL_ITEMS,
    CLANK_PACK_NAME,
    ARMOUR_DISPLAY_TO_INTERNAL,
    ARMOUR_ITEM_TABLE,
    ARMOUR_PROGRESSIVE_ITEM_TABLE,
    ARMOUR_PROGRESSIVE_UNIFIED_ITEM_TABLE,
    ARMOUR_SETS,
    GADGET_ITEM_TABLE,
    GLITCHES_ITEM_NAME,
    INFOBOT_ITEM_TABLE,
    NG_PLUS_ARMOUR_SETS,
    NG_PLUS_WEAPON_MODS,
    NG_PLUS_WEAPONS,
    PROGRESSIVE_ARMOUR_NAME,
    PROGRESSIVE_ARMOUR_UNIFIED_NAME,
    PROGRESSIVE_CHALLENGE_MODE_NAME,
    PROGRESSIVE_MOD_NAME,
    PROGRESSIVE_WEAPON_NAME,
    TRAP_ITEM_TABLE,
    WEAPON_DISPLAY_TO_INTERNAL,
    WEAPON_ITEM_TABLE,
    WEAPON_MOD_ITEM_TABLE,
    WEAPON_MOD_NAME_TO_SLOT,
    WEAPON_NG_PLUS_MOD_COUNTS,
    WEAPON_PROGRESSIVE_STEPS,
    enabled_weapon_names,
)
from .locations import ALL_LOCATIONS
from .options import (
    AllCutscenes,
    AllMissions,
    ArmourSetChecks,
    ClankChallenges,
    EnabledWeapons,
    EnableClankChallengeSkillPoints,
    EnableSkyboardChallengeSkillPoints,
    ProgressiveArmour,
    ProgressiveWeapons,
    RACSizeMatterOptions,
    RandomStartingPlanet,
    ShrinkRayOptions,
    SkillPoints,
    SkyboardChallenges,
    WeaponLevelChecks,
    racsm_option_groups,
)
from .regions import create_regions
from .rules import set_rules
from .settings import RACSizeMatterSettings
from .universal_tracker import setup_options_from_slot_data, tracker_world

try:
    from worlds.dynamicpine import DynamicPineGame

    _DYNAMIC_PINE_SPEC = DynamicPineGame(
        game_ids="SCUS-97615",
        client_component="Ratchet & Clank: Size Matters Client",
        launcher_options="simple",
    )
except ImportError:
    _DYNAMIC_PINE_SPEC = None


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
    settings: ClassVar[RACSizeMatterSettings]

    item_name_to_id: dict[str, int] = {name: data.code for name, data in ALL_ITEMS.items()}
    location_name_to_id: dict[str, int] = {name: data.code for name, data in ALL_LOCATIONS.items()}

    using_ut: bool = False
    passthrough: dict[str, Any]
    ut_can_gen_without_yaml: bool = True
    disable_ut: bool = False
    glitches_item_name: ClassVar[str] = GLITCHES_ITEM_NAME
    tracker_world: ClassVar = tracker_world
    dynamic_pine = _DYNAMIC_PINE_SPEC

    starting_planet_id: int | None = None

    preplaced_items: list[str]

    def create_item(self, name: str) -> RACItem:
        data = ALL_ITEMS[name]
        classification = data.classification
        if (
            classification == ItemClassification.useful
            and self.options.armour_set_checks
            and (
                name in ARMOUR_ITEM_TABLE
                or name in ARMOUR_PROGRESSIVE_ITEM_TABLE
                or name in ARMOUR_PROGRESSIVE_UNIFIED_ITEM_TABLE
            )
        ):
            classification = ItemClassification.progression_skip_balancing
        if (
            classification == ItemClassification.useful
            and self.options.weapon_level_checks
            and name in WEAPON_ITEM_TABLE
        ):
            classification = ItemClassification.progression_skip_balancing
        return RACItem(name, classification, data.code, self.player)

    def create_event(self, name: str) -> RACItem:
        return RACItem(name, ItemClassification.progression, None, self.player)

    def generate_early(self) -> None:
        setup_options_from_slot_data(self)
        self._validate_weapon_options()

    def _validate_weapon_options(self) -> None:
        """Require a projectile weapon that will actually survive item-pool filtering."""
        enabled_weapons = enabled_weapon_names(dict(self.options.enabled_weapons.value))
        if not self.options.ng_plus_items:
            enabled_weapons -= NG_PLUS_WEAPONS
        player_name = self.multiworld.get_player_name(self.player)
        if not any(WEAPON_DATA[WEAPON_DISPLAY_TO_INTERNAL[name]].is_projectile for name in enabled_weapons):
            raise OptionError(
                f"{player_name}'s RAC Size Matters: {EnabledWeapons.display_name} must include at least "
                "one projectile weapon available with NG+ Items applied - many locations "
                "are only reachable with one."
            )

    def create_regions(self) -> None:
        create_regions(self)

    def set_rules(self) -> None:
        set_rules(self)

    def _choose_preplaced_items(self) -> list[str]:
        """Items precollected ahead of the pool: starting-planet infobot(s) plus
        any Starting Weapons/Starting Gadgets rolls."""
        preplaced: list[str] = []

        random_start = self.options.random_starting_planet.value
        if random_start != RandomStartingPlanet.option_off:
            weighted = random_start == RandomStartingPlanet.option_weighted
            planets = choose_starting_planets(self, weighted=weighted)
            self.starting_planet_id = PLANET_TO_ID[planets[0]]
            preplaced += [PLANET_TO_INFOBOT[planet] for planet in planets]
        else:
            preplaced += [Rac5Infobots.POKITARU]

        ng_plus = bool(self.options.ng_plus_items)
        enabled_weapons = enabled_weapon_names(dict(self.options.enabled_weapons.value))
        weapon_count = self.options.starting_weapons.value
        if weapon_count > 0:
            if self.options.progressive_weapons:
                weapon_pool = [
                    PROGRESSIVE_WEAPON_NAME[display]
                    for display in WEAPON_PROGRESSIVE_STEPS
                    if (ng_plus or display not in NG_PLUS_WEAPONS) and display in enabled_weapons
                ]
            else:
                weapon_pool = [
                    name
                    for name in WEAPON_ITEM_TABLE
                    if (ng_plus or name not in NG_PLUS_WEAPONS) and name in enabled_weapons
                ]
            preplaced += self.random.sample(weapon_pool, min(weapon_count, len(weapon_pool)))

        gadget_count = self.options.starting_gadgets.value
        if gadget_count > 0:
            gadget_pool = list(GADGET_ITEM_TABLE.keys())
            preplaced += self.random.sample(gadget_pool, min(gadget_count, len(gadget_pool)))

        return preplaced

    def create_items(self) -> None:
        self.preplaced_items = self._choose_preplaced_items()

        pool: list[str] = []
        ng_plus = bool(self.options.ng_plus_items)
        enabled_weapons = enabled_weapon_names(dict(self.options.enabled_weapons.value))
        if self.options.progressive_weapons:
            for display, steps in WEAPON_PROGRESSIVE_STEPS.items():
                if not ng_plus and display in NG_PLUS_WEAPONS:
                    continue
                if display not in enabled_weapons:
                    continue
                pool += [PROGRESSIVE_WEAPON_NAME[display]] * steps
        else:
            pool += [
                name
                for name in WEAPON_ITEM_TABLE
                if (ng_plus or name not in NG_PLUS_WEAPONS) and name in enabled_weapons
            ]

        if self.options.progressive_mods:
            for display in PROGRESSIVE_MOD_NAME:
                if display not in enabled_weapons:
                    continue
                internal = WEAPON_DISPLAY_TO_INTERNAL[display]
                steps = WEAPON_MOD_COUNTS.get(internal, 0)
                if not ng_plus:
                    steps -= WEAPON_NG_PLUS_MOD_COUNTS.get(internal, 0)
                pool += [PROGRESSIVE_MOD_NAME[display]] * steps
        else:
            pool += [
                name
                for name in WEAPON_MOD_ITEM_TABLE
                if (ng_plus or name not in NG_PLUS_WEAPON_MODS) and WEAPON_MOD_NAME_TO_SLOT[name][0] in enabled_weapons
            ]

        pool += list(GADGET_ITEM_TABLE)
        if self.options.clank_pack:
            pool.append(CLANK_PACK_NAME)
        pool += list(INFOBOT_ITEM_TABLE)

        if self.options.progressive_challenge_mode:
            pool += [PROGRESSIVE_CHALLENGE_MODE_NAME] * self.options.challenge_mode.value

        # Hyperborean/Chameleon are also gated behind Challenge Mode tiers 1/2,
        # independent of the NG+ Items toggle above; both gates must agree.
        challenge_mode = self.options.challenge_mode.value

        def _armour_set_enabled(internal: str) -> bool:
            if not ng_plus and internal in NG_PLUS_ARMOUR_SETS:
                return False
            if internal == "hyperborean" and challenge_mode < 1:
                return False
            if internal == "chameleon" and challenge_mode < 2:
                return False
            return True

        progressive_armour_mode = self.options.progressive_armour.value
        if progressive_armour_mode == ProgressiveArmour.option_per_set:
            for display, internal in ARMOUR_SETS:
                if not _armour_set_enabled(internal):
                    continue
                pool += [PROGRESSIVE_ARMOUR_NAME[display]] * 4
        elif progressive_armour_mode == ProgressiveArmour.option_unified:
            steps = sum(4 for _display, internal in ARMOUR_SETS if _armour_set_enabled(internal))
            pool += [PROGRESSIVE_ARMOUR_UNIFIED_NAME] * steps
        else:
            pool += [name for name in ARMOUR_ITEM_TABLE if _armour_set_enabled(ARMOUR_DISPLAY_TO_INTERNAL[name][0])]

        for name in self.preplaced_items:
            pool.remove(name)
            self.multiworld.push_precollected(self.create_item(name))

        if self.options.starting_bolts.value > 0:
            self.multiworld.push_precollected(self.create_item("Bolts"))

        unfilled = len(self.multiworld.get_unfilled_locations(self.player))
        deficit = len(pool) - unfilled
        filler_count = -deficit

        excluded_count = self.get_excluded_count()
        if excluded_count > filler_count and self.multiworld.players == 1:
            self.handle_not_enough_locations(excluded_count - filler_count)

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
        if self.options.shrink_ray_options.value != ShrinkRayOptions.option_locations:
            option_list.append(ShrinkRayOptions.display_name)
        if excluded_count > 10:
            option_list.append("Exclude Locations")
        if not option_list:
            option_list = ["dunno"]

        player_name = self.multiworld.get_player_name(self.player)
        message = (
            f"{player_name}'s RAC Size Matters: Not enough location options enabled! "
            f"{count} items have nowhere to be placed."
        )
        if count >= 20:
            message += (
                f"\nThis large of a difference requires {ProgressiveWeapons.display_name} to be disabled, "
                f"{ClankChallenges.display_name} set to All, or {SkyboardChallenges.display_name} set to All."
            )
        if count <= 10 and sum(self.options.start_inventory_from_pool.value.values()) <= 10:
            message += "Consider adding some items to your starting_items_from_pool or "
        else:
            message += "Consider "
        message += f"adjusting some of the following options: {option_list}"
        raise OptionError(message)

    def fill_slot_data(self) -> dict[str, Any]:
        return {
            "split_infobots": True,
            Rac5Options.DEATH_LINK: bool(self.options.death_link.value),
            Rac5Options.AMMO_LINK: bool(self.options.ammo_link.value),
            Rac5Options.BOLT_LINK: bool(self.options.bolt_link.value),
            Rac5Options.GHOST_LINK: bool(self.options.ghost_link.value) and bool(self.settings.ghost_link),
            Rac5Options.GHOST_LINK_UPDATE_INTERVAL: int(self.options.ghost_link_update_interval.value),
            Rac5Options.ALL_MISSIONS: bool(self.options.all_missions.value),
            Rac5Options.ALL_CUTSCENES: bool(self.options.all_cutscenes.value),
            Rac5Options.GIANT_CLANK: bool(self.options.giant_clank.value),
            Rac5Options.CLANK_CHALLENGES: self.options.clank_challenges.value,
            Rac5Options.CLANK_CHALLENGE_GROUPS: dict(self.options.clank_challenge_groups.value),
            Rac5Options.SKYBOARD_CHALLENGES: self.options.skyboard_challenges.value,
            Rac5Options.SHRINK_RAY_OPTIONS: self.options.shrink_ray_options.value,
            Rac5Options.SKILL_POINTS: self.options.skill_points.value,
            Rac5Options.ENABLE_CLANK_CHALLENGE_SKILL_POINTS: bool(
                self.options.enable_clank_challenge_skill_points.value
            ),
            Rac5Options.ENABLE_SKYBOARD_CHALLENGE_SKILL_POINTS: bool(
                self.options.enable_skyboard_challenge_skill_points.value
            ),
            Rac5Options.ARMOUR_SET_CHECKS: bool(self.options.armour_set_checks.value),
            Rac5Options.NG_PLUS_ITEMS: bool(self.options.ng_plus_items.value),
            Rac5Options.CHALLENGE_MODE: self.options.challenge_mode.value,
            Rac5Options.PROGRESSIVE_CHALLENGE_MODE: bool(self.options.progressive_challenge_mode.value),
            Rac5Options.CLANK_PACK: bool(self.options.clank_pack.value),
            Rac5Options.STARTING_BOLTS: self.options.starting_bolts.value,
            Rac5Options.DEATH_AMNESTY: self.options.death_amnesty.value,
            Rac5Options.PROGRESSIVE_WEAPONS: self.options.progressive_weapons.value,
            Rac5Options.PROGRESSIVE_MODS: self.options.progressive_mods.value,
            Rac5Options.PROGRESSIVE_ARMOUR: self.options.progressive_armour.value,
            Rac5Options.ENABLED_WEAPONS: dict(self.options.enabled_weapons.value),
            Rac5Options.STARTING_WEAPONS: self.options.starting_weapons.value,
            Rac5Options.STARTING_GADGETS: self.options.starting_gadgets.value,
            Rac5Options.RANDOM_STARTING_PLANET: self.options.random_starting_planet.value,
            "starting_planet_id": self.starting_planet_id,
            Rac5Options.STARTING_SKIN: self.options.starting_skin.value,
            Rac5Options.WEAPON_EXPERIENCE_MULTIPLIER: self.options.weapon_experience_multiplier.value,
            Rac5Options.BOLT_MULTIPLIER: self.options.bolt_multiplier.value,
            Rac5Options.NANOTECH_EXPERIENCE_MULTIPLIER: self.options.nanotech_experience_multiplier.value,
            Rac5Options.NANOTECH_LEVEL_INTERVAL: self.options.nanotech_level_interval.value,
            Rac5Options.NANOTECH_LEVEL_MAX: self.options.nanotech_level_max.value,
            Rac5Options.WEAPON_LEVEL_CHECKS: self.options.weapon_level_checks.value,
            Rac5Options.TRAP_DURATION: dict(self.options.trap_duration.value),
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
