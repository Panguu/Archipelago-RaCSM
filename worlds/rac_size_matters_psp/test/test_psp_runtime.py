import unittest
from unittest.mock import Mock, patch

from ..core.native_runtime import NativeRuntime
from ..core.patches import Patch, Plan
from ..procmem.transport import ProcMemTransport


class Memory:
    def __init__(self):
        self.data = bytearray(b"abcd")
        self.writes = []

    def get_game_id(self):
        return "UCUS98633"

    def read_bytes(self, address, size):
        offset = address - 0x08800000
        return bytes(self.data[offset:offset + size])

    def write_bytes(self, address, data):
        self.writes.append((address, data))
        offset = address - 0x08800000
        self.data[offset:offset + len(data)] = data


class TestPspPatches(unittest.TestCase):
    def setUp(self):
        self.memory = Memory()
        self.plan = Plan(self.memory, [Patch(0x08800000, b"ab", b"xy")], name="test", planet_id=1)

    def test_round_trip_and_idempotence(self):
        self.plan.install()
        self.plan.install()
        self.assertEqual(len(self.memory.writes), 1)
        self.plan.restore()
        self.assertEqual(self.memory.data, b"abcd")

    def test_mismatch_has_no_writes(self):
        self.memory.data[0] = 0
        with self.assertRaises(RuntimeError):
            self.plan.install()
        self.assertFalse(self.memory.writes)

    def test_changed_overlay_is_not_restored(self):
        self.plan.install()
        self.memory.data[0] = 0
        with self.assertRaises(RuntimeError):
            self.plan.restore()
        self.assertEqual(len(self.memory.writes), 1)

    def test_runtime_gates_on_ready_and_planet(self):
        runtime = NativeRuntime(self.memory)
        runtime.register(self.plan)
        runtime.tick(1, False)
        runtime.tick(2, True)
        self.assertFalse(self.memory.writes)
        runtime.tick(1, True)
        self.assertTrue(self.plan.installed)
        runtime.tick(1, False)
        self.assertFalse(self.plan.installed)

    def test_overlapping_plans_rejected(self):
        runtime = NativeRuntime(self.memory)
        runtime.register(self.plan)
        with self.assertRaises(ValueError):
            runtime.register(Plan(self.memory, [Patch(0x08800001, b"b", b"z")], name="overlap"))

    def test_ps2_address_rejected(self):
        with self.assertRaises(ValueError):
            Plan(self.memory, [Patch(0x1F4B354, b"a", b"b")], name="PS2")

    def test_partial_install_rolls_back(self):
        plan = Plan(self.memory, [Patch(0x08800000, b"ab", b"xy"), Patch(0x08800002, b"cd", b"zz")], name="transaction")
        write = self.memory.write_bytes
        def failing(address, data):
            if data == b"zz":
                raise OSError("write failed")
            write(address, data)
        self.memory.write_bytes = failing
        with self.assertRaises(OSError):
            plan.install()
        self.assertEqual(self.memory.data, b"abcd")
        self.assertFalse(plan.installed)


class TestPymemTransport(unittest.TestCase):
    def setUp(self):
        self.memory = ProcMemTransport()
        self.memory._handle = 123
        self.memory._base = 0x200000000
        self.memory._cached_game_id = "UCUS98633"

    def test_guest_alias_translation_and_64_bit_host(self):
        self.assertEqual(self.memory._host_address(0x48800000), 0x208800000)

    def test_rejects_invalid_and_cross_boundary_ranges(self):
        for address, size in ((-1, 1), (0x1F4B354, 4), (0x09FFFFFF, 2), (0x08800000, -1)):
            with self.subTest(address=address, size=size), self.assertRaises(self.memory.RequestError):
                self.memory._host_address(address, size)

    def test_64_bit_read_is_one_operation(self):
        with patch("worlds.rac_size_matters_psp.procmem.winmem.read_process_memory", return_value=b"\x01" * 8) as read:
            self.assertEqual(self.memory.read_int64(0x08800000), 0x0101010101010101)
            read.assert_called_once_with(123, 0x208800000, 8)

    def test_64_bit_write_is_one_operation(self):
        with patch("worlds.rac_size_matters_psp.procmem.winmem.write_process_memory") as write:
            self.memory.write_int64(0x08800000, 0x0101010101010101)
            write.assert_called_once_with(123, 0x208800000, b"\x01" * 8)

    def test_backend_uses_pymem(self):
        from ..procmem import winmem
        with patch("pymem.memory.read_bytes", return_value=b"abc") as read:
            self.assertEqual(winmem.read_process_memory(123, 456, 3), b"abc")
            read.assert_called_once_with(123, 456, 3)
        with patch("pymem.memory.write_bytes") as write:
            winmem.write_process_memory(123, 456, b"abc")
            write.assert_called_once_with(123, 456, b"abc", 3)

    def test_game_swap_closes_session(self):
        self.memory._control = Mock()
        self.memory._control.get_game_id.return_value = "OTHER"
        with patch.object(self.memory, "is_connected", return_value=True), patch("worlds.rac_size_matters_psp.procmem.winmem.close_handle"):
            with self.assertRaises(self.memory.ConnectionError):
                self.memory.validate_session()
        self.assertIsNone(self.memory._handle)
        self.assertEqual(self.memory.get_game_id(), "")

    def test_failed_bootstrap_clears_state(self):
        self.memory._handle = None
        with patch("worlds.rac_size_matters_psp.procmem.winmem.find_pid_by_name", return_value=1), patch.object(self.memory, "_bootstrap", return_value=("OTHER", 123)):
            with self.assertRaises(self.memory.ConnectionError):
                self.memory.connect()
        self.assertIsNone(self.memory._base)


class TestPlatformParity(unittest.TestCase):
    def test_ids_match_ps2(self):
        from ..world import RACSizeMatterWorld as PSP
        import json
        from pathlib import Path
        # Snapshot pinned after live PS2/PSP equality passed during the port.
        baseline = json.loads((Path(__file__).parent / "fixtures/ps2_ids.json").read_text())
        self.assertEqual(PSP.game, "Ratchet & Clank: Size Matters PSP")
        self.assertEqual(PSP.item_name_to_id, baseline["items"])
        self.assertEqual(PSP.location_name_to_id, baseline["locations"])

    def test_location_memory_sources_are_psp_addresses(self):
        from ..locations import ALL_LOCATIONS
        for location in ALL_LOCATIONS.values():
            if location.completed.source in ("missions", "challenges", "skyboard"):
                self.assertTrue(0x08000000 <= location.completed.key < 0x0A000000, location.name)


class TestInventoryReceipts(unittest.TestCase):
    def test_unified_armour_crosses_sets(self):
        from types import SimpleNamespace
        from ..client.vendor import InventoryMixin
        from ..items import ARMOUR_PIECE_BITMASKS, ARMOUR_SETS, PROGRESSIVE_ARMOUR_UNIFIED_NAME
        ctx = SimpleNamespace(
            items_received=[SimpleNamespace(item=1)] * 5,
            item_names={"PSP": {1: PROGRESSIVE_ARMOUR_UNIFIED_NAME}}, game="PSP",
            _wiring=SimpleNamespace(planet=SimpleNamespace(planet_id=1)),
        )
        inventory = InventoryMixin._parse_inventory(ctx)
        self.assertEqual(inventory["armour_unlocked"][ARMOUR_SETS[0][1]], sum(ARMOUR_PIECE_BITMASKS))
        self.assertEqual(inventory["armour_unlocked"][ARMOUR_SETS[1][1]], ARMOUR_PIECE_BITMASKS[0])
