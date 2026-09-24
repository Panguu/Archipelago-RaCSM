from dataclasses import dataclass

from Options import (
    Choice,
    DeathLink,
    DefaultOnToggle,
    ItemDict,
    OptionCounter,
    OptionGroup,
    PerGameCommonOptions,
    Range,
    StartInventoryPool,
    Toggle,
)

from .constants.cheats import TRAP_DURATIONS
from .constants.operatives import ALL_OPERATIVES


class Missions(Choice):
    """Controls the granularity of story-mission location checks."""
    display_name = "Missions"
    option_level_completion = 0
    option_all = 1
    default = 0


class AllCutscenes(Toggle):
    """Include cutscene/flag-triggered events as location checks."""
    display_name = "All Cutscenes"


class SkillPoints(Toggle):
    """Include skill point challenges as location checks."""
    display_name = "Skill Points"


class AllKeycards(Toggle):
    """Include the 3 keycard pickups as optional AP location checks."""
    display_name = "All Keycards"


class AllAlienCodes(Toggle):
    """Include the 27 Alien Codes as optional AP location checks."""
    display_name = "All Alien Codes"


class SendScoutedLocations(DefaultOnToggle):
    """Send vendor-scouted locations out as real AP hints (visible to trackers/other
    players), not just shown locally in the vendor menu. Off keeps scouting local-only,
    same as before this option existed."""
    display_name = "Send Scouted Locations"


class Infobots(Choice):
    """Choose how access is unlocked."""
    display_name = "Infobots"
    option_planets = 0
    option_cases = 1
    option_progressive_planet = 2
    option_character_unlocks = 3
    default = 1


class Operatives(OptionCounter):
    """Enabled operatives (Ratchet, Clank, Qwark, Gadgetbots, and Special Missions)."""
    display_name = "Operatives"
    min = 0
    max = 1
    valid_keys = ALL_OPERATIVES
    default = dict.fromkeys(ALL_OPERATIVES, 1)

    def __init__(self, value: dict[str, int]) -> None:
        # Cull 0s so "set to 0" and "removed from the list" both collapse
        # to "key absent from .value" -- matches ItemDict's convention,
        # which regions.py's disabled_operatives relies on.
        value = {name: amount for name, amount in value.items() if amount != 0}
        super().__init__(value)


class Goal(Choice):
    """Victory condition."""
    display_name = "Goal"
    option_defeat_klunk    = 0
    option_qwark_opera     = 1
    option_any             = 2
    option_chalice_of_power = 3
    option_alien_codes      = 4
    option_all_gadgetbots   = 5
    option_ratchet_prison_escape = 6
    default = 0


class NgPlus(Range):
    """New Game Plus level: 0 is the base game, 1 is NG+, and 2 is NG++."""
    display_name = "NG+"
    range_start = 0
    range_end = 2
    default = 0


class ProgressiveWeapons(Toggle):
    """AP weapon copies grant V1, then one level each."""
    display_name = "Progressive Weapons"


class ProgressiveWrench(Toggle):
    """Adds 5 Progressive Wrench items to the pool (Ratchet only) -- each copy upgrades the wrench a level."""
    display_name = "Progressive Wrench"


class WeaponXPMultiplier(Range):
    """Combat weapon XP multiplier. Inactive with Progressive Weapons on."""
    display_name = "Weapon XP Multiplier"
    range_start = 1
    range_end = 10
    default = 1


class HealthXPMultiplier(Range):
    """Multiplier for native health experience gains."""
    display_name = "Health XP Multiplier"
    range_start = 1
    range_end = 10
    default = 1


class BoltMultiplier(Range):
    """Multiplier for earned bolts. Purchases and AP percentage rewards are unchanged."""
    display_name = "Bolt Multiplier"
    range_start = 1
    range_end = 10
    default = 1


class DeathAmnesty(Range):
    """Number of deaths allowed before items are stripped from the player's inventory on death."""
    display_name = "Death Amnesty"
    range_start = 0
    range_end = 5
    default = 0


class StartingWeapons(Range):
    """Number of random Ratchet weapons the player begins the game with."""
    display_name = "Starting Weapons"
    range_start = 0
    range_end = 4
    default = 1


class StartingGadgets(Range):
    """Number of random Clank spy gadgets the player begins the game with."""
    display_name = "Starting Gadgets"
    range_start = 0
    range_end = 3
    default = 1


class StartingBolts(Range):
    """Number of bolts the player begins the game with."""
    display_name = "Starting Bolts"
    range_start = 0
    range_end = 100_000
    default = 5_000


class TrapChance(Range):
    """Percent chance for each filler item to be replaced with a trap instead of Bolts."""
    display_name = "Trap Chance"
    range_start = 0
    range_end = 100
    default = 0


class TrapWeight(ItemDict):
    """Sets the relative weights of trap types in the filler pool."""
    display_name = "Trap Weight"
    min = 0
    max = 100
    valid_keys = TRAP_DURATIONS.keys()
    default = dict.fromkeys(TRAP_DURATIONS.keys(), 1)


class TrapDuration(OptionCounter):
    """How many seconds each trap type stays active once triggered."""
    display_name = "Trap Duration"
    min = 1
    max = 300
    valid_keys = TRAP_DURATIONS.keys()
    default = dict(TRAP_DURATIONS)


@dataclass
class SecretAgentClankOptions(PerGameCommonOptions):
    start_inventory_from_pool: StartInventoryPool
    death_link: DeathLink
    death_amnesty: DeathAmnesty
    all_missions: Missions
    all_cutscenes: AllCutscenes
    skill_points: SkillPoints
    all_keycards: AllKeycards
    all_alien_codes: AllAlienCodes
    send_scouted_locations: SendScoutedLocations
    goal: Goal
    infobots: Infobots
    operatives: Operatives
    ng_plus: NgPlus
    progressive_weapons: ProgressiveWeapons
    progressive_wrench: ProgressiveWrench
    weapon_xp_multiplier: WeaponXPMultiplier
    health_xp_multiplier: HealthXPMultiplier
    bolt_multiplier: BoltMultiplier
    starting_weapons: StartingWeapons
    starting_gadgets: StartingGadgets
    starting_bolts: StartingBolts
    trap_chance: TrapChance
    trap_weight: TrapWeight
    trap_duration: TrapDuration


sac_option_groups = [
    OptionGroup("SAC Item Options", [
        ProgressiveWeapons,
        ProgressiveWrench,
        WeaponXPMultiplier,
        HealthXPMultiplier,
        BoltMultiplier,
        StartingWeapons,
        StartingGadgets,
        StartingBolts,
        TrapChance,
        TrapWeight,
        TrapDuration,
    ]),
    OptionGroup("SAC Location Options", [
        Missions,
        AllCutscenes,
        SkillPoints,
        AllKeycards,
        AllAlienCodes,
        SendScoutedLocations,
        Goal,
        NgPlus,
    ]),
    OptionGroup("SAC Character Options", [
        Infobots,
        Operatives,
    ]),
]
