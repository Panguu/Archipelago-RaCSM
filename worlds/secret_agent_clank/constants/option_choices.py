from dataclasses import dataclass


@dataclass(frozen=True)
class ClankSkinOptions:
    IN_GAME = 0
    SUIT = 11
    COWBOY = 12
    KLUNK = 13
    CLANK_70S = 14
    COP_CLANK = 15
    BLENDER = 16
    ZONI = 17


@dataclass(frozen=True)
class RatchetSkinOptions:
    IN_GAME = 0
    PRISON_SCRUBS = 1
    TOWEL = 2
    SUPER_INCOGNITO = 3
    TROPICAL_VACATION = 4
    PLUNDERING_PIRATE_CAPTAIN = 5
    RATCHETZILLA = 6
    KUNG_FU_RATCHET = 8
    ZOMBIE_RATCHET = 9
    DAN = 10


@dataclass(frozen=True)
class QwarkSkinOptions:
    IN_GAME = 0
    REGULAR = 18
    COWBOY = 19
    MAID_QWARK = 20
    LUCHA_LIBRE_QWARK = 21


@dataclass(frozen=True)
class MissionsOptions:
    LEVEL_COMPLETION = 0
    ALL = 1


@dataclass(frozen=True)
class SkillPointsOptions:
    OFF = 0
    EASY = 1
    NORMAL = 2
    HARD = 3


@dataclass(frozen=True)
class InfobotsOptions:
    CASES = 1
    PROGRESSIVE_PLANET = 2


@dataclass(frozen=True)
class RingLinkBehaviorOptions:
    ITEMS = 0
    ITEMS_AND_TRAPS = 1
    NEITHER = 2


@dataclass(frozen=True)
class GoalOptions:
    DEFEAT_KLUNK = 0
    QWARK_OPERA = 1
    ALL_GADGETBOTS = 2
    RATCHET_PRISON_ESCAPE = 3
    THESE_ARE_THE_REAL_ADVENTURES_OF_CAPTAIN_QWARK = 4
    ALIEN_CODES = 5
    CHALICE_OF_POWER = 6
    ANY = 7
    PICK_AND_MIX = 8


@dataclass(frozen=True)
class ProgressiveWeaponsOptions:
    OFF = 0
    MANUAL = 1
    AUTOMATIC = 2


@dataclass(frozen=True)
class WeaponLevelChecksOptions:
    OFF = 0
    LEVEL_4 = 1
    LEVEL_8 = 2
    LEVEL_4_AND_8 = 3
    ALL = 4
