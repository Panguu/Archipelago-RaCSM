import copy
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from ..core.patches.kernel import KernelBridge
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
