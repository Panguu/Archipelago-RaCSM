import unittest

from ..client.item_names import canonical_item_name
from ..constants.weapons import EQUIPMENT_DISPLAY_TO_INTERNAL, SACRatchetWeapons
from ..constants.weapon_progression import PROGRESSIVE_TO_INTERNAL
from ..core.core import Core
from ..core.inventories.weapons import WEAPON_ORDER
from .test_runtime import Memory


class ItemNameCompatibilityTests(unittest.TestCase):
    def test_old_ratchet_receipts_grant_each_native_weapon(self):
        for internal in ("blaster", "shardgun", "beemineglove", "walloper", "minelauncher",
                         "shockrocket", "plasmawhip", "porkbomb", "ryno"):
            with self.subTest(weapon=internal):
                names = [canonical_item_name("Unlock: Ratchet " + internal)]
                memory = Memory()
                core = Core(memory)
                core.case.ratchet_items.set_base(0x100000)
                core.apply_inventory(ratchet={slot: display in names for display, slot in
                                              EQUIPMENT_DISPLAY_TO_INTERNAL.items()},
                                     clank={}, received_names=names)
                core._reapply_all_inventories()
                slot = WEAPON_ORDER.index(internal)
                self.assertEqual(memory.read_int32(0x100000 + slot * 0x74 + 0x70), 1)
                self.assertTrue(core._entitlements()[slot])
                self.assertEqual(core.case.ratchet_items.check(), [])

    def test_old_progressive_names_and_misclassified_clank_weapon(self):
        self.assertEqual(PROGRESSIVE_TO_INTERNAL[canonical_item_name("Progressive: Ratchet blaster")], "blaster")
        self.assertEqual(PROGRESSIVE_TO_INTERNAL[canonical_item_name("Progressive: Ratchet LightningUmbrella")], "LightningUmbrella")
        self.assertEqual(EQUIPMENT_DISPLAY_TO_INTERNAL[canonical_item_name("Unlock: Clank Bowtie")], "throwTie")

    def test_current_and_unknown_names_are_not_reinterpreted(self):
        self.assertEqual(canonical_item_name(SACRatchetWeapons.BLASTER), SACRatchetWeapons.BLASTER)
        self.assertEqual(canonical_item_name("Unknown item (ID: 77800007)"), "Unknown item (ID: 77800007)")
