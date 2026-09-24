from functools import partial

from rule_builder.options import OptionFilter
from rule_builder.rules import Has, HasAny

from .. import constants as C
from ..constants import Rac5Weapons
from ..items import PROGRESSIVE_WEAPON_NAME
from ..options import ChallengeMode, NgPlusItems, WeaponLevelChecks
from ..rules._helpers import HasChallengeMode, HasGoodExpPlanet
from .model import Completion, LocationOptions, Rac5Locations

_NEEDS_GOOD_EXP_PLANET = frozenset((Rac5Weapons.RYNO, Rac5Weapons.LASER_TRACER, Rac5Weapons.STATIC_BARRIER))


def access_rule(world, *, weapon, level):
    rule = (
        Has(PROGRESSIVE_WEAPON_NAME[weapon], level)
        if world.options.progressive_weapons
        else HasAny(weapon, PROGRESSIVE_WEAPON_NAME[weapon])
    )
    if level >= 5:
        rule = rule & HasChallengeMode(world, 1)
    if weapon in _NEEDS_GOOD_EXP_PLANET:
        rule = rule & HasGoodExpPlanet()
    return rule


LOCATIONS = (
    Rac5Locations(
        C.Rac5WeaponLevels.LACERATOR_LEVEL_2,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.LACERATOR, level=2),
        Completion("weapon_levels", ("lacerator", 2)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.LACERATOR
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="lacerator",
        level=2,
        definition_order=156,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.LACERATOR_LEVEL_3,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.LACERATOR, level=3),
        Completion("weapon_levels", ("lacerator", 3)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.LACERATOR
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="lacerator",
        level=3,
        definition_order=157,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.LACERATOR_LEVEL_4,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.LACERATOR, level=4),
        Completion("weapon_levels", ("lacerator", 4)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (1, 3, 4), "in"),), weapon=C.Rac5Weapons.LACERATOR
        ),
        categories=frozenset(("weapon_level", "weapon_max_level")),
        weapon="lacerator",
        level=4,
        definition_order=158,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.LACERATOR_LEVEL_5,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.LACERATOR, level=5),
        Completion("weapon_levels", ("lacerator", 5)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.LACERATOR,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="lacerator",
        level=5,
        definition_order=159,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.LACERATOR_LEVEL_6,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.LACERATOR, level=6),
        Completion("weapon_levels", ("lacerator", 6)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.LACERATOR,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="lacerator",
        level=6,
        definition_order=160,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.LACERATOR_LEVEL_7,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.LACERATOR, level=7),
        Completion("weapon_levels", ("lacerator", 7)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.LACERATOR,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="lacerator",
        level=7,
        definition_order=161,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.LACERATOR_LEVEL_8,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.LACERATOR, level=8),
        Completion("weapon_levels", ("lacerator", 8)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (2, 3, 4), "in"),
            ),
            weapon=C.Rac5Weapons.LACERATOR,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_max_level", "challenge_mode_weapon_level")),
        weapon="lacerator",
        level=8,
        definition_order=162,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.CONCUSSION_GUN_LEVEL_2,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.CONCUSSION_GUN, level=2),
        Completion("weapon_levels", ("concussion_gun", 2)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.CONCUSSION_GUN
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="concussion_gun",
        level=2,
        definition_order=163,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.CONCUSSION_GUN_LEVEL_3,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.CONCUSSION_GUN, level=3),
        Completion("weapon_levels", ("concussion_gun", 3)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.CONCUSSION_GUN
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="concussion_gun",
        level=3,
        definition_order=164,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.CONCUSSION_GUN_LEVEL_4,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.CONCUSSION_GUN, level=4),
        Completion("weapon_levels", ("concussion_gun", 4)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (1, 3, 4), "in"),), weapon=C.Rac5Weapons.CONCUSSION_GUN
        ),
        categories=frozenset(("weapon_level", "weapon_max_level")),
        weapon="concussion_gun",
        level=4,
        definition_order=165,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.CONCUSSION_GUN_LEVEL_5,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.CONCUSSION_GUN, level=5),
        Completion("weapon_levels", ("concussion_gun", 5)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.CONCUSSION_GUN,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="concussion_gun",
        level=5,
        definition_order=166,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.CONCUSSION_GUN_LEVEL_6,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.CONCUSSION_GUN, level=6),
        Completion("weapon_levels", ("concussion_gun", 6)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.CONCUSSION_GUN,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="concussion_gun",
        level=6,
        definition_order=167,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.CONCUSSION_GUN_LEVEL_7,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.CONCUSSION_GUN, level=7),
        Completion("weapon_levels", ("concussion_gun", 7)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.CONCUSSION_GUN,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="concussion_gun",
        level=7,
        definition_order=168,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.CONCUSSION_GUN_LEVEL_8,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.CONCUSSION_GUN, level=8),
        Completion("weapon_levels", ("concussion_gun", 8)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (2, 3, 4), "in"),
            ),
            weapon=C.Rac5Weapons.CONCUSSION_GUN,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_max_level", "challenge_mode_weapon_level")),
        weapon="concussion_gun",
        level=8,
        definition_order=169,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.ACID_BOMB_GLOVE_LEVEL_2,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.ACID_BOMB_GLOVE, level=2),
        Completion("weapon_levels", ("acid_bomb_glove", 2)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.ACID_BOMB_GLOVE
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="acid_bomb_glove",
        level=2,
        definition_order=170,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.ACID_BOMB_GLOVE_LEVEL_3,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.ACID_BOMB_GLOVE, level=3),
        Completion("weapon_levels", ("acid_bomb_glove", 3)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.ACID_BOMB_GLOVE
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="acid_bomb_glove",
        level=3,
        definition_order=171,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.ACID_BOMB_GLOVE_LEVEL_4,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.ACID_BOMB_GLOVE, level=4),
        Completion("weapon_levels", ("acid_bomb_glove", 4)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (1, 3, 4), "in"),), weapon=C.Rac5Weapons.ACID_BOMB_GLOVE
        ),
        categories=frozenset(("weapon_level", "weapon_max_level")),
        weapon="acid_bomb_glove",
        level=4,
        definition_order=172,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.ACID_BOMB_GLOVE_LEVEL_5,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.ACID_BOMB_GLOVE, level=5),
        Completion("weapon_levels", ("acid_bomb_glove", 5)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.ACID_BOMB_GLOVE,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="acid_bomb_glove",
        level=5,
        definition_order=173,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.ACID_BOMB_GLOVE_LEVEL_6,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.ACID_BOMB_GLOVE, level=6),
        Completion("weapon_levels", ("acid_bomb_glove", 6)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.ACID_BOMB_GLOVE,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="acid_bomb_glove",
        level=6,
        definition_order=174,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.ACID_BOMB_GLOVE_LEVEL_7,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.ACID_BOMB_GLOVE, level=7),
        Completion("weapon_levels", ("acid_bomb_glove", 7)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.ACID_BOMB_GLOVE,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="acid_bomb_glove",
        level=7,
        definition_order=175,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.ACID_BOMB_GLOVE_LEVEL_8,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.ACID_BOMB_GLOVE, level=8),
        Completion("weapon_levels", ("acid_bomb_glove", 8)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (2, 3, 4), "in"),
            ),
            weapon=C.Rac5Weapons.ACID_BOMB_GLOVE,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_max_level", "challenge_mode_weapon_level")),
        weapon="acid_bomb_glove",
        level=8,
        definition_order=176,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.AGENTS_OF_DOOM_LEVEL_2,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.AGENTS_OF_DOOM, level=2),
        Completion("weapon_levels", ("agents_of_doom", 2)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.AGENTS_OF_DOOM
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="agents_of_doom",
        level=2,
        definition_order=177,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.AGENTS_OF_DOOM_LEVEL_3,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.AGENTS_OF_DOOM, level=3),
        Completion("weapon_levels", ("agents_of_doom", 3)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.AGENTS_OF_DOOM
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="agents_of_doom",
        level=3,
        definition_order=178,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.AGENTS_OF_DOOM_LEVEL_4,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.AGENTS_OF_DOOM, level=4),
        Completion("weapon_levels", ("agents_of_doom", 4)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (1, 3, 4), "in"),), weapon=C.Rac5Weapons.AGENTS_OF_DOOM
        ),
        categories=frozenset(("weapon_level", "weapon_max_level")),
        weapon="agents_of_doom",
        level=4,
        definition_order=179,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.AGENTS_OF_DOOM_LEVEL_5,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.AGENTS_OF_DOOM, level=5),
        Completion("weapon_levels", ("agents_of_doom", 5)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.AGENTS_OF_DOOM,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="agents_of_doom",
        level=5,
        definition_order=180,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.AGENTS_OF_DOOM_LEVEL_6,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.AGENTS_OF_DOOM, level=6),
        Completion("weapon_levels", ("agents_of_doom", 6)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.AGENTS_OF_DOOM,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="agents_of_doom",
        level=6,
        definition_order=181,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.AGENTS_OF_DOOM_LEVEL_7,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.AGENTS_OF_DOOM, level=7),
        Completion("weapon_levels", ("agents_of_doom", 7)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.AGENTS_OF_DOOM,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="agents_of_doom",
        level=7,
        definition_order=182,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.AGENTS_OF_DOOM_LEVEL_8,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.AGENTS_OF_DOOM, level=8),
        Completion("weapon_levels", ("agents_of_doom", 8)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (2, 3, 4), "in"),
            ),
            weapon=C.Rac5Weapons.AGENTS_OF_DOOM,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_max_level", "challenge_mode_weapon_level")),
        weapon="agents_of_doom",
        level=8,
        definition_order=183,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.BEE_MINE_GLOVE_LEVEL_2,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.BEE_MINE_GLOVE, level=2),
        Completion("weapon_levels", ("bee_mine_glove", 2)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.BEE_MINE_GLOVE
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="bee_mine_glove",
        level=2,
        definition_order=184,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.BEE_MINE_GLOVE_LEVEL_3,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.BEE_MINE_GLOVE, level=3),
        Completion("weapon_levels", ("bee_mine_glove", 3)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.BEE_MINE_GLOVE
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="bee_mine_glove",
        level=3,
        definition_order=185,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.BEE_MINE_GLOVE_LEVEL_4,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.BEE_MINE_GLOVE, level=4),
        Completion("weapon_levels", ("bee_mine_glove", 4)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (1, 3, 4), "in"),), weapon=C.Rac5Weapons.BEE_MINE_GLOVE
        ),
        categories=frozenset(("weapon_level", "weapon_max_level")),
        weapon="bee_mine_glove",
        level=4,
        definition_order=186,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.BEE_MINE_GLOVE_LEVEL_5,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.BEE_MINE_GLOVE, level=5),
        Completion("weapon_levels", ("bee_mine_glove", 5)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.BEE_MINE_GLOVE,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="bee_mine_glove",
        level=5,
        definition_order=187,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.BEE_MINE_GLOVE_LEVEL_6,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.BEE_MINE_GLOVE, level=6),
        Completion("weapon_levels", ("bee_mine_glove", 6)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.BEE_MINE_GLOVE,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="bee_mine_glove",
        level=6,
        definition_order=188,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.BEE_MINE_GLOVE_LEVEL_7,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.BEE_MINE_GLOVE, level=7),
        Completion("weapon_levels", ("bee_mine_glove", 7)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.BEE_MINE_GLOVE,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="bee_mine_glove",
        level=7,
        definition_order=189,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.BEE_MINE_GLOVE_LEVEL_8,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.BEE_MINE_GLOVE, level=8),
        Completion("weapon_levels", ("bee_mine_glove", 8)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (2, 3, 4), "in"),
            ),
            weapon=C.Rac5Weapons.BEE_MINE_GLOVE,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_max_level", "challenge_mode_weapon_level")),
        weapon="bee_mine_glove",
        level=8,
        definition_order=190,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.STATIC_BARRIER_LEVEL_2,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.STATIC_BARRIER, level=2),
        Completion("weapon_levels", ("static_barrier", 2)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.STATIC_BARRIER
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="static_barrier",
        level=2,
        definition_order=191,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.STATIC_BARRIER_LEVEL_3,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.STATIC_BARRIER, level=3),
        Completion("weapon_levels", ("static_barrier", 3)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.STATIC_BARRIER
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="static_barrier",
        level=3,
        definition_order=192,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.STATIC_BARRIER_LEVEL_4,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.STATIC_BARRIER, level=4),
        Completion("weapon_levels", ("static_barrier", 4)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (1, 3, 4), "in"),), weapon=C.Rac5Weapons.STATIC_BARRIER
        ),
        categories=frozenset(("weapon_level", "weapon_max_level")),
        weapon="static_barrier",
        level=4,
        definition_order=193,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.STATIC_BARRIER_LEVEL_5,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.STATIC_BARRIER, level=5),
        Completion("weapon_levels", ("static_barrier", 5)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.STATIC_BARRIER,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="static_barrier",
        level=5,
        definition_order=194,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.STATIC_BARRIER_LEVEL_6,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.STATIC_BARRIER, level=6),
        Completion("weapon_levels", ("static_barrier", 6)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.STATIC_BARRIER,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="static_barrier",
        level=6,
        definition_order=195,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.STATIC_BARRIER_LEVEL_7,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.STATIC_BARRIER, level=7),
        Completion("weapon_levels", ("static_barrier", 7)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.STATIC_BARRIER,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="static_barrier",
        level=7,
        definition_order=196,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.STATIC_BARRIER_LEVEL_8,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.STATIC_BARRIER, level=8),
        Completion("weapon_levels", ("static_barrier", 8)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (2, 3, 4), "in"),
            ),
            weapon=C.Rac5Weapons.STATIC_BARRIER,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_max_level", "challenge_mode_weapon_level")),
        weapon="static_barrier",
        level=8,
        definition_order=197,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SHOCK_ROCKET_LEVEL_2,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SHOCK_ROCKET, level=2),
        Completion("weapon_levels", ("shock_rocket", 2)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.SHOCK_ROCKET
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="shock_rocket",
        level=2,
        definition_order=198,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SHOCK_ROCKET_LEVEL_3,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SHOCK_ROCKET, level=3),
        Completion("weapon_levels", ("shock_rocket", 3)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.SHOCK_ROCKET
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="shock_rocket",
        level=3,
        definition_order=199,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SHOCK_ROCKET_LEVEL_4,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SHOCK_ROCKET, level=4),
        Completion("weapon_levels", ("shock_rocket", 4)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (1, 3, 4), "in"),), weapon=C.Rac5Weapons.SHOCK_ROCKET
        ),
        categories=frozenset(("weapon_level", "weapon_max_level")),
        weapon="shock_rocket",
        level=4,
        definition_order=200,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SHOCK_ROCKET_LEVEL_5,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SHOCK_ROCKET, level=5),
        Completion("weapon_levels", ("shock_rocket", 5)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.SHOCK_ROCKET,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="shock_rocket",
        level=5,
        definition_order=201,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SHOCK_ROCKET_LEVEL_6,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SHOCK_ROCKET, level=6),
        Completion("weapon_levels", ("shock_rocket", 6)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.SHOCK_ROCKET,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="shock_rocket",
        level=6,
        definition_order=202,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SHOCK_ROCKET_LEVEL_7,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SHOCK_ROCKET, level=7),
        Completion("weapon_levels", ("shock_rocket", 7)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.SHOCK_ROCKET,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="shock_rocket",
        level=7,
        definition_order=203,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SHOCK_ROCKET_LEVEL_8,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SHOCK_ROCKET, level=8),
        Completion("weapon_levels", ("shock_rocket", 8)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (2, 3, 4), "in"),
            ),
            weapon=C.Rac5Weapons.SHOCK_ROCKET,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_max_level", "challenge_mode_weapon_level")),
        weapon="shock_rocket",
        level=8,
        definition_order=204,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SNIPER_MINE_LEVEL_2,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SNIPER_MINE, level=2),
        Completion("weapon_levels", ("sniper_mine", 2)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.SNIPER_MINE
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="sniper_mine",
        level=2,
        definition_order=205,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SNIPER_MINE_LEVEL_3,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SNIPER_MINE, level=3),
        Completion("weapon_levels", ("sniper_mine", 3)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.SNIPER_MINE
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="sniper_mine",
        level=3,
        definition_order=206,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SNIPER_MINE_LEVEL_4,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SNIPER_MINE, level=4),
        Completion("weapon_levels", ("sniper_mine", 4)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (1, 3, 4), "in"),), weapon=C.Rac5Weapons.SNIPER_MINE
        ),
        categories=frozenset(("weapon_level", "weapon_max_level")),
        weapon="sniper_mine",
        level=4,
        definition_order=207,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SNIPER_MINE_LEVEL_5,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SNIPER_MINE, level=5),
        Completion("weapon_levels", ("sniper_mine", 5)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.SNIPER_MINE,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="sniper_mine",
        level=5,
        definition_order=208,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SNIPER_MINE_LEVEL_6,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SNIPER_MINE, level=6),
        Completion("weapon_levels", ("sniper_mine", 6)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.SNIPER_MINE,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="sniper_mine",
        level=6,
        definition_order=209,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SNIPER_MINE_LEVEL_7,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SNIPER_MINE, level=7),
        Completion("weapon_levels", ("sniper_mine", 7)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.SNIPER_MINE,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="sniper_mine",
        level=7,
        definition_order=210,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SNIPER_MINE_LEVEL_8,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SNIPER_MINE, level=8),
        Completion("weapon_levels", ("sniper_mine", 8)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (2, 3, 4), "in"),
            ),
            weapon=C.Rac5Weapons.SNIPER_MINE,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_max_level", "challenge_mode_weapon_level")),
        weapon="sniper_mine",
        level=8,
        definition_order=211,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SCORCHER_LEVEL_2,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SCORCHER, level=2),
        Completion("weapon_levels", ("scorcher", 2)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.SCORCHER
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="scorcher",
        level=2,
        definition_order=212,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SCORCHER_LEVEL_3,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SCORCHER, level=3),
        Completion("weapon_levels", ("scorcher", 3)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.SCORCHER
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="scorcher",
        level=3,
        definition_order=213,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SCORCHER_LEVEL_4,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SCORCHER, level=4),
        Completion("weapon_levels", ("scorcher", 4)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (1, 3, 4), "in"),), weapon=C.Rac5Weapons.SCORCHER
        ),
        categories=frozenset(("weapon_level", "weapon_max_level")),
        weapon="scorcher",
        level=4,
        definition_order=214,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SCORCHER_LEVEL_5,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SCORCHER, level=5),
        Completion("weapon_levels", ("scorcher", 5)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.SCORCHER,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="scorcher",
        level=5,
        definition_order=215,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SCORCHER_LEVEL_6,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SCORCHER, level=6),
        Completion("weapon_levels", ("scorcher", 6)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.SCORCHER,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="scorcher",
        level=6,
        definition_order=216,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SCORCHER_LEVEL_7,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SCORCHER, level=7),
        Completion("weapon_levels", ("scorcher", 7)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.SCORCHER,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="scorcher",
        level=7,
        definition_order=217,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SCORCHER_LEVEL_8,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SCORCHER, level=8),
        Completion("weapon_levels", ("scorcher", 8)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (2, 3, 4), "in"),
            ),
            weapon=C.Rac5Weapons.SCORCHER,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_max_level", "challenge_mode_weapon_level")),
        weapon="scorcher",
        level=8,
        definition_order=218,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.LASER_TRACER_LEVEL_2,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.LASER_TRACER, level=2),
        Completion("weapon_levels", ("laser_tracer", 2)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.LASER_TRACER
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="laser_tracer",
        level=2,
        definition_order=219,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.LASER_TRACER_LEVEL_3,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.LASER_TRACER, level=3),
        Completion("weapon_levels", ("laser_tracer", 3)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.LASER_TRACER
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="laser_tracer",
        level=3,
        definition_order=220,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.LASER_TRACER_LEVEL_4,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.LASER_TRACER, level=4),
        Completion("weapon_levels", ("laser_tracer", 4)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (1, 3, 4), "in"),), weapon=C.Rac5Weapons.LASER_TRACER
        ),
        categories=frozenset(("weapon_level", "weapon_max_level")),
        weapon="laser_tracer",
        level=4,
        definition_order=221,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.LASER_TRACER_LEVEL_5,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.LASER_TRACER, level=5),
        Completion("weapon_levels", ("laser_tracer", 5)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.LASER_TRACER,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="laser_tracer",
        level=5,
        definition_order=222,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.LASER_TRACER_LEVEL_6,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.LASER_TRACER, level=6),
        Completion("weapon_levels", ("laser_tracer", 6)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.LASER_TRACER,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="laser_tracer",
        level=6,
        definition_order=223,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.LASER_TRACER_LEVEL_7,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.LASER_TRACER, level=7),
        Completion("weapon_levels", ("laser_tracer", 7)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.LASER_TRACER,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="laser_tracer",
        level=7,
        definition_order=224,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.LASER_TRACER_LEVEL_8,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.LASER_TRACER, level=8),
        Completion("weapon_levels", ("laser_tracer", 8)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (2, 3, 4), "in"),
            ),
            weapon=C.Rac5Weapons.LASER_TRACER,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_max_level", "challenge_mode_weapon_level")),
        weapon="laser_tracer",
        level=8,
        definition_order=225,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SUCK_CANNON_LEVEL_2,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SUCK_CANNON, level=2),
        Completion("weapon_levels", ("suck_cannon", 2)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.SUCK_CANNON
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="suck_cannon",
        level=2,
        definition_order=226,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SUCK_CANNON_LEVEL_3,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SUCK_CANNON, level=3),
        Completion("weapon_levels", ("suck_cannon", 3)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.SUCK_CANNON
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="suck_cannon",
        level=3,
        definition_order=227,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SUCK_CANNON_LEVEL_4,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SUCK_CANNON, level=4),
        Completion("weapon_levels", ("suck_cannon", 4)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (1, 3, 4), "in"),), weapon=C.Rac5Weapons.SUCK_CANNON
        ),
        categories=frozenset(("weapon_level", "weapon_max_level")),
        weapon="suck_cannon",
        level=4,
        definition_order=228,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SUCK_CANNON_LEVEL_5,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SUCK_CANNON, level=5),
        Completion("weapon_levels", ("suck_cannon", 5)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.SUCK_CANNON,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="suck_cannon",
        level=5,
        definition_order=229,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SUCK_CANNON_LEVEL_6,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SUCK_CANNON, level=6),
        Completion("weapon_levels", ("suck_cannon", 6)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.SUCK_CANNON,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="suck_cannon",
        level=6,
        definition_order=230,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SUCK_CANNON_LEVEL_7,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SUCK_CANNON, level=7),
        Completion("weapon_levels", ("suck_cannon", 7)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.SUCK_CANNON,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="suck_cannon",
        level=7,
        definition_order=231,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.SUCK_CANNON_LEVEL_8,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.SUCK_CANNON, level=8),
        Completion("weapon_levels", ("suck_cannon", 8)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (2, 3, 4), "in"),
            ),
            weapon=C.Rac5Weapons.SUCK_CANNON,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_max_level", "challenge_mode_weapon_level")),
        weapon="suck_cannon",
        level=8,
        definition_order=232,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.MOOTATOR_LEVEL_2,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.MOOTATOR, level=2),
        Completion("weapon_levels", ("mootator", 2)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.MOOTATOR
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="mootator",
        level=2,
        definition_order=233,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.MOOTATOR_LEVEL_3,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.MOOTATOR, level=3),
        Completion("weapon_levels", ("mootator", 3)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (4,), "in"),), weapon=C.Rac5Weapons.MOOTATOR
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level")),
        weapon="mootator",
        level=3,
        definition_order=234,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.MOOTATOR_LEVEL_4,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.MOOTATOR, level=4),
        Completion("weapon_levels", ("mootator", 4)),
        options=LocationOptions(
            requirements=(OptionFilter(WeaponLevelChecks, (1, 3, 4), "in"),), weapon=C.Rac5Weapons.MOOTATOR
        ),
        categories=frozenset(("weapon_level", "weapon_max_level")),
        weapon="mootator",
        level=4,
        definition_order=235,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.MOOTATOR_LEVEL_5,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.MOOTATOR, level=5),
        Completion("weapon_levels", ("mootator", 5)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.MOOTATOR,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="mootator",
        level=5,
        definition_order=236,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.MOOTATOR_LEVEL_6,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.MOOTATOR, level=6),
        Completion("weapon_levels", ("mootator", 6)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.MOOTATOR,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="mootator",
        level=6,
        definition_order=237,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.MOOTATOR_LEVEL_7,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.MOOTATOR, level=7),
        Completion("weapon_levels", ("mootator", 7)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.MOOTATOR,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_sub_max_level", "challenge_mode_weapon_level")),
        weapon="mootator",
        level=7,
        definition_order=238,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.MOOTATOR_LEVEL_8,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.MOOTATOR, level=8),
        Completion("weapon_levels", ("mootator", 8)),
        options=LocationOptions(
            requirements=(
                OptionFilter(ChallengeMode, (1, 2), "in"),
                OptionFilter(WeaponLevelChecks, (2, 3, 4), "in"),
            ),
            weapon=C.Rac5Weapons.MOOTATOR,
        ),
        categories=frozenset(("weapon_level", "challenge_mode_max_level", "challenge_mode_weapon_level")),
        weapon="mootator",
        level=8,
        definition_order=239,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.RYNO_LEVEL_2,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.RYNO, level=2),
        Completion("weapon_levels", ("ryno", 2)),
        options=LocationOptions(
            requirements=(
                OptionFilter(NgPlusItems, (1,), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.RYNO,
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level", "ng_plus_weapon_level")),
        weapon="ryno",
        level=2,
        definition_order=240,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.RYNO_LEVEL_3,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.RYNO, level=3),
        Completion("weapon_levels", ("ryno", 3)),
        options=LocationOptions(
            requirements=(
                OptionFilter(NgPlusItems, (1,), "in"),
                OptionFilter(WeaponLevelChecks, (4,), "in"),
            ),
            weapon=C.Rac5Weapons.RYNO,
        ),
        categories=frozenset(("weapon_level", "weapon_sub_max_level", "ng_plus_weapon_level")),
        weapon="ryno",
        level=3,
        definition_order=241,
    ),
    Rac5Locations(
        C.Rac5WeaponLevels.RYNO_LEVEL_4,
        C.Rac5Planets.POKITARU,
        partial(access_rule, weapon=C.Rac5Weapons.RYNO, level=4),
        Completion("weapon_levels", ("ryno", 4)),
        options=LocationOptions(
            requirements=(
                OptionFilter(NgPlusItems, (1,), "in"),
                OptionFilter(WeaponLevelChecks, (1, 3, 4), "in"),
            ),
            weapon=C.Rac5Weapons.RYNO,
        ),
        categories=frozenset(("weapon_level", "weapon_max_level", "ng_plus_weapon_level")),
        weapon="ryno",
        level=4,
        definition_order=242,
    ),
)
