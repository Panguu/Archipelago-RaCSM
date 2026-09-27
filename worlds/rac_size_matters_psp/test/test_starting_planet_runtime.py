import struct
import unittest
from contextlib import nullcontext
from unittest.mock import Mock
from .test_client_gameplay import GameMemory
from ..core.address_maps import CURRENT_PLANET_ADDRESS
from ..core.patches.starting_planet import StartingPlanet, ELIGIBLE, INIT, ANCHOR, ANCHOR_OFFSET, initializer, packed, prepare
from ..core.structs.game import TransitionGateStruct


class TestStartingPlanetRuntime(unittest.TestCase):
    def test_unchanged_frontend_does_not_pause_or_clear_jit_again(self):
        self.runtime.configure(3)
        self.runtime.service()
        # Unrelated compiled entry markers must not trigger a global flush.
        self.memory.write_int32(self.base+INIT, 0x682C90E2)
        self.memory.invalidate_code.reset_mock()
        self.memory.paused = Mock(side_effect=AssertionError('Unexpected pause'))
        self.memory._write_raw = Mock(wraps=self.memory._write_raw)
        for _ in range(10):
            self.runtime.service()
        self.memory.paused.assert_not_called()
        self.memory.invalidate_code.assert_not_called()
        self.memory._write_raw.assert_not_called()

    def setUp(self):
        self.memory = GameMemory()
        self.memory.paused = nullcontext
        self.memory.invalidate_code = Mock()
        self.memory.get_game_id = lambda: 'UCUS98633'
        self.memory.write_int8(CURRENT_PLANET_ADDRESS, 0)
        self.base = 0x09138D00
        self.memory.write_bytes(self.base+INIT, initializer(self.base))
        self.memory.write_bytes(self.base+ANCHOR_OFFSET, ANCHOR)
        pointer = self.base+0x112690
        self.memory.write_bytes(self.base+0x1AAC, packed(0x8E240000|(pointer&65535),0x3C060005,0xAC851C2C))
        for offset in (0x198B4,0x19E34):
            self.memory.write_bytes(self.base+offset, packed(0x34040014,0x0C000000|((self.base+0xF38)>>2),0x34050001))
        self.original = bytes(self.memory.data)
        self.runtime = StartingPlanet(self.memory)

    def test_all_eligible_destinations_install_and_restore(self):
        for planet in sorted(ELIGIBLE):
            self.runtime.configure(planet)
            self.runtime.service()
            if planet != 1:
                self.assertEqual(self.memory.read_int32(self.base+0x198B4),0x34040000|planet)
                self.assertEqual(self.memory.read_int32(self.base+0x19E34),0x34040000|planet)
            self.runtime.close()
            self.assertEqual(bytes(self.memory.data), self.original)

    def test_new_save_rewrite_preserves_unrelated_defaults(self):
        plan = prepare(self.memory,self.base,23)
        # Interpret the three replacement instructions using MIPS semantics.
        regs = [0]*32
        regs[4],regs[5],regs[6] = 0x088C0B00,1,0xDEADBEEF
        stores = {}
        for word in struct.unpack('<3I',plan.edits[0].replacement):
            op,rs,rt,imm = word>>26,(word>>21)&31,(word>>16)&31,word&65535
            if op == 13: regs[rt] = regs[rs]|imm
            elif op == 43: stores[regs[rs]+((imm^32768)-32768)] = regs[rt]
            elif op == 15: regs[rt] = imm<<16
            else: self.fail('Unexpected instruction')
        self.assertEqual(stores,{0x088C0B00+0x1C2C:23})
        self.assertEqual(regs[4:7],[0x088C0B00,1,0x50000])

    def test_loading_or_gameplay_never_patches(self):
        self.runtime.configure(3)
        for planet,gate in ((1,0xFFFFFFFF),(2,0xFFFFFFFF),(0,0)):
            self.memory.write_int8(CURRENT_PLANET_ADDRESS,planet)
            self.memory.write_int32(TransitionGateStruct.BASE_ADDRESS,gate)
            before = bytes(self.memory.data)
            self.runtime.service()
            self.assertEqual(bytes(self.memory.data),before)
        self.memory.invalidate_code.assert_not_called()

    def test_changed_travel_call_fails_before_any_write(self):
        self.runtime.configure(3)
        self.memory.write_int32(self.base+0x19E38,0)
        before = bytes(self.memory.data)
        with self.assertRaises(RuntimeError): self.runtime.service()
        self.assertEqual(bytes(self.memory.data),before)

    def test_savestate_restored_originals_can_be_repatched(self):
        self.runtime.configure(3)
        self.runtime.service()
        self.memory.data[:] = self.original
        self.runtime.service()
        self.assertEqual(self.memory.read_int32(self.base+0x198B4),0x34040003)
        self.runtime.close()

    def test_departed_overlay_is_not_restored(self):
        self.runtime.configure(3)
        self.runtime.service()
        self.memory.write_int8(CURRENT_PLANET_ADDRESS,3)
        self.memory.write_bytes(self.base+0x1AAC,b'new overlay!')
        before = bytes(self.memory.data)
        self.runtime.close()
        self.assertEqual(bytes(self.memory.data),before)

    def test_option_change_and_disable_restore_originals(self):
        self.runtime.configure(2);self.runtime.service()
        self.runtime.configure(23);self.runtime.service()
        self.assertEqual(self.memory.read_int32(self.base+0x198B4),0x34040017)
        self.runtime.configure(None);self.runtime.service()
        self.assertEqual(bytes(self.memory.data),self.original)

    def test_invalid_destination_rejected(self):
        for planet in (0,5,6,9,10,20,True,'2'):
            with self.assertRaises(ValueError):self.runtime.configure(planet)
        self.assertEqual(bytes(self.memory.data),self.original)
