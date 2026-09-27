from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from .test_client_gameplay import GameMemory
from ..core.challenge_mode import ChallengeModeState, CHALLENGE_MODE_ADDRESS
from ..core.address_maps import CURRENT_PLANET_ADDRESS, MENU_ADDR_BY_PLANET_ID
from ..core.structs.game import TransitionGateStruct
from ..core.core import Core
from ..client.vendor import InventoryMixin
from ..items import PROGRESSIVE_CHALLENGE_MODE_NAME


class TestChallengeModeRuntime(unittest.TestCase):
    def setUp(self):
        self.memory = GameMemory()
        self.state = ChallengeModeState(self.memory)

    def test_fixed_tiers_use_word_writes_and_preserve_adjacent_fields(self):
        self.memory.write_bytes(CHALLENGE_MODE_ADDRESS-4,b'ABCD'+b'\xff'*4+b'EFGH')
        for tier in (2,0,1):
            self.state.configure(tier)
            self.assertTrue(self.state.apply(1,True))
            self.assertEqual(self.memory.read_int32(CHALLENGE_MODE_ADDRESS),tier)
            self.assertEqual(self.memory.read_bytes(CHALLENGE_MODE_ADDRESS-4,4),b'ABCD')
            self.assertEqual(self.memory.read_bytes(CHALLENGE_MODE_ADDRESS+4,4),b'EFGH')

    def test_progressive_receipts_are_bounded_and_rebuilt_not_accumulated(self):
        self.state.configure(2,True)
        for count,expected in ((0,0),(1,1),(1,1),(2,2),(50,2),(0,0)):
            self.state.set_received(count)
            self.state.apply(1,True)
            self.assertEqual(self.state.tier,expected)
        self.state.configure(1,True)
        self.state.set_received(2)
        self.state.apply(1,True)
        self.assertEqual(self.state.tier,1)

    def test_unconfigured_loading_wrong_planet_and_unknown_overlay_never_write(self):
        self.memory.write_int32(CHALLENGE_MODE_ADDRESS,1)
        self.assertFalse(self.state.apply(1,True))
        self.state.configure(2)
        before = bytes(self.memory.data)
        for planet,ready in ((1,False),(2,True),(0,True),(21,True)):
            self.assertFalse(self.state.apply(planet,ready))
        self.assertEqual(bytes(self.memory.data),before)
        self.memory.write_int32(TransitionGateStruct.BASE_ADDRESS,0)
        self.assertFalse(self.state.apply(1,True))
        self.assertEqual(self.memory.read_int32(CHALLENGE_MODE_ADDRESS),1)

    def test_vendor_defers_receipt_until_closed(self):
        self.state.configure(2,True)
        self.state.set_received(1)
        for menu in (9,14):
            self.memory.write_int8(MENU_ADDR_BY_PLANET_ID[1],menu)
            self.assertFalse(self.state.apply(1,True))
            self.assertEqual(self.state.tier,0)
            self.assertEqual(self.memory.read_int32(CHALLENGE_MODE_ADDRESS),0)
        self.memory.write_int8(MENU_ADDR_BY_PLANET_ID[1],0)
        self.assertTrue(self.state.apply(1,True))
        self.assertEqual(self.state.tier,1)

    def test_new_connection_clears_previous_progressive_receipts(self):
        self.state.configure(2,True)
        self.state.set_received(2)
        self.state.apply(1,True)
        self.state.configure(1,True)
        self.state.apply(1,True)
        self.assertEqual(self.state.tier,0)

    def test_planet_load_reset_reapplies_tier_without_repeated_writes(self):
        self.state.configure(2)
        self.state.apply(1,True)
        self.memory.write_int8(CURRENT_PLANET_ADDRESS,3)
        self.memory.write_int32(CHALLENGE_MODE_ADDRESS,0)
        self.state.apply(3,True)
        self.memory.write_int32 = Mock(wraps=self.memory.write_int32)
        self.state.apply(3,True)
        self.memory.write_int32.assert_not_called()
        self.assertEqual(self.memory.read_int32(CHALLENGE_MODE_ADDRESS),2)

    def test_inventory_decodes_progressive_challenge_mode_without_writes(self):
        ctx = SimpleNamespace(items_received=[SimpleNamespace(item=1),SimpleNamespace(item=2),SimpleNamespace(item=1)],
            item_names={'PSP':{1:PROGRESSIVE_CHALLENGE_MODE_NAME,2:'Bolts'}},game='PSP',
            _wiring=SimpleNamespace(planet=SimpleNamespace(planet_id=1)))
        self.assertEqual(InventoryMixin._parse_inventory(ctx)['challenge_mode'],2)
        ctx.items_received.pop()
        self.assertEqual(InventoryMixin._parse_inventory(ctx)['challenge_mode'],1)

    def test_core_ryno_gate_tracks_applied_tier(self):
        core = Core(self.memory)
        core.clank_enabled = False
        core.challenge_mode.configure(2,True)
        core.challenge_mode.set_received(0)
        core.tick()
        core.planet_unlock.is_vendor_accessible = lambda key: True
        self.assertNotIn('ryno',core.vendor._purchasable_names())
        core.challenge_mode.set_received(1)
        core.tick()
        self.assertIn('ryno',core.vendor._purchasable_names())
        self.assertEqual(self.memory.read_int32(CHALLENGE_MODE_ADDRESS),1)

    def test_invalid_settings_and_receipts_rejected(self):
        for tier in (-1,3,True,'2'):
            with self.assertRaises(ValueError):self.state.configure(tier)
        for count in (-1,True,'2'):
            with self.assertRaises(ValueError):self.state.set_received(count)
