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
    options = {"clank_pack": True, "random_starting_planet": "random"}

    def test_pack_required_for_field_checks_but_not_initial_pickup(self):
        self.collect_all_but(CLANK_PACK_NAME)
        self.assertFalse(self.can_reach_location("Quodrona: Defeat Otto Destruct"))
        self.collect_by_name(CLANK_PACK_NAME)
        self.assertTrue(self.can_reach_location("Quodrona: Defeat Otto Destruct"))
