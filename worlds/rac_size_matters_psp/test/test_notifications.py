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
        self.profile = SimpleNamespace(timer=0x09300000, frame=0x09100000)
        self.original = bytes.fromhex('a0ffbd272c09043c')
        self.memory.write_bytes(self.profile.frame, self.original)
        self.kernel = Kernel()
        from ..core.patches.notification import Font
        for name, value in (
            ('notifications.resolve', self.profile),
            ('notifications.KernelBridge', self.kernel),
            ('patches.notification.resolve_font', Font(0x09110000, 0x09120000, 0x09310000, 0x09310004))):
            context = patch('worlds.rac_size_matters_psp.core.'+name, return_value=value)
            context.start()
            self.addCleanup(context.stop)
        self.hud = HudNotifications(self.memory)

    def test_native_prompt_untouched_during_notification_and_after_close(self):
        original = bytes(range(64))
        self.memory.write_bytes(self.profile.timer, original)
        self.hud.enqueue('Received Lacerator from Player Two')
        self.hud.tick(1, True)
        self.assertFalse(self.hud.failed)
        self.assertEqual(self.memory.read_int32(self.hud.hook.state.address), 180)
        self.assertEqual(self.memory.read_bytes(self.profile.timer, 64), original)
        self.hud.close()
        self.assertEqual(self.memory.read_bytes(self.profile.timer, 64), original)
        self.assertEqual(self.memory.read_bytes(self.profile.frame, 8), self.original)
        self.assertEqual(self.kernel.freed, [12])

    def test_transition_defers_without_writing(self):
        self.hud.enqueue('AP message')
        self.memory.write_int32(TransitionGateStruct.BASE_ADDRESS, 0)
        before = bytes(self.memory.data)
        self.hud.tick(1, True)
        self.assertEqual(bytes(self.memory.data), before)
        self.assertIsNone(self.hud.storage)

    def test_messages_wait_for_own_countdown_not_native_prompt(self):
        self.hud.enqueue('First')
        self.hud.enqueue('Second')
        self.hud.tick(1, True)
        self.hud.tick(1, True)
        self.assertEqual(list(self.hud.pending), ['Second'])
        self.memory.write_int32(self.hud.hook.state.address, 0)
        self.memory.write_int32(self.profile.timer, 100)
        self.hud.tick(1, True)
        self.assertEqual(list(self.hud.pending), [])
        self.assertEqual(self.memory.read_bytes(self.hud.hook.text.address, 7), b'Second\0')
        self.assertEqual(self.memory.read_int32(self.profile.timer), 100)
        self.hud.close()

    def test_queue_is_bounded_and_text_is_safe(self):
        for _ in range(30):
            self.hud.enqueue('X'*80+'\0\u00e9')
        self.assertEqual(len(self.hud.pending), 12)
        self.assertEqual(self.hud.pending[0], 'X'*60)

    def test_retains_allocation_if_old_hook_still_reachable(self):
        self.hud.enqueue('AP message')
        self.hud.tick(1, True)
        self.memory.write_int8(CURRENT_PLANET_ADDRESS, 3)
        with self.assertLogs('CommonClient', level='ERROR'):
            self.hud.tick(3, True)
        self.assertTrue(self.hud.failed)
        self.assertEqual(self.kernel.freed, [])

    def test_departed_overlay_code_is_not_restored(self):
        self.hud.enqueue('AP message')
        self.hud.tick(1, True)
        self.memory.write_int8(CURRENT_PLANET_ADDRESS, 3)
        self.memory.write_bytes(self.profile.frame, b'new code')
        self.hud.tick(3, True)
        self.assertEqual(self.memory.read_bytes(self.profile.frame, 8), b'new code')
        self.assertEqual(self.kernel.freed, [12])
        self.assertIsNone(self.hud.storage)
