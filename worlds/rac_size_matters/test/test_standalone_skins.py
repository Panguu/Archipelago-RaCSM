import json
import struct
import unittest

from ..core.patches import asm as m
from ..tools.build_skin_pnach import ROOT, Memory, build, make_plan, pnach
from .test_native_patches import CPU


def apply_pnach(memory, text):
    skip = 0
    for line in text.splitlines():
        if not line.startswith("patch="):
            continue
        if skip:
            skip -= 1
            continue
        _, _, address, _, value = line.removeprefix("patch=").split(",")
        address, value = int(address, 16), int(value, 16)
        if address >> 28 == 0xE:
            actual = int.from_bytes(memory.read_bytes(value & 0x0FFFFFFF, 2), "little")
            matches = actual != (address & 65535) if value >> 28 else actual == (address & 65535)
            if not matches:
                skip = (address >> 16) & 255
        else:
            assert address >> 28 == 2
            memory.write_int32(address & 0x0FFFFFFF, value)


class InstallerMemory(Memory):
    def read_int8(self, address):
        return self.data[address]

    def write_int8(self, address, value):
        self.data[address] = value


def setup(region, name=None):
    result = build(region)
    fixtures = json.loads((ROOT / f"test/fixtures/multiplayer_skins_{region}.json").read_text())
    f = fixtures[name] if name else result.fixture
    memory = InstallerMemory(f)
    # These bounded MP fixtures omit the menu-close wrapper and the four
    # scanner instructions; supply the contract checked by skins.prepare.
    close = f["base"] + 0x100
    memory.write_bytes(close, m.packed(0x806402E0, 0x10A40007, 0, 0x00A0202D,
                                     m.jump(f["begin"]), 0x24050001, m.jump(f["finish"]), 0))
    signature = ([0x8E050000, 0x0220302D, 0xAFB30000, 0x0240202D, 0x0000382D]
                 if region == "jp" else [0x8E030000, 0x1074000A, 0x0240202D, 0x8E050008])
    memory.write_bytes(f["gate"], m.packed(*signature))
    memory.write_int32(f["begin"], 0x27BDFFB0)
    memory.write_int32(f["finish"], 0x27BDFFB0)
    expected = make_plan(memory, f)
    memory.write_bytes(result.entry, result.code)
    memory.write_bytes(result.data_address, result.data)
    # Cache syscalls have no data effect in this interpreter. Their real
    # opcodes are checked before replacing them with NOPs for execution.
    syscalls = []
    for off in range(0, len(result.code), 4):
        if struct.unpack_from("<I", result.code, off)[0] == 0xC:
            syscalls.append(off)
            memory.write_int32(result.entry + off, 0)
    assert len(syscalls) == 2
    memory.write_int32(result.gate.STATE, 4)
    memory.write_int32(result.gate.LOAD_THREAD, 0)
    memory.write_int32(result.gate.HANDLE, 0)
    memory.write_int32(result.gate.MODULES + 4, f["base"])
    memory.write_int32(result.gate.MODULES + 8, 1)
    return result, memory, expected


class TestStandaloneSkins(unittest.TestCase):
    def run_installer(self, result, memory):
        cpu = CPU(memory)
        cpu.r[m.V0] = 0x1F50000
        before = list(cpu.r)
        cpu.run(result.entry, stop=result.gate.SITE + 8, max_steps=16000000)
        before[m.A0] = 5
        before[m.V0] = (before[m.V0] + struct.unpack("<h", m.packed(result.gate.SIGNATURE[6])[:2])[0]) & 0xFFFFFFFF
        self.assertEqual(cpu.r, before)
        return cpu

    def test_installer_matches_existing_loader_for_all_regions(self):
        for region in ("us", "eu", "jp"):
            with self.subTest(region=region):
                result, memory, expected = setup(region)
                self.run_installer(result, memory)
                for edit in expected.edits:
                    self.assertEqual(memory.read_bytes(edit.address, len(edit.replacement)), edit.replacement,
                                     f"{region} {edit.address:#x}")
                self.assertEqual(memory.read_int8(result.skin_byte), 0x7F)

    def test_wrong_loader_state_does_not_install(self):
        result, memory, expected = setup("us")
        memory.write_int32(result.gate.STATE, 6)
        original = memory.read_bytes(expected.table, 320)
        self.run_installer(result, memory)
        self.assertEqual(memory.read_bytes(expected.table, 320), original)

    def test_relocated_planet_uses_its_own_addresses(self):
        result, memory, expected = setup("us", "quodrona")
        self.run_installer(result, memory)
        for edit in expected.edits:
            self.assertEqual(memory.read_bytes(edit.address, len(edit.replacement)), edit.replacement,
                             f"{edit.address:#x}")

    def test_pnach_is_reproducible_and_uses_only_bounded_raw_commands(self):
        for region in ("us", "eu", "jp"):
            result = build(region)
            text = pnach(result)
            path = ROOT / "standalone_skins" / f"{result.game_id}_{result.crc}.pnach"
            self.assertEqual(path.read_text(), text)
            for line in text.splitlines():
                if line.startswith("patch="):
                    place, cpu, address, kind, value = line.removeprefix("patch=").split(",")
                    self.assertEqual((place, cpu, kind), ("1", "EE", "extended"))
                    self.assertEqual(len(address), 8)
                    self.assertEqual(len(value), 8)

    def test_pnach_guards_hook_and_does_not_reset_live_menu_data(self):
        for region in ("us", "eu", "jp"):
            result = build(region)
            memory = InstallerMemory(result.fixture)
            memory.write_bytes(result.gate.SITE, m.packed(result.gate.ORIGINAL, result.gate.SIGNATURE[6]))
            text = pnach(result)
            apply_pnach(memory, text)
            self.assertEqual(memory.read_int32(result.gate.SITE), m.j(result.entry))
            self.assertEqual(memory.read_bytes(result.entry, len(result.code)), result.code)
            memory.write_int32(result.plan.rows, 123)
            memory.write_int32(result.plan.descriptors + 20, 456)
            apply_pnach(memory, text)
            self.assertEqual(memory.read_int32(result.plan.rows), 123)
            self.assertEqual(memory.read_int32(result.plan.descriptors + 20), 456)
            from ..core.patches.multiplayer_skins import mcp_address
            memory.write_int32(mcp_address(result.game_id) + 0x2DC, 0)
            apply_pnach(memory, text)
            self.assertEqual(memory.read_bytes(result.gate.SITE, 8),
                             m.packed(result.gate.ORIGINAL, result.gate.SIGNATURE[6]))
