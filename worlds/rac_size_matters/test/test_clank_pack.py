import unittest
from types import SimpleNamespace

from ..client.vendor import InventoryMixin
from ..core.options import ClientOptions
from ..items import CLANK_PACK_NAME, TRAP_ITEM_TABLE
from ..constants import Rac5Traps, Rac5VendorLocations
from .bases import RACSizeMatterTestBase


class TestClankPackEnabled(RACSizeMatterTestBase):
    options = {"clank_pack": True}

    def test_single_unlock_and_trap_available(self):
        self.assertEqual(sum(item.name == CLANK_PACK_NAME for item in self.multiworld.itempool), 1)
        self.assertIn(Rac5Traps.TRAP_NO_CLANK, TRAP_ITEM_TABLE)
        self.assertTrue(self.world.fill_slot_data()["clank_pack"])

    def test_pack_required_for_field_checks_but_not_initial_pickup(self):
        self.assertTrue(self.can_reach_location(Rac5VendorLocations.POKITARU_LACERATOR))
        self.collect_all_but(CLANK_PACK_NAME)
        self.assertFalse(self.can_reach_location("Quodrona: Defeat Otto Destruct"))
        self.collect_by_name(CLANK_PACK_NAME)
        self.assertTrue(self.can_reach_location("Quodrona: Defeat Otto Destruct"))


class TestClankPackDisabled(RACSizeMatterTestBase):
    def test_no_unlock_item_by_default(self):
        self.assertFalse(any(item.name == CLANK_PACK_NAME for item in self.multiworld.itempool))
        self.assertFalse(self.world.fill_slot_data()["clank_pack"])
        self.assertFalse(ClientOptions.from_slot_data({}).clank_pack_enabled)
        self.assertTrue(ClientOptions.from_slot_data({"clank_pack": True}).clank_pack_enabled)


class TestClankPackRandomStart(TestClankPackEnabled):
    options = {"clank_pack": True, "random_starting_planet": "unweighted"}

    def test_pack_required_for_field_checks_but_not_initial_pickup(self):
        self.collect_all_but(CLANK_PACK_NAME)
        self.assertFalse(self.can_reach_location("Quodrona: Defeat Otto Destruct"))
        self.collect_by_name(CLANK_PACK_NAME)
        self.assertTrue(self.can_reach_location("Quodrona: Defeat Otto Destruct"))


class TestClankPackInventory(unittest.TestCase):
    def test_fill_with_pack_across_starting_options(self):
        from Fill import distribute_items_restrictive
        from test.general import setup_multiworld
        from ..world import RACSizeMatterWorld

        for start in range(3):
            for equipment in (0, 1, 2):
                with self.subTest(start=start, equipment=equipment):
                    mw = setup_multiworld(RACSizeMatterWorld, seed=100 + start * 3 + equipment, options={
                        "clank_pack": True, "random_starting_planet": start,
                        "starting_weapons": equipment, "starting_gadgets": equipment,
                    })
                    distribute_items_restrictive(mw)
                    self.assertTrue(mw.can_beat_game())
                    self.assertTrue(mw.fulfills_accessibility())

    def test_receipts_rebuild_single_unlock_after_reconnect(self):
        inventory = InventoryMixin()
        inventory.game = "test"
        inventory.item_names = {"test": {109: CLANK_PACK_NAME, 607: Rac5Traps.TRAP_NO_CLANK}}
        inventory._wiring = SimpleNamespace(planet=SimpleNamespace(planet_id=1))
        inventory.items_received = [SimpleNamespace(item=607)]
        self.assertFalse(inventory._parse_inventory()["clank_pack"])
        inventory.items_received += [SimpleNamespace(item=109), SimpleNamespace(item=109)]
        snapshot = inventory._parse_inventory()
        self.assertIs(snapshot["clank_pack"], True)
        self.assertNotIn("clank_pack", snapshot["gadgets"])
        self.assertEqual(snapshot, inventory._parse_inventory())
