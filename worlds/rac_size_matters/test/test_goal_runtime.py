import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from NetUtils import ClientStatus

from ..client import protocol
from ..client.context import RACContext
from ..constants import Rac5CutsceneLocations
from ..core import address_maps
from ..core.core import Core
from ..core.location_checks import LocationChecks
from ..core.missions import MissionInventory
from ..core.options import ClientOptions
from ..locations import ALL_LOCATIONS
from .test_missions import FakePine


class TestGoalRuntime(unittest.TestCase):
    def test_ending_is_captured_before_loader_return_and_survives_reset(self):
        original = address_maps.GAME_ID
        try:
            for serial in address_maps.SUPPORTED_GAMES:
                with self.subTest(serial=serial):
                    address_maps.select_game(serial)
                    pine = FakePine()
                    goal = Rac5CutsceneLocations.QUODRONA_GOAL
                    completion = ALL_LOCATIONS[goal].completed
                    address = address_maps.save_address(completion.key)
                    core = SimpleNamespace(
                        pine=pine, missions=MissionInventory(pine),
                        _goal_reported=False, _initial_load_done=True, options=ClientOptions(),
                        _ap_inventory_ready=True, on_goal=Mock(), send_location=Mock(),
                        native=SimpleNamespace(tick=Mock(return_value=True)),
                    )
                    # Earlier boss stages must not complete the game.
                    pine.mem[address] = 0x3F
                    LocationChecks(core).goal()
                    core.on_goal.assert_not_called()
                    pine.mem[address] |= 0x40
                    # The native loader gate would previously skip world checks.
                    with patch('worlds.rac_size_matters.core.core.service_traps'):
                        Core.tick(core)
                    core.on_goal.assert_called_once()
                    core.send_location.assert_called_once_with(goal)
                    pine.mem[address] = 0
                    LocationChecks(core).goal()
                    core.on_goal.assert_called_once()
        finally:
            address_maps.select_game(original)

    def test_checked_otto_recovers_goal_before_loading_a_save(self):
        goal = Rac5CutsceneLocations.QUODRONA_GOAL
        core = SimpleNamespace(
            missions=MissionInventory(FakePine()), _goal_reported=False, options=ClientOptions(),
            _initial_load_done=False, _ap_inventory_ready=False,
            on_goal=Mock(), send_location=Mock(),
        )
        LocationChecks(core).goal()
        core.on_goal.assert_not_called()
        core.missions.sync_from_ap({goal})
        LocationChecks(core).goal()
        core.on_goal.assert_called_once()


class TestGoalStatus(unittest.TestCase):
    @patch('worlds.rac_size_matters.client.context.asyncio.create_task')
    def test_playing_after_goal_does_not_downgrade_or_drop_other_messages(self, create_task):
        context = SimpleNamespace(finished_game=False, send_msgs=Mock())
        goal = {'cmd': 'StatusUpdate', 'status': ClientStatus.CLIENT_GOAL}
        playing = {'cmd': 'StatusUpdate', 'status': ClientStatus.CLIENT_PLAYING}
        other = {'cmd': 'LocationChecks', 'locations': [123]}
        RACContext._on_worker_message(context, (protocol.SEND_MSGS, [goal]))
        self.assertTrue(context.finished_game)
        RACContext._on_worker_message(context, (protocol.SEND_MSGS, [playing, other]))
        self.assertEqual(context.send_msgs.call_args_list[0].args[0], [goal])
        self.assertEqual(context.send_msgs.call_args_list[1].args[0], [other])
