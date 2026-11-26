import random
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ..constants import Rac5Filler, Rac5Traps
from ..core.filler import grant_filler
from ..core.player_health_exp import PlayerHealthExpInventory
from ..core.traps import activate_trap
from ..core.vendor import WEAPON_VENDOR_IDS
from ..options import RingLink
from ..world import RACSizeMatterWorld
from .test_cross_game_links import LinkContext
from ..client.vendor import InventoryMixin


class FillerTests(unittest.TestCase):
    def test_weighted_selection_keeps_debt_enabled(self):
        world = SimpleNamespace(random=random.Random(1), options=SimpleNamespace(
            trap_chance=SimpleNamespace(value=100),
            trap_weight=SimpleNamespace(value={Rac5Traps.TRAP_GADGETRON_DEBT: 1}),
            ring_link=SimpleNamespace(value=1),
            filler_weight=SimpleNamespace(value={Rac5Filler.REFILL_AMMO: 1})))
        self.assertEqual(RACSizeMatterWorld.get_filler_item_name(world), Rac5Traps.TRAP_GADGETRON_DEBT)
        world.options.ring_link.value = 2
        self.assertEqual(RACSizeMatterWorld.get_filler_item_name(world), Rac5Traps.TRAP_GADGETRON_DEBT)
        self.assertEqual(RingLink.default, 0)

    def test_nanotech_reward_rebaselines(self):
        c = LinkContext()
        xp = PlayerHealthExpInventory(c.pine)
        c.pine.value = 0
        c.pine.read_int8 = lambda _: 0
        core = SimpleNamespace(pine=c.pine, player_health_exp=xp)
        grant_filler(core, Rac5Filler.NANOTECH_EXP)
        self.assertEqual(c.pine.value, 180)
        xp.multiplier = 4
        xp.apply_boost()
        self.assertEqual(c.pine.value, 180)

    def test_weapon_rewards_target_equipped_weapon_and_respect_cap(self):
        weapons = Mock(progressive_mode=1, _prev_experience={})
        weapons.has_weapon.return_value = True
        weapons.get_level.return_value = 0
        weapons.level_ceiling.return_value = 3
        weapons.get_experience.return_value = 100
        weapons.get_ammo.return_value = 0
        core = SimpleNamespace(planet=SimpleNamespace(weapons=weapons,
            weapon_cycler=SimpleNamespace(current_weapon=WEAPON_VENDOR_IDS['Lacerator'])))
        grant_filler(core, Rac5Filler.WEAPON_EXP)
        weapons.set_experience.assert_called_once_with('Lacerator', 850)
        self.assertEqual(weapons._prev_experience['Lacerator'], 850)
        grant_filler(core, Rac5Filler.REFILL_AMMO)
        weapons.set_ammo.assert_called_with('Lacerator', 60)
        weapons.get_level.return_value = 4
        grant_filler(core, Rac5Filler.REFILL_AMMO)
        weapons.set_ammo.assert_called_with('Lacerator', 120)
        weapons.set_experience.reset_mock()
        grant_filler(core, Rac5Filler.WEAPON_EXP)
        weapons.set_experience.assert_not_called()

    def test_debt_bounds(self):
        c = LinkContext()
        with patch('worlds.rac_size_matters.core.traps.traps_ready', return_value=True):
            for before, after in ((0, 0), (1, 1), (1000, 800), (100000, 80000), (500000, 400000), (2000000, 1600000)):
                c.pine.value = before
                activate_trap(c.pine, Rac5Traps.TRAP_GADGETRON_DEBT)
                self.assertEqual(c.pine.value, after)

    def test_debt_delivery_modes_and_checkpoint(self):
        for mode, balance, shared in ((0, 400000, 0), (1, 400000, 0), (2, 400000, -100000)):
            c = LinkContext()
            c.slot_data = {'ring_link': mode}
            c.pine.value = 500000
            c._wiring.player_bolts.rebaseline()
            c.game = 'Ratchet'
            c.item_names = {'Ratchet': {1: Rac5Traps.TRAP_GADGETRON_DEBT}}
            c.items_received = [SimpleNamespace(item=1)]
            c._processed_trap_count = 0
            c._send_trap_link = Mock()
            c._log = Mock()
            with patch('worlds.rac_size_matters.client.vendor.traps_ready', return_value=True), \
                 patch('worlds.rac_size_matters.client.ring_link.traps_ready', return_value=True), \
                 patch('worlds.rac_size_matters.core.traps.traps_ready', return_value=True):
                InventoryMixin._grant_new_trap_items(c)
                InventoryMixin._grant_new_trap_items(c)
                c._wiring.player_bolts.apply_boost()
            self.assertEqual(c.pine.value, balance)
            self.assertEqual(c._ring_link_remainder, shared)
            c._log.assert_not_called()

    def test_dropped_ammo_empties_all_owned_weapons_only(self):
        c = LinkContext()
        weapons = Mock(weapons={'Lacerator': True, 'Acid Bomb Glove': True, 'RYNO': False})
        with patch('worlds.rac_size_matters.core.traps.traps_ready', return_value=True):
            activate_trap(c.pine, Rac5Traps.TRAP_DROPPED_AMMO, weapons=weapons)
        self.assertEqual(weapons.set_ammo.call_args_list,
                         [unittest.mock.call('Lacerator', 0), unittest.mock.call('Acid Bomb Glove', 0)])
        weapons.reset_mock()
        with patch('worlds.rac_size_matters.core.traps.traps_ready', return_value=False):
            activate_trap(c.pine, Rac5Traps.TRAP_DROPPED_AMMO, weapons=weapons)
        weapons.set_ammo.assert_not_called()

    def test_dropped_ammo_delivery_is_not_replayed(self):
        c = LinkContext()
        c._processed_trap_count = 0
        c.game = 'Ratchet'
        c.item_names = {'Ratchet': {1: Rac5Traps.TRAP_DROPPED_AMMO}}
        c.items_received = [SimpleNamespace(item=1)]
        c._send_trap_link = Mock()
        c._log = Mock()
        with patch('worlds.rac_size_matters.client.vendor.traps_ready', return_value=True), \
             patch('worlds.rac_size_matters.client.vendor.activate_trap') as activate:
            InventoryMixin._grant_new_trap_items(c)
            InventoryMixin._grant_new_trap_items(c)
        activate.assert_called_once_with(c.pine, Rac5Traps.TRAP_DROPPED_AMMO,
                                         weapons=c._wiring.planet.weapons)
        c._send_trap_link.assert_called_once_with(Rac5Traps.TRAP_DROPPED_AMMO)

    def test_debt_percentage_range_and_bounds(self):
        from ..options import GadgetronDebtPercent
        self.assertEqual(GadgetronDebtPercent.default, 20)
        for invalid in (9, 100):
            with self.assertRaises(Exception):
                GadgetronDebtPercent(invalid)
        c = LinkContext()
        with patch('worlds.rac_size_matters.core.traps.traps_ready', return_value=True):
            for percent, before, after in ((10, 400000, 360000), (20, 400000, 320000),
                                           (99, 100000, 1000), (99, 1000000, 10000),
                                           (10, 100000, 90000)):
                c.pine.value = before
                activate_trap(c.pine, Rac5Traps.TRAP_GADGETRON_DEBT, debt_percent=percent)
                self.assertEqual(c.pine.value, after)
