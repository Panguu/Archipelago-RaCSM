import unittest
from collections import Counter
from types import SimpleNamespace

from ..constants import Rac5CutsceneLocations, Rac5Gadgets, Rac5Planets
from ..locations import ALL_LOCATIONS

_FREE_CATEGORIES = {"skyboard_item", "extra_skyboard", "skyboard_challenge_skill_point"}


def _is_free(location) -> bool:
    return (
        bool(location.categories & _FREE_CATEGORIES)
        or "Rematch" in location.name
        or location.name == Rac5CutsceneLocations.OUTPOST_OMEGA_ENTER
    )


class TestOutpostRules(unittest.TestCase):
    def test_facility_and_vendor_checks_require_shrink_ray(self):
        world = SimpleNamespace(player=1, options=SimpleNamespace(progressive_challenge_mode=False))
        checked = 0
        for location in ALL_LOCATIONS.values():
            if location.planet != Rac5Planets.OUTPOST_OMEGA or _is_free(location):
                continue
            with self.subTest(location=location.name):
                rule = location.rule(world).resolve(world)
                items = Counter({name: 1 for name in rule.item_dependencies()})
                items[Rac5Gadgets.SHRINK_RAY] = 0
                state = SimpleNamespace(prog_items={1: items})
                self.assertFalse(rule(state))
                items[Rac5Gadgets.SHRINK_RAY] = 1
                self.assertTrue(rule(state))
                checked += 1
        self.assertEqual(checked, 10)

    def test_skyboard_and_entry_checks_do_not_require_shrink_ray(self):
        world = SimpleNamespace(player=1, options=SimpleNamespace(progressive_challenge_mode=False))
        for location in ALL_LOCATIONS.values():
            if location.planet != Rac5Planets.OUTPOST_OMEGA or not _is_free(location):
                continue
            with self.subTest(location=location.name):
                rule = location.rule(world).resolve(world)
                self.assertTrue(rule(SimpleNamespace(prog_items={1: Counter()})))
