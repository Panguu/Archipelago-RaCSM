import unittest
from unittest.mock import Mock

from ..constants.cheats import SACTraps
from ..core.traps import Traps, TRAP_BITS
from .test_runtime import Memory


class TrapTests(unittest.TestCase):
    def setUp(self):
        self.memory = Memory()
        self.memory.write_int32 = lambda address, value: self.memory.batch_write_int32([(address, value)])
        self.now = 0
        self.traps = Traps(self.memory, lambda: self.now)
        self.traps.address = Mock(return_value=0x100000)
        self.traps.switching_timer = Mock(return_value=0x100004)

    def test_duration_stacking_pause_and_preserving_cheats(self):
        self.memory.write_int32(0x100000, (1 << 12) | (1 << 1))
        self.traps.durations[SACTraps.BIG_HEADED] = 1
        self.traps.activate(SACTraps.BIG_HEADED, {})
        self.traps.activate(SACTraps.BIG_HEADED, {})
        self.now = 20
        self.traps.tick({}, False)
        self.assertEqual(self.traps.remaining[SACTraps.BIG_HEADED], 2)
        self.traps.tick({}, True)
        for _ in range(4):
            self.now += 0.5
            self.traps.tick({}, True)
        self.assertEqual(self.memory.read_int32(0x100000), (1 << 12) | (1 << 1))
        self.assertFalse(self.traps.remaining)

    def test_failed_activation_is_not_consumed(self):
        self.memory.write_int32 = Mock(side_effect=OSError("disconnected"))
        with self.assertRaises(OSError):
            self.traps.activate(SACTraps.MIRRORED_LEVELS, {})
        self.assertFalse(self.traps.remaining)
        self.assertEqual(self.traps.managed, 0)

    def test_switching_initializes_native_countdown(self):
        self.traps.activate(SACTraps.WEAPON_SWITCHING, {})
        self.assertEqual(self.memory.read_int32(0x100004), 360)
        self.assertEqual(self.memory.read_int32(0x100000), TRAP_BITS[SACTraps.WEAPON_SWITCHING])

    def test_rebind_and_disconnect_restoration(self):
        self.traps.activate(SACTraps.MIRRORED_LEVELS, {})
        self.traps.address.return_value = 0x110000
        self.traps.last_tick = None
        self.traps.tick({}, True)
        self.assertEqual(self.memory.read_int32(0x110000), 1 << 3)
        self.traps.restore({})
        self.assertEqual(self.memory.read_int32(0x110000), 0)
        self.assertFalse(self.traps.remaining)

    def test_current_module_capture_layout(self):
        from pathlib import Path
        from ..core.symbols import RuntimeSymbols
        path = Path(__file__).resolve().parents[1] / ".research/showers_forced_graveyard.bin"
        if not path.exists():
            self.skipTest("Local research capture unavailable")
        self.memory.data = bytearray(path.read_bytes())
        symbols = RuntimeSymbols.parse(self.memory.data[:0x1000000], 0)
        traps = Traps(self.memory)
        self.assertEqual(traps.address(symbols), self.memory.read_int32(0x58CB30) + 0x8E0)
        self.assertEqual(traps.switching_timer(symbols), 0x58D548)
