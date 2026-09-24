"""Single-weapon generation regressions, including deterministic option fuzzing."""
import random
import unittest

from Fill import distribute_items_restrictive
from Options import OptionError
from test.general import setup_multiworld

from ..data.weapons import WEAPON_DATA
from ..items import NG_PLUS_WEAPONS, PROGRESSIVE_WEAPON_NAME, WEAPON_DISPLAY_TO_INTERNAL
from ..world import RACSizeMatterWorld


PROJECTILES = tuple(
    name for name, internal in WEAPON_DISPLAY_TO_INTERNAL.items()
    if WEAPON_DATA[internal].is_projectile
)


class TestWeaponGeneration(unittest.TestCase):
    def test_no_available_projectile_rejected(self):
        non_projectiles = {name: 1 for name in WEAPON_DISPLAY_TO_INTERNAL if name not in PROJECTILES}
        for weapons, ng_plus in (({}, 1), (non_projectiles, 1), ({"RYNO": 1}, 0),
                                 ({**non_projectiles, "RYNO": 1}, 0)):
            with self.subTest(weapons=weapons, ng_plus=ng_plus):
                with self.assertRaisesRegex(OptionError, "at least one projectile weapon"):
                    setup_multiworld(RACSizeMatterWorld, options={
                        "enabled_weapons": weapons, "ng_plus_items": ng_plus,
                    })

    def test_single_weapon_with_default_starting_count(self):
        for weapon in PROJECTILES:
            for progressive in range(3):
                with self.subTest(weapon=weapon, progressive=progressive):
                    mw = setup_multiworld(RACSizeMatterWorld, seed=42, options={
                        "enabled_weapons": {weapon: 1}, "progressive_weapons": progressive,
                    })
                    expected = PROGRESSIVE_WEAPON_NAME[weapon] if progressive else weapon
                    weapons = [item.name for item in mw.precollected_items[1]
                               if item.name in WEAPON_DISPLAY_TO_INTERNAL
                               or item.name in PROGRESSIVE_WEAPON_NAME.values()]
                    self.assertEqual(weapons, [expected])
                    distribute_items_restrictive(mw)
                    self.assertTrue(mw.can_beat_game())
                    self.assertTrue(mw.fulfills_accessibility())

    def test_single_weapon_option_fuzz(self):
        # Every projectile, with and without precollection, across progressive modes,
        # planet starts, optional checks and Challenge Mode. Seeds reproduce failures.
        for index, weapon in enumerate(PROJECTILES):
            for case in range(30):
                seed = index * 1000 + case
                rng = random.Random(seed)
                options = {
                    "enabled_weapons": {weapon: 1},
                    "starting_weapons": case % 3,
                    "starting_gadgets": rng.randrange(9),
                    "progressive_weapons": (case // 3) % 3,
                    "progressive_mods": rng.randrange(2),
                    "progressive_armour": rng.randrange(3),
                    "random_starting_planet": rng.randrange(3),
                    "ng_plus_items": 1 if weapon in NG_PLUS_WEAPONS else rng.randrange(2),
                    "challenge_mode": rng.randrange(3),
                    "progressive_challenge_mode": rng.randrange(2),
                    "all_missions": rng.randrange(2),
                    "all_cutscenes": rng.randrange(2),
                    "armour_set_checks": rng.randrange(2),
                    "skill_points": rng.randrange(3),
                    "clank_challenges": rng.randrange(3),
                    "skyboard_challenges": rng.randrange(2),
                    "giant_clank": rng.randrange(2),
                    "enable_clank_challenge_skill_points": rng.randrange(2),
                    "enable_skyboard_challenge_skill_points": rng.randrange(2),
                    "shrink_ray_options": rng.randrange(3),
                    "weapon_level_checks": rng.randrange(5),
                    "nanotech_level_interval": rng.choice((0, 1, 5, 10, 25)),
                    "nanotech_level_max": rng.randrange(6, 76),
                }
                with self.subTest(weapon=weapon, seed=seed, options=options):
                    mw = setup_multiworld(RACSizeMatterWorld, seed=seed, options=options)
                    self.assertEqual(len(mw.itempool), len(mw.get_unfilled_locations()))
                    state = mw.get_all_state(False)
                    self.assertEqual([], [loc.name for loc in mw.get_locations() if not loc.can_reach(state)])
                    distribute_items_restrictive(mw)
                    self.assertTrue(mw.can_beat_game())
                    self.assertTrue(mw.fulfills_accessibility())
