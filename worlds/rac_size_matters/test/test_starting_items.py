"""Tests for starting item options: starting gadgets and starting bolts."""
from ..items import GADGET_ITEM_TABLE
from .bases import RACSizeMatterTestBase


class TestStartingGadgets(RACSizeMatterTestBase):
    run_default_tests = False
    options = {"starting_gadgets": 2}

    def test_precollected_gadget_count(self) -> None:
        precollected = [
            item.name for item in self.multiworld.precollected_items[self.player]
            if item.name in GADGET_ITEM_TABLE
        ]
        self.assertEqual(len(precollected), 2)

    def test_precollected_gadgets_not_in_pool(self) -> None:
        precollected = {
            item.name for item in self.multiworld.precollected_items[self.player]
            if item.name in GADGET_ITEM_TABLE
        }
        pool_names = [item.name for item in self.multiworld.itempool]
        for gadget in precollected:
            self.assertEqual(pool_names.count(gadget), 0, f"Precollected gadget {gadget} still in pool")


class TestStartingGadgetsZero(RACSizeMatterTestBase):
    run_default_tests = False
    options = {"starting_gadgets": 0}

    def test_no_precollected_gadgets(self) -> None:
        precollected = [
            item.name for item in self.multiworld.precollected_items[self.player]
            if item.name in GADGET_ITEM_TABLE
        ]
        self.assertEqual(len(precollected), 0)

    def test_all_gadgets_in_pool(self) -> None:
        pool_names = {item.name for item in self.multiworld.itempool}
        for gadget in GADGET_ITEM_TABLE:
            self.assertIn(gadget, pool_names)


class TestStartingGadgetsAll(RACSizeMatterTestBase):
    run_default_tests = False
    options = {"starting_gadgets": 8}

    def test_all_gadgets_precollected(self) -> None:
        precollected = {
            item.name for item in self.multiworld.precollected_items[self.player]
            if item.name in GADGET_ITEM_TABLE
        }
        self.assertEqual(len(precollected), len(GADGET_ITEM_TABLE))

    def test_no_gadgets_in_pool(self) -> None:
        pool_names = {item.name for item in self.multiworld.itempool}
        for gadget in GADGET_ITEM_TABLE:
            self.assertNotIn(gadget, pool_names)

    def test_item_count_matches_location_count(self) -> None:
        self.assertEqual(
            len(self.multiworld.itempool),
            len(self.multiworld.get_unfilled_locations(self.player)),
        )


class TestStartingBoltsZero(RACSizeMatterTestBase):
    run_default_tests = False
    options = {"starting_bolts": 0}

    def test_no_bolt_precollected(self) -> None:
        precollected_names = [item.name for item in self.multiworld.precollected_items[self.player]]
        self.assertNotIn("Bolts", precollected_names)


class TestStartingBoltsNonZero(RACSizeMatterTestBase):
    run_default_tests = False
    options = {"starting_bolts": 1000}

    def test_bolt_item_precollected(self) -> None:
        precollected_names = [item.name for item in self.multiworld.precollected_items[self.player]]
        self.assertIn("Bolts", precollected_names)
