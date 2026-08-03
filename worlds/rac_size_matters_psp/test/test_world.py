"""Registration and default-generation tests."""
from ..items import ALL_ITEMS
from ..locations import (
    ALL_LOCATIONS,
    ARMOUR_PICKUP_LOCATIONS,
    BOSS_LOCATIONS,
    GADGET_PICKUP_LOCATIONS,
    GADGET_VENDOR_LOCATIONS,
    TITANIUM_BOLT_LOCATIONS,
    WEAPON_MOD_VENDOR_LOCATIONS,
    WEAPON_VENDOR_LOCATIONS,
)
from .bases import RACSizeMatterTestBase


class TestRegistration(RACSizeMatterTestBase):
    def test_no_duplicate_location_ids(self) -> None:
        ids = [data.code for data in ALL_LOCATIONS.values()]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate location IDs")

    def test_no_duplicate_item_ids(self) -> None:
        ids = [data.code for data in ALL_ITEMS.values()]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate item IDs")

    def test_all_location_tables_non_empty(self) -> None:
        for table, label in (
            (TITANIUM_BOLT_LOCATIONS,     "titanium bolts"),
            (ARMOUR_PICKUP_LOCATIONS,     "armour pickups"),
            (BOSS_LOCATIONS,              "boss"),
            (GADGET_PICKUP_LOCATIONS,     "gadget pickups"),
            (WEAPON_VENDOR_LOCATIONS,     "weapon vendors"),
            (GADGET_VENDOR_LOCATIONS,     "gadget vendors"),
            (WEAPON_MOD_VENDOR_LOCATIONS, "weapon mod vendors"),
        ):
            self.assertTrue(table, f"{label} table is empty")


class TestDefaultGeneration(RACSizeMatterTestBase):
    """Standard WorldTestBase suite with all defaults."""

    def test_boss_location_present(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertIn("Quodrona: Defeat Otto Destruct", names)

    def test_all_titanium_bolts_present(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for name in TITANIUM_BOLT_LOCATIONS:
            self.assertIn(name, names)

    def test_all_armour_pickups_present(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for name in ARMOUR_PICKUP_LOCATIONS:
            self.assertIn(name, names)

    def test_all_vendor_locations_present(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for name in WEAPON_VENDOR_LOCATIONS:
            self.assertIn(name, names)
        for name in GADGET_VENDOR_LOCATIONS:
            self.assertIn(name, names)
        for name in WEAPON_MOD_VENDOR_LOCATIONS:
            self.assertIn(name, names)

    def test_item_count_matches_location_count(self) -> None:
        self.assertEqual(
            len(self.multiworld.itempool),
            len(self.multiworld.get_unfilled_locations(self.player)),
        )
