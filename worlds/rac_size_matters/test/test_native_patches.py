"""Guarded native hooks tested with retail instruction excerpts and a tiny CPU.

Fixtures contain only the instructions read by the plan builders, not complete
game binaries. The CPU executes emitted branches and delay slots so tests check
observable journal/ownership behavior rather than only comparing opcodes.
"""
import json
import struct
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ..core.armour_spawn_gate import _scan
from ..core.native_runtime import NativeRuntime
from ..core.notifications import receipt_text
from ..core.patches import armour_pickup, item_toast, pokitaru_ship, sprout_pickup, vendor
from ..core.patches.asm import packed

FIXTURES = json.loads((Path(__file__).parent / "fixtures/native_us.json").read_text())
SHIP_FIXTURES = json.loads((Path(__file__).parent / "fixtures/ship_menu_us.json").read_text())
SKIN_EXIT_FIXTURES = json.loads((Path(__file__).parent / "fixtures/skins_exit_us.json").read_text())


class Memory:
    def __init__(self, fixture="pokitaru"):
        self.data = bytearray(0x2000000)
        self.fixture = FIXTURES[fixture]
        self.writes = []
        self.fail_once = None
        for address, data in self.fixture["segments"]:
            self.data[address:address + len(data) // 2] = bytes.fromhex(data)
        for address, data in SHIP_FIXTURES[fixture]["segments"]:
            self.data[address:address + len(data) // 2] = bytes.fromhex(data)
        for address, data in SKIN_EXIT_FIXTURES[fixture]["segments"]:
            self.data[address:address + len(data) // 2] = bytes.fromhex(data)
        self.write_int32(0x1F4C76C, self.fixture["planet"])
        self.writes.clear()

    def get_game_id(self): return "SCUS-97615"
    def read_bytes(self, address, size): return bytes(self.data[address:address + size])
    def read_int8(self, address): return self.data[address]
    def read_int32(self, address): return struct.unpack_from("<I", self.data, address)[0]

    def write_bytes(self, address, data):
        self.writes.append((address, bytes(data)))
        if self.fail_once == address:
            self.fail_once = None
            raise OSError("injected IPC failure")
        self.data[address:address + len(data)] = data

    def write_int8(self, address, value): self.write_bytes(address, bytes([value]))
    def write_int32(self, address, value): self.write_bytes(address, packed(value))


class CPU:
    STOP = 0x1FFF00

    def __init__(self, memory):
        self.memory = memory
        self.r = [0] * 32
        self.r[31], self.r[29] = self.STOP, 0x1FF0000
        self.calls = []

    def run(self, pc, stop=None, stubs=(), max_steps=1000):
        stop = self.STOP if stop is None else stop
        delayed = None
        for _ in range(max_steps):
            if pc == stop: return
            if pc in stubs:
                self.calls.append(pc)
                if isinstance(stubs, dict):
                    stubs[pc](self)
                pc = self.r[31]
                continue
            instruction = self.memory.read_int32(pc)
            op, rs, rt = instruction >> 26, instruction >> 21 & 31, instruction >> 16 & 31
            rd, shift, fn = instruction >> 11 & 31, instruction >> 6 & 31, instruction & 63
            imm = instruction & 65535
            signed = imm - 65536 if imm & 32768 else imm
            destination, delayed = delayed, None
            addr = (self.r[rs] + signed) & 0xFFFFFFFF
            if instruction == 0: pass
            elif op == 0:
                if fn == 0: self.r[rd] = self.r[rt] << shift
                elif fn == 2: self.r[rd] = self.r[rt] >> shift
                elif fn in (0x21, 0x2D): self.r[rd] = self.r[rs] + self.r[rt]
                elif fn == 0x25: self.r[rd] = self.r[rs] | self.r[rt]
                elif fn == 0x2B: self.r[rd] = int(self.r[rs] < self.r[rt])
                elif fn == 8: delayed = self.r[rs]
                else: raise AssertionError(hex(instruction))
            elif op == 2:
                delayed = (instruction & 0x3FFFFFF) << 2
            elif op == 3:
                self.r[31] = pc + 8
                delayed = (instruction & 0x3FFFFFF) << 2
            elif op == 4:
                if self.r[rs] == self.r[rt]: delayed = pc + 4 + signed * 4
            elif op == 5:
                if self.r[rs] != self.r[rt]: delayed = pc + 4 + signed * 4
            elif op == 9: self.r[rt] = self.r[rs] + signed
            elif op == 11: self.r[rt] = int(self.r[rs] < (signed & 0xFFFFFFFF))
            elif op == 12: self.r[rt] = self.r[rs] & imm
            elif op == 13: self.r[rt] = self.r[rs] | imm
            elif op == 14: self.r[rt] = self.r[rs] ^ imm
            elif op == 15: self.r[rt] = imm << 16
            elif op == 35: self.r[rt] = self.memory.read_int32(addr)
            elif op == 36: self.r[rt] = self.memory.read_int8(addr)
            elif op == 40: self.memory.write_int8(addr, self.r[rt] & 255)
            elif op == 43: self.memory.write_int32(addr, self.r[rt])
            elif op == 55: self.r[rt] = int.from_bytes(self.memory.read_bytes(addr, 8), "little")
            elif op == 63: self.memory.write_bytes(addr, self.r[rt].to_bytes(8, "little"))
            else: raise AssertionError(hex(instruction))
            self.r = [x & 0xFFFFFFFF for x in self.r]
            self.r[0] = 0
            pc = destination if destination is not None else pc + 4
        raise AssertionError("Native code did not return")


def plans(memory):
    code = memory.read_bytes(0xD00000, 0x400000)
    v = vendor.prepare(memory, code_start=0xD00000, code=code,
                       base_locations={2: "weapon"}, titan_locations={2: "titan"})
    t = item_toast.prepare(memory, code_start=0xD00000, code=code,
                          small_box=memory.fixture["small_box"], starter=v.starter)
    a = armour_pickup.prepare(memory, code_start=0xD00000, code=code, locations={0: "armour"})
    return v, t, a


class NativePatchTests(unittest.TestCase):
    def test_vendor_display_survives_post_relocation_loading(self):
        p = Memory()
        planet = SimpleNamespace(is_ready=False, planet_id=1, starting_planet_id=None,
                                 menu=SimpleNamespace(get=lambda: 9))
        v = SimpleNamespace(planet=planet, native_plan=None,
                            _is_titan_pending=lambda name: False)
        runtime = NativeRuntime(p, v, lambda _: None, lambda _: None)
        runtime.enabled = True
        runtime.vendor_scouts = object()
        display = Mock()
        with patch("worlds.rac_size_matters.core.native_runtime.vendor_presentation.prepare",
                   return_value=display):
            runtime.gate.held_module = lambda: (1, 0xD4B380)
            runtime._prepare(1, 0xD4B380)
        runtime.gate.arm = lambda: None
        runtime.gate.held_module = lambda: None
        runtime._released = True
        p.write_int32(runtime.gate.STATE, 5)
        self.assertTrue(runtime.tick())
        display.close.assert_not_called()
        display.tick.assert_not_called()
        p.write_int32(runtime.gate.STATE, 6)
        runtime.tick()
        display.tick.assert_not_called()
        planet.is_ready = True
        runtime.tick()
        display.tick.assert_called_once_with(True, runtime.vendor_scouts)
        self.assertIs(runtime.presentation, display)
        self.assertIsNone(runtime._presentation_pending)

    def test_all_supported_layout_variants_install_and_restore(self):
        for fixture in FIXTURES:
            with self.subTest(fixture=fixture):
                p = Memory(fixture)
                original = bytes(p.data)
                patches = plans(p)
                for patch in patches: patch.install()
                item_toast.show(patches[1], receipt_text("Lacerator", "Sender"))
                for patch in reversed(patches): patch.restore()
                self.assertEqual(p.data, original)

    def test_vendor_purchase_records_even_when_already_owned(self):
        p = Memory()
        v, _, _ = plans(p)
        v.install()
        selection, ownership = 0x1800000, 0xF3EA5C
        p.write_int32(selection + 0x14, 2)
        p.write_int32(ownership, 1)
        cpu = CPU(p)
        cpu.r[17] = selection
        base = v.edits[0].address
        cpu.run(base, stop=base + 76)
        self.assertEqual(p.read_int8(v.tables["base"] + 2), 2)
        self.assertEqual(p.read_int32(ownership), 1)
        self.assertEqual(p.read_int8(v.tables["titan"] + 2), 3)

    def test_armour_gate_uses_physical_journal(self):
        p = Memory()
        _, _, a = plans(p)
        a.install()
        p.write_int8(0x1F4B35A, 1)
        getter = (p.read_int32(a.edits[0].address) & 0x3FFFFFF) << 2
        cpu = CPU(p)
        cpu.r[4] = 0
        cpu.run(getter)
        self.assertEqual(cpu.r[2], 0)
        recorder = getter + 20
        cpu = CPU(p)
        cpu.run(recorder)
        self.assertEqual(p.read_int8(a.table), 2)
        self.assertEqual(p.read_int8(0x1F4B35A), 1)
        cpu = CPU(p)
        cpu.run(getter)
        self.assertEqual(cpu.r[2], 1)

    def test_sprout_records_without_granting_or_equipping(self):
        p = Memory("ryllus")
        s = sprout_pickup.prepare(p)
        s.install()
        cpu = CPU(p)
        cpu.r[8], cpu.r[10] = 0x1800000, 2
        cpu.run(sprout_pickup.START + 0x40, stop=sprout_pickup.START + 0x58)
        self.assertEqual(p.read_int8(sprout_pickup.JOURNAL), 2)
        self.assertEqual(p.read_int8(0x1800045), 2)
        self.assertEqual(cpu.calls, [])
        p.write_int8(sprout_pickup.JOURNAL, 1)
        cpu = CPU(p)
        cpu.run(sprout_pickup.START - 0xC4, stop=sprout_pickup.START - 0xB8)
        self.assertEqual(cpu.r[2], 0)

    def test_toast_only_calls_rendering_functions_and_expires(self):
        p = Memory()
        v, t, _ = plans(p)
        v.install(); t.install()
        before = p.read_bytes(p.fixture["small_box"], 0x40)
        text = receipt_text("Lacerator", "Sender")
        item_toast.show(t, text)
        self.assertEqual(p.read_bytes(t.message, len(text)), text)
        entry = t.edits[0].address
        stubs = [(p.read_int32(entry + offset) & 0x3FFFFFF) << 2 for offset in (8, 40, 52, 72)]
        p.write_int32(t.timer, 1)
        cpu = CPU(p); cpu.run(entry, stubs=stubs)
        self.assertEqual(cpu.calls, stubs)
        self.assertEqual(p.read_int32(t.timer), 0)
        cpu = CPU(p); cpu.run(entry, stubs=stubs)
        self.assertEqual(cpu.calls, stubs[:1])
        self.assertEqual(p.read_bytes(p.fixture["small_box"], 0x40), before)

    def test_receipt_colours_and_control_byte_sanitization(self):
        normal = receipt_text("Lacerator", "Player\x90\nTwo")
        self.assertIn(b"\x90\x0dLacerator", normal)
        self.assertIn(b"\x90\x0bPlayer??Two", normal)
        self.assertIn(b"\x90\x03Trap", receipt_text("Trap", "Sender", True))
        formatted = item_toast.format_text(receipt_text("X" * 200, "Y" * 200))
        self.assertLessEqual(len(formatted), 96)
        self.assertEqual(formatted[-1], 0)
        self.assertEqual(formatted.count(b"\n"), 1)

    def test_bad_signature_causes_no_writes(self):
        p = Memory()
        v, _, _ = plans(p)
        p.data[v.edits[0].address] ^= 1
        with self.assertRaises(RuntimeError): v.install()
        self.assertEqual(p.writes, [])

    def test_partial_install_rolls_back(self):
        p = Memory()
        v, _, _ = plans(p)
        before = bytes(p.data)
        p.fail_once = v.edits[1].address
        with self.assertRaises(OSError): v.install()
        self.assertEqual(p.data, before)

    def test_scan_terminates_at_short_final_chunk(self):
        p = Memory()
        self.assertIsNone(_scan(p, b"abcdefghijk", start=0, end=101, chunk=32))

    def test_runtime_installs_before_rebinding_same_planet(self):
        p = Memory()
        planet = SimpleNamespace(is_ready=True, planet_id=1)
        v = SimpleNamespace(planet=planet, native_plan=None)
        runtime = NativeRuntime(p, v, lambda _: None, lambda _: None)
        runtime.gate.held_module = lambda: (1, 0xD4B380)
        runtime._prepare(1, 0xD4B380)
        self.assertFalse(planet.is_ready)
        self.assertEqual(planet._pending_planet_id, 1)
        self.assertEqual(planet._prev_gate, -1)
        self.assertEqual(len(runtime.plans), 7)
        self.assertIn(runtime.skin, runtime.plans)
        self.assertEqual(p.read_int32(pokitaru_ship.SITE), 0x24020001)
