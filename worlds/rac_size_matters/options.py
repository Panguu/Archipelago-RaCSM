from dataclasses import dataclass

from Options import (
    Accessibility,
    Choice,
    DeathLink,
    DefaultOnToggle,
    ItemDict,
    OptionCounter,
    OptionGroup,
    PerGameCommonOptions,
    ProgressionBalancing,
    Range,
    StartInventoryPool,
    Toggle,
)

from .core.traps import TRAP_DURATIONS
from .locations import (
    CHALLENGE_GROUP_DERBY,
    CHALLENGE_GROUP_GADGETBOT,
    CHALLENGE_GROUP_GADGETBOT_TOSS,
    DEFAULT_CLANK_CHALLENGE_GROUPS,
)


class ProgressiveWeapons(Choice):
    """Replace each weapon's individual unlock item with a single Progressive Weapon
    item per weapon: the first copy unlocks the weapon, each subsequent copy grants
    the next level upgrade.
    off: weapons are normal individual items with no level-up items (levels work as
    in vanilla).
    manual: leveling still happens by playing normally, but is capped at whatever
    level the Progressive Weapon items received so far allow — reaching that cap
    freezes further experience gain until the next copy arrives.
    automatic: level is set directly to match Progressive Weapon items received,
    with experience gain disabled entirely (no need to play to level up)."""
    display_name = "Progressive Weapons"
    option_off       = 0
    option_manual    = 1
    option_automatic = 2
    default = 0


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


class ClankChallengeGroups(ItemDict):
    """Selects which Clank Challenge groups (Metalis/Dayni Moon) are included
    as location checks, whenever Clank Challenges is on. Set a group to 0 to
    exclude all of its locations (both the item-reward and individual-
    completion tiers) from generation entirely — the challenge is still
    playable in-game, it just has no AP checks. Default 1 includes every
    group."""
    display_name = "Clank Challenge Groups"
    verify_item_name = False
    min = 0
    max = 1
    valid_keys = (CHALLENGE_GROUP_DERBY, CHALLENGE_GROUP_GADGETBOT_TOSS, CHALLENGE_GROUP_GADGETBOT)
    default = DEFAULT_CLANK_CHALLENGE_GROUPS


class SkyboardChallenges(Choice):
    """Controls whether Skyboard race challenges are included as location checks.
    all: every individual race completion is a separate check."""
    display_name = "Skyboard Challenges"
    option_off = 0
    option_all = 1
    default = 0


class ShrinkRayOptions(Choice):
    """Controls how Shrink Ray puzzles are handled.
    off: normal vanilla behavior — puzzles must be solved as usual, no checks.
    locations: include Shrink Ray puzzle completions as location checks.
    skip: writes every tracked puzzle-gate bit to solved every tick, bypassing
    whatever it would otherwise block."""
    display_name = "Shrink Ray Options"
    option_off       = 0
    option_locations = 1
    option_skip      = 2
    default = 1


class AmmoLink(Toggle):
    """Share weapon ammo with every other connected player who also has
    AmmoLink enabled (and toggled on client-side, same as DeathLink):
    whenever your ammo for a weapon changes, everyone else linked for that
    weapon gets mirrored to the same count, and vice versa. Players don't
    need to own the same weapons for this to work — a weapon you don't
    have simply isn't affected."""
    display_name = "Ammo Link"


class BoltLink(Toggle):
    """Share your bolt count with every other connected player who also has
    Bolt Link enabled (and toggled on client-side, same as DeathLink): your
    bolt count mirrors everyone else's -- spend or collect bolts on any
    linked player and everyone else's balance matches."""
    display_name = "Bolt Link"


class GhostLink(Toggle):
    """See another connected player as a ghost clone whenever you're both on
    the same planet (and they also have Ghost Link enabled and toggled on
    client-side, same as DeathLink). Only one ghost can be rendered at a
    time -- if more than one linked player shares your planet, one is
    picked automatically."""
    display_name = "Ghost Link"


class GhostLinkUpdateInterval(Range):
    """How often (in seconds) your position is broadcast to other Ghost Link
    players while Ghost Link is enabled. 0 broadcasts as fast as possible
    (every poll tick, no throttling)."""
    display_name = "Ghost Link Update Interval"
    range_start = 0
    range_end = 100
    default = 5


class AllMissions(DefaultOnToggle):
    """Include story mission completions as location checks.
    Covers main narrative objectives on each planet."""
    display_name = "All Missions"


class AllCutscenes(Toggle):
    """Include cutscene and flag events as location checks.
    Covers encounter triggers and scripted events detected via flag bits."""
    display_name = "All Cutscenes"


class GiantClank(Toggle):
    """Include the Giant Clank Metalis and Giant Clank Challax sequences: their
    completion/armour-pickup location checks, and (with Skill Points on) their
    skill point checks.
    off (default): both sequences are locked out entirely — entering either one
    immediately forces a load back out, exactly like vanilla before this option
    existed. Nothing from them is ever checked or required.
    on: both sequences become playable; entering plays them start-to-finish with
    no AP items/notifications until their location(s) fire."""
    display_name = "Giant Clank"


class ArmourSetChecks(DefaultOnToggle):
    """Treat equipping a complete armour set as a location check. Adds 13 locations to the pool."""
    display_name = "Armour Set Checks"


class NgPlusItems(DefaultOnToggle):
    """Include RYNO and the Chameleon/Hyperborean armour sets in generation. These are New
    Game Plus exclusives in vanilla, so turning this off is intended for players doing a
    fresh (non-NG+) playthrough where those items would never actually be obtainable.
    off: RYNO and the Chameleon/Hyperborean armour pieces are removed from the item pool
    entirely. Also removes the RYNO Weapon Level checks, and the Chameleon/Hyperborean
    Armour Set checks along with Stalker/Ice II (both of which need a Chameleon or
    Hyperborean piece to complete)."""
    display_name = "NG+ Items"


class ChallengeMode(Range):
    """Enables the game's Challenge Mode (New Game Plus) and controls how far
    into it generation reaches. Also written to game memory at connect so the
    game itself enters the matching Challenge Mode tier.
    0: vanilla — no Challenge Mode content.
    1: Challenge Mode 1 — adds the RYNO vendor purchase, 10 Challenge-Mode-only
    weapon mod purchases, and the 4 Hyperborean armour pieces as real pickups.
    2: Challenge Mode 2 — everything from tier 1, plus the 4 Chameleon armour
    pieces as real pickups.
    Every item this unlocks a location for is still governed by NG+ Items —
    with that option off, none of them are placed in the pool at all, so this
    option alone has no effect."""
    display_name = "Challenge Mode"
    range_start = 0
    range_end = 2
    default = 0


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


class RandomStartingPlanet(Choice):
    """Randomizes which two planets Ratchet starts with access to, instead of always
    starting on Pokitaru and Ryllus. Their infobots go back into the normal item pool
    and two random planets' infobots are precollected in their place. Dreamtime,
    Inside Clank, and Quodrona are never candidates: the first two need extra gadgets
    beyond their own infobot to enter, and Quodrona is the goal planet.
    off: always start on Pokitaru and Ryllus, as in vanilla.
    logic: candidate planets are weighted by how many locations they offer under the
    current options, so denser planets are more likely to be picked. Weapon/Gadget
    Vendor locations only count towards a planet's weight if Starting Weapons/Starting
    Gadgets is set above 0.
    no_logic: two of the 6 candidate planets are chosen completely at random, ignoring
    location counts entirely."""
    display_name = "Random Starting Planet"
    option_off      = 0
    option_logic    = 1
    option_no_logic = 2
    default = 0


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


class TrapWeight(ItemDict):
    """Sets the relative weights of trap types in the filler pool. A higher value increases
    how often that trap is chosen over the others when a filler item rolls as a trap (see
    Trap Chance). Has no effect when Trap Chance is 0, or when every weight here is 0
    (Bolts fills in instead)."""
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


class WeaponExperienceMultiplier(Range):
    """Multiplies weapon experience gained each time the game grants it, speeding up
    weapon leveling. Stops applying once a weapon reaches level 4 (max level for
    every weapon). 0/1 = no boost."""
    display_name = "Weapon Experience Multiplier"
    range_start = 0
    range_end = 16
    default = 4


class BoltMultiplier(Range):
    """Multiplies bolts gained each time the game grants them (crates, enemies, etc.),
    speeding up bolt income. Does not affect one-off AP grants like starting bolts.
    0/1 = no boost."""
    display_name = "Bolt Multiplier"
    range_start = 0
    range_end = 16
    default = 4


class NanotechExperienceMultiplier(Range):
    """Multiplies Nanotech (health) experience gained each time the game grants it,
    speeding up Nanotech leveling. 0/1 = no boost."""
    display_name = "Nanotech Experience Multiplier"
    range_start = 0
    range_end = 16
    default = 4


class NanotechLevelInterval(Choice):
    """Include reaching Nanotech (health) Levels as location checks, one every N
    levels (e.g. every_5 checks levels 10, 15, 20, ...). See Nanotech Level Max
    for where this stops. Levels above 20 require access to a good EXP planet."""
    display_name = "Nanotech Level Interval"
    option_off     = 0
    option_every_5  = 5
    option_every_10 = 10
    option_every_25 = 25
    default = 0


class NanotechLevelMax(Range):
    """Highest Nanotech Level Nanotech Level Interval creates a check for — e.g.
    every_5 with this set to 25 checks only levels 10, 15, 20, 25. No effect while
    Nanotech Level Interval is off."""
    display_name = "Nanotech Level Max"
    range_start = 6
    range_end = 75
    default = 75


class WeaponLevelChecks(Choice):
    """Adds location checks for reaching weapon levels, in addition to whatever
    unlocks the weapon in the first place.
    off: no weapon level checks.
    level_4: one check per weapon, for reaching level 4 (vanilla max level).
    level_8: one check per weapon, for reaching level 8 (Challenge Mode Titan max
    level) — only meaningful with Challenge Mode 1+.
    level_4_and_8: both of the above.
    all: one check per weapon per level (2 through 8, Challenge Mode levels 5-8
    included when Challenge Mode is 1+)."""
    display_name = "Weapon Level Checks"
    option_off           = 0
    option_level_4       = 1
    option_level_8       = 2
    option_level_4_and_8 = 3
    option_all           = 4
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
    ammo_link: AmmoLink
    bolt_link: BoltLink
    ghost_link: GhostLink
    ghost_link_update_interval: GhostLinkUpdateInterval
    all_missions: AllMissions
    all_cutscenes: AllCutscenes
    giant_clank: GiantClank
    clank_challenges: ClankChallenges
    clank_challenge_groups: ClankChallengeGroups
    enable_clank_challenge_skill_points: EnableClankChallengeSkillPoints
    skyboard_challenges: SkyboardChallenges
    enable_skyboard_challenge_skill_points: EnableSkyboardChallengeSkillPoints
    shrink_ray_options: ShrinkRayOptions
    armour_set_checks: ArmourSetChecks
    ng_plus_items: NgPlusItems
    challenge_mode: ChallengeMode
    skill_points: SkillPoints
    starting_weapons: StartingWeapons
    starting_gadgets: StartingGadgets
    random_starting_planet: RandomStartingPlanet
    starting_bolts: StartingBolts
    starting_skin: StartingSkin
    trap_chance: TrapChance
    trap_weight: TrapWeight
    trap_duration: TrapDuration
    weapon_experience_multiplier: WeaponExperienceMultiplier
    bolt_multiplier: BoltMultiplier
    nanotech_experience_multiplier: NanotechExperienceMultiplier
    weapon_level_checks: WeaponLevelChecks
    nanotech_level_interval: NanotechLevelInterval
    nanotech_level_max: NanotechLevelMax

racsm_option_groups = [
    OptionGroup("Generic Options", [
        ProgressionBalancing,
        Accessibility,
    ]),
    OptionGroup("RACSM Game Links", [
        DeathLink,
        DeathAmnesty,
        AmmoLink,
        BoltLink,
        GhostLink,
        GhostLinkUpdateInterval,
    ]),
    OptionGroup("RACSM Item Options", [
        StartingWeapons,
        StartingGadgets,
        RandomStartingPlanet,
        StartingBolts,
        ProgressiveWeapons,
        ProgressiveMods,
        ProgressiveArmour,
        TrapChance,
        TrapWeight,
        TrapDuration,
        WeaponExperienceMultiplier,
        BoltMultiplier,
        NanotechExperienceMultiplier,
    ]),
    OptionGroup("RACSM Challenges", [
        ClankChallenges,
        ClankChallengeGroups,
        EnableClankChallengeSkillPoints,
        SkyboardChallenges,
        EnableSkyboardChallengeSkillPoints,
        GiantClank,
    ]),
    OptionGroup("RACSM Location Options", [
        AllMissions,
        AllCutscenes,
        ShrinkRayOptions,
        SkillPoints,
        ArmourSetChecks,
        WeaponLevelChecks,
        NanotechLevelInterval,
        NanotechLevelMax,
        NgPlusItems,
        ChallengeMode,
    ]),
    OptionGroup("RACSM Cosmetic Options", [
        StartingSkin,
    ])
]
