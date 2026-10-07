import unittest
from unittest.mock import Mock

from Options import OptionError

from test.general import setup_multiworld

from ..constants.operatives import ALL_OPERATIVES, SACOperatives
from ..constants.planets import SACCases
from ..constants.skill_point_requirements import (
    EASY_SKILL_POINTS,
    HARD_SKILL_POINTS,
    NORMAL_SKILL_POINTS,
    SKILL_POINT_DIFFICULTY,
)
from ..constants.skillpoints import SKILL_POINT_FLAGS
from ..constants.skillpoints import SACSkillPointLocations as Locations
from ..locations import LOCATION_NAME_TO_ID, SKILL_POINT_LOCATIONS
from ..options import SkillPoints
from ..locations.skill_points import select_skill_points
from ..core.skill_points import SkillPointState
from .test_runtime import Memory
from ..universal_tracker import setup_options_from_slot_data
from ..world import SecretAgentClankWorld


class SkillPointTests(unittest.TestCase):
    def test_client_only_reports_selected_skill_points(self):
        memory = Memory()
        tracker = SkillPointState(memory)
        selected = Locations.GONDOLA_ASCENT_STEEL_RAIN
        other = Locations.MAX_SECURITY_CELLS_PLAYING_WITH_FIRE
        for name in (selected, other):
            flag = SKILL_POINT_FLAGS[name]
            memory.data[flag.address] |= flag.mask
        tracker.allowed_locations = {selected}
        self.assertEqual(tracker.check(), [selected])
        tracker.confirm(selected)
        self.assertEqual(tracker.check(), [])

    def test_old_hard_slot_is_still_hard(self):
        mw = setup_multiworld(SecretAgentClankWorld, options={"skill_points": "hard"})
        world = mw.worlds[1]
        slot = world.fill_slot_data()
        slot.pop("skill_point_tiers_version")
        slot["skill_points"] = 2
        for name in ("random_skill_points", "skill_point_count", "selected_skill_points"):
            slot.pop(name)
        mw.re_gen_passthrough = {world.game: slot}
        setup_options_from_slot_data(world)
        self.assertEqual(world.options.skill_points.value, SkillPoints.option_hard)
        self.assertEqual(len(select_skill_points(world)), 65)

    def test_random_count_within_cumulative_tier(self):
        for tier, allowed in (("easy", EASY_SKILL_POINTS),
                              ("normal", EASY_SKILL_POINTS | NORMAL_SKILL_POINTS),
                              ("hard", set(SKILL_POINT_LOCATIONS))):
            mw = setup_multiworld(SecretAgentClankWorld, options={
                "skill_points": tier, "random_skill_points": True, "skill_point_count": 5})
            actual = {loc.name for loc in mw.get_locations(1)} & SKILL_POINT_LOCATIONS.keys()
            self.assertEqual(len(actual), 5)
            self.assertLessEqual(actual, allowed)

    def test_zero_disabled_and_max_count(self):
        for tier, random, count, expected in (("hard", True, 0, 0), ("hard", True, 30, 30),
                                               ("off", True, 30, 0), ("easy", False, 30, 12)):
            mw = setup_multiworld(SecretAgentClankWorld, options={
                "skill_points": tier, "random_skill_points": random, "skill_point_count": count})
            self.assertEqual(len(mw.worlds[1].selected_skill_points), expected)

    def test_insufficient_eligible_points_is_an_options_error(self):
        for overrides in ({"skill_points": "easy", "skill_point_count": 13},
                          {"skill_points": "hard", "skill_point_count": 30,
                           "operatives": {"Qwark": 1}, "goal": "qwark_opera"}):
            with self.assertRaisesRegex(OptionError, 'only .* available'):
                setup_multiworld(SecretAgentClankWorld, options={"random_skill_points": True, **overrides})

    def test_selection_is_seeded_and_tracker_does_not_reroll(self):
        mw = setup_multiworld(SecretAgentClankWorld, options={
            "skill_points": "normal", "random_skill_points": True, "skill_point_count": 5})
        world = mw.worlds[1]
        world.random.seed(101)
        first = select_skill_points(world)
        world.random.seed(101)
        self.assertEqual(select_skill_points(world), first)
        slot = world.fill_slot_data()
        mw.re_gen_passthrough = {world.game: slot}
        setup_options_from_slot_data(world)
        world.random = Mock()
        self.assertEqual(select_skill_points(world), set(slot['selected_skill_points']))
        world.random.sample.assert_not_called()

    def test_every_point_has_one_tier_a_flag_and_a_location(self):
        self.assertFalse(EASY_SKILL_POINTS & HARD_SKILL_POINTS)
        self.assertFalse(EASY_SKILL_POINTS & NORMAL_SKILL_POINTS)
        self.assertFalse(NORMAL_SKILL_POINTS & HARD_SKILL_POINTS)
        self.assertEqual((len(EASY_SKILL_POINTS), len(NORMAL_SKILL_POINTS), len(HARD_SKILL_POINTS)), (12, 33, 20))
        self.assertEqual(len(SKILL_POINT_DIFFICULTY), 65)
        self.assertEqual(SKILL_POINT_DIFFICULTY.keys(), SKILL_POINT_FLAGS.keys())
        self.assertEqual(SKILL_POINT_DIFFICULTY.keys(), SKILL_POINT_LOCATIONS.keys())

    def test_option_legacy_booleans_and_new_values(self):
        for value, expected in ((True, 3), (False, 0), ("true", 3), ("false", 0),
                                ("off", 0), ("easy", 1), ("hard", 3), ("normal", 2), (1, 1), (2, 2), (3, 3)):
            with self.subTest(value=value):
                self.assertEqual(SkillPoints.from_any(value).value, expected)

    def test_generation_tiers_and_each_disabled_operative(self):
        for tier in ("off", "easy", "normal", "hard"):
            for disabled in (None, *ALL_OPERATIVES):
                # Exercise both omitted keys and explicit YAML zeroes.
                for explicit_zero in (False, True):
                    enabled = {op: int(op != disabled) for op in ALL_OPERATIVES
                               if op != disabled or explicit_zero}
                    with self.subTest(tier=tier, disabled=disabled, zero=explicit_zero):
                        mw = setup_multiworld(SecretAgentClankWorld, options={
                            "skill_points": tier, "operatives": enabled, "goal": "any",
                        })
                        actual = {loc.name for loc in mw.get_locations(1)} & SKILL_POINT_LOCATIONS.keys()
                        expected = {name for name, location in SKILL_POINT_LOCATIONS.items()
                                    if SKILL_POINT_DIFFICULTY[name] <= SkillPoints.from_any(tier).value
                                    and disabled not in location.operatives}
                        self.assertEqual(actual, expected)

    def test_mixed_mission_and_vault_ownership(self):
        vault = SKILL_POINT_LOCATIONS[Locations.GALACTIC_BOLT_RESERVE_VAULT_VAULT]
        self.assertEqual(vault.case, SACCases.INSIDE_THE_A_EYE)
        self.assertEqual(vault.operatives, {SACOperatives.GADGETBOTS})
        casino = SKILL_POINT_LOCATIONS[Locations.HIGH_STAKES_ROOM_GADGEBOT_STANDS_ALONE]
        self.assertEqual(casino.operatives, {SACOperatives.SPECIAL_MISSIONS, SACOperatives.GADGETBOTS})
        mw = setup_multiworld(SecretAgentClankWorld, options={"skill_points": "hard"})
        location = mw.get_location(Locations.GALACTIC_BOLT_RESERVE_VAULT_VAULT, 1)
        self.assertEqual(location.parent_region.name, SACCases.INSIDE_THE_A_EYE)
        self.assertEqual(location.address, LOCATION_NAME_TO_ID[Locations.GALACTIC_BOLT_RESERVE_VAULT_VAULT])

    def test_slot_data_preserves_tier_and_tracker_reads_legacy_booleans(self):
        for value, expected in (("off", 0), ("easy", 1), ("hard", 3), (True, 3), (False, 0)):
            with self.subTest(value=value):
                mw = setup_multiworld(SecretAgentClankWorld, options={"skill_points": value})
                world = mw.worlds[1]
                slot = world.fill_slot_data()
                self.assertIs(type(slot["skill_points"]), int)
                self.assertEqual(slot["skill_points"], expected)
                if isinstance(value, bool):
                    slot["skill_points"] = value
                mw.re_gen_passthrough = {world.game: slot}
                world.options.skill_points.value = -1
                setup_options_from_slot_data(world)
                self.assertEqual(world.options.skill_points.value, expected)
