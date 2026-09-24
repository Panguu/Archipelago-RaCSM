from contextlib import nullcontext
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from ..core.notifications import HudNotifications
from ..core.address_maps import CURRENT_PLANET_ADDRESS
from ..core.structs.game import TransitionGateStruct
from .test_client_gameplay import GameMemory


class Kernel:
    def __init__(self):
        self.address = 0x09900000
        self.freed = []

    def frame(self):
        return nullcontext()

    def allocate(self, size):
        return 12

    def head(self, block):
        return self.address

    def free(self, block):
        self.freed.append(block)
        return 0


class TestNotifications(unittest.TestCase):
    def setUp(self):
        self.memory = GameMemory()
        self.memory.paused = lambda **kwargs: nullcontext()
        self.memory.invalidate_code = Mock()
        self.memory.get_game_id = lambda: 'UCUS98633'
        calls = tuple((0x09101000+i*16, bytes.fromhex('0040400c00000000')) for i in range(3))
        for address, code in calls:
            self.memory.write_bytes(address, code)
        self.profile = SimpleNamespace(timer=0x09300000, panel_calls=calls)
        self.kernel = Kernel()
        self.resolve = patch('worlds.rac_size_matters_psp.core.notifications.resolve', return_value=self.profile)
        self.bridge = patch('worlds.rac_size_matters_psp.core.notifications.KernelBridge', return_value=self.kernel)
        self.resolve.start()
        self.bridge.start()
        self.addCleanup(self.resolve.stop)
        self.addCleanup(self.bridge.stop)
        self.hud = HudNotifications(self.memory)

    def test_text_only_message_restores_code_and_hud_then_frees_storage(self):
        self.memory.write_int32(self.profile.timer+20, 0x09800000)
        self.memory.write_int32(self.profile.timer+28, 99)
        self.hud.enqueue('Received Lacerator from Player Two')
        self.hud.tick(1, True)
        self.assertFalse(self.hud.failed)
        self.assertEqual(self.memory.read_int32(self.profile.timer), 180)
        self.assertEqual(self.memory.read_int32(self.profile.timer+20), self.hud.buffer.address)
        for address, code in self.profile.panel_calls:
            self.assertEqual(self.memory.read_bytes(address, 8), b'\0'*4+code[4:])
        self.memory.write_int32(self.profile.timer, 0)
        self.hud.tick(1, True)
        self.assertEqual(self.memory.read_int32(self.profile.timer+20), 0x09800000)
        self.assertEqual(self.memory.read_int32(self.profile.timer+28), 99)
        for address, code in self.profile.panel_calls:
            self.assertEqual(self.memory.read_bytes(address, 8), code)
        self.hud.close()
        self.assertEqual(self.kernel.freed, [12])

    def test_defers_while_native_message_or_transition_is_active(self):
        self.hud.enqueue('AP message')
        self.memory.write_int32(self.profile.timer, 7)
        before = bytes(self.memory.data)
        self.hud.tick(1, True)
        self.assertIsNone(self.hud.storage)
        self.assertEqual(bytes(self.memory.data), before)
        self.memory.write_int32(self.profile.timer, 0)
        self.memory.write_int32(TransitionGateStruct.BASE_ADDRESS, 0)
        before = bytes(self.memory.data)
        self.hud.tick(1, True)
        self.assertEqual(bytes(self.memory.data), before)

    def test_native_message_can_take_over_without_being_cleared(self):
        self.hud.enqueue('AP message')
        self.hud.tick(1, True)
        self.memory.write_int32(self.profile.timer+20, 0x09801100)
        self.memory.write_int32(self.profile.timer+28, 180)
        self.memory.write_int32(self.profile.timer, 20)
        self.hud.tick(1, True)
        self.assertEqual(self.memory.read_int32(self.profile.timer+20), 0x09801100)
        self.assertEqual(self.memory.read_int32(self.profile.timer), 20)
        self.hud.close()

    def test_close_restores_active_message_before_free(self):
        self.hud.enqueue('AP message')
        self.hud.tick(1, True)
        self.hud.close()
        self.assertEqual(self.memory.read_int32(self.profile.timer), 0)
        for address, code in self.profile.panel_calls:
            self.assertEqual(self.memory.read_bytes(address, 8), code)
        self.assertEqual(self.kernel.freed, [12])

    def test_queue_is_bounded_and_text_is_safe(self):
        for _ in range(30):
            self.hud.enqueue('X'*80+'\0é')
        self.assertEqual(len(self.hud.pending), 12)
        self.assertEqual(self.hud.pending[0], 'X'*60)

    def test_departed_overlay_is_not_restored(self):
        self.hud.enqueue('AP message')
        self.hud.tick(1, True)
        self.memory.write_int8(CURRENT_PLANET_ADDRESS, 3)
        before = bytes(self.memory.data)
        self.hud.tick(3, True)
        self.assertEqual(bytes(self.memory.data), before)
        self.assertIsNone(self.hud.active)
