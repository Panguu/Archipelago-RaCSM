import unittest

from ..core.patches import Entitlements
from .test_game_flags import Memory


class RoutineLifecycleTests(unittest.TestCase):
    def test_entitlement_prepare_and_read_are_write_free(self):
        pine = Memory()
        routine = Entitlements(pine).prepare(address=0x110000, table=0x120000,
                                            gadget_base=0x130000, fallback=0x140000)
        self.assertEqual(pine.writes, [])
        self.assertFalse(hasattr(routine, "apply"))
        pine.data[0x120000:0x120028] = bytes([2] * 40)
        pine.data[0x120028] = 7
        writes = list(pine.writes)
        self.assertEqual(routine.read(), {"flags": bytes([2] * 40), "initializations": 7})
        self.assertEqual(pine.writes, writes)
