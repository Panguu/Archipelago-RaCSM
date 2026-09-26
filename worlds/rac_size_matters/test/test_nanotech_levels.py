"""Tests for Nanotech Levels 51-75 only existing in Challenge Mode."""
from ..constants.nanotech_levels import Rac5NanotechLevels
from .bases import ALL_PLANETS, RACSizeMatterTestBase


def _location_names(test: RACSizeMatterTestBase) -> set[str]:
    return {location.name for location in test.multiworld.get_locations(test.player)}


class TestNanotechLevelsNoChallengeMode(RACSizeMatterTestBase):
    options = {"nanotech_level_interval": 5, "nanotech_level_max": 75, "challenge_mode": 0}

    def test_max_clamped_to_50(self) -> None:
        self.assertEqual(self.world.options.nanotech_level_max.value, 50)

    def test_levels_above_50_do_not_exist(self) -> None:
        names = _location_names(self)
        self.assertIn(Rac5NanotechLevels.LEVEL_50, names)
        self.assertNotIn(Rac5NanotechLevels.LEVEL_55, names)
        self.assertNotIn(Rac5NanotechLevels.LEVEL_75, names)


class TestNanotechLevelsChallengeMode(RACSizeMatterTestBase):
    options = {"nanotech_level_interval": 5, "nanotech_level_max": 75, "challenge_mode": 1}

    def test_levels_above_50_exist(self) -> None:
        self.assertEqual(self.world.options.nanotech_level_max.value, 75)
        names = _location_names(self)
        self.assertIn(Rac5NanotechLevels.LEVEL_55, names)
        self.assertIn(Rac5NanotechLevels.LEVEL_75, names)


class TestNanotechLevelsProgressiveChallengeMode(RACSizeMatterTestBase):
    options = {
        "nanotech_level_interval": 5,
        "nanotech_level_max": 75,
        "nanotech_experience_multiplier": 10,
        "challenge_mode": 1,
        "progressive_challenge_mode": 1,
    }

    def test_levels_above_50_need_progressive_challenge_mode(self) -> None:
        self.collect_by_name(ALL_PLANETS)
        self.assertTrue(self.can_reach_location(Rac5NanotechLevels.LEVEL_50))
        self.assertFalse(self.can_reach_location(Rac5NanotechLevels.LEVEL_55))
        self.collect_by_name("Progressive Challenge Mode")
        self.assertTrue(self.can_reach_location(Rac5NanotechLevels.LEVEL_55))
