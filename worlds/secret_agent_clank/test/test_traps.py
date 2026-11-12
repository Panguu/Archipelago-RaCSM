import unittest
from pathlib import Path
from unittest.mock import Mock

from ..constants import SACTraps
from ..core import RATCHET_PACK_BIT, TRAP_BITS, RuntimeSymbols, Traps
from ..core.address_maps import BOLTS_ADDRESS
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

    def test_menu_ticks_enforce_traps_without_spending_duration(self):
        for name in TRAP_BITS:
            with self.subTest(trap=name):
                self.traps.activate(name, {})
                duration = dict(self.traps.remaining)
                for _ in range(3):
                    self.memory.write_int32(0x100000, 1 << 12)
                    self.now += 10
                    self.traps.tick({}, False)
                    self.assertEqual(self.memory.read_int32(0x100000),
                                     (1 << 12) | self.traps.managed)
                    self.assertEqual(self.traps.remaining, duration)
                self.traps.restore({})

    def test_switching_reactivation_does_not_reset_running_countdown(self):
        self.traps.activate(SACTraps.WEAPON_SWITCHING, {})
        self.memory.write_int32(0x100004, 123)
        self.traps.tick({}, False)
        self.assertEqual(self.memory.read_int32(0x100004), 123)
        self.memory.write_int32(0x100000, 0)
        self.traps.tick({}, False)
        self.assertEqual(self.memory.read_int32(0x100004), 360)

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

    def test_reset_clears_all_traps_including_unmanaged(self):
        self.traps.activate(SACTraps.MIRRORED_LEVELS, {})
        stale = TRAP_BITS[SACTraps.BIG_HEADED] | TRAP_BITS[SACTraps.WEAPON_SWITCHING]
        self.memory.write_int32(0x100000, self.memory.read_int32(0x100000) | stale | RATCHET_PACK_BIT)
        self.assertTrue(self.traps.reset({}))
        self.assertEqual(self.memory.read_int32(0x100000), RATCHET_PACK_BIT)
        self.assertFalse(self.traps.remaining)
        self.assertEqual(self.traps.managed, 0)
        self.traps.address.return_value = None
        self.assertFalse(self.traps.reset({}))

    def test_gadgetron_debt_takes_eight_percent_of_bolts(self):
        for bolts, left in ((10_000, 9_200), (12_345, 11_358), (12, 12), (0, 0)):
            with self.subTest(bolts=bolts):
                self.memory.write_int32(BOLTS_ADDRESS, bolts)
                self.assertEqual(self.traps.gadgetron_debt(), bolts - left)
                self.assertEqual(self.memory.read_int32(BOLTS_ADDRESS), left)
        self.assertNotIn(SACTraps.GADGETRON_DEBT, TRAP_BITS)  # not a timed cheat

    def test_ratchet_pack_survives_trap_expiry_and_restore(self):
        self.memory.write_int32(0x100000, 1 << 12)
        self.assertTrue(self.traps.grant_ratchet_pack({}))
        self.assertEqual(self.memory.read_int32(0x100000), (1 << 12) | RATCHET_PACK_BIT)
        self.traps.durations[SACTraps.MIRRORED_LEVELS] = 1
        self.traps.activate(SACTraps.MIRRORED_LEVELS, {})
        self.traps.tick({}, True)
        self.now = 2
        self.traps.tick({}, True)
        self.traps.tick({}, True)
        self.traps.restore({})
        self.assertEqual(self.memory.read_int32(0x100000), (1 << 12) | RATCHET_PACK_BIT)
        self.traps.address.return_value = None
        self.assertFalse(self.traps.grant_ratchet_pack({}))

    def test_current_module_capture_layout(self):

        path = Path(__file__).resolve().parents[1] / ".research/showers_forced_graveyard.bin"
        if not path.exists():
            self.skipTest("Local research capture unavailable")
        self.memory.data = bytearray(path.read_bytes())
        symbols = RuntimeSymbols.parse(self.memory.data[:0x1000000], 0)
        traps = Traps(self.memory)
        self.assertEqual(traps.address(symbols), self.memory.read_int32(0x58CB30) + 0x8E0)
        self.assertEqual(traps.switching_timer(symbols), 0x58D548)
