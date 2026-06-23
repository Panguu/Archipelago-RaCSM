from dataclasses import dataclass

from Options import (
    Accessibility,
    Choice,
    DeathLink,
    DefaultOnToggle,
    OptionGroup,
    PerGameCommonOptions,
    ProgressionBalancing,
    Range,
    StartInventoryPool,
    Toggle,
)


class ProgressiveWeapons(Toggle):
    """Replace each weapon's individual unlock item with a single Progressive Weapon
    item per weapon: the first copy unlocks the weapon, each subsequent copy grants
    the next level upgrade. When off, weapons are normal individual items with no
    level-up items (levels work as in vanilla)."""
    display_name = "Progressive Weapons"


class ProgressiveMods(Toggle):
    """Replace each weapon's individual mod items with a single Progressive Mod item
    per weapon: each copy grants the next mod slot in sequence. When off, each mod
    slot is its own individual item."""
    display_name = "Progressive Mods"


class ProgressiveArmour(Toggle):
    """Unlock armour pieces in a fixed order via Progressive Armour items rather than as individual pieces."""
    display_name = "Progressive Armour"


class ClankChallenges(Choice):
    """Controls how Clank challenge arenas are included as location checks.
    item_challenges: only the armour/gadget reward for each challenge arena (default).
    all: every individual challenge completion is a separate check."""
    display_name = "Clank Challenges"
    option_off             = 0
    option_item_challenges = 1
    option_all             = 2
    default = 1


class SkyboardChallenges(Choice):
    """Controls whether Skyboard race challenges are included as location checks.
    all: every individual race completion is a separate check."""
    display_name = "Skyboard Challenges"
    option_off = 0
    option_all = 1
    default = 0



class AllMissions(DefaultOnToggle):
    """Include story mission completions as location checks.
    Covers main narrative objectives on each planet."""
    display_name = "All Missions"


class AllCutscenes(Toggle):
    """Include cutscene and flag events as location checks.
    Covers encounter triggers and scripted events detected via flag bits."""
    display_name = "All Cutscenes"


class ArmourSetChecks(DefaultOnToggle):
    """Treat equipping a complete armour set as a location check. Adds 13 locations to the pool."""
    display_name = "Armour Set Checks"


class SkillPoints(Choice):
    """Include skill point challenges as location checks.
    off: no skill point checks.
    easy: a curated set of easier skill points only.
    hard: also includes a curated set of harder skill points.
    Clank Challenge and Skyboard Challenge skill points are controlled separately
    by the Enable Clank Challenge Skill Points and Enable Skyboard Challenge Skill
    Points options below, regardless of this setting."""
    display_name = "Skill Points"
    option_off  = 0
    option_easy = 1
    option_hard = 2
    default = 0


class EnableClankChallengeSkillPoints(Toggle):
    """Include skill points earned from Clank Challenge arenas as location checks,
    regardless of the Clank Challenges option."""
    display_name = "Enable Clank Challenge Skill Points"


class EnableSkyboardChallengeSkillPoints(Toggle):
    """Include skill points earned from Skyboard Challenges as location checks,
    regardless of the Skyboard Challenges option."""
    display_name = "Enable Skyboard Challenge Skill Points"


class StartingWeapons(Range):
    """Number of random weapons the player begins the game with."""
    display_name = "Starting Weapons"
    range_start = 0
    range_end = 13
    default = 2


class StartingGadgets(Range):
    """Number of random gadgets the player begins the game with. Default of 1 grants the Hypershot."""
    display_name = "Starting Gadgets"
    range_start = 0
    range_end = 8
    default = 1


class DeathAmnesty(Range):
    """Number of deaths allowed before items are removed from the player's inventory on death.
    Higher values are more forgiving."""
    display_name = "Death Amnesty"
    range_start = 0
    range_end = 5
    default = 0


class StartingBolts(Range):
    """Number of bolts the player begins the game with."""
    display_name = "Starting Bolts"
    range_start = 0
    range_end = 100_000
    default = 45_000


class TrapChance(Range):
    """Percent chance for each filler item to be replaced with a trap instead of Bolts."""
    display_name = "Trap Chance"
    range_start = 0
    range_end = 100
    default = 0


class StartingSkin(Choice):
    """Cosmetic skin for Ratchet. Applied automatically on each planet load.
    All skins are unlocked in-game regardless of this choice."""
    display_name = "Starting Skin"
    option_default          = 0
    option_pirate_ratchet   = 1
    option_godzilla_ratchet = 2
    option_trash_ratchet    = 3
    option_swim_ratchet     = 4
    option_kanga_ratchet    = 5
    option_hiro_ratchet     = 6
    default = 0


@dataclass
class RACSizeMatterOptions(PerGameCommonOptions):
    start_inventory_from_pool: StartInventoryPool
    progressive_weapons: ProgressiveWeapons
    progressive_mods: ProgressiveMods
    progressive_armour: ProgressiveArmour
    death_link: DeathLink
    death_amnesty: DeathAmnesty
    all_missions: AllMissions
    all_cutscenes: AllCutscenes
    clank_challenges: ClankChallenges
    skyboard_challenges: SkyboardChallenges
    armour_set_checks: ArmourSetChecks
    skill_points: SkillPoints
    enable_clank_challenge_skill_points: EnableClankChallengeSkillPoints
    enable_skyboard_challenge_skill_points: EnableSkyboardChallengeSkillPoints
    starting_weapons: StartingWeapons
    starting_gadgets: StartingGadgets
    starting_bolts: StartingBolts
    starting_skin: StartingSkin
    trap_chance: TrapChance

racsm_option_groups = [
    OptionGroup("Generic Options", [
        ProgressionBalancing,
        Accessibility,
        DeathLink,
        DeathAmnesty,
    ]),
    OptionGroup("RACSM Item Options", [
        StartingWeapons,
        StartingGadgets,
        StartingBolts,
        ProgressiveWeapons,
        ProgressiveMods,
        ProgressiveArmour,
        TrapChance,
    ]),
    OptionGroup("RACSM Location Options", [
        AllMissions,
        AllCutscenes,
        ClankChallenges,
        SkyboardChallenges,
        SkillPoints,
        EnableClankChallengeSkillPoints,
        EnableSkyboardChallengeSkillPoints,
        ArmourSetChecks,
    ]),
    OptionGroup("RACSM Cosmetic Options", [
        StartingSkin,
    ])
]
