"""String constants for skill point locations."""

from dataclasses import dataclass

from .planets import SACCases
from .types import CaseStructure, SACTags, group_by_case


@dataclass(frozen=True)
class SACSkillPoints:
    """String constants for skill point event titles (short form only -- see SKILL_POINTS below for which case/address each belongs to)."""

    FURIOUS_FISTS = "Furious Fists of Fury"
    SILENT_NIGHT = "Silent Night"
    PYRRHIC_VICTORY = "Pyrrhic Victory"
    TRIPLE_PLATINUM = "Triple Platinum Record"
    STAINLESS_STEEL = "Stainless Steel"
    PLAYING_WITH_FIRE = "Playing With Fire"
    SPEED_DEMON = "Speed Demon"
    PERFECT_CHROME_FINISH = "Perfect Chrome Finish"
    ROBOT_FINDS_NINJA = "Robot Finds Ninja"
    BLACK_TIE_AFFAIR = "Black Tie Affair"
    LIKE_THE_WIND = "Like The Wind"
    INVERSE_NINJA_LAW = "Inverse Ninja Law"
    BLASTER_OVERLOAD = "Blaster Overload"
    PERFECT_TANGO = "Perfect Tango"
    BLACK_DIAMOND = "Black Diamond"
    SMOOTH_MOVES = "Smooth Moves"
    RINGLEADER = "Ringleader"
    EMPTY_THE_WARRENS = "Empty The Warrens"
    ANTAEUS = "Antaeus"
    MASTER_OF_DISGUISE = "Master of Disguise"
    TRASH_TALK = "Trash Talk"
    DEADLY_HANDS = "Deadly Hands"
    STEEL_RAIN = "Steel Rain"
    CARD_PICKUP = "52 Card Pickup"
    DRESS_FOR_SUCCESS = "Dress For Success"
    BEAT_THE_HOUSE = "Beat The House"
    INDIAN_BURN = "Indian Burn"
    LAW_CANT_TOUCH_ME = "The Law Can't Touch Me"
    LUCKY_SEVENS = "Lucky Sevens"
    GADGEBOT_STANDS_ALONE = "A Gadgebot Stands Alone"
    ALL_SLIME_MUST_BURN = "All Slime Must Burn"
    RAMMING_SPEED = "Ramming Speed!"
    EVASIVE_MANEUVERS = "Evasive Maneuvers"
    DEEP_SIX = "Deep Six"
    WAKE_OF_DESTRUCTION = "Wake Of Destruction"
    RINGMASTER = "Ringmaster"
    TWINKLE_TOES = "Twinkle Toes"
    MAGNUM_OPUS = "Magnum Opus"
    SOLD_OUT = "Sold Out"
    WITH_INTEREST = "With Interest"
    ANDROIDS_IN_DISGUISE = "Androids In Disguise"
    VAULT_VAULT = "Vault Vault"
    DIA_DE_LOS_MUERTOS = "El Día de los Muertos"
    RUBA_DUB_CLUB = "Ruba-Dub Club"
    MODESTY = "Modesty"
    DELICACY_SOMEWHERE = "It's A Delicacy Somewhere"
    REVENANT = "Revenant"
    PUNCHY = "Punchy"
    SOUR_VICTORY = "Sour Victory"
    MIN_MAXING = "Min Maxing"
    KILL_THE_ROCK = "I Kill the Rock"
    WHIP_IT_GOOD = "Whip It Good"
    HANGING_JUDGE = "Hanging Judge"
    YEEE_HAAAAAW = "Yeeee Haaaaaw!"
    OFFENSIVE_DRIVER = "Offensive Driver"
    SLIPPERY_SLOPE = "Slippery Slope"
    RING_AROUND_THE_ROSIE = "Ring Around the Rosie"
    CLEANS_POOLS_TOO = "He Cleans pools, Too!"
    PERFECT_MIRROR = "Perfect Mirror"
    CEREAL_DECODER_RING = "Cerial Decoder Rung"
    LEET_HAXXOR = "I33t h4XX0r"
    RUST_PROOF = "Rust Proof"
    IM_NOT_THERE = "I'm not There"
    TURN_THE_TABLES = "Turn The Tables"
    PRETTY_GOOD_LIKENESS = "A Pretty Good Likeness"


# One CaseStructure per skill point -- order matches the case_id (1-30)
# order in constants/planets.py, which cross-confirms that flat list's
# ordering (does NOT confirm the planet groupings, still best-guess).
# address/flag walk 0x206BF8-0x206C00 one bit at a time, in this same order.
SKILL_POINTS: tuple[CaseStructure, ...] = (
    CaseStructure(SACCases.BOLTAIRE_MUSEUM, SACSkillPoints.FURIOUS_FISTS, SACTags.SKILL_POINT, event_flag=0b00000001, event_address=0x206BF8),
    CaseStructure(SACCases.BOLTAIRE_MUSEUM, SACSkillPoints.SILENT_NIGHT, SACTags.SKILL_POINT, event_flag=0b00000010, event_address=0x206BF8),
    CaseStructure(SACCases.BOLTAIRE_GEM_WING, SACSkillPoints.PYRRHIC_VICTORY, SACTags.SKILL_POINT, event_flag=0b00000100, event_address=0x206BF8),
    CaseStructure(SACCases.BOLTAIRE_GEM_WING, SACSkillPoints.TRIPLE_PLATINUM, SACTags.SKILL_POINT, event_flag=0b00001000, event_address=0x206BF8),
    CaseStructure(SACCases.MAX_SECURITY_CELLS, SACSkillPoints.STAINLESS_STEEL, SACTags.SKILL_POINT, event_flag=0b00010000, event_address=0x206BF8),
    CaseStructure(SACCases.MAX_SECURITY_CELLS, SACSkillPoints.PLAYING_WITH_FIRE, SACTags.SKILL_POINT, event_flag=0b00100000, event_address=0x206BF8),
    CaseStructure(SACCases.ROOFTOP_DEATHTRAP, SACSkillPoints.SPEED_DEMON, SACTags.SKILL_POINT, event_flag=0b01000000, event_address=0x206BF8),
    CaseStructure(SACCases.ROOFTOP_DEATHTRAP, SACSkillPoints.PERFECT_CHROME_FINISH, SACTags.SKILL_POINT, event_flag=0b10000000, event_address=0x206BF8),
    CaseStructure(SACCases.ASYANICA_ROOFTOPS, SACSkillPoints.ROBOT_FINDS_NINJA, SACTags.SKILL_POINT, event_flag=0b00000001, event_address=0x206BF9),
    CaseStructure(SACCases.ASYANICA_ROOFTOPS, SACSkillPoints.BLACK_TIE_AFFAIR, SACTags.SKILL_POINT, event_flag=0b00000010, event_address=0x206BF9),
    CaseStructure(SACCases.ASYANICA_ROOFTOPS, SACSkillPoints.LIKE_THE_WIND, SACTags.SKILL_POINT, event_flag=0b00000100, event_address=0x206BF9),
    CaseStructure(SACCases.LARGER_THAN_LIFE, SACSkillPoints.INVERSE_NINJA_LAW, SACTags.SKILL_POINT, event_flag=0b00001000, event_address=0x206BF9),
    CaseStructure(SACCases.LARGER_THAN_LIFE, SACSkillPoints.BLASTER_OVERLOAD, SACTags.SKILL_POINT, event_flag=0b00010000, event_address=0x206BF9),
    CaseStructure(SACCases.COUNTESS_VILLA, SACSkillPoints.PERFECT_TANGO, SACTags.SKILL_POINT, event_flag=0b00100000, event_address=0x206BF9),
    CaseStructure(SACCases.GLACIARA_SKI_SLOPES, SACSkillPoints.BLACK_DIAMOND, SACTags.SKILL_POINT, event_flag=0b01000000, event_address=0x206BF9),
    CaseStructure(SACCases.GLACIARA_SKI_SLOPES, SACSkillPoints.SMOOTH_MOVES, SACTags.SKILL_POINT, event_flag=0b10000000, event_address=0x206BF9),
    CaseStructure(SACCases.GLACIARA_SKI_SLOPES, SACSkillPoints.RINGLEADER, SACTags.SKILL_POINT, event_flag=0b00000001, event_address=0x206BFA),
    CaseStructure(SACCases.THE_MESS_HALL, SACSkillPoints.EMPTY_THE_WARRENS, SACTags.SKILL_POINT, event_flag=0b00000010, event_address=0x206BFA),
    CaseStructure(SACCases.THE_MESS_HALL, SACSkillPoints.ANTAEUS, SACTags.SKILL_POINT, event_flag=0b00000100, event_address=0x206BFA),
    CaseStructure(SACCases.AZCOTAL_ALLEY, SACSkillPoints.MASTER_OF_DISGUISE, SACTags.SKILL_POINT, event_flag=0b00001000, event_address=0x206BFA),
    CaseStructure(SACCases.AZCOTAL_ALLEY, SACSkillPoints.TRASH_TALK, SACTags.SKILL_POINT, event_flag=0b00010000, event_address=0x206BFA),
    CaseStructure(SACCases.AZCOTAL_ALLEY, SACSkillPoints.DEADLY_HANDS, SACTags.SKILL_POINT, event_flag=0b00100000, event_address=0x206BFA),
    CaseStructure(SACCases.GONDOLA_ASCENT, SACSkillPoints.STEEL_RAIN, SACTags.SKILL_POINT, event_flag=0b01000000, event_address=0x206BFA),
    CaseStructure(SACCases.SUCK_AND_JIVE, SACSkillPoints.CARD_PICKUP, SACTags.SKILL_POINT, event_flag=0b10000000, event_address=0x206BFA),
    CaseStructure(SACCases.SUCK_AND_JIVE, SACSkillPoints.DRESS_FOR_SUCCESS, SACTags.SKILL_POINT, event_flag=0b00000001, event_address=0x206BFB),
    CaseStructure(SACCases.HIGH_ROLLERS_CASINO, SACSkillPoints.BEAT_THE_HOUSE, SACTags.SKILL_POINT, event_flag=0b00000010, event_address=0x206BFB),
    CaseStructure(SACCases.THE_EXERCISE_YARD, SACSkillPoints.INDIAN_BURN, SACTags.SKILL_POINT, event_flag=0b00000100, event_address=0x206BFB),
    CaseStructure(SACCases.THE_EXERCISE_YARD, SACSkillPoints.LAW_CANT_TOUCH_ME, SACTags.SKILL_POINT, event_flag=0b00001000, event_address=0x206BFB),
    CaseStructure(SACCases.HIGH_STAKES_ROOM, SACSkillPoints.LUCKY_SEVENS, SACTags.SKILL_POINT, event_flag=0b00010000, event_address=0x206BFB),
    CaseStructure(SACCases.HIGH_STAKES_ROOM, SACSkillPoints.GADGEBOT_STANDS_ALONE, SACTags.SKILL_POINT, event_flag=0b00100000, event_address=0x206BFB),
    CaseStructure(SACCases.VENANTONIO_LABS, SACSkillPoints.ALL_SLIME_MUST_BURN, SACTags.SKILL_POINT, event_flag=0b01000000, event_address=0x206BFB),
    CaseStructure(SACCases.VENANTONIO_LABS, SACSkillPoints.RAMMING_SPEED, SACTags.SKILL_POINT, event_flag=0b10000000, event_address=0x206BFB),
    CaseStructure(SACCases.VENANTONIO_CANALS, SACSkillPoints.EVASIVE_MANEUVERS, SACTags.SKILL_POINT, event_flag=0b00000001, event_address=0x206BFC),
    CaseStructure(SACCases.VENANTONIO_CANALS, SACSkillPoints.DEEP_SIX, SACTags.SKILL_POINT, event_flag=0b00000010, event_address=0x206BFC),
    CaseStructure(SACCases.VENANTONIO_CANALS, SACSkillPoints.WAKE_OF_DESTRUCTION, SACTags.SKILL_POINT, event_flag=0b00000100, event_address=0x206BFC),
    CaseStructure(SACCases.VENANTONIO_CANALS, SACSkillPoints.RINGMASTER, SACTags.SKILL_POINT, event_flag=0b00001000, event_address=0x206BFC),
    CaseStructure(SACCases.MADAM_BUTTERQWARK, SACSkillPoints.TWINKLE_TOES, SACTags.SKILL_POINT, event_flag=0b00010000, event_address=0x206BFC),
    CaseStructure(SACCases.MADAM_BUTTERQWARK, SACSkillPoints.MAGNUM_OPUS, SACTags.SKILL_POINT, event_flag=0b00100000, event_address=0x206BFC),
    CaseStructure(SACCases.MADAM_BUTTERQWARK, SACSkillPoints.SOLD_OUT, SACTags.SKILL_POINT, event_flag=0b01000000, event_address=0x206BFC),
    CaseStructure(SACCases.GALACTIC_BOLT_RESERVE, SACSkillPoints.WITH_INTEREST, SACTags.SKILL_POINT, event_flag=0b10000000, event_address=0x206BFC),
    CaseStructure(SACCases.GALACTIC_BOLT_RESERVE, SACSkillPoints.ANDROIDS_IN_DISGUISE, SACTags.SKILL_POINT, event_flag=0b00000001, event_address=0x206BFD),
    # Vault Vault confirmed here (Galactic Bolt Reserve), not Inside the
    # A-Eye -- corrects the earlier best-guess grouping.
    CaseStructure(SACCases.GALACTIC_BOLT_RESERVE, SACSkillPoints.VAULT_VAULT, SACTags.SKILL_POINT, event_flag=0b00000010, event_address=0x206BFD),
    CaseStructure(SACCases.INSIDE_THE_A_EYE, SACSkillPoints.DIA_DE_LOS_MUERTOS, SACTags.SKILL_POINT, event_flag=0b00000100, event_address=0x206BFD),
    CaseStructure(SACCases.THE_SHOWERS, SACSkillPoints.RUBA_DUB_CLUB, SACTags.SKILL_POINT, event_flag=0b00001000, event_address=0x206BFD),
    CaseStructure(SACCases.THE_SHOWERS, SACSkillPoints.MODESTY, SACTags.SKILL_POINT, event_flag=0b00010000, event_address=0x206BFD),
    CaseStructure(SACCases.SPACESHIP_GRAVEYARD, SACSkillPoints.DELICACY_SOMEWHERE, SACTags.SKILL_POINT, event_flag=0b00100000, event_address=0x206BFD),
    CaseStructure(SACCases.SPACESHIP_GRAVEYARD, SACSkillPoints.REVENANT, SACTags.SKILL_POINT, event_flag=0b01000000, event_address=0x206BFD),
    CaseStructure(SACCases.SAINT_QWARK, SACSkillPoints.PUNCHY, SACTags.SKILL_POINT, event_flag=0b10000000, event_address=0x206BFD),
    CaseStructure(SACCases.SAINT_QWARK, SACSkillPoints.SOUR_VICTORY, SACTags.SKILL_POINT, event_flag=0b00000001, event_address=0x206BFE),
    CaseStructure(SACCases.THE_QUASAR_FIELDS, SACSkillPoints.MIN_MAXING, SACTags.SKILL_POINT, event_flag=0b00000010, event_address=0x206BFE),
    CaseStructure(SACCases.THE_QUASAR_FIELDS, SACSkillPoints.KILL_THE_ROCK, SACTags.SKILL_POINT, event_flag=0b00000100, event_address=0x206BFE),
    CaseStructure(SACCases.PRISON_BREAKOUT, SACSkillPoints.WHIP_IT_GOOD, SACTags.SKILL_POINT, event_flag=0b00001000, event_address=0x206BFE),
    CaseStructure(SACCases.PRISON_BREAKOUT, SACSkillPoints.HANGING_JUDGE, SACTags.SKILL_POINT, event_flag=0b00010000, event_address=0x206BFE),
    CaseStructure(SACCases.DAMS_EDGE_HYDRANO, SACSkillPoints.YEEE_HAAAAAW, SACTags.SKILL_POINT, event_flag=0b00100000, event_address=0x206BFE),
    CaseStructure(SACCases.DAMS_EDGE_HYDRANO, SACSkillPoints.OFFENSIVE_DRIVER, SACTags.SKILL_POINT, event_flag=0b01000000, event_address=0x206BFE),
    CaseStructure(SACCases.DAMS_EDGE_HYDRANO, SACSkillPoints.SLIPPERY_SLOPE, SACTags.SKILL_POINT, event_flag=0b10000000, event_address=0x206BFE),
    CaseStructure(SACCases.DAMS_EDGE_HYDRANO, SACSkillPoints.RING_AROUND_THE_ROSIE, SACTags.SKILL_POINT, event_flag=0b00000001, event_address=0x206BFF),
    CaseStructure(SACCases.A_FICTION_FULL_OF_DOLLARS, SACSkillPoints.CLEANS_POOLS_TOO, SACTags.SKILL_POINT, event_flag=0b00000010, event_address=0x206BFF),
    CaseStructure(SACCases.A_FICTION_FULL_OF_DOLLARS, SACSkillPoints.PERFECT_MIRROR, SACTags.SKILL_POINT, event_flag=0b00000100, event_address=0x206BFF),
    CaseStructure(SACCases.BULKHEAD_LOCK, SACSkillPoints.CEREAL_DECODER_RING, SACTags.SKILL_POINT, event_flag=0b00001000, event_address=0x206BFF),
    CaseStructure(SACCases.UNDERWATER_BUNKER, SACSkillPoints.LEET_HAXXOR, SACTags.SKILL_POINT, event_flag=0b00010000, event_address=0x206BFF),
    CaseStructure(SACCases.UNDERWATER_BUNKER, SACSkillPoints.RUST_PROOF, SACTags.SKILL_POINT, event_flag=0b00100000, event_address=0x206BFF),
    CaseStructure(SACCases.UNDERWATER_BUNKER, SACSkillPoints.IM_NOT_THERE, SACTags.SKILL_POINT, event_flag=0b01000000, event_address=0x206BFF),
    CaseStructure(SACCases.KLUNKS_LAIR, SACSkillPoints.TURN_THE_TABLES, SACTags.SKILL_POINT, event_flag=0b10000000, event_address=0x206BFF),
    CaseStructure(SACCases.KLUNKS_LAIR, SACSkillPoints.PRETTY_GOOD_LIKENESS, SACTags.SKILL_POINT, event_flag=0b00000001, event_address=0x206C00),
)

# Case.name -> its skill points' full display names, derived from
# SKILL_POINTS above. Order matches case_id (1-30) order, same caveat as
# the tuple itself.
SKILL_POINTS_BY_CASE: dict[str, tuple[str, ...]] = group_by_case(SKILL_POINTS)


@dataclass(frozen=True)
class SACSkillPointLocations:
    BOLTAIRE_MUSEUM_FURIOUS_FISTS = "Boltaire (Clank) - Boltaire Museum: Skill Point: Furious Fists of Fury"
    BOLTAIRE_MUSEUM_SILENT_NIGHT = "Boltaire (Clank) - Boltaire Museum: Skill Point: Silent Night"
    BOLTAIRE_GEM_WING_PYRRHIC_VICTORY = "Boltaire (Special Missions) - Boltaire Gem Wing: Skill Point: Pyrrhic Victory"
    BOLTAIRE_GEM_WING_TRIPLE_PLATINUM = "Boltaire (Special Missions) - Boltaire Gem Wing: Skill Point: Triple Platinum Record"
    MAX_SECURITY_CELLS_STAINLESS_STEEL = "Prison Planet (Ratchet) - Max-Security Cells: Skill Point: Stainless Steel"
    MAX_SECURITY_CELLS_PLAYING_WITH_FIRE = "Prison Planet (Ratchet) - Max-Security Cells: Skill Point: Playing With Fire"
    ROOFTOP_DEATHTRAP_SPEED_DEMON = "Asyanica (Gadgetbots) - Rooftop Deathtrap: Skill Point: Speed Demon"
    ROOFTOP_DEATHTRAP_PERFECT_CHROME_FINISH = "Asyanica (Gadgetbots) - Rooftop Deathtrap: Skill Point: Perfect Chrome Finish"
    ASYANICA_ROOFTOPS_ROBOT_FINDS_NINJA = "Asyanica (Clank) - Asyanica Rooftops: Skill Point: Robot Finds Ninja"
    ASYANICA_ROOFTOPS_BLACK_TIE_AFFAIR = "Asyanica (Clank) - Asyanica Rooftops: Skill Point: Black Tie Affair"
    ASYANICA_ROOFTOPS_LIKE_THE_WIND = "Asyanica (Clank) - Asyanica Rooftops: Skill Point: Like The Wind"
    LARGER_THAN_LIFE_INVERSE_NINJA_LAW = "Asyanica (Qwark) - Larger Than Life: Skill Point: Inverse Ninja Law"
    LARGER_THAN_LIFE_BLASTER_OVERLOAD = "Asyanica (Qwark) - Larger Than Life: Skill Point: Blaster Overload"
    COUNTESS_VILLA_PERFECT_TANGO = "Glaciara (Special Missions) - Countess's Villa: Skill Point: Perfect Tango"
    GLACIARA_SKI_SLOPES_BLACK_DIAMOND = "Glaciara (Special Missions) - Glaciara, Ski Slopes: Skill Point: Black Diamond"
    GLACIARA_SKI_SLOPES_SMOOTH_MOVES = "Glaciara (Special Missions) - Glaciara, Ski Slopes: Skill Point: Smooth Moves"
    GLACIARA_SKI_SLOPES_RINGLEADER = "Glaciara (Special Missions) - Glaciara, Ski Slopes: Skill Point: Ringleader"
    THE_MESS_HALL_EMPTY_THE_WARRENS = "Prison Planet (Ratchet) - The Mess Hall: Skill Point: Empty The Warrens"
    THE_MESS_HALL_ANTAEUS = "Prison Planet (Ratchet) - The Mess Hall: Skill Point: Antaeus"
    AZCOTAL_ALLEY_MASTER_OF_DISGUISE = "Rionosis (Clank) - Azcotal Alley: Skill Point: Master of Disguise"
    AZCOTAL_ALLEY_TRASH_TALK = "Rionosis (Clank) - Azcotal Alley: Skill Point: Trash Talk"
    AZCOTAL_ALLEY_DEADLY_HANDS = "Rionosis (Clank) - Azcotal Alley: Skill Point: Deadly Hands"
    GONDOLA_ASCENT_STEEL_RAIN = "Rionosis (Clank) - Gondola Ascent: Skill Point: Steel Rain"
    SUCK_AND_JIVE_CARD_PICKUP = "Rionosis (Qwark) - Suck and Jive: Skill Point: 52 Card Pickup"
    SUCK_AND_JIVE_DRESS_FOR_SUCCESS = "Rionosis (Qwark) - Suck and Jive: Skill Point: Dress For Success"
    HIGH_ROLLERS_CASINO_BEAT_THE_HOUSE = "The Paradis Des Tricheurs Casino (Clank) - High-Rollers Casino: Skill Point: Beat The House"
    THE_EXERCISE_YARD_INDIAN_BURN = "Prison Planet (Ratchet) - The Exercise Yard: Skill Point: Indian Burn"
    THE_EXERCISE_YARD_LAW_CANT_TOUCH_ME = "Prison Planet (Ratchet) - The Exercise Yard: Skill Point: The Law Can't Touch Me"
    HIGH_STAKES_ROOM_LUCKY_SEVENS = "The Paradis Des Tricheurs Casino (Special Missions) - High Stakes Room: Skill Point: Lucky Sevens"
    HIGH_STAKES_ROOM_GADGEBOT_STANDS_ALONE = "The Paradis Des Tricheurs Casino (Special Missions) - High Stakes Room: Skill Point: A Gadgebot Stands Alone"
    VENANTONIO_LABS_ALL_SLIME_MUST_BURN = "Venantonio (Clank) - Venantonio Labs: Skill Point: All Slime Must Burn"
    VENANTONIO_LABS_RAMMING_SPEED = "Venantonio (Clank) - Venantonio Labs: Skill Point: Ramming Speed!"
    VENANTONIO_CANALS_EVASIVE_MANEUVERS = "Venantonio (Special Missions) - Venantonio Canals: Skill Point: Evasive Maneuvers"
    VENANTONIO_CANALS_DEEP_SIX = "Venantonio (Special Missions) - Venantonio Canals: Skill Point: Deep Six"
    VENANTONIO_CANALS_WAKE_OF_DESTRUCTION = "Venantonio (Special Missions) - Venantonio Canals: Skill Point: Wake Of Destruction"
    VENANTONIO_CANALS_RINGMASTER = "Venantonio (Special Missions) - Venantonio Canals: Skill Point: Ringmaster"
    MADAM_BUTTERQWARK_TWINKLE_TOES = "Venantonio (Qwark) - Madam Butterqwark: Skill Point: Twinkle Toes"
    MADAM_BUTTERQWARK_MAGNUM_OPUS = "Venantonio (Qwark) - Madam Butterqwark: Skill Point: Magnum Opus"
    MADAM_BUTTERQWARK_SOLD_OUT = "Venantonio (Qwark) - Madam Butterqwark: Skill Point: Sold Out"
    GALACTIC_BOLT_RESERVE_WITH_INTEREST = "Fort Sprocket (Clank) - Galactic Bolt Reserve: Skill Point: With Interest"
    GALACTIC_BOLT_RESERVE_ANDROIDS_IN_DISGUISE = "Fort Sprocket (Clank) - Galactic Bolt Reserve: Skill Point: Androids In Disguise"
    GALACTIC_BOLT_RESERVE_VAULT_VAULT = "Fort Sprocket (Clank) - Galactic Bolt Reserve: Skill Point: Vault Vault"
    INSIDE_THE_A_EYE_DIA_DE_LOS_MUERTOS = "Fort Sprocket (Gadgetbots) - Inside the A-Eye: Skill Point: El Día de los Muertos"
    THE_SHOWERS_RUBA_DUB_CLUB = "Prison Planet (Ratchet) - The Showers: Skill Point: Ruba-Dub Club"
    THE_SHOWERS_MODESTY = "Prison Planet (Ratchet) - The Showers: Skill Point: Modesty"
    SPACESHIP_GRAVEYARD_DELICACY_SOMEWHERE = "Spaceship Graveyard (Clank) - Spaceship Graveyard: Skill Point: It's A Delicacy Somewhere"
    SPACESHIP_GRAVEYARD_REVENANT = "Spaceship Graveyard (Clank) - Spaceship Graveyard: Skill Point: Revenant"
    SAINT_QWARK_PUNCHY = "Spaceship Graveyard (Qwark) - Saint Qwark: Skill Point: Punchy"
    SAINT_QWARK_SOUR_VICTORY = "Spaceship Graveyard (Qwark) - Saint Qwark: Skill Point: Sour Victory"
    THE_QUASAR_FIELDS_MIN_MAXING = "Spaceship Graveyard (Special Missions) - The Quasar Fields: Skill Point: Min Maxing"
    THE_QUASAR_FIELDS_KILL_THE_ROCK = "Spaceship Graveyard (Special Missions) - The Quasar Fields: Skill Point: I Kill the Rock"
    PRISON_BREAKOUT_WHIP_IT_GOOD = "Prison Planet (Ratchet) -  Prison Breakout!: Skill Point: Whip It Good"
    PRISON_BREAKOUT_HANGING_JUDGE = "Prison Planet (Ratchet) -  Prison Breakout!: Skill Point: Hanging Judge"
    DAMS_EDGE_HYDRANO_YEEE_HAAAAAW = "Hydrano (Special Missions) - Dam's Edge, Hydrano: Skill Point: Yeeee Haaaaaw!"
    DAMS_EDGE_HYDRANO_OFFENSIVE_DRIVER = "Hydrano (Special Missions) - Dam's Edge, Hydrano: Skill Point: Offensive Driver"
    DAMS_EDGE_HYDRANO_SLIPPERY_SLOPE = "Hydrano (Special Missions) - Dam's Edge, Hydrano: Skill Point: Slippery Slope"
    DAMS_EDGE_HYDRANO_RING_AROUND_THE_ROSIE = "Hydrano (Special Missions) - Dam's Edge, Hydrano: Skill Point: Ring Around the Rosie"
    A_FICTION_FULL_OF_DOLLARS_CLEANS_POOLS_TOO = "Hydrano (Qwark) - A Fiction Full Of Dollars: Skill Point: He Cleans pools, Too!"
    A_FICTION_FULL_OF_DOLLARS_PERFECT_MIRROR = "Hydrano (Qwark) - A Fiction Full Of Dollars: Skill Point: Perfect Mirror"
    BULKHEAD_LOCK_CEREAL_DECODER_RING = "Hydrano (Gadgetbots) - Bulkhead Lock: Skill Point: Cerial Decoder Rung"
    UNDERWATER_BUNKER_LEET_HAXXOR = "Hydrano (Clank) - Underwater Bunker: Skill Point: I33t h4XX0r"
    UNDERWATER_BUNKER_RUST_PROOF = "Hydrano (Clank) - Underwater Bunker: Skill Point: Rust Proof"
    UNDERWATER_BUNKER_IM_NOT_THERE = "Hydrano (Clank) - Underwater Bunker: Skill Point: I'm not There"
    KLUNKS_LAIR_TURN_THE_TABLES = "Hydrano (Clank) - Klunk's Lair: Skill Point: Turn The Tables"
    KLUNKS_LAIR_PRETTY_GOOD_LIKENESS = "Hydrano (Clank) - Klunk's Lair: Skill Point: A Pretty Good Likeness"
