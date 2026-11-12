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

from .constants import (
    OPTIONAL_OPERATIVES,
    STEALTH_MAX_PER_CASE,
    ALL_TRAPS,
    TRAP_DURATIONS,
    ClankSkinOptions,
    GoalOptions,
    InfobotsOptions,
    MissionsOptions,
    ProgressiveWeaponsOptions,
    QwarkSkinOptions,
    RatchetSkinOptions,
    RingLinkBehaviorOptions,
    SkillPointsOptions,
    WeaponLevelChecksOptions,
    SACOperatives,
)


class ClankSkin(Choice):
    """Clank's cosmetic skin. In-game keeps your selection in the game's Skins menu.
    All skins are unlocked on AP initialization. A chosen skin is the initial default;
    later in-game selections are preserved.
    """
    display_name = "Clank Skin"
    option_in_game = ClankSkinOptions.IN_GAME
    option_suit = ClankSkinOptions.SUIT
    option_cowboy = ClankSkinOptions.COWBOY
    option_klunk = ClankSkinOptions.KLUNK
    option_70s_clank = ClankSkinOptions.CLANK_70S
    option_cop_clank = ClankSkinOptions.COP_CLANK
    option_blender = ClankSkinOptions.BLENDER
    option_zoni = ClankSkinOptions.ZONI
    default = ClankSkinOptions.IN_GAME


class RatchetSkin(Choice):
    """Ratchet's cosmetic skin. In-game keeps your selection in the game's Skins menu.
    Supported skins are unlocked on AP initialization. Robo-Ratchet is unavailable
    in the PS2 release. A chosen skin is the initial default;
    later in-game selections are preserved.
    """
    display_name = "Ratchet Skin"
    option_in_game = RatchetSkinOptions.IN_GAME
    option_prison_scrubs = RatchetSkinOptions.PRISON_SCRUBS
    option_towel = RatchetSkinOptions.TOWEL
    option_super_incognito = RatchetSkinOptions.SUPER_INCOGNITO
    option_tropical_vacation = RatchetSkinOptions.TROPICAL_VACATION
    option_plundering_pirate_captain = RatchetSkinOptions.PLUNDERING_PIRATE_CAPTAIN
    option_ratchetzilla = RatchetSkinOptions.RATCHETZILLA
    option_kung_fu_ratchet = RatchetSkinOptions.KUNG_FU_RATCHET
    option_zombie_ratchet = RatchetSkinOptions.ZOMBIE_RATCHET
    option_dan = RatchetSkinOptions.DAN
    default = RatchetSkinOptions.IN_GAME


class QwarkSkin(Choice):
    """Qwark's cosmetic skin, including its matching giant form.
    In-game keeps your selection in the game's Skins menu. All skins are unlocked
    on AP initialization. A chosen skin is the initial default; later in-game
    selections are preserved.
    """
    display_name = "Qwark Skin"
    option_in_game = QwarkSkinOptions.IN_GAME
    option_regular = QwarkSkinOptions.REGULAR
    option_cowboy = QwarkSkinOptions.COWBOY
    option_maid_qwark = QwarkSkinOptions.MAID_QWARK
    option_lucha_libre_qwark = QwarkSkinOptions.LUCHA_LIBRE_QWARK
    default = QwarkSkinOptions.IN_GAME


class Missions(Choice):
    """Controls the granularity of story-mission location checks."""
    display_name = "Missions"
    option_level_completion = MissionsOptions.LEVEL_COMPLETION
    option_all = MissionsOptions.ALL
    default = MissionsOptions.LEVEL_COMPLETION


class AllCutscenes(Toggle):
    """Include cutscene/flag-triggered events as location checks."""
    display_name = "All Cutscenes"


class SkillPoints(Choice):
    """Off: no skill point checks. Easy: the easier challenges only.
    Normal: Easy and Normal challenges. Hard: all three difficulties.
    Checks requiring disabled operatives are excluded.
    """
    display_name = "Skill Points"
    option_off = SkillPointsOptions.OFF
    option_easy = SkillPointsOptions.EASY
    option_normal = SkillPointsOptions.NORMAL
    option_hard = SkillPointsOptions.HARD
    default = SkillPointsOptions.OFF


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
    """Include the 3 keycard pickups and all 27 Alien Codes as AP location checks.
    If an Operative is excluded their location will not be included.
    """
    display_name = "Keycards & Alien Codes"


class KeycardHunt(Toggle):
    """Shuffle Red, Blue, and Yellow Keycards into the AP item pool.
    All three received cards open the keycard door inside the Treehouse.
    Treehouse access still requires collecting the Alien Codes.
    Physical keycard pickups remain separate location checks when enabled.
    """
    display_name = "Keycard Hunt"


class SendScoutedLocations(DefaultOnToggle):
    """Send vendor-scouted locations out as real AP hints (visible to trackers/other
    players), not just shown locally in the vendor menu. Off keeps scouting local-only."""
    display_name = "Send Scouted Locations"


class Infobots(Choice):
    """Choose how access is unlocked."""
    display_name = "Infobots"
    option_cases = InfobotsOptions.CASES
    option_progressive_planet = InfobotsOptions.PROGRESSIVE_PLANET
    default = InfobotsOptions.CASES


class Operatives(OptionCounter):
    """Enabled optional operatives (Ratchet, Qwark, Gadgetbots, and Special Missions).
    Clank is always included and cannot be disabled."""
    display_name = "Operatives"
    min = 0
    max = 1
    valid_keys = OPTIONAL_OPERATIVES
    default = dict.fromkeys(OPTIONAL_OPERATIVES, 1)


class Goal(Choice):
    """
    Determines what the player needs to complete to achieve their goal.
    - Defeat Klunk: Complete the showdown with Klunk in the Klunk's Lair case file.
    - Qwark Opera: Complete the Madam Butterqwark case file.
    - All Gadgetbots: Complete all Gadgetbot case files.
    - Ratchet Prison Escape: Complete all Ratchet case files.
    - These Are the Real Adventures of Captain Qwark: Complete all Qwark case files.
    - Alien Codes: Scan all 27 alien codes.
    - Chalice of Power: Obtain the Chalice of Power.
    - Any: Complete any one of the objectives above.
    - Pick and Mix: Complete every goal you select in Pick and Mix Goals.
    """
    display_name = "Goal"
    option_defeat_klunk = GoalOptions.DEFEAT_KLUNK
    option_qwark_opera = GoalOptions.QWARK_OPERA
    option_all_gadgetbots = GoalOptions.ALL_GADGETBOTS
    option_ratchet_prison_escape = GoalOptions.RATCHET_PRISON_ESCAPE
    option_these_are_the_real_adventures_of_captain_qwark = GoalOptions.THESE_ARE_THE_REAL_ADVENTURES_OF_CAPTAIN_QWARK
    option_alien_codes = GoalOptions.ALIEN_CODES
    option_chalice_of_power = GoalOptions.CHALICE_OF_POWER
    option_any = GoalOptions.ANY
    option_pick_and_mix = GoalOptions.PICK_AND_MIX
    default = GoalOptions.DEFEAT_KLUNK



class PickAndMixGoals(OptionSet):
    """Add or remove victory conditions. All selected conditions must be completed.
    At least one must be selected when Goal is Pick and Mix.
    The valid options are: defeat_klunk, qwark_opera, all_gadgetbots, ratchet_prison_escape,
    these_are_the_real_adventures_of_captain_qwark, alien_codes, chalice_of_power
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
    Only upgradeable weapons participate.
    """
    display_name = "Progressive Weapons"
    option_off = ProgressiveWeaponsOptions.OFF
    option_manual = ProgressiveWeaponsOptions.MANUAL
    option_automatic = ProgressiveWeaponsOptions.AUTOMATIC
    default = ProgressiveWeaponsOptions.OFF


class WeaponLevelChecks(Choice):
    """Checks for reaching weapon levels: V4, V8, both, or every level from V2.
    V5-V8 require NG+. The RYNO stops at V4. Gadgets and Clank Fu moves are excluded.
    """
    display_name = "Weapon Level Checks"
    option_off = WeaponLevelChecksOptions.OFF
    option_level_4 = WeaponLevelChecksOptions.LEVEL_4
    option_level_8 = WeaponLevelChecksOptions.LEVEL_8
    option_level_4_and_8 = WeaponLevelChecksOptions.LEVEL_4_AND_8
    option_all = WeaponLevelChecksOptions.ALL
    default = WeaponLevelChecksOptions.OFF


class StealthTakedownChecks(Range):
    """Successful Clank stealth takedown checks per case: takedowns 1 up to this
    number in every case that has stealth takedowns, capped at what the case offers.
    Takedowns add up across replays of a case. 0 turns them off.
    Progress is tracked while the AP client is connected.
    The locations included in this setting are:
    - Boltaire (Clank) - Boltaire Museum
    - Asyanica (Clank) - Asyanica Rooftops
    - Rionosis (Clank) - Azcotal Alley
    - The Paradis Des Tricheurs Casino (Clank) - High-Rollers Casino
    - Venantonio (Clank) - Venantonio Labs
    - Fort Sprocket (Clank) - Galactic Bolt Reserve
    - Spaceship Graveyard (Clank) - Spaceship Graveyard
    - Hydrano (Clank) - Underwater Bunker
    """
    display_name = "Stealth Takedown Checks"
    range_start = 0
    range_end = STEALTH_MAX_PER_CASE
    default = 0


class NanotechChecks(Toggle):
    """Add a location for each Clank nanotech increase: 16-60 in NG, 16-85 in NG+.
    Other operatives never award these locations.
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


class RingLink(Toggle):
    """Share bolt gains and losses with every player who has Ring Link on, in any game that supports it.
    One bolt is one ring. Your bolts never go below 0."""
    display_name = "Ring Link"


class RingLinkBehavior(Choice):
    """Which bolt changes made by received items are shared over Ring Link. Bolts you pick up or spend in game
    are always shared. Starting bolts are never shared.

    - Items: Bolts items are shared, Gadgetron Debt Traps are not.
    - Items and Traps: both Bolts items and Gadgetron Debt Traps are shared.
    - Neither: only bolts you pick up or spend in game are shared."""
    display_name = "Ring Link Behavior"
    option_items = RingLinkBehaviorOptions.ITEMS
    option_items_and_traps = RingLinkBehaviorOptions.ITEMS_AND_TRAPS
    option_neither = RingLinkBehaviorOptions.NEITHER
    default = RingLinkBehaviorOptions.ITEMS


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
    default = 25_000


class TrapChance(Range):
    """Percent chance for each filler item (Bolts, Nanotech XP or Weapon XP) to be a trap instead."""
    display_name = "Trap Chance"
    range_start = 0
    range_end = 100
    default = 0


class TrapWeight(ItemDict):
    """Sets the relative weights of trap types in the filler pool."""
    display_name = "Trap Weight"
    min = 0
    max = 100
    valid_keys = ALL_TRAPS
    default = dict.fromkeys(ALL_TRAPS, 1)


class TrapDuration(OptionCounter):
    """How many seconds each trap type stays active once triggered. Gadgetron Debt and One HP are instant, so they have no duration."""
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
    ring_link: RingLink
    ring_link_behavior: RingLinkBehavior
    all_missions: Missions
    all_cutscenes: AllCutscenes
    skill_points: SkillPoints
    random_skill_points: RandomSkillPoints
    skill_point_count: SkillPointCount
    keycards_and_alien_codes: KeycardsAndAlienCodes
    keycard_hunt: KeycardHunt
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
        return bool(self.keycards_and_alien_codes)

    @property
    def alien_code_checks_enabled(self):
        return bool(self.keycards_and_alien_codes)


# Options sent in slot_data, for the client and for Universal Tracker to regenerate from.
SLOT_DATA_OPTIONS = (
    "infobots", "death_link", "death_amnesty", "ring_link", "ring_link_behavior", "all_missions", "all_cutscenes",
    "skill_points", "random_skill_points", "skill_point_count", "keycard_hunt", "keycards_and_alien_codes",
    "send_scouted_locations", "goal", "pick_and_mix_goals", "progressive_wrench", "progressive_weapons",
    "weapon_level_checks", "nanotech_checks", "ratchet_nanotech_checks", "stealth_takedown_checks",
    "weapon_xp_multiplier", "health_xp_multiplier", "bolt_multiplier", "ng_plus", "progressive_challenge_mode",
    "starting_weapons", "starting_gadgets", "starting_bolts", "clank_skin", "ratchet_skin", "qwark_skin",
    "trap_chance", "trap_weight", "trap_duration",
)


sac_option_groups = [
    OptionGroup("SAC Goal Options", [Goal, PickAndMixGoals]),
    OptionGroup("SAC Game Options", [
        Infobots,
        Operatives,
        NgPlus,
        ProgressiveChallengeMode,
        WeaponXPMultiplier,
        HealthXPMultiplier,
        BoltMultiplier,
        RingLink,
        RingLinkBehavior,
    ]),
    OptionGroup("SAC Item Options", [
        KeycardHunt,
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


def enabled_operatives(options: SecretAgentClankOptions) -> frozenset[str]:
    return frozenset({SACOperatives.CLANK, *(name for name, amount in options.operatives.value.items() if amount)})
