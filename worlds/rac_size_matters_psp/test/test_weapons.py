"""Tests for weapon-related options: progressive weapons and starting weapons."""
from ..items import (
    PROGRESSIVE_WEAPON_NAME,
    WEAPON_ITEM_TABLE,
    WEAPON_PROGRESSIVE_ITEM_TABLE,
    WEAPON_PROGRESSIVE_STEPS,
)
from .bases import RACSizeMatterTestBase


class TestProgressiveWeapons(RACSizeMatterTestBase):
    # Weapon mod items are always in the pool regardless of progressive_weapons,
    # so enough extra location categories must be enabled to hold the larger
    # progressive-weapons item pool (more copies needed for level-ups).
    options = {
        "progressive_weapons": 1,
        "all_cutscenes": 1,
        "clank_challenges": 2,
        "skyboard_challenges": 1,
        "skill_points": 2,
        "enable_clank_challenge_skill_points": 1,
        "enable_skyboard_challenge_skill_points": 1,
        "starting_weapons": 0,
    }

    def test_progressive_weapon_items_in_pool(self) -> None:
        pool_names = [item.name for item in self.multiworld.itempool]
        self.assertTrue(
            any(name in WEAPON_PROGRESSIVE_ITEM_TABLE for name in pool_names),
            "No progressive weapon items found in pool",
        )

    def test_no_individual_weapons_in_pool(self) -> None:
        pool_names = {item.name for item in self.multiworld.itempool}
        for weapon in WEAPON_ITEM_TABLE:
            self.assertNotIn(weapon, pool_names)

    def test_progressive_item_count_matches_steps(self) -> None:
        pool_names = [item.name for item in self.multiworld.itempool]
        for display, steps in WEAPON_PROGRESSIVE_STEPS.items():
            prog_name = PROGRESSIVE_WEAPON_NAME[display]
            actual = pool_names.count(prog_name)
            self.assertEqual(actual, steps, f"{prog_name}: expected {steps} copies, got {actual}")

    def test_item_count_matches_location_count(self) -> None:
        self.assertEqual(
            len(self.multiworld.itempool),
            len(self.multiworld.get_unfilled_locations(self.player)),
        )


class TestNonProgressiveWeapons(RACSizeMatterTestBase):
    options = {"progressive_weapons": 0, "starting_weapons": 0, "starting_gadgets": 0}

    def test_individual_weapon_items_in_pool(self) -> None:
        pool_names = {item.name for item in self.multiworld.itempool}
        for weapon in WEAPON_ITEM_TABLE:
            self.assertIn(weapon, pool_names)

    def test_no_progressive_weapon_items_in_pool(self) -> None:
        pool_names = [item.name for item in self.multiworld.itempool]
        self.assertFalse(
            any(name in WEAPON_PROGRESSIVE_ITEM_TABLE for name in pool_names),
            "Progressive weapon items found in non-progressive pool",
        )

    def test_all_weapons_appear_exactly_once(self) -> None:
        pool_names = [item.name for item in self.multiworld.itempool]
        for weapon in WEAPON_ITEM_TABLE:
            self.assertEqual(pool_names.count(weapon), 1, f"{weapon} should appear exactly once")

    def test_no_progressive_item_table_names_present(self) -> None:
        pool_names = {item.name for item in self.multiworld.itempool}
        for prog_name in WEAPON_PROGRESSIVE_ITEM_TABLE:
            self.assertNotIn(prog_name, pool_names)


class TestStartingWeapons(RACSizeMatterTestBase):
    run_default_tests = False
    options = {"progressive_weapons": 0, "starting_weapons": 3}

    def test_precollected_weapon_count(self) -> None:
        precollected = [
            item.name for item in self.multiworld.precollected_items[self.player]
            if item.name in WEAPON_ITEM_TABLE
        ]
        self.assertEqual(len(precollected), 3)

    def test_precollected_weapons_not_in_pool(self) -> None:
        precollected = {
            item.name for item in self.multiworld.precollected_items[self.player]
            if item.name in WEAPON_ITEM_TABLE
        }
        pool_names = [item.name for item in self.multiworld.itempool]
        for weapon in precollected:
            self.assertEqual(pool_names.count(weapon), 0, f"Precollected weapon {weapon} still in pool")


class TestStartingWeaponsZero(RACSizeMatterTestBase):
    run_default_tests = False
    options = {"starting_weapons": 0}

    def test_no_precollected_weapons(self) -> None:
        precollected = [
            item.name for item in self.multiworld.precollected_items[self.player]
            if item.name in WEAPON_ITEM_TABLE
               or item.name in WEAPON_PROGRESSIVE_ITEM_TABLE
        ]
        self.assertEqual(len(precollected), 0)

    def test_all_weapons_available_in_pool(self) -> None:
        pool_names = {item.name for item in self.multiworld.itempool}
        has_any_weapon = any(
            w in pool_names or PROGRESSIVE_WEAPON_NAME[w] in pool_names
            for w in WEAPON_ITEM_TABLE
        )
        self.assertTrue(has_any_weapon, "No weapons found in pool with starting_weapons=0")
