import copy
import struct
from contextlib import nullcontext
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from ..core.patches.kernel import KernelBridge
from ..core.vendor_profiles import ANCHOR
from .test_client_gameplay import GameMemory


class CPU:
    def __init__(self, frame):
        self.frame = frame
        self.regs = [dict(id=i, uintValues=list(range(n))) for i,n in enumerate((35,32,128))]
        self.regs[0]['uintValues'][29] = 0x09801000
        self.regs[0]['uintValues'][32] = frame
        self.original = copy.deepcopy(self.regs)
        self.fail = False

    def _request(self, event, **args):
        names = {'v0': 2, 'sp': 29, 'ra': 31, 'pc': 32}
        if event == 'cpu.getAllRegs':
            return {'categories': copy.deepcopy(self.regs)}
        if event == 'cpu.status':
            return {'stepping': True, 'pc': self.regs[0]['uintValues'][32]}
        if event == 'cpu.getReg':
            return {'uintValue': self.regs[0]['uintValues'][names[args['name']]]}
        if event == 'cpu.setReg':
            category = args.get('category', 0)
            index = names[args['name']] if 'name' in args else args['register']
            self.regs[category]['uintValues'][index] = args['value']
            return {}
        if event == 'cpu.runUntil':
            for category in self.regs:
                category['uintValues'] = [0xDEADBEEF]*len(category['uintValues'])
            self.regs[0]['uintValues'][32] = self.frame
            self.regs[0]['uintValues'][2] = 123
            if self.fail:
                raise RuntimeError('Simulated control failure')
            return {}
        raise AssertionError(event)


class TestKernelBridge(unittest.TestCase):
    def make_frame_bridge(self, interior):
        memory = GameMemory()
        profile = SimpleNamespace(frame=0x091DD360, timer=0x09300000)
        bridge = KernelBridge(memory, profile, interior=interior)
        memory._control = CPU(bridge.boundary)
        memory._control._request = Mock(wraps=memory._control._request)
        memory.paused = lambda **kwargs: nullcontext()
        memory.invalidate_code = Mock()
        expected = ANCHOR if interior else struct.pack(
            '<3I', 0x27BDFFA0, 0x3C040930, 0x8C840000)
        memory.write_bytes(bridge.boundary, expected)
        return bridge, memory, expected

    def test_frame_waits_for_deferred_jit_invalidation(self):
        for interior in (False, True):
            with self.subTest(interior=interior):
                bridge, memory, expected = self.make_frame_bridge(interior)
                memory.write_int32(bridge.boundary, 0x682C90E2)
                before = bytes(memory.data)
                def finish_invalidation(_):
                    self.assertFalse(bridge._active)
                    memory._control._request.assert_not_called()
                    self.assertEqual(bytes(memory.data), before)
                    memory.write_bytes(bridge.boundary, expected)
                with patch('worlds.rac_size_matters_psp.core.patches.kernel.time.sleep',
                           side_effect=finish_invalidation) as sleep:
                    with bridge.frame():
                        self.assertTrue(bridge._active)
                sleep.assert_called_once_with(0.05)
                self.assertFalse(bridge._active)

    def test_frame_rejects_persistent_mismatch_without_running_cpu(self):
        for replacement in (0, 0x682C90E2):
            with self.subTest(replacement=replacement):
                bridge, memory, expected = self.make_frame_bridge(True)
                memory.write_int32(bridge.boundary, replacement)
                before = bytes(memory.data)
                with patch('worlds.rac_size_matters_psp.core.patches.kernel.time.monotonic',
                           side_effect=[0, 2]):
                    with self.assertRaisesRegex(RuntimeError, 'HUD boundary changed at') as error:
                        with bridge.frame():
                            self.fail('Invalid boundary was accepted')
                self.assertIn(expected.hex(), str(error.exception))
                self.assertIn(memory.read_bytes(bridge.boundary, len(expected)).hex(), str(error.exception))
                memory._control._request.assert_not_called()
                self.assertEqual(bytes(memory.data), before)
                self.assertFalse(bridge._active)

    def test_valid_frame_does_not_wait(self):
        bridge, memory, _ = self.make_frame_bridge(True)
        with patch('worlds.rac_size_matters_psp.core.patches.kernel.time.sleep') as sleep:
            with bridge.frame():
                self.assertTrue(bridge._active)
        sleep.assert_not_called()
        memory.invalidate_code.assert_called_once()
        self.assertFalse(bridge._active)

    def make_bridge(self):
        memory = GameMemory()
        profile = SimpleNamespace(frame=0x091DD360)
        memory._control = CPU(profile.frame)
        memory.invalidate_code = Mock()
        for address, data in KernelBridge.STUBS.values():
            memory.write_bytes(address, data)
        bridge = KernelBridge(memory, profile)
        bridge._active = True
        return bridge, memory

    def test_all_register_categories_restore_after_call(self):
        bridge, memory = self.make_bridge()
        self.assertEqual(bridge.head(1), 123)
        self.assertEqual(memory._control.regs, memory._control.original)

    def test_registers_restore_after_control_failure(self):
        bridge, memory = self.make_bridge()
        memory._control.fail = True
        with self.assertRaisesRegex(RuntimeError, 'control failure'):
            bridge.head(1)
        self.assertEqual(memory._control.regs, memory._control.original)

    def test_allocation_restores_borrowed_stack(self):
        bridge, memory = self.make_bridge()
        memory.write_bytes(0x09801000-64, b'previous stack!!')
        original = bytes(memory.data)
        self.assertEqual(bridge.allocate(1024), 123)
        self.assertEqual(bytes(memory.data), original)

    def test_allocation_failure_restores_borrowed_stack(self):
        bridge, memory = self.make_bridge()
        original = bytes(memory.data)
        memory._control.fail = True
        with self.assertRaises(RuntimeError):
            bridge.allocate(1024)
        self.assertEqual(bytes(memory.data), original)

    def test_rejects_unknown_stub_and_calls_outside_boundary(self):
        bridge, memory = self.make_bridge()
        memory.write_int32(KernelBridge.STUBS['head'][0], 0)
        with self.assertRaisesRegex(RuntimeError, 'import changed'):
            bridge.head(1)
        bridge._active = False
        with self.assertRaisesRegex(RuntimeError, 'requires the HUD boundary'):
            bridge.head(1)
