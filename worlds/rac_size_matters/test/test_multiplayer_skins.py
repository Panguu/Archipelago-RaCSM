import json
import struct
import unittest
from pathlib import Path
from types import SimpleNamespace

from .test_native_patches import Memory, CPU
from ..core.patches import multiplayer_skins as mp
from ..core.patches.asm import Patch
from ..core.patches import mips as m

FIXTURES = json.loads((Path(__file__).parent / 'fixtures/multiplayer_skins_us.json').read_text())
GEOMETRY = json.loads((Path(__file__).parent / 'fixtures/multiplayer_geometry_us.json').read_text())


def prepare(name='pokitaru'):
    p = Memory()
    p.data = bytearray(0x2000000)
    f = FIXTURES[name]
    for address, data in f['segments']:
        p.write_bytes(address, bytes.fromhex(data))
    code = p.read_bytes(f['base'], 0x280000)
    skin = SimpleNamespace(begin=f['begin'], finish=f['finish'],
                           edits=[Patch(f['gate'] + 4, b'0000', b'0000')])
    plan = mp.prepare(p, code_start=f['base'], code=code, skin=skin)
    return p, f, plan


class MultiplayerSkinsTests(unittest.TestCase):
    def test_reinstalled_loader_forces_fresh_multiplayer_assets(self):
        p, _, plan = prepare()
        plan.install()
        for selected in range(mp.COUNT):
            with self.subTest(skin=selected):
                # A level reload retains the loaded id but installs descriptors
                # whose sizes are zero. Native begin must not skip the read.
                descriptor = plan.descriptors + selected * 24
                if selected >= 7:
                    self.assertEqual(p.read_int32(descriptor + 20), 0)
                cpu = CPU(p)
                cpu.r[m.S0] = cpu.r[m.S3] = selected
                cpu.r[m.S4] = plan.buffer
                cpu.r[m.S6] = plan.buffer + mp.PRIMARY_LIMIT
                calls = []
                cpu.run(plan.buffer + 0x75900, stubs={
                    0x1E92A20: lambda c: calls.append(c.r[m.S6]),
                })
                self.assertEqual(calls, [plan.buffer + 0x84000])
                self.assertEqual(cpu.r[m.S3], selected)
                self.assertEqual(cpu.r[m.S0] & 0xFFFFFFFF,
                                 0xFFFFFFFF if selected >= 7 else selected)

    def test_all_levels_install_restore_and_red_only_menu(self):
        for name in FIXTURES:
            with self.subTest(level=name):
                p, _, plan = prepare(name)
                before = bytes(p.data)
                plan.install()
                self.assertEqual(plan.count, 20)
                self.assertLessEqual(plan.count * 0xE4, 0x2000)
                for index in range(13):
                    row = plan.table + (7 + index) * 16
                    self.assertEqual(p.read_int32(row), 7 + index)
                    self.assertEqual(p.read_int32(row + 12), 7 + index)
                    descriptor = plan.descriptors + (7 + index) * 24
                    self.assertEqual(p.read_int32(descriptor + 4),
                                     p.read_int32(mp.MP_TABLE + index * 64 + 4))
                plan.restore()
                self.assertEqual(p.data, before)

    def test_native_converter_matches_full_skeleton_for_all_meshes(self):
        for index, (name, geometry) in enumerate(GEOMETRY.items()):
            with self.subTest(skin=name):
                p, f, plan = prepare()
                code = p.read_bytes(f['base'], 0x280000)
                def word(a): return struct.unpack_from('<I', code, a - f['base'])[0]
                def ptr(a, b):
                    low = word(b) & 65535
                    return ((word(a) & 65535) << 16) + (low - 65536 if low & 32768 else low)
                end, begin = f['finish'], f['begin']
                pending = ptr(end + 4, end + 16)
                changed = ptr(end + 0x98, end + 0xA4)
                apply = ptr(end + 0x9C, end + 0xA8)
                asset = (word(end + 0xB4) & 0x3FFFFFF) << 2
                size = (word(begin + 0xAC) & 0x3FFFFFF) << 2
                load = (word(begin + 0xE4) & 0x3FFFFFF) << 2
                commands = bytes.fromhex(geometry['commands'])
                mapping = bytes.fromhex(geometry['mapping'])
                plan.install()
                p.write_int32(pending, index + 7)
                p.write_int8(changed, 1)
                p.write_int8(apply, 1)
                b = plan.buffer
                p.write_int32(b + 28, b + 0x100)
                p.write_int32(b + 32, b + 0x200)
                p.write_int32(b + 36, b + 0x300)
                p.write_int32(b + 0x204, len(mapping))
                p.write_int32(b + 0x314, b + 0x400)
                p.write_bytes(b + 0x400, mapping)
                p.write_int32(b + 0x118, b + 0x600)  # placeholder
                p.write_int32(b + 0x11C, b + 0x1000)
                p.write_int32(b + 0x120, b + 0x1000 + len(commands))
                p.write_bytes(b + 0x1000, commands)
                cpu = CPU(p)
                cpu.run(plan.finish, stubs={
                    size: lambda c: c.r.__setitem__(m.V0, 0x4550),
                    load: lambda c: c.r.__setitem__(m.V0, 1),
                    asset: lambda c: c.r.__setitem__(m.V0, 1),
                }, max_steps=200000)
                self.assertEqual(cpu.r[m.V0], 1)
                self.assertEqual(p.read_int8(mp.MCP + 0x2E0), index + 7)
                self.assertEqual(p.read_int32(pending), 0xFFFFFFFF)
                self.assertEqual(p.read_int32(b + 32), b + 0x200)
                self.assertEqual(p.read_int32(b + 0x118), plan.promoted)
                self.assertEqual(p.read_bytes(plan.promoted, len(commands)),
                                 mp.promoted_commands(commands, mapping))
                self.assertEqual(p.read_bytes(b + 0x1000, len(commands)), commands)

    def test_missing_bone_mapping_is_rejected(self):
        with self.assertRaises(ValueError):
            mp.promoted_commands(struct.pack('<2I', 0xFA000002, 0xFE000000), b'\0\1')

    def test_unallocated_hero_buffer_rejected_without_writes(self):
        p, f, _ = prepare()
        p.write_int32(mp.MCP + 0x2DC, 0)
        before = bytes(p.data)
        with self.assertRaisesRegex(RuntimeError, 'not allocated'):
            mp.prepare(p, code_start=f['base'], code=p.read_bytes(f['base'], 0x280000), skin=None)
        self.assertEqual(p.data, before)
