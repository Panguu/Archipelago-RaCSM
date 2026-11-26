import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ..client.command_processor import RACCommandProcessor
from ..client.worker import GameWorker
from ..constants import Rac5CutsceneLocations
from ..core.location_checks import CLANK_CHALLENGE_NAMES
from ..core.locations.skill_point_locations import TIERED_SKILL_POINTS
from . import test_goals


class GoalCommandTests(unittest.TestCase):
    def output(self, worker):
        with patch('worlds.rac_size_matters.client.worker.logger.info') as log:
            GameWorker.cmd_goal(worker)
        return [call.args[0] for call in log.call_args_list]

    def worker(self, data, allowed=()):
        return SimpleNamespace(slot=1, slot_data=data, finished_game=False,
                               _wiring=test_goals.ClientGoalTests().core(data, allowed))

    def test_parser_dispatches_goal(self):
        processor = RACCommandProcessor(SimpleNamespace(call_worker=Mock()))
        self.assertTrue(processor('/goal'))
        processor.ctx.call_worker.assert_called_once_with('cmd_goal')

    def test_single_goal_and_completion_are_read_only(self):
        worker = self.worker({})
        self.assertEqual(self.output(worker), ['Defeat Otto Destruct: incomplete'])
        worker._wiring.missions.completed.add(Rac5CutsceneLocations.QUODRONA_GOAL)
        self.assertEqual(self.output(worker), ['Defeat Otto Destruct: completed'])
        worker._wiring.on_goal.assert_not_called()
        worker._wiring.send_location.assert_not_called()

    def test_pick_and_mix_count_and_seed_scoped_completion(self):
        skill = next(iter(TIERED_SKILL_POINTS))
        clank = next(iter(CLANK_CHALLENGE_NAMES))
        worker = self.worker({'goal': 3, 'pick_and_mix_goals': [
            'defeat_otto', 'all_skill_points', 'all_clank_challenges']}, {skill, clank})
        worker._wiring.skill_points.completed.add(skill)
        self.assertEqual(self.output(worker), [
            'Goals: 1/3 completed', 'Defeat Otto Destruct: incomplete',
            'All Skill Points: completed', 'All Clank Challenges: incomplete'])
        worker._wiring.clank.completed.add(clank)
        self.assertEqual(self.output(worker)[0], 'Goals: 2/3 completed')
        worker.finished_game = True
        self.assertEqual(self.output(worker), [
            'Goals: 3/3 completed', 'Defeat Otto Destruct: completed',
            'All Skill Points: completed', 'All Clank Challenges: completed'])

    def test_only_selected_goal_is_shown_and_victory_stays_complete(self):
        worker = self.worker({'goal': 2})
        self.assertEqual(self.output(worker), ['All Clank Challenges: incomplete'])
        worker._wiring._goal_reported = True
        self.assertEqual(self.output(worker), ['All Clank Challenges: completed'])

    def test_no_slot_does_not_read_game(self):
        self.assertEqual(self.output(SimpleNamespace(slot=None)),
                         ['Connect to an Archipelago slot to see goal status.'])
