import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from test.general import setup_multiworld

from Options import OptionError

from ..constants import Rac5CutsceneLocations
from ..core.location_checks import CLANK_CHALLENGE_NAMES, LocationChecks
from ..core.locations.skill_point_locations import TIERED_SKILL_POINTS
from ..core.options import ClientOptions
from ..goals import GOAL_EVENTS
from ..locations.shared import required_clank_challenges, required_skill_points
from ..options import Goal, racsm_option_groups
from ..universal_tracker import setup_options_from_slot_data
from ..world import RACSizeMatterWorld

GOAL_EVENT_NAMES = frozenset(GOAL_EVENTS.values())


def victories(mw):
    return [location.name for location in mw.get_locations(1) if location.name in GOAL_EVENT_NAMES]


class GoalGenerationTests(unittest.TestCase):
    def test_option_group(self):
        self.assertIn("RACSM Goal Options", [group.name for group in racsm_option_groups])

    def test_single_goals_create_one_victory(self):
        for goal, options in (
            ("defeat_otto", {}),
            ("all_skill_points", {"skill_points": "easy"}),
            ("all_clank_challenges", {"clank_challenges": "all"}),
        ):
            with self.subTest(goal=goal):
                mw = setup_multiworld(RACSizeMatterWorld, options={"goal": goal, **options})
                self.assertEqual(victories(mw), [GOAL_EVENTS[Goal.from_any(goal).value]])
                self.assertTrue(mw.completion_condition[1](mw.get_all_state()))

    def test_pick_and_mix_creates_one_victory(self):
        mw = setup_multiworld(RACSizeMatterWorld, options={
            "goal": "pick_and_mix", "pick_and_mix_goals": {"defeat_otto", "all_skill_points", "all_clank_challenges"},
            "skill_points": "hard",
        })
        self.assertEqual(victories(mw), [GOAL_EVENTS[Goal.option_pick_and_mix]])
        self.assertTrue(mw.completion_condition[1](mw.get_all_state()))

    def test_pick_and_mix_requires_every_selected_goal(self):
        mw = setup_multiworld(RACSizeMatterWorld, options={
            "goal": "pick_and_mix", "pick_and_mix_goals": {"defeat_otto", "all_skill_points"},
            "skill_points": "easy",
        })
        victory = mw.get_location(GOAL_EVENTS[Goal.option_pick_and_mix], 1)
        state = mw.get_all_state()
        self.assertTrue(victory.can_reach(state))
        state.remove(mw.worlds[1].create_item("Infobot: Quodrona"))
        self.assertFalse(victory.can_reach(state))

    def test_invalid_goals_fail(self):
        for options in (
            {"goal": "pick_and_mix"},
            {"goal": "all_skill_points", "skill_points": "off"},
            {"goal": "all_clank_challenges", "clank_challenges": "off"},
            {"goal": "pick_and_mix", "pick_and_mix_goals": {"all_skill_points"}, "skill_points": "off"},
        ):
            with self.subTest(options=options), self.assertRaises(OptionError):
                setup_multiworld(RACSizeMatterWorld, options=options)

    def test_pick_and_mix_ignored_without_pick_and_mix_goal(self):
        mw = setup_multiworld(RACSizeMatterWorld, options={
            "goal": "defeat_otto", "pick_and_mix_goals": {"all_skill_points"}})
        self.assertEqual(victories(mw), [GOAL_EVENTS[Goal.option_defeat_otto]])

    def test_tracker_restores_goals(self):
        mw = setup_multiworld(RACSizeMatterWorld, options={
            "goal": "pick_and_mix", "pick_and_mix_goals": {"all_skill_points"}, "skill_points": "easy"})
        world = mw.worlds[1]
        slot = world.fill_slot_data()
        mw.re_gen_passthrough = {world.game: slot}
        world.options.goal.value = Goal.option_defeat_otto
        world.options.pick_and_mix_goals.value = set()
        setup_options_from_slot_data(world)
        self.assertEqual(world.options.goal.value, Goal.option_pick_and_mix)
        self.assertEqual(world.options.pick_and_mix_goals.value, {"all_skill_points"})


class ClientGoalTests(unittest.TestCase):
    def core(self, slot_data, allowed):
        return SimpleNamespace(
            options=ClientOptions.from_slot_data(slot_data), _goal_reported=False, on_goal=Mock(),
            send_location=Mock(), _initial_load_done=False, _ap_inventory_ready=False,
            native=SimpleNamespace(allowed_locations=set(allowed)),
            missions=SimpleNamespace(completed=set()),
            skill_points=SimpleNamespace(completed=set()),
            clank=SimpleNamespace(completed=set()),
        )

    def test_slot_data_goals(self):
        self.assertEqual(ClientOptions.from_slot_data({}).goals, (Goal.option_defeat_otto,))
        self.assertEqual(ClientOptions.from_slot_data({"goal": Goal.option_all_skill_points}).goals,
                         (Goal.option_all_skill_points,))
        self.assertEqual(ClientOptions.from_slot_data({
            "goal": Goal.option_pick_and_mix, "pick_and_mix_goals": ["all_clank_challenges", "defeat_otto"],
        }).goals, (Goal.option_defeat_otto, Goal.option_all_clank_challenges))
        self.assertEqual(ClientOptions.from_slot_data({"goal": Goal.option_pick_and_mix}).goals, ())

    def test_pick_and_mix_requires_every_goal_and_sends_once(self):
        skill_points = set(TIERED_SKILL_POINTS) - {next(iter(TIERED_SKILL_POINTS))}
        challenges = set(list(CLANK_CHALLENGE_NAMES)[:4])
        core = self.core({
            "goal": Goal.option_pick_and_mix,
            "pick_and_mix_goals": ["defeat_otto", "all_skill_points", "all_clank_challenges"],
        }, {*skill_points, *challenges})
        checks = LocationChecks(core)
        core.skill_points.completed |= skill_points
        core.clank.completed |= challenges
        checks.goal()
        core.on_goal.assert_not_called()
        core.missions.completed.add(Rac5CutsceneLocations.QUODRONA_GOAL)
        checks.goal()
        checks.goal()
        core.on_goal.assert_called_once()

    def test_single_goal_ignores_otto(self):
        challenges = set(list(CLANK_CHALLENGE_NAMES)[:4])
        core = self.core({"goal": Goal.option_all_clank_challenges}, challenges)
        core.missions.completed.add(Rac5CutsceneLocations.QUODRONA_GOAL)
        LocationChecks(core).goal()
        core.on_goal.assert_not_called()
        core.clank.completed |= challenges
        LocationChecks(core).goal()
        core.on_goal.assert_called_once()

    def test_only_seed_locations_count(self):
        required = set(list(TIERED_SKILL_POINTS)[:3])
        core = self.core({"goal": Goal.option_all_skill_points}, required)
        core.skill_points.completed |= required
        LocationChecks(core).goal()
        core.on_goal.assert_called_once()

    def test_empty_selection_cannot_win(self):
        core = self.core({"goal": Goal.option_pick_and_mix}, ())
        core.missions.completed.add(Rac5CutsceneLocations.QUODRONA_GOAL)
        LocationChecks(core).goal()
        core.on_goal.assert_not_called()

    def test_generation_and_client_agree_on_required_sets(self):
        mw = setup_multiworld(RACSizeMatterWorld, options={
            "goal": "pick_and_mix", "pick_and_mix_goals": {"all_skill_points", "all_clank_challenges"},
            "skill_points": "hard", "clank_challenges": "all", "enable_hig_treehouse": 1,
        })
        options = mw.worlds[1].options
        pool = {location.name for location in mw.get_locations(1)}
        self.assertEqual(set(required_skill_points(options)), TIERED_SKILL_POINTS & pool)
        self.assertEqual(set(required_clank_challenges(options)), CLANK_CHALLENGE_NAMES & pool)
