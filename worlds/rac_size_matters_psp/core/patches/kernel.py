"""Nonblocking PSP SysMem calls at an identified HUD frame boundary.

Debugger traffic is CPU control/register metadata only. RAM uses pymem.
"""
from contextlib import contextmanager


class KernelBridge:
    STUBS = {
        'allocate': (0x0883BC08, bytes.fromhex('0800e003cc001400')),
        'head': (0x0883BC18, bytes.fromhex('0800e0034c011400')),
        'maximum': (0x0883BC20, bytes.fromhex('0800e0030c001400')),
        'free': (0x0883BC28, bytes.fromhex('0800e0030c011400')),
    }

    def __init__(self, memory, profile, *, interior=False):
        self.memory, self.profile = memory, profile
        self._active = False
        self.interior = interior

    @property
    def boundary(self):
        return self.profile.frame + (12 if self.interior else 0)

    @contextmanager
    def frame(self):
        from ..address_maps import CURRENT_PLANET_ADDRESS
        from ..structs.game import TransitionGateStruct, TRANSITION_GATE_IDLE
        with self.memory.paused(resume_on_error=False):
            planet = self.memory.read_int8(CURRENT_PLANET_ADDRESS)
            if self.memory.read_int32(TransitionGateStruct.BASE_ADDRESS) != TRANSITION_GATE_IDLE:
                raise RuntimeError('Cannot call SysMem during a transition')
            self.memory.invalidate_code()
            timer = self.profile.timer
            import struct
            expected = struct.pack('<3I', 0x27BDFFA0, 0x3C040000 | ((timer+0x8000)>>16),
                                   0x8C840000 | (timer&65535))
            if self.interior:
                from ..vendor_profiles import ANCHOR
                expected = ANCHOR
            if self.memory.read_bytes(self.boundary, len(expected)) != expected:
                raise RuntimeError('HUD boundary changed')
            control = self.memory._control
            if control._request('cpu.status')['pc'] != self.boundary:
                control._request('cpu.runUntil', address=self.boundary, response_event='cpu.stepping')
            status = control._request('cpu.status')
            if not status['stepping'] or status['pc'] != self.boundary:
                raise RuntimeError('Did not reach the HUD boundary')
            if (self.memory.read_int8(CURRENT_PLANET_ADDRESS) != planet
                    or self.memory.read_int32(TransitionGateStruct.BASE_ADDRESS) != TRANSITION_GATE_IDLE):
                raise RuntimeError('Planet changed before SysMem call')
            self._active = True
            try:
                yield
            finally:
                self._active = False

    def _call(self, name, *args):
        if not self._active:
            raise RuntimeError('SysMem call requires the HUD boundary')
        address, expected = self.STUBS[name]
        if self.memory.read_bytes(address, len(expected)) != expected:
            self.memory.invalidate_code()
            if self.memory.read_bytes(address, len(expected)) != expected:
                raise RuntimeError('PSP SysMem import changed')
        control = self.memory._control
        before = control._request('cpu.getAllRegs')['categories']
        if before[0]['uintValues'][32] != self.boundary:
            raise RuntimeError('CPU left the HUD boundary')
        try:
            for index, value in enumerate(args):
                control._request('cpu.setReg', category=0, register=4+index, value=value & 0xFFFFFFFF)
            control._request('cpu.setReg', name='ra', value=self.boundary)
            control._request('cpu.setReg', name='pc', value=address)
            control._request('cpu.runUntil', address=self.boundary, response_event='cpu.stepping')
            status = control._request('cpu.status')
            if not status['stepping'] or status['pc'] != self.boundary:
                raise RuntimeError('SysMem call did not return')
            return control._request('cpu.getReg', name='v0')['uintValue']
        finally:
            if not control._request('cpu.status')['stepping']:
                control._request('cpu.stepping')
            after = control._request('cpu.getAllRegs')['categories']
            for original, current in zip(before, after, strict=True):
                for index, (value, now) in enumerate(zip(original['uintValues'], current['uintValues'], strict=True)):
                    if value != now:
                        control._request('cpu.setReg', category=original['id'], register=index, value=value)
            restored = control._request('cpu.getAllRegs')['categories']
            if any(a['uintValues'] != b['uintValues'] for a,b in zip(before, restored, strict=True)):
                raise RuntimeError('CPU register restoration failed; emulator left paused')

    def allocate(self, size):
        if not self._active:
            raise RuntimeError('Allocation requires the HUD boundary')
        # Borrow a small stack span only around the nonblocking HLE call.
        stack = self.memory._control._request('cpu.getReg', name='sp')['uintValue']-64
        original = self.memory.read_bytes(stack, 16)
        try:
            self.memory.write_bytes(stack, b'Archipelago\0'.ljust(16, b'\0'))
            value = self._call('allocate', 2, stack, 1, size, 0)
            return value if value < 0x80000000 else value-0x100000000
        finally:
            self.memory.write_bytes(stack, original)

    def head(self, block):
        return self._call('head', block)

    def free(self, block):
        return self._call('free', block)

    def maximum(self):
        return self._call('maximum')
