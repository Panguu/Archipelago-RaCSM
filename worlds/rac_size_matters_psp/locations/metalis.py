from __future__ import annotations

from rule_builder.options import OptionFilter
from rule_builder.rules import HasAll, True_

from .. import constants as C
from ..constants import (
    Rac5Gadgets,
)
from ..constants.options import Rac5Options
from ..options import (
    AllCutscenes,
    AllMissions,
    ClankChallenges,
    EnableClankChallengeSkillPoints,
    GiantClank,
    SkillPoints,
)
from .model import Completion, LocationOptions, Rac5Locations

LOCATIONS = (
    Rac5Locations(
        C.Rac5TBolts.METALIS_DOOR,
        C.Rac5Planets.METALIS,
        lambda world: HasAll(Rac5Gadgets.POLARIZER, Rac5Gadgets.HYPERSHOT),
        Completion("bolt_bits", None, 4096),
        categories=frozenset(("titanium_bolt",)),
        native_planets=(4,),
        definition_order=7,
    ),
    Rac5Locations(
        C.Rac5Locations.METALIS_GLOVES,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("armour", "electroshock", 4),
        options=LocationOptions(requirements=(OptionFilter(GiantClank, (1,), "in"),)),
        categories=frozenset(("armour_pickup", Rac5Options.GIANT_CLANK)),
        definition_order=31,
    ),
    Rac5Locations(
        C.Rac5SkillPoints.METALIS_SHUTOUT,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("skill_bits", None, 4096),
        options=LocationOptions(requirements=(OptionFilter(EnableClankChallengeSkillPoints, (1,), "in"),)),
        categories=frozenset(("skill_point", "clank_challenge_skill_point")),
        native_planets=(4,),
        definition_order=53,
    ),
    Rac5Locations(
        C.Rac5SkillPoints.METALIS_GLADIATOR,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("skill_bits", None, 16384),
        options=LocationOptions(requirements=(OptionFilter(EnableClankChallengeSkillPoints, (1,), "in"),)),
        categories=frozenset(("skill_point", "clank_challenge_skill_point")),
        native_planets=(4,),
        definition_order=54,
    ),
    Rac5Locations(
        C.Rac5SkillPoints.METALIS_TERROR,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("skill_bits", None, 8192),
        options=LocationOptions(
            requirements=(
                OptionFilter(GiantClank, (1,), "in"),
                OptionFilter(SkillPoints, (2,), "in"),
            )
        ),
        categories=frozenset((Rac5Options.GIANT_CLANK, "skill_point", "hard_skill_point")),
        native_planets=(4,),
        definition_order=66,
    ),
    Rac5Locations(
        C.Rac5CutsceneLocations.METALIS_WAR,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("missions", 0x088c138a, 2, 4),
        options=LocationOptions(
            requirements=(
                OptionFilter(AllMissions, (1,), "in"),
                OptionFilter(ClankChallenges, (1, 2), "in"),
            )
        ),
        categories=frozenset(("story_mission", "mission")),
        check_order=7,
        definition_order=72,
    ),
    Rac5Locations(
        C.Rac5CutsceneLocations.METALIS_ESCAPE,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("events", C.Rac5CutsceneLocations.METALIS_ESCAPE),
        options=LocationOptions(
            requirements=(
                OptionFilter(GiantClank, (1,), "in"),
                OptionFilter(AllMissions, (1,), "in"),
            )
        ),
        categories=frozenset((Rac5Options.GIANT_CLANK, "story_mission", "mission")),
        definition_order=81,
    ),
    Rac5Locations(
        C.Rac5CutsceneLocations.METALIS_ENTER,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("missions", 0x088c138a, 1, 4),
        options=LocationOptions(requirements=(OptionFilter(AllCutscenes, (1,), "in"),)),
        categories=frozenset(("cutscene", "mission")),
        check_order=20,
        definition_order=97,
    ),
    Rac5Locations(
        C.Rac5ClankChallenges.METALIS_BUZZSAW,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("challenges", 0x088c139e, increasing=True),
        options=LocationOptions(
            requirements=(OptionFilter(ClankChallenges, (1, 2), "in"),), challenge_group="Demolition Derby"
        ),
        categories=frozenset(("challenge",)),
        check_order=0,
        definition_order=326,
    ),
    Rac5Locations(
        C.Rac5ClankChallenges.METALIS_REVENGE,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("challenges", 0x088c13a2, increasing=True),
        options=LocationOptions(
            requirements=(OptionFilter(ClankChallenges, (1, 2), "in"),), challenge_group="Demolition Derby"
        ),
        categories=frozenset(("challenge",)),
        check_order=1,
        definition_order=327,
    ),
    Rac5Locations(
        C.Rac5ClankChallenges.METALIS_UBER,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("challenges", 0x088c13a7, increasing=True),
        options=LocationOptions(
            requirements=(OptionFilter(ClankChallenges, (1, 2), "in"),), challenge_group="Gadgetbot Toss"
        ),
        categories=frozenset(("challenge",)),
        check_order=2,
        definition_order=328,
    ),
    Rac5Locations(
        C.Rac5ClankChallenges.METALIS_NIGHT,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("challenges", 0x088c13ac, increasing=True),
        options=LocationOptions(
            requirements=(OptionFilter(ClankChallenges, (1, 2), "in"),), challenge_group="Gadgetbot"
        ),
        categories=frozenset(("challenge",)),
        check_order=3,
        definition_order=329,
    ),
    Rac5Locations(
        C.Rac5ClankChallenges.METALIS_CHARGE,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("challenges", 0x088c139f, increasing=True),
        options=LocationOptions(
            requirements=(OptionFilter(ClankChallenges, (2,), "in"),), challenge_group="Demolition Derby"
        ),
        categories=frozenset(("all_clank",)),
        check_order=6,
        definition_order=332,
    ),
    Rac5Locations(
        C.Rac5ClankChallenges.METALIS_BOOGALOO,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("challenges", 0x088c13a0, increasing=True),
        options=LocationOptions(
            requirements=(OptionFilter(ClankChallenges, (2,), "in"),), challenge_group="Demolition Derby"
        ),
        categories=frozenset(("all_clank",)),
        check_order=7,
        definition_order=333,
    ),
    Rac5Locations(
        C.Rac5ClankChallenges.METALIS_SHOWDOWN,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("challenges", 0x088c13a1, increasing=True),
        options=LocationOptions(
            requirements=(OptionFilter(ClankChallenges, (2,), "in"),), challenge_group="Demolition Derby"
        ),
        categories=frozenset(("all_clank",)),
        check_order=8,
        definition_order=334,
    ),
    Rac5Locations(
        C.Rac5ClankChallenges.METALIS_LEAGUE,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("challenges", 0x088c13a3, increasing=True),
        options=LocationOptions(
            requirements=(OptionFilter(ClankChallenges, (2,), "in"),), challenge_group="Gadgetbot Toss"
        ),
        categories=frozenset(("all_clank",)),
        check_order=14,
        definition_order=340,
    ),
    Rac5Locations(
        C.Rac5ClankChallenges.METALIS_BRACKET,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("challenges", 0x088c13a4, increasing=True),
        options=LocationOptions(
            requirements=(OptionFilter(ClankChallenges, (2,), "in"),), challenge_group="Gadgetbot Toss"
        ),
        categories=frozenset(("all_clank",)),
        check_order=15,
        definition_order=341,
    ),
    Rac5Locations(
        C.Rac5ClankChallenges.METALIS_DIVISION,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("challenges", 0x088c13a5, increasing=True),
        options=LocationOptions(
            requirements=(OptionFilter(ClankChallenges, (2,), "in"),), challenge_group="Gadgetbot Toss"
        ),
        categories=frozenset(("all_clank",)),
        check_order=16,
        definition_order=342,
    ),
    Rac5Locations(
        C.Rac5ClankChallenges.METALIS_PROFESSIONAL,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("challenges", 0x088c13a6, increasing=True),
        options=LocationOptions(
            requirements=(OptionFilter(ClankChallenges, (2,), "in"),), challenge_group="Gadgetbot Toss"
        ),
        categories=frozenset(("all_clank",)),
        check_order=17,
        definition_order=343,
    ),
    Rac5Locations(
        C.Rac5ClankChallenges.METALLIS_TEAM,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("challenges", 0x088c13a8, increasing=True),
        options=LocationOptions(requirements=(OptionFilter(ClankChallenges, (2,), "in"),), challenge_group="Gadgetbot"),
        categories=frozenset(("all_clank",)),
        check_order=22,
        definition_order=348,
    ),
    Rac5Locations(
        C.Rac5ClankChallenges.METALIS_GAP,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("challenges", 0x088c13a9, increasing=True),
        options=LocationOptions(requirements=(OptionFilter(ClankChallenges, (2,), "in"),), challenge_group="Gadgetbot"),
        categories=frozenset(("all_clank",)),
        check_order=23,
        definition_order=349,
    ),
    Rac5Locations(
        C.Rac5ClankChallenges.METALIS_TELEPORTERS,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("challenges", 0x088c13aa, increasing=True),
        options=LocationOptions(requirements=(OptionFilter(ClankChallenges, (2,), "in"),), challenge_group="Gadgetbot"),
        categories=frozenset(("all_clank",)),
        check_order=24,
        definition_order=350,
    ),
    Rac5Locations(
        C.Rac5ClankChallenges.METALIS_BRAIN,
        C.Rac5Planets.METALIS,
        lambda world: True_(),
        Completion("challenges", 0x088c13ab, increasing=True),
        options=LocationOptions(requirements=(OptionFilter(ClankChallenges, (2,), "in"),), challenge_group="Gadgetbot"),
        categories=frozenset(("all_clank",)),
        check_order=25,
        definition_order=351,
    ),
)
