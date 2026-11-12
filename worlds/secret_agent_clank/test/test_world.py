import unittest

from BaseClasses import CollectionState
from Options import OptionError
from test.general import setup_multiworld

from ..locations import ALIEN_CODE_LOCATIONS, KEYCARD_LOCATIONS
from ..world import SecretAgentClankWorld
from .bases import SecretAgentClankTestBase
from ..options import SecretAgentClankOptions
from ..universal_tracker import setup_options_from_slot_data
from ..constants import CASE_NAME_TO_OPERATIVE, SACOperatives
from ..constants.operatives import OPTIONAL_OPERATIVES
from BaseClasses import PlandoOptions
from ..options import Operatives, enabled_operatives
from ..constants import CASE_NAME_TO_INFOBOT, CASES_BY_OPERATIVE, SACCases, SACOperatives
from argparse import Namespace
from BaseClasses import MultiWorld
from test.general import gen_steps
from worlds.AutoWorld import call_all
from ..constants.ratchet_challenges import SACRatchetChallengeLocations
from ..constants import PROGRESSIVE_WRENCH
from ..locations import ALL_ALIEN_CODES_EVENT
from ..constants.planets import SACCases


class TestGeneration(SecretAgentClankTestBase):
    options = {}


class TestGenerationWithSkillPoints(SecretAgentClankTestBase):
    options = {"skill_points": "hard"}


class TestGenerationWithCutscenes(SecretAgentClankTestBase):
    options = {"all_cutscenes": True}


class TestGenerationProgressivePlanet(SecretAgentClankTestBase):
    options = {"skill_points": "hard", "infobots": "progressive_planet"}


class TestGenerationOperativeDisabled(SecretAgentClankTestBase):
    options = {
        "skill_points": "hard",
        "operatives": {"Ratchet": 1, "Clank": 1, "Gadgetbots": 1},
    }


class TestGenerationGoalQwarkOpera(SecretAgentClankTestBase):
    options = {"goal": "qwark_opera"}


class TestGenerationGoalAny(SecretAgentClankTestBase):
    options = {"goal": "any"}


class TestGenerationEverythingOn(SecretAgentClankTestBase):
    options = {
        "skill_points": "hard",
        "infobots": "progressive_planet",
        "goal": "any",
    }


class TestGenerationWithKeycards(SecretAgentClankTestBase):
    options = {"keycards_and_alien_codes": True}


class TestCombinedCollectibles(unittest.TestCase):
    def test_toggle_controls_both_categories_and_tracker_restores_it(self):
        self.assertNotIn('all_keycards', SecretAgentClankOptions.type_hints)
        self.assertNotIn('all_alien_codes', SecretAgentClankOptions.type_hints)
        for enabled in (False, True):
            mw = setup_multiworld(SecretAgentClankWorld, options={'keycards_and_alien_codes': enabled})
            names = {loc.name for loc in mw.get_locations(1)}
            for category in (KEYCARD_LOCATIONS, ALIEN_CODE_LOCATIONS):
                self.assertEqual(set(category) & names, set(category) if enabled else set())
            world = mw.worlds[1]
            slot = world.fill_slot_data()
            self.assertEqual(slot['keycards_and_alien_codes'], enabled)
            mw.re_gen_passthrough = {world.game: slot}
            setup_options_from_slot_data(world)
            self.assertEqual(world.options.keycard_checks_enabled, enabled)
            self.assertEqual(world.options.alien_code_checks_enabled, enabled)

    def test_collectibles_of_disabled_operatives_are_excluded(self):
        for disabled in (SACOperatives.GADGETBOTS, SACOperatives.QWARK):
            with self.subTest(disabled=disabled):
                operatives = {operative: int(operative != disabled) for operative in OPTIONAL_OPERATIVES}
                mw = setup_multiworld(SecretAgentClankWorld, options={
                    'keycards_and_alien_codes': True, 'operatives': operatives, 'goal': 'defeat_klunk'})
                world = mw.worlds[1]
                names = {loc.name for loc in mw.get_locations(1)}
                for category in (KEYCARD_LOCATIONS, ALIEN_CODE_LOCATIONS):
                    for loc in category.values():
                        expected = CASE_NAME_TO_OPERATIVE[loc.case] != disabled
                        self.assertEqual(loc.available(world.options), expected, loc.name)
                        self.assertEqual(loc.name in names, expected, loc.name)


class TestGoalCharacterMismatch(unittest.TestCase):
    def test_clank_cannot_be_configured(self):
        for value in ({"Clank": 0}, {"Clank": 1, "Qwark": 1}):
            with self.subTest(value=value), self.assertRaises(OptionError):
                Operatives.from_any(value).verify(SecretAgentClankWorld, "Tester", PlandoOptions.none)
        option = Operatives.from_any({"Qwark": 1})
        option.verify(SecretAgentClankWorld, "Tester", PlandoOptions.none)
        self.assertEqual(dict(option.value), {"Qwark": 1})
        world = setup_multiworld(SecretAgentClankWorld, options={"goal": "defeat_klunk", "operatives": {"Qwark": 1}}).worlds[1]
        self.assertEqual(enabled_operatives(world.options), {"Clank", "Qwark"})
        self.assertEqual(world.fill_slot_data()["operatives"], {"Clank": 1, "Qwark": 1})

    def test_qwark_opera_requires_qwark(self):
        with self.assertRaises(OptionError):
            setup_multiworld(SecretAgentClankWorld, options={"goal": "qwark_opera", "operatives": {"Qwark": 0}})

    def test_any_always_includes_defeat_klunk(self):
        mw = setup_multiworld(SecretAgentClankWorld, options={"goal": "any", "operatives": {"Special Missions": 1}})
        victories = sorted(loc.name for loc in mw.get_locations(1) if loc.name.startswith("Victory:"))
        self.assertIn("Victory: Defeat Klunk", victories)

    def test_any_creates_a_victory_for_every_achievable_goal(self):
        mw = setup_multiworld(SecretAgentClankWorld, options={
            "goal": "any", "operatives": {"Ratchet": 1, "Gadgetbots": 1, "Special Missions": 1}})
        victories = sorted(loc.name for loc in mw.get_locations(1) if loc.name.startswith("Victory:"))
        self.assertEqual(victories, ["Victory: All Alien Codes", "Victory: All Gadgetbots",
                                     "Victory: Defeat Klunk", "Victory: Ratchet Prison Escape"])

    def test_qwark_goals_split_butterqwark_from_every_qwark_case(self):
        for goal, needed in (("qwark_opera", [SACCases.MADAM_BUTTERQWARK]),
                             ("these_are_the_real_adventures_of_captain_qwark",
                              [case.name for case in CASES_BY_OPERATIVE[SACOperatives.QWARK]])):
            with self.subTest(goal=goal):
                mw = setup_multiworld(SecretAgentClankWorld, options={"goal": goal, "infobots": "cases"})
                world = mw.worlds[1]
                victory = next(loc for loc in mw.get_locations(1) if loc.name.startswith("Victory:"))
                state = CollectionState(mw)
                for item in mw.precollected_items[1]:
                    state.remove(item)
                for case in needed[:-1]:
                    state.collect(world.create_item(CASE_NAME_TO_INFOBOT[case]))
                self.assertEqual(victory.can_reach(state), len(needed) == 0)
                state.collect(world.create_item(CASE_NAME_TO_INFOBOT[needed[-1]]))
                self.assertTrue(victory.can_reach(state))

    def test_any_survives_with_only_clank(self):
        setup_multiworld(
            SecretAgentClankWorld,
            options={"goal": "any", "operatives": {"Ratchet": 1, "Gadgetbots": 1}},
        )


class TestCollectibleGoals(unittest.TestCase):
    def test_chalice_goal_without_keycard_locations(self):
        mw = setup_multiworld(SecretAgentClankWorld, options={"goal": "chalice_of_power"})
        self.assertFalse(set(KEYCARD_LOCATIONS) & {loc.name for loc in mw.get_locations(1)})

    def test_chalice_goal_generates_with_keycards(self):
        setup_multiworld(SecretAgentClankWorld, options={"goal": "chalice_of_power", "keycards_and_alien_codes": True})

    def test_alien_goal_without_code_locations(self):
        mw = setup_multiworld(SecretAgentClankWorld, options={"goal": "alien_codes"})
        self.assertFalse(set(ALIEN_CODE_LOCATIONS) & {loc.name for loc in mw.get_locations(1)})

    def test_alien_code_goal_generates_with_all_codes(self):
        setup_multiworld(SecretAgentClankWorld, options={"goal": "alien_codes", "keycards_and_alien_codes": True})

    def test_any_survives_with_only_qwark(self):
        setup_multiworld(
            SecretAgentClankWorld,
            options={"goal": "any", "operatives": {"Ratchet": 1, "Qwark": 1, "Gadgetbots": 1}},
        )


class TestUniversalTrackerRegeneration(unittest.TestCase):
    @staticmethod
    def regenerate(slot, seed):
        mw = MultiWorld(1)
        mw.game = {1: SecretAgentClankWorld.game}
        mw.player_name = {1: "Tester1"}
        mw.set_seed(seed)
        args = Namespace()
        for key, option in SecretAgentClankWorld.options_dataclass.type_hints.items():
            setattr(args, key, {1: option.from_any(option.default)})
        mw.set_options(args)
        mw.re_gen_passthrough = {SecretAgentClankWorld.game: slot}
        mw.state = CollectionState(mw)
        for step in gen_steps:
            call_all(mw, step)
        return mw

    def test_progressive_wrench_keeps_mess_hall_challenges_gated(self):
        original = setup_multiworld(SecretAgentClankWorld, seed=1, options={"progressive_wrench": True})
        mw = self.regenerate(original.worlds[1].fill_slot_data(), seed=2)
        self.assertTrue(mw.worlds[1].options.progressive_wrench)
        self.assertEqual({l.name for l in mw.get_locations(1)}, {l.name for l in original.get_locations(1)})
        location = mw.get_location(SACRatchetChallengeLocations.THE_MESS_HALL_NAILS_FOR_BREAKFAST, 1)
        state = mw.get_all_state(False)
        while state.has(PROGRESSIVE_WRENCH, 1):
            state.remove(mw.worlds[1].create_item(PROGRESSIVE_WRENCH))
        self.assertFalse(location.can_reach(state))
        state.collect(mw.worlds[1].create_item(PROGRESSIVE_WRENCH))
        self.assertTrue(location.can_reach(state))


class TestTreehouseEvent(unittest.TestCase):
    def test_treehouse_is_received_once_every_alien_code_is_reachable(self):
        for codes_enabled in (False, True):
            with self.subTest(keycards_and_alien_codes=codes_enabled):
                mw = setup_multiworld(SecretAgentClankWorld, options={"keycards_and_alien_codes": codes_enabled})
                event = mw.get_location(ALL_ALIEN_CODES_EVENT, 1)
                self.assertIsNone(event.address)
                self.assertEqual(event.item.name, SACCases.HIGH_TREEHOUSE)
                self.assertTrue(event.locked)
                state = mw.get_all_state(False)
                self.assertTrue(state.has(SACCases.HIGH_TREEHOUSE, 1))
                self.assertFalse(event.can_reach(CollectionState(mw)))
