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

    def test_owned_notification_hook_coexists_with_vendor_resolution(self):
        from types import SimpleNamespace
        from ..core.patches.notification import NotificationHook
        from ..core.patches.code import CodePlan
        from ..core.patches.plan import Patch
        memory = self.make_memory()
        profile = resolve(memory, 3)
        original = memory.read_bytes(profile.frame, 8)
        replacement = struct.pack('<2I', 0x0A640000, 0)
        hook = NotificationHook(memory, SimpleNamespace(), profile, 3)
        hook.plan = CodePlan(memory, [Patch(profile.frame, original, replacement)], name='Test')
        hook.plan.installed = True
        memory.write_bytes(profile.frame, replacement)
        self.assertIsNone(resolve(memory, 3))
        memory._notification_hook = hook
        self.assertEqual(resolve(memory, 3), profile)
        memory.write_int32(profile.frame, 0)
        self.assertIsNone(resolve(memory, 3))

    def test_icons_preview_and_scouted_text_restore_on_every_profile(self):
        from ..core.address_maps import WEAPON_VENDOR_ITEMS, WEAPON_VENDOR_SLOTS, WEAPON_ARRAY_BASE_BY_PLANET
        for planet in map(int, PROFILES):
            with self.subTest(planet=planet):
                memory = self.make_memory(planet)
                memory.get_game_id = lambda: 'UCUS98633'
                profile = resolve(memory, planet)
                self.assertIsNotNone(profile)
                view = VendorPresentation(memory)
                memory.write_int32(profile.menu, 9)
                memory.write_int32(WEAPON_VENDOR_SLOTS, 1)
                memory.write_int32(WEAPON_VENDOR_ITEMS, 4)
                memory.write_bytes(profile.rows, struct.pack('<7I', 4, 0, 1, 95, 0, 10000, 0))
                for i in range(2):
                    base = 0x09800000+i*0x1000
                    memory.write_int32(profile.icons+(95+i)*4, 438+i)
                    memory.write_bytes(profile.textures+(438+i)*44+12, struct.pack('<II', base, base+64))
                    memory.write_bytes(base+4, struct.pack('<4H', 4, 1, 32, 32))
                    memory.write_bytes(base+68, struct.pack('<3H', 3, 0, 16))
                    memory.write_int32(base+48, base+128)
                    memory.write_int32(base+112, base+640)
                    memory.write_bytes(base+128, bytes([i+1])*512)
                    memory.write_bytes(base+640, bytes([i+3])*64)
                memory.write_int32(WEAPON_ARRAY_BASE_BY_PLANET[planet]+1+2*88, 0x09900000)
                memory.write_bytes(0x09900010, struct.pack('<III', 30, 367, 96))
                memory.write_bytes(profile.text, struct.pack('<6I', 0x09901000, 1, 1, 0, 2, 1))
                memory.write_bytes(0x09901000, b'TDEF'+struct.pack('<II', 30, 0x09902000)+b'TDEF'+struct.pack('<II', 367, 0x09903000))
                memory.write_bytes(0x09903000, b'Original weapon description. '*12+b'\0')
                view.reward_for_id = lambda identity: ('Progressive Armour', 'Player Two')
                before = bytes(memory.data)
                view.update(planet, True, True)
                self.assertFalse(view.failed)
                self.assertIsNotNone(view.plan)
                for address in (0x09800080, 0x09801080):
                    self.assertEqual(memory.read_bytes(address, 512), view.pixels)
                self.assertIn(b'Progressive Armour', memory.read_bytes(0x09903000, 100))
                self.assertIn(b'For Player Two', memory.read_bytes(0x09903000, 100))
                view.update(planet, True, False)
                self.assertEqual(bytes(memory.data), before)

    def test_ryllus_weapon_table_matches_live_code_reference(self):
        from ..core.address_maps import WEAPON_ARRAY_BASE_BY_PLANET
        # Live UCUS98633: lui a0,0x0940; addiu a0,a0,-0x2dc4.
        # Table + 0xbf is the level byte for weapon ID 2.
        table = (0x0940 << 16) - 0x2dc4
        self.assertEqual(WEAPON_ARRAY_BASE_BY_PLANET[2], table+0xbf)
        self.assertEqual(WEAPON_ARRAY_BASE_BY_PLANET[2]+1+88, 0x093fd354)
