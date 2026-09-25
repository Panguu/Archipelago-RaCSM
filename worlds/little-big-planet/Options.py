from collections import Counter
from dataclasses import dataclass

from Options import PerGameCommonOptions, OptionSet, Toggle, Choice, DeathLink, Range

from .chapters import DLC_PACKS
from .content_packs import PACK_BY_NAME
from .dlc import ADDON_PACKS
from .levels import LEVELS

_name_counts = Counter(level['name'] for level in LEVELS.values())
LEVEL_LABELS = {guid: (level['name'] if _name_counts[level['name']] == 1
                      else level['name'] + ' (' + level['constant'].replace('_', ' ').title() + ')')
                for guid, level in LEVELS.items()}
LEVEL_BY_LABEL = {label:guid for guid,label in LEVEL_LABELS.items()}
if len(LEVEL_BY_LABEL) != len(LEVELS):
    raise ValueError('Level selector labels must be unique')


class ExcludedLevels(OptionSet):
    """Remove selected base-game or DLC levels. Base-game levels are otherwise
    all enabled. Selecting a DLC level here does not enable its pack."""
    display_name = 'Excluded Levels'
    valid_keys = set(LEVEL_BY_LABEL)
    default = frozenset()


class DLCLevelPacks(OptionSet):
    """All catalogued level packs are selected by default. Remove packs you do not own. Empty enables none. Each selected pack
    contributes its levels, checks, rewards and kit-unlock item."""
    display_name = 'DLC Level Packs'
    valid_keys = set(DLC_PACKS)
    default = frozenset(valid_keys)


class DLCItemPacks(OptionSet):
    """All catalogued item packs are selected by default. Remove packs you do not own. Empty enables none. These
    catalogue asset families add inventory items without adding level checks."""
    display_name = 'DLC Item Packs'
    valid_keys = set(ADDON_PACKS.values())
    default = frozenset(valid_keys)


class DLCCostumes(OptionSet):
    """My Content costume collections and individual characters. Receive their
    unlock items to check their locations, then collect the contents in My Content.
    A collection unlock also opens its included characters. Select only owned DLC."""
    display_name = 'DLC Costumes'
    valid_keys = set(PACK_BY_NAME)
    default = frozenset(valid_keys)


class Goal(Choice):
    """What must be completed to finish:
    single_level: beat Goal Level only.
    all_levels: beat every enabled level.
    chapter_completion: beat every enabled chapter's finale level (its story-chapter or
    DLC-kit's final level, per the game's own level order)."""
    display_name = 'Goal'
    option_single_level = 0
    option_all_levels = 1
    option_chapter_completion = 2
    default = 0


class LevelChoice(Choice):
    """Named selection for a catalogued level."""
    @classmethod
    def get_option_name(cls, value):
        return LEVEL_LABELS[f'g{value}']

    @classmethod
    def from_text(cls, text):
        for label,guid in LEVEL_BY_LABEL.items():
            if text.casefold() in (label.casefold(), guid.casefold()):
                return cls(int(guid[1:]))
        return super().from_text(text)


GoalLevel = type('GoalLevel', (LevelChoice,), {
    '__module__': __name__,
    '__doc__': 'Level to complete for the single-level goal. Its DLC pack must be enabled and the level must not be excluded.',
    'display_name': 'Goal Level', 'default': 48456,
    **{'option_' + level['constant'].lower(): int(guid[1:]) for guid,level in LEVELS.items()},
})


class StartingLevelChoice(LevelChoice):
    @classmethod
    def get_option_name(cls, value):
        return 'Random' if value == 0 else super().get_option_name(value)

    @classmethod
    def from_text(cls, text):
        if text.casefold() == 'random':
            return cls(0)
        return super().from_text(text)


StartingLevel = type('StartingLevel', (StartingLevelChoice,), {
    '__module__': __name__,
    '__doc__': 'Start in a random enabled level, or choose a named level. Its DLC pack must be enabled and the level must not be excluded.',
    'display_name': 'Starting Level', 'default': 0,
    'option_random_start': 0,
    **{'option_' + level['constant'].lower(): int(guid[1:]) for guid,level in LEVELS.items()},
})


class ScoreBubbles(Toggle):
    """Include authored score bubbles as individual checks (Score Bubble Sanity). The host must
    also enable score_bubble_sanity in their host.yaml, or this option has no effect: exact
    pickup detection is still experimental and defaults off until verified."""
    display_name = 'Score Bubble Checks'


class StickerSanity(Toggle):
    """Sticker switches become checks requiring the matching sticker and level
    unlock. Requires v1.30. Sensors without a known sticker are excluded."""
    display_name = 'Sticker Sanity'


class KeySanity(Toggle):
    """Collectible keys inside levels become checks. Their original bonus levels
    still require AP level unlocks. Requires the v1.30 key pickup hook."""
    display_name = 'Key Sanity'


class ProgressiveCurators(Toggle):
    """Replace each story chapter's individual level-unlock items with a single
    'Progressive <Chapter>' item (one per chapter: The Gardens, The Savannah, The Wedding,
    The Canyons, The Metropolis, The Islands, The Temples, The Wilderness) that unlocks that
    chapter's levels one at a time, in the game's own story order, as copies are received.
    DLC kits, the GOTY bonus levels, and Introduction are unaffected."""
    display_name = 'Progressive Curators'


class Players(Range):
    """Number of players playing this world together in co-op. Logic-only: some
    locations require more than one player physically present to reach (e.g. seesaws,
    switches held simultaneously) and are excluded from logic below their requirement."""
    display_name = 'Players'
    range_start = 1
    range_end = 4
    default = 1


class TrapPercentage(Range):
    """Percentage of Nothing filler replaced by selected good and bad traps combined.
    Each selected effect is equally likely. Empty selections disable effects.
    Requires the v1.30 patches; gameplay effects wait for solo play."""
    display_name = 'Trap Percentage'
    range_start = 0
    range_end = 100
    default = 10


class GoodTraps(OptionSet):
    """Helpful effects eligible for the shared Trap Percentage. Select any number;
    an empty selection disables good traps."""
    display_name = 'Good Traps'
    valid_keys = {'Checkpoint Refill', 'Temporary Jetpack', 'Temporary Paintball Gun'}
    default = frozenset()


class BadTraps(OptionSet):
    """Disruptive effects eligible for the shared Trap Percentage. Select any number;
    an empty selection disables bad traps."""
    display_name = 'Bad Traps'
    valid_keys = {'Random Costume Trap', 'Restart Level Trap', 'Disable Checkpoint Trap'}
    default = frozenset({'Random Costume Trap'})


@dataclass
class LBPOptions(PerGameCommonOptions):
    excluded_levels: ExcludedLevels
    dlc_level_packs: DLCLevelPacks
    dlc_item_packs: DLCItemPacks
    dlc_costumes: DLCCostumes
    starting_level: StartingLevel
    goal: Goal
    goal_level: GoalLevel
    score_bubbles: ScoreBubbles
    sticker_sanity: StickerSanity
    key_sanity: KeySanity
    progressive_curators: ProgressiveCurators
    players: Players
    death_link: DeathLink
    trap_percentage: TrapPercentage
    good_traps: GoodTraps
    bad_traps: BadTraps
