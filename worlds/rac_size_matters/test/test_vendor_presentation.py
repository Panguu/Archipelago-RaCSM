import json
import struct
import unittest
from pathlib import Path
from types import SimpleNamespace

from .test_native_patches import Memory
from ..client.vendor_scouts import VendorScouts, VendorReward
from ..core import vendor_presentation as native
from ..core.patches.asm import packed


class TestVendorPresentation(unittest.TestCase):
    def test_purchase_mapping_and_scout_scope(self):
        scouts = VendorScouts({})
        scouts.locations = {(0, 4): 100, (2, 4): 101}
        scouts.allowed = {100, 101}
        self.assertEqual(scouts.request({100, 999}), {
            'cmd': 'LocationScouts', 'locations': [100], 'create_as_hint': 0})
        scouts.update([SimpleNamespace(location=100, item=200, player=2, flags=1),
                       SimpleNamespace(location=101, item=201, player=3, flags=0)],
                      lambda item, slot: f'Item {item} from game {slot}', lambda slot: f'Player {slot}')
        self.assertEqual(scouts.for_purchase(0, 4).recipient_slot, 2)
        self.assertEqual(scouts.for_purchase(2, 4).recipient_slot, 3)
        self.assertIsNone(scouts.for_purchase(1, 4))
        self.assertEqual(scouts.for_purchase(0, 4).title_color, 2)

    def test_retail_module_resolution(self):
        fixtures = json.loads((Path(__file__).parent / 'fixtures/vendor_presentation_us.json').read_text())
        for name, row in fixtures.items():
            with self.subTest(planet=name):
                memory = Memory()
                for address, data in row['segments']:
                    memory.write_bytes(address, bytes.fromhex(data))
                plan = native.prepare(memory, 0xD00000, memory.read_bytes(0xD00000, 0x500000))
                for field, value in row['addresses'].items():
                    self.assertEqual(getattr(plan, field), value)

    def test_text_icons_restore_and_purchase_identity(self):
        memory = Memory()
        render, header, strings, equipment, icons, textures = (0xD10000, 0x300000, 0x310000, 0x320000, 0x330000, 0x340000)
        memory.write_bytes(render, native.RENDER_SIGNATURE)
        plan = native.VendorPresentation(memory, render, header, strings, equipment, icons, textures)
        rows, table, title, description, spec = 0x350000, 0x360000, 0x370000, 0x370100, 0x380000
        offer = (1, 50, 0, 35000, 0, 4, 0)
        ammo = (1, 50, 0, 100, 0, 4, 1)
        memory.write_bytes(rows, packed(*offer, *ammo))
        memory.write_bytes(header, packed(rows, 2, 1, 0))
        memory.write_bytes(strings, packed(table, 1, 1, 0, 2, 0))
        memory.write_bytes(table, packed(44, title, 818, description))
        memory.write_bytes(title, b'Acid Bomb Glove\0')
        vanilla = b'Original weapon description. ' * 8 + b'\0'
        memory.write_bytes(description, vanilla)
        memory.write_int32(equipment + 4 * 88 + 16, spec)
        memory.write_bytes(spec + 16, packed(44, 818))
        memory.write_int32(icons + 4, 10)
        image, palette, pixels, colors = 0x390000, 0x391000, 0x392000, 0x393000
        memory.write_bytes(textures + 10 * 100 + 12, packed(image, palette))
        memory.write_bytes(image + 4, struct.pack('<4H', 5, 0, 32, 32))
        memory.write_bytes(palette + 8, struct.pack('<H', 256))
        memory.write_int32(image + 48, pixels)
        memory.write_int32(palette + 48, colors)
        reward = VendorReward(100, 200, 2, 'Progressive Sword', 'Other Player', 1)
        scouts = SimpleNamespace(for_purchase=lambda kind, key: reward if (kind, key) == (0, 4) else None)
        baseline = bytes(memory.data)
        plan.tick(True, scouts)
        self.assertEqual(memory.read_int32(rows + 4), 1)
        self.assertEqual(memory.read_bytes(rows + 12, 16), packed(*offer[3:]))
        self.assertEqual(memory.read_bytes(rows + 28, 28), packed(*ammo))
        self.assertIn(b'Progressive Sword', memory.read_bytes(description, len(vanilla)))
        self.assertIn(b'For Other Player', memory.read_bytes(description, len(vanilla)))
        memory.write_int32(header + 12, 1)
        plan.tick(True, scouts)
        self.assertEqual(memory.read_bytes(description, len(vanilla)), vanilla)
        plan.tick(False, scouts)
        memory.write_int32(header + 12, 0)
        self.assertEqual(bytes(memory.data), baseline)

    def test_changed_module_refuses_writes(self):
        memory = Memory()
        plan = native.VendorPresentation(memory, 0xD10000, 0, 0, 0, 0, 0)
        memory.writes.clear()
        with self.assertRaises(RuntimeError):
            plan.tick(True, None)
        self.assertEqual(memory.writes, [])
