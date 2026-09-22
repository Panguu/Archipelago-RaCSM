"""One-time UCUS98633 Pokitaru -> Kalidon live-test travel request.

Uses the game's travel routine at a verified frame boundary. All RAM access is
pymem; debugger commands are limited to CPU control and session metadata.
"""
import sys
import types
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / '.research/deps'))
# Keep this diagnostic independent of the shared Archipelago environment.
package = types.ModuleType('psp_probe')
package.__path__ = [str(root)]
sys.modules['psp_probe'] = package
from psp_probe.procmem import ProcMemTransport

m = ProcMemTransport()
try:
    m.connect()
    with m.paused():
        if m.read_int32(0x088c272c) != 1 or m.read_int32(0x088c0744) != 0xffffffff:
            raise RuntimeError('Requires loaded Pokitaru with no travel in progress')
        m.invalidate_code()
        for address, expected in ((0x091dd638, bytes.fromhex('a0ffbd274009043c')),
                                  (0x0914d8f4, bytes.fromhex('e0ffbd27ff00a530')),
                                  (0x0914d8a4, bytes.fromhex('0400c4ac0800c5ac'))):
            if m.read_bytes(address, len(expected)) != expected:
                raise RuntimeError(f'Travel instruction signature changed at {address:#x}')
        m._control._request('cpu.runUntil', address=0x091dd638, response_event='cpu.stepping')
        if m._control._request('cpu.status')['pc'] != 0x091dd638:
            raise RuntimeError('Did not reach frame boundary')
        categories = m._control._request('cpu.getAllRegs')['categories']
        print('CPU categories', [(c.get('name'), len(c.get('uintValues', []))) for c in categories], flush=True)
        try:
            m._control._request('cpu.setReg', name='a0', value=3)
            m._control._request('cpu.setReg', name='a1', value=0)
            m._control._request('cpu.setReg', name='ra', value=0x091dd638)
            m._control._request('cpu.setReg', name='pc', value=0x0914d8f4)
            m._control._request('cpu.runUntil', address=0x091dd638, response_event='cpu.stepping')
            if m._control._request('cpu.status')['pc'] != 0x091dd638:
                raise RuntimeError('Travel routine did not return')
            print('Queued travel', m.read_int32(0x094a0fcc), m.read_int32(0x094a0fd0), flush=True)
        finally:
            for category, values in enumerate(categories):
                for index, value in enumerate(values['uintValues']):
                    if category == 0 and index == 0:
                        continue
                    m._control._request('cpu.setReg', category=category, register=index, value=value)
    deadline = time.monotonic() + 45
    previous = None
    while time.monotonic() < deadline:
        state = (m.read_int32(0x088c272c), m.read_int32(0x088c0744))
        if state != previous:
            print('Travel state', state, flush=True)
            previous = state
        if state == (3, 0xffffffff):
            print('Kalidon loaded', flush=True)
            break
        time.sleep(.2)
    else:
        raise RuntimeError('Kalidon arrival not confirmed within 45 seconds')
finally:
    m.disconnect()
