import unittest

from test.general import gen_steps, setup_multiworld
from worlds.AutoWorld import call_all

from ..constants import (
    ALL_CASES,
    CASE_NAME_TO_CASE,
    CASE_NAME_TO_INFOBOT,
    PROGRESSIVE_PLANET_ITEM_NAME,
    SACCases,
)
from ..core.inventories import resolve_owned_cases
from ..core.patches import StartingCase
from ..world import SecretAgentClankWorld


class StartingCaseTests(unittest.TestCase):
    def test_starting_case_configuration_rejects_disabled_or_unknown_cases(self):
        config = StartingCase()
        for name in ("unknown", SACCases.BOLTAIRE_MUSEUM):
            with self.subTest(name=name), self.assertRaises(ValueError):
                config.configure({"starting_case": name, "operatives": {"Qwark": 1}})
        config.configure({"starting_case": SACCases.SUCK_AND_JIVE, "operatives": {"Qwark": 1}})
        self.assertEqual(config.case_name, SACCases.SUCK_AND_JIVE)
        config.configure({})
        self.assertIsNone(config.case_name)

    def test_tracker_restores_saved_start_instead_of_rerolling(self):
        original = setup_multiworld(SecretAgentClankWorld, seed=812)
        saved = original.worlds[1].fill_slot_data()
        restored = setup_multiworld(SecretAgentClankWorld, seed=456, steps=())
        restored.re_gen_passthrough = {SecretAgentClankWorld.game: saved}
        for step in gen_steps:
            call_all(restored, step)
        self.assertEqual(restored.worlds[1].starting_case, saved["starting_case"])
        self.assertIn(CASE_NAME_TO_INFOBOT[saved["starting_case"]],
                      [item.name for item in restored.precollected_items[1]])

    def test_two_random_starts_include_a_clank_case(self):
        by_name = {case.name: case for case in ALL_CASES}
        pairs = set()
        for mode in ("cases", "progressive_planet"):
            for seed in range(10):
                with self.subTest(mode=mode, seed=seed):
                    world = setup_multiworld(SecretAgentClankWorld, seed=seed, options={
                        "operatives": {"Qwark": 1}, "goal": "qwark_opera", "infobots": mode}).worlds[1]
                    pair = (world.starting_case, world.second_starting_case)
                    self.assertNotEqual(*pair)
                    self.assertIn("Clank", {by_name[name].operative for name in pair})
                    for name in pair:
                        self.assertTrue(world.multiworld.state.can_reach(name, "Region", 1))
                    pairs.add(pair)
        self.assertGreater(len(pairs), 5)

    def test_random_start_respects_characters_and_access_in_every_mode(self):
        observed = set()
        for mode in ("cases", "progressive_planet"):
            for seed in range(8):
                mw = setup_multiworld(SecretAgentClankWorld, seed=seed, options={
                    "operatives": {"Ratchet": 1, "Qwark": 1, "Gadgetbots": 1},
                    "goal": "qwark_opera", "infobots": mode, "all_missions": "all"})
                world = mw.worlds[1]
                name = world.starting_case
                observed.add(name)
                case = next(case for case in ALL_CASES if case.name == name)
                self.assertIn(case.operative, ("Ratchet", "Clank", "Qwark", "Gadgetbots"))
                self.assertTrue(mw.state.can_reach(name, "Region", 1))
                self.assertEqual(world.fill_slot_data()["starting_case"], name)
        self.assertGreater(len(observed), 1)

    def test_progressive_planet_starts_with_planets_not_case_files(self):
        for seed in range(8):
            with self.subTest(seed=seed):
                mw = setup_multiworld(SecretAgentClankWorld, seed=seed, options={
                    "operatives": {"Ratchet": 1, "Qwark": 1, "Gadgetbots": 1}, "infobots": "progressive_planet"})
                world = mw.worlds[1]
                names = [item.name for item in mw.precollected_items[1]]
                pool = [item.name for item in mw.itempool if item.player == 1]
                for case_name in (world.starting_case, world.second_starting_case):
                    planet = CASE_NAME_TO_CASE[case_name].planet
                    self.assertTrue(mw.state.can_reach(case_name, "Region", 1))
                    needed = world.planet_cases[planet].index(case_name) + 1
                    self.assertGreaterEqual(names.count(PROGRESSIVE_PLANET_ITEM_NAME[planet]), needed)
                    self.assertNotIn(CASE_NAME_TO_INFOBOT[case_name], names)
                for planet, cases in world.planet_cases.items():
                    item = PROGRESSIVE_PLANET_ITEM_NAME[planet]
                    self.assertEqual(names.count(item) + pool.count(item), len(cases))

    def test_progressive_planets_unlock_only_their_own_cases(self):
        for seed in range(6):
            with self.subTest(seed=seed):
                mw = setup_multiworld(SecretAgentClankWorld, seed=seed, options={"infobots": "progressive_planet"})
                world = mw.worlds[1]
                names = [item.name for item in mw.precollected_items[1]]
                starts = (world.starting_case, world.second_starting_case)
                owned = resolve_owned_cases(names, planet_cases=world.planet_cases)
                expected = {name for planet, cases in world.planet_cases.items()
                            for name in cases[:max((cases.index(start) + 1 for start in starts if start in cases),
                                                   default=0)]}
                self.assertEqual(owned, expected)
                self.assertLessEqual(len(owned), 2 * max(len(cases) for cases in world.planet_cases.values()))
