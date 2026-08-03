"""Tests for armour-related options: progressive armour and armour set checks."""
from ..items import ARMOUR_ITEM_TABLE, ARMOUR_PROGRESSIVE_ITEM_TABLE
from ..locations import ARMOUR_SET_CHECK_LOCATIONS
from .bases import RACSizeMatterTestBase


class TestProgressiveArmour(RACSizeMatterTestBase):
    options = {"progressive_armour": 1}

    def test_progressive_armour_items_in_pool(self) -> None:
        pool_names = [item.name for item in self.multiworld.itempool]
        self.assertTrue(
            any(name in ARMOUR_PROGRESSIVE_ITEM_TABLE for name in pool_names),
            "No progressive armour items found in pool",
        )

    def test_no_individual_armour_in_pool(self) -> None:
        pool_names = {item.name for item in self.multiworld.itempool}
        for piece in ARMOUR_ITEM_TABLE:
            self.assertNotIn(piece, pool_names)

    def test_progressive_armour_count_matches_table(self) -> None:
        pool_names = [item.name for item in self.multiworld.itempool]
        for prog_name in ARMOUR_PROGRESSIVE_ITEM_TABLE:
            self.assertGreaterEqual(
                pool_names.count(prog_name), 1,
                f"{prog_name} not found in pool",
            )

    def test_item_count_matches_location_count(self) -> None:
        self.assertEqual(
            len(self.multiworld.itempool),
            len(self.multiworld.get_unfilled_locations(self.player)),
        )


class TestNonProgressiveArmour(RACSizeMatterTestBase):
    options = {"progressive_armour": 0}

    def test_individual_armour_items_in_pool(self) -> None:
        pool_names = {item.name for item in self.multiworld.itempool}
        for piece in ARMOUR_ITEM_TABLE:
            self.assertIn(piece, pool_names)

    def test_no_progressive_armour_in_pool(self) -> None:
        pool_names = [item.name for item in self.multiworld.itempool]
        self.assertFalse(
            any(name in ARMOUR_PROGRESSIVE_ITEM_TABLE for name in pool_names),
            "Progressive armour items found in non-progressive pool",
        )

    def test_all_armour_pieces_appear_exactly_once(self) -> None:
        pool_names = [item.name for item in self.multiworld.itempool]
        for piece in ARMOUR_ITEM_TABLE:
            self.assertEqual(pool_names.count(piece), 1, f"{piece} should appear exactly once")


class TestArmourSetChecksEnabled(RACSizeMatterTestBase):
    options = {"armour_set_checks": 1}

    def test_armour_set_check_locations_present(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for name in ARMOUR_SET_CHECK_LOCATIONS:
            self.assertIn(name, names)

    def test_item_count_matches_location_count(self) -> None:
        self.assertEqual(
            len(self.multiworld.itempool),
            len(self.multiworld.get_unfilled_locations(self.player)),
        )


class TestArmourSetChecksDisabled(RACSizeMatterTestBase):
    options = {"armour_set_checks": 0}

    def test_armour_set_check_locations_excluded(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for name in ARMOUR_SET_CHECK_LOCATIONS:
            self.assertNotIn(name, names)

    def test_item_count_matches_location_count(self) -> None:
        self.assertEqual(
            len(self.multiworld.itempool),
            len(self.multiworld.get_unfilled_locations(self.player)),
        )


class TestAllOptionalChecksEnabled(RACSizeMatterTestBase):
    options = {"armour_set_checks": 1}

    def test_all_optional_locations_present(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for name in ARMOUR_SET_CHECK_LOCATIONS:
            self.assertIn(name, names)

    def test_item_count_matches_location_count(self) -> None:
        self.assertEqual(
            len(self.multiworld.itempool),
            len(self.multiworld.get_unfilled_locations(self.player)),
        )
