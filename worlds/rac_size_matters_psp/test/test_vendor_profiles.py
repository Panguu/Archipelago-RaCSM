import struct
import unittest
from contextlib import nullcontext
from unittest.mock import Mock

from ..core.address_maps import CURRENT_PLANET_ADDRESS, MENU_ADDR_BY_PLANET_ID
from ..core.structs.game import TransitionGateStruct
from ..core.vendor_profiles import ANCHOR, PROFILES, resolve
from ..core.vendor_presentation import VendorPresentation
from .test_client_gameplay import GameMemory


class TestVendorProfiles(unittest.TestCase):
    def make_memory(self, planet=3):
        memory = GameMemory()
        memory.paused = nullcontext
        memory.invalidate_code = Mock()
        memory.write_int8(CURRENT_PLANET_ADDRESS, planet)
        base = 0x09138D00
        profile = PROFILES[str(planet)]
        timer = base+profile['renderer']['relative']
        memory.write_bytes(base+profile['renderer']['code'], struct.pack('<3I',
            0x27BDFFA0, 0x3C040000 | ((timer+0x8000)>>16), 0x8C840000 | (timer&65535)))
        memory.write_bytes(base+profile['renderer']['code']+12, ANCHOR)
        for call in profile['panel_calls']:
            memory.write_bytes(base+profile['renderer']['code']+call['offset'], struct.pack('<2I',
                0x0C000000 | (((base+call['target'])>>2)&0x3FFFFFF), call['delay']))
        for name in ('rows', 'icons', 'textures', 'text'):
            ref = profile[name]
            words = ref['words'] + [0]*(16-len(ref['words']))
            address = base+ref['relative']-ref['delta']
            words[ref['hi']] = ref['address_ops'][0] | ((address+0x8000)>>16)
            words[ref['lo']] = ref['address_ops'][1] | (address&65535)
            memory.write_bytes(base+ref['code'], struct.pack('<16I', *words))
        return memory

    def test_resolves_every_mapped_overlay(self):
        for planet in map(int, PROFILES):
            if planet not in MENU_ADDR_BY_PLANET_ID:
                continue
            with self.subTest(planet=planet):
                memory = self.make_memory(planet)
                result = resolve(memory, planet)
                self.assertIsNotNone(result)
                for field in ('rows', 'icons', 'textures', 'text'):
                    self.assertEqual(getattr(result, field), 0x09138D00+PROFILES[str(planet)][field]['relative'])
                memory.invalidate_code.assert_called_once()

    def test_known_live_pokitaru_addresses_match_recovered_references(self):
        result = resolve(self.make_memory(1), 1)
        self.assertEqual((result.rows, result.icons, result.textures, result.menu), VendorPresentation.PROFILES[1])
        self.assertEqual(result.text, 0x094A0EC0)

    def test_known_live_kalidon_addresses(self):
        result = resolve(self.make_memory(), 3)
        self.assertEqual((result.rows, result.icons, result.textures, result.text),
                         (0x0941341C, 0x0940C23C, 0x09457FC0, 0x094B6F80))

    def test_rejects_jit_markers_and_modified_instructions(self):
        for replacement in (0x682C90E2, 0):
            memory = self.make_memory()
            address = 0x09138D00+PROFILES['3']['icons']['code']+8
            memory.write_int32(address, replacement)
            self.assertIsNone(resolve(memory, 3))

    def test_rejects_changed_relocation_and_duplicate_anchor(self):
        memory = self.make_memory()
        memory.write_bytes(0x09900000, ANCHOR)
        self.assertIsNone(resolve(memory, 3))
        memory = self.make_memory()
        ref = PROFILES['3']['text']
        address = 0x09138D00+ref['code']+ref['lo']*4
        memory.write_int32(address, memory.read_int32(address)+4)
        self.assertIsNone(resolve(memory, 3))

    def test_does_not_resolve_a_loading_or_wrong_overlay(self):
        memory = self.make_memory()
        self.assertIsNone(resolve(memory, 2))
        memory.write_int32(TransitionGateStruct.BASE_ADDRESS, 0)
        self.assertIsNone(resolve(memory, 3))
        memory.invalidate_code.assert_not_called()
