from dataclasses import dataclass

from Options import (
    Choice,
    DeathLink,
    DefaultOnToggle,
    ItemDict,
    OptionCounter,
    OptionGroup,
    OptionSet,
    PerGameCommonOptions,
    Range,
    StartInventoryPool,
    Toggle,
)

from .constants.cheats import TRAP_DURATIONS
from .constants.operatives import ALL_OPERATIVES
from .constants.stealth import STEALTH_MAX_PER_CASE


class ClankSkin(Choice):
    """Clank's cosmetic skin. In-game keeps your selection in the game's Skins menu.
    All skins are unlocked on AP initialization. A chosen skin is the initial default;
    later in-game selections are preserved.
    """
    display_name = "Clank Skin"
    option_in_game = 0
    option_suit = 11
    option_cowboy = 12
    option_klunk = 13
    option_70s_clank = 14
    option_cop_clank = 15
    option_blender = 16
    option_zoni = 17
    default = 0


class RatchetSkin(Choice):
    """Ratchet's cosmetic skin. In-game keeps your selection in the game's Skins menu.
    Supported skins are unlocked on AP initialization. Robo-Ratchet is unavailable
    in the PS2 release. A chosen skin is the initial default;
    later in-game selections are preserved.
    """
    display_name = "Ratchet Skin"
    option_in_game = 0
    option_prison_scrubs = 1
    option_towel = 2
    option_super_incognito = 3
    option_tropical_vacation = 4
    option_plundering_pirate_captain = 5
    option_ratchetzilla = 6
    option_kung_fu_ratchet = 8
    option_zombie_ratchet = 9
    option_dan = 10
    default = 0


class QwarkSkin(Choice):
    """Qwark's cosmetic skin, including its matching giant form.
    In-game keeps your selection in the game's Skins menu. All skins are unlocked
    on AP initialization. A chosen skin is the initial default; later in-game
    selections are preserved.
    """
    display_name = "Qwark Skin"
    option_in_game = 0
    option_regular = 18
    option_cowboy = 19
    option_maid_qwark = 20
    option_lucha_libre_qwark = 21
    default = 0


class Missions(Choice):
    """Controls the granularity of story-mission location checks."""
    display_name = "Missions"
    option_level_completion = 0
    option_all = 1
    default = 0


class AllCutscenes(Toggle):
    """Include cutscene/flag-triggered events as location checks."""
    display_name = "All Cutscenes"


class SkillPoints(Choice):
    """Off: no skill point checks. Easy: the easier challenges only.
    Normal: Easy and Normal challenges. Hard: all three difficulties.
    Checks requiring disabled operatives are excluded. Legacy true means hard.
    """
    display_name = "Skill Points"
    option_off = 0
    option_easy = 1
    option_normal = 2
    option_hard = 3
    alias_false = 0
    alias_true = 3
    default = 0

    @classmethod
    def from_any(cls, data):
        if isinstance(data, bool):
            return cls(cls.option_hard if data else cls.option_off)
        return super().from_any(data)


class RandomSkillPoints(Toggle):
    """Select a random subset of eligible skill points, up to the chosen difficulty.
    Off includes every eligible skill point. Skill Points Off always disables them.
    """
    display_name = "Random Skill Points"


class SkillPointCount(Range):
    """Total skill points to select when Random Skill Points is enabled.
    Raises an options error if difficulty and enabled operatives leave too few.
    """
    display_name = "Random Skill Point Count"
    range_start = 0
    range_end = 30
    default = 5


class KeycardsAndAlienCodes(Toggle):
    """Include the 3 keycard pickups and all 27 Alien Codes as AP location checks."""
    display_name = "Keycards & Alien Codes"


class SendScoutedLocations(DefaultOnToggle):
    """Send vendor-scouted locations out as real AP hints (visible to trackers/other
    players), not just shown locally in the vendor menu. Off keeps scouting local-only."""
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
        # Drop zeros so a disabled operative is simply absent from .value.
        value = {name: amount for name, amount in value.items() if amount != 0}
        super().__init__(value)


class Goal(Choice):
    """Victory condition.
    Qwark Opera completes Madam Butterqwark; These Are The Real Adventures Of Captain Qwark
    completes every Qwark case. Any completes on whichever goal is finished first.
    Pick and Mix requires every condition selected below.
    """
    display_name = "Goal"
    option_defeat_klunk    = 0
    option_qwark_opera     = 1
    option_all_gadgetbots   = 2
    option_ratchet_prison_escape = 3
    option_these_are_the_real_adventures_of_captain_qwark = 4
    option_alien_codes      = 5
    option_chalice_of_power = 6
    option_any             = 7
    option_pick_and_mix    = 8
    default = 0



class PickAndMixGoals(OptionSet):
    """Add or remove victory conditions. All selected conditions must be completed.
    At least one must be selected when Goal is Pick and Mix.
    """
    display_name = "Pick and Mix Goals"
    valid_keys = {"defeat_klunk", "qwark_opera", "all_gadgetbots", "ratchet_prison_escape",
                  "these_are_the_real_adventures_of_captain_qwark", "alien_codes", "chalice_of_power"}
    default = frozenset()


class NgPlus(Range):
    """0 is the base game, 1 is challenge mode, and 2 is challenge mode level 2.
    With Progressive Challenge Mode enabled, this is the maximum obtainable level.
    Otherwise, this is the challenge-mode level used from the start.
    """
    display_name = "Max Challenge Mode"
    range_start = 0
    range_end = 2
    default = 0


class ProgressiveChallengeMode(Toggle):
    """Start at challenge level 0 and add one Progressive Challenge Mode item per
    Max Challenge Mode level. Each received copy raises the level by one, up to
    that maximum. Off starts directly at Max Challenge Mode.
    """
    display_name = "Progressive Challenge Mode"


class ProgressiveWeapons(Choice):
    """Off: weapons level through combat normally.
    Manual: the first copy unlocks a weapon; further copies raise its combat XP level cap.
    Automatic: each copy immediately grants the next level, with combat XP disabled.
    Only upgradeable weapons participate. Legacy true means automatic.
    """
    display_name = "Progressive Weapons"
    option_off = 0
    option_manual = 1
    option_automatic = 2
    alias_true = 2
    alias_false = 0
    default = 0

    @classmethod
    def from_any(cls, data):
        if isinstance(data, bool):
            return cls(cls.option_automatic if data else cls.option_off)
        return super().from_any(data)


class WeaponLevelChecks(Choice):
    """Checks for reaching weapon levels: V4, V8, both, or every level from V2.
    V5-V8 require NG+. The RYNO stops at V4. Gadgets and Clank Fu moves are excluded.
    """
    display_name = "Weapon Level Checks"
    option_off = 0
    option_level_4 = 1
    option_level_8 = 2
    option_level_4_and_8 = 3
    option_all = 4
    default = 0


class StealthTakedownChecks(Range):
    """Successful Clank stealth takedown checks per case: takedowns 1 up to this
    number in every case that has stealth takedowns, capped at what the case offers.
    Takedowns add up across replays of a case. 0 turns them off.
    Requires Clank. Progress is tracked while the AP client is connected.
    """
    display_name = "Stealth Takedown Checks"
    range_start = 0
    range_end = STEALTH_MAX_PER_CASE
    default = 0


class NanotechChecks(Toggle):
    """Add a location for each Clank nanotech increase: 16-60 in NG, 16-85 in NG+.
    Requires Clank to be enabled. Other operatives never award these locations.
    """
    display_name = "Clank Nanotech Locations"


class RatchetNanotechChecks(Toggle):
    """Add a location for each Ratchet nanotech increase: 21-60 in NG, 21-90 in NG+.
    Requires Ratchet. Locations use his saved XP, once per level across all missions.
    """
    display_name = "Ratchet Nanotech Locations"


class ProgressiveWrench(Toggle):
    """Adds 5 Progressive Wrench items to the pool (Ratchet only) each copy upgrades the wrench a level. Wrench starts as disabled if this is turned on."""
    display_name = "Progressive Wrench"


class WeaponXPMultiplier(Range):
    """Combat weapon XP multiplier. Inactive with automatic Progressive Weapons."""
    display_name = "Weapon XP Multiplier"
    range_start = 1
    range_end = 10
    default = 5


class HealthXPMultiplier(Range):
    """Multiplier for native health experience gains."""
    display_name = "Nanotech XP Multiplier"
    range_start = 1
    range_end = 10
    default = 5


class BoltMultiplier(Range):
    """Multiplier for earned bolts. Purchases and AP percentage rewards are unchanged."""
    display_name = "Bolt Multiplier"
    range_start = 1
    range_end = 10
    default = 5


class DeathAmnesty(Range):
    """Number of deaths allowed before triggering a death link."""
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
    clank_skin: ClankSkin
    ratchet_skin: RatchetSkin
    qwark_skin: QwarkSkin
    start_inventory_from_pool: StartInventoryPool
    death_link: DeathLink
    death_amnesty: DeathAmnesty
    all_missions: Missions
    all_cutscenes: AllCutscenes
    skill_points: SkillPoints
    random_skill_points: RandomSkillPoints
    skill_point_count: SkillPointCount
    keycards_and_alien_codes: KeycardsAndAlienCodes
    send_scouted_locations: SendScoutedLocations
    goal: Goal
    pick_and_mix_goals: PickAndMixGoals
    infobots: Infobots
    operatives: Operatives
    ng_plus: NgPlus
    progressive_challenge_mode: ProgressiveChallengeMode
    progressive_weapons: ProgressiveWeapons
    weapon_level_checks: WeaponLevelChecks
    stealth_takedown_checks: StealthTakedownChecks
    nanotech_checks: NanotechChecks
    ratchet_nanotech_checks: RatchetNanotechChecks
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

    @property
    def keycard_checks_enabled(self):
        return getattr(self, '_legacy_collectible_checks',
                       (bool(self.keycards_and_alien_codes),) * 2)[0]

    @property
    def alien_code_checks_enabled(self):
        return getattr(self, '_legacy_collectible_checks',
                       (bool(self.keycards_and_alien_codes),) * 2)[1]


sac_option_groups = [
    OptionGroup("SAC Goal Options", [Goal, PickAndMixGoals]),
    OptionGroup("SAC Game Options", [
        Infobots,
        Operatives,
        NgPlus,
        ProgressiveChallengeMode,
        WeaponXPMultiplier,
        HealthXPMultiplier,
        BoltMultiplier
    ]),
    OptionGroup("SAC Item Options", [
        ProgressiveWeapons,
        ProgressiveWrench,
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
        RandomSkillPoints,
        SkillPointCount,
        WeaponLevelChecks,
        NanotechChecks,
        RatchetNanotechChecks,
        StealthTakedownChecks,
        KeycardsAndAlienCodes,
        SendScoutedLocations,
    ]),
    OptionGroup("SAC Cosmetics", [ClankSkin, RatchetSkin, QwarkSkin]),
]
