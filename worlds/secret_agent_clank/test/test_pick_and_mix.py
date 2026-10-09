import unittest
from itertools import combinations
from types import SimpleNamespace
from unittest.mock import Mock

from Options import OptionError
from test.general import setup_multiworld

from ..constants.missions import MISSION_COMPLETE_NAME
from ..constants.planets import SACCases
from ..core.core import Core
from ..options import Goal, PickAndMixGoals, SecretAgentClankOptions, sac_option_groups
from ..universal_tracker import setup_options_from_slot_data
from ..world import SecretAgentClankWorld
from .test_runtime import Memory


class QwarkGoalDetectionTests(unittest.TestCase):
    def test_qwark_opera_is_butterqwark_and_real_adventures_is_every_qwark_case(self):
        from ..constants import CASES_BY_OPERATIVE, SACOperatives
        core = Core(Memory())
        core.on_goal = Mock()
        core.missions._reported.add(MISSION_COMPLETE_NAME[SACCases.MADAM_BUTTERQWARK])
        core.goal = Goal.option_these_are_the_real_adventures_of_captain_qwark
        core._check_goal()
        core.on_goal.assert_not_called()
        core.goal = Goal.option_qwark_opera
        core._check_goal()
        core.on_goal.assert_called_once()
        core._goal_sent = False
        core.goal = Goal.option_these_are_the_real_adventures_of_captain_qwark
        core.missions._reported.update(MISSION_COMPLETE_NAME[case.name]
                                       for case in CASES_BY_OPERATIVE[SACOperatives.QWARK])
        core._check_goal()
        self.assertEqual(core.on_goal.call_count, 2)

    def test_qwark_opera_detects_the_butterqwark_mission(self):
        from ..constants.missions import SACMissionLocations
        core = Core(Memory())
        core.on_goal = Mock()
        core.goal = Goal.option_qwark_opera
        core.missions.completed[SACMissionLocations.MADAM_BUTTERQWARK_QWARKOGRAPHY_CH_3] = True
        core._check_goal()
        core.on_goal.assert_called_once()


class PickAndMixTests(unittest.TestCase):
    def test_option_layout_has_dropdown_and_no_toggle(self):
        self.assertEqual(Goal.from_any('pick_and_mix').value, Goal.option_pick_and_mix)
        self.assertNotIn('pick_and_mix', SecretAgentClankOptions.type_hints)
        self.assertEqual(sac_option_groups[0].options, [Goal, PickAndMixGoals])

    def test_each_pair_generates_one_combined_victory(self):
        for goals in combinations(sorted(PickAndMixGoals.valid_keys), 2):
            with self.subTest(goals=goals):
                mw = setup_multiworld(SecretAgentClankWorld, options={
                    'goal': 'pick_and_mix', 'pick_and_mix_goals': set(goals)})
                victories = [loc for loc in mw.get_locations(1) if loc.name.startswith('Victory:')]
                self.assertEqual([loc.name for loc in victories], ['Victory: Pick and Mix'])

    def test_empty_and_disabled_goals_fail(self):
        with self.assertRaisesRegex(OptionError, 'at least one'):
            setup_multiworld(SecretAgentClankWorld, options={'goal': 'pick_and_mix'})
        for name, operative in (('defeat_klunk', 'Clank'), ('qwark_opera', 'Qwark'),
                                ('all_gadgetbots', 'Gadgetbots'), ('ratchet_prison_escape', 'Ratchet')):
            with self.subTest(goal=name), self.assertRaises(OptionError):
                setup_multiworld(SecretAgentClankWorld, options={
                    'goal': 'pick_and_mix', 'pick_and_mix_goals': {name}, 'operatives': {operative: 0}})

    def test_dropdown_and_tracker_restore_selected_goals(self):
        mw = setup_multiworld(SecretAgentClankWorld, options={
            'goal': 'pick_and_mix', 'pick_and_mix_goals': {'qwark_opera'}, 'operatives': {'Qwark': 1}})
        world = mw.worlds[1]
        slot = world.fill_slot_data()
        mw.re_gen_passthrough = {world.game: slot}
        world.options.goal.value = Goal.option_defeat_klunk
        world.options.pick_and_mix_goals.value = set()
        setup_options_from_slot_data(world)
        self.assertEqual(world.options.goal.value, Goal.option_pick_and_mix)
        self.assertEqual(world.options.pick_and_mix_goals.value, {'qwark_opera'})
        # Seeds generated with the former checkbox still regenerate correctly.
        slot['goal'] = Goal.option_defeat_klunk
        slot['pick_and_mix'] = True
        setup_options_from_slot_data(world)
        self.assertEqual(world.options.goal.value, Goal.option_pick_and_mix)
        mw = setup_multiworld(SecretAgentClankWorld, options={
            'goal': 'defeat_klunk', 'pick_and_mix_goals': {'alien_codes'}})
        self.assertEqual([loc.name for loc in mw.get_locations(1) if loc.name.startswith('Victory:')],
                         ['Victory: Defeat Klunk'])

    def test_client_requires_every_selected_goal_and_sends_once(self):
        core = Core(Memory())
        core.pick_and_mix_goals = (Goal.option_defeat_klunk, Goal.option_chalice_of_power)
        core.on_goal = Mock()
        core.keycards.chalice_collected = True
        core._check_goal()
        core.on_goal.assert_not_called()
        core.missions._reported.add(MISSION_COMPLETE_NAME[SACCases.KLUNKS_LAIR])
        core._check_goal()
        core._check_goal()
        core.on_goal.assert_called_once()

    def test_all_six_conditions_and_missing_condition(self):
        core = Core(Memory())
        core.pick_and_mix_goals = tuple(Goal.from_any(name).value for name in PickAndMixGoals.valid_keys)
        core.on_goal = Mock()
        core.missions._reported.update(MISSION_COMPLETE_NAME.values())
        core.ratchet_challenges.completed = dict.fromkeys(core.ratchet_challenges.names, True)
        core.keycards.chalice_collected = True
        core.alien_codes = SimpleNamespace(all_found=False)
        core._check_goal()
        core.on_goal.assert_not_called()
        core.alien_codes.all_found = True
        core._check_goal()
        core.on_goal.assert_called_once()

    def test_empty_client_selection_cannot_win(self):
        core = Core(Memory())
        core.pick_and_mix_goals = ()
        core.on_goal = Mock()
        core._check_goal()
        core.on_goal.assert_not_called()

    def test_generation_requires_both_goal_rules(self):
        from ..constants.clank_gadgets import SACClankGadgets
        mw = setup_multiworld(SecretAgentClankWorld, options={
            'goal': 'pick_and_mix', 'pick_and_mix_goals': {'defeat_klunk', 'alien_codes'}})
        state = mw.get_all_state(False)
        self.assertTrue(mw.completion_condition[1](state))
        # Alien Codes require these even when Klunk is reachable.
        state.remove(mw.worlds[1].create_item(SACClankGadgets.THERM_OPTIC_SHADES))
        self.assertFalse(mw.get_location('Victory: Pick and Mix', 1).can_reach(state))
