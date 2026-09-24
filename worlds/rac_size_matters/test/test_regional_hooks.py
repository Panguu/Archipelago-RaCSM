"""Region-specific hooks must reject a changed game or instruction stream."""

import json
import struct
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from ..constants import Rac5Locations
from ..core.native_runtime import NativeRuntime
from ..core.patches import pokitaru_ship, sprout_pickup
from ..core.patches.loader_gate import LoaderGate


FIXTURES = json.loads((Path(__file__).parent / "fixtures/regional_hooks.json").read_text())


class Memory:
    def __init__(self, fixture):
        self.game_id = fixture["game_id"]
        self.data = bytearray(0x2000000)
        self.writes = []
        for address, raw in fixture["segments"]:
            raw = bytes.fromhex(raw)
            self.data[address:address + len(raw)] = raw
        struct.pack_into("<I", self.data, 0x1F4C5AC if self.game_id == "SCPS-15120" else 0x1F4C76C, fixture["planet"])

    def get_game_id(self):
        return self.game_id

    def read_bytes(self, address, size):
        return bytes(self.data[address:address + size])

    def read_int32(self, address):
        return struct.unpack_from("<I", self.data, address)[0]

    def write_bytes(self, address, data):
        self.writes.append(address)
        self.data[address:address + len(data)] = data

    def write_int32(self, address, value):
        self.write_bytes(address, struct.pack("<I", value))


class RegionalHookTests(unittest.TestCase):
    def test_loader_regions_arm_and_restore_without_changing_defaults(self):
        for region in ("us", "eu", "jp"):
            fixture = FIXTURES[region + "_pokitaru"]
            memory = Memory(fixture)
            address, data = fixture["loader_segment"]
            memory.data[address:address + len(data) // 2] = bytes.fromhex(data)
            original = bytes(memory.data)
            gate = LoaderGate(memory, game_id=fixture["game_id"])
            gate.arm()
            self.assertEqual(memory.read_int32(gate.SITE), gate.HELD)
            gate.release()
            self.assertEqual(memory.data, original)
            memory.game_id = "UNSUPPORTED"
            memory.writes.clear()
            with self.assertRaises(RuntimeError):
                gate.arm()
            self.assertFalse(memory.writes)
        self.assertEqual(LoaderGate.SITE, 0x01E66414)
        self.assertEqual(LoaderGate.STATE, 0x01EDDAB8)

    def prepare(self, name, memory):
        return (pokitaru_ship if name.endswith("pokitaru") else sprout_pickup).prepare(memory)

    def test_us_and_eu_restore_exactly(self):
        for name, fixture in FIXTURES.items():
            with self.subTest(name=name):
                memory = Memory(fixture)
                original = bytes(memory.data)
                plan = self.prepare(name, memory)
                self.assertFalse(memory.writes)
                plan.install()
                self.assertNotEqual(memory.data, original)
                plan.restore()
                self.assertEqual(memory.data, original)

    def test_game_switch_rejects_install_before_any_write(self):
        for name, fixture in FIXTURES.items():
            with self.subTest(name=name):
                memory = Memory(fixture)
                plan = self.prepare(name, memory)
                memory.game_id = "SCES-55019" if memory.game_id == "SCUS-97615" else "SCUS-97615"
                with self.assertRaises(RuntimeError):
                    plan.install()
                self.assertFalse(memory.writes)

    def test_changed_instruction_rejects_prepare(self):
        for name, fixture in FIXTURES.items():
            with self.subTest(name=name):
                memory = Memory(fixture)
                memory.data[fixture["segments"][0][0]] ^= 1
                with self.assertRaises(RuntimeError):
                    self.prepare(name, memory)
                self.assertFalse(memory.writes)

    def test_sprout_journal_is_in_regional_function(self):
        for region, start in (("us", 0xF06610), ("eu", 0xF06708), ("jp", 0xF060D8)):
            memory = Memory(FIXTURES[region + "_ryllus"])
            plan = sprout_pickup.prepare(memory)
            self.assertEqual(plan.journals, ((start + 0x50, 1),))
            plan.install()
            self.assertEqual(memory.data[start + 0x50], 1)
            memory.data[start + 0x50] = 2
            plan._validate(replacement=True)
            plan.restore()

    def test_runtime_reports_and_restores_regional_sprout_check(self):
        for region in ("us", "eu", "jp"):
            with self.subTest(region=region):
                memory = Memory(FIXTURES[region + "_ryllus"])
                memory.read_int8 = lambda address: memory.data[address]
                memory.write_int8 = lambda address, value: memory.write_bytes(address, bytes([value]))
                plan = sprout_pickup.prepare(memory)
                plan.install()
                journal = plan.journals[0][0]
                runtime = NativeRuntime.__new__(NativeRuntime)
                runtime.pine = memory
                runtime.pickup = plan
                runtime.connection_warning = runtime.presentation = None
                runtime.armour = runtime.toast = None
                runtime.vendor = SimpleNamespace(planet=SimpleNamespace(is_ready=False), native_plan=None)
                runtime.checked = set()
                runtime.allowed_locations = None
                runtime.send_location = Mock()
                memory.data[journal] = 2
                runtime._poll()
                runtime.send_location.assert_called_once_with(Rac5Locations.RYLLUS_SPROUT)
                memory.data[journal] = 1
                runtime._poll()
                self.assertEqual(memory.data[journal], 2)
                runtime.send_location.assert_called_once()
