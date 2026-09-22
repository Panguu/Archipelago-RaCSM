"""Probe PSP allocator imports at a known frame boundary; restore CPU registers."""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from worlds.rac_size_matters_psp.procmem import ProcMemTransport
from worlds.rac_size_matters_psp.core.patches.storage import PatchStorage
from worlds.rac_size_matters_psp.core.patches.counter import CounterHook
m=ProcMemTransport()
try:
    m.connect()
    with m.paused():
        # Research-only profile, verified on UCUS98633 Pokitaru. Never redirect
        # execution using these addresses on another overlay or executable.
        if m.read_int32(0x088c272c) != 1:
            raise RuntimeError("Allocator probe requires Pokitaru")
        m.invalidate_code()
        if m.read_bytes(0x091dd638, 8) != bytes.fromhex("a0ffbd274009043c"):
            raise RuntimeError("Unexpected Pokitaru frame-boundary instructions")
        for stub, syscall in ((0x0883bc08, 0x5003), (0x0883bc18, 0x5005),
                              (0x0883bc20, 0x5000), (0x0883bc28, 0x5004)):
            expected = (0x03e00008).to_bytes(4, "little") + ((syscall << 6) | 12).to_bytes(4, "little")
            if m.read_bytes(stub, 8) != expected:
                raise RuntimeError(f"Unexpected allocator stub at {stub:#x}")
        m._control._request("cpu.runUntil", address=0x091dd638, response_event="cpu.stepping")
        status=m._control._request("cpu.status")
        assert status['pc']==0x091dd638, status
        m.invalidate_code()
        regs=m._control._request("cpu.getAllRegs")["categories"][0]["uintValues"]
        print("saved", regs[32:], m._control._request("cpu.status"))
        def call(address, args):
            try:
                for index,value in enumerate(args):
                    m._control._request("cpu.setReg", category=0, register=4+index, value=value)
                m._control._request("cpu.setReg", name="ra", value=regs[32])
                m._control._request("cpu.setReg", name="pc", value=address)
                m._control._request("cpu.runUntil", address=regs[32], response_event="cpu.stepping")
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline:
                    state=m._control._request("cpu.status")
                    if state["pc"] == regs[32]:
                        break
                    time.sleep(.02)
                print("after call",state)
                assert state["pc"]==regs[32], state
                return m._control._request("cpu.getReg", name="v0")["uintValue"]
            finally:
                for index,value in enumerate(regs):
                    if index:
                        m._control._request("cpu.setReg", category=0, register=index, value=value)
        before = call(0x0883bc20, [])
        class Kernel:
            def allocate(self, size):
                return call(0x0883bc08, [2, 0x0883bf60, 1, size, 0])
            def head(self, block):
                return call(0x0883bc18, [block])
            def free(self, block):
                return call(0x0883bc28, [block])
        storage = PatchStorage(m, Kernel())
        storage.open()
        try:
            payload = storage.reserve("probe", 64)
            storage.write("probe", b"Archipelago PSP storage probe\0")
            assert m.read_bytes(payload.address, 30) == b"Archipelago PSP storage probe\0"
            print('owned buffer verified', hex(payload.address))
            hook = CounterHook(m, storage, 0x091dd638, bytes.fromhex("a0ffbd274009043c"), planet_id=1)
            hook.install()
            try:
                m._control._request("cpu.runUntil", address=0x091dd640, response_event="cpu.stepping")
                state = m._control._request("cpu.status")
                if not state.get("stepping") or state["pc"] != 0x091dd640:
                    raise RuntimeError(f"Counter hook did not reach return boundary: {state}")
                updated = m._control._request("cpu.getAllRegs")["categories"][0]["uintValues"]
                expected = list(regs)
                expected[4] = 0x09400000
                expected[29] = (expected[29] - 0x60) & 0xffffffff
                expected[32] = 0x091dd640
                # Subsequent allocator calls must restore the state after the
                # replayed prologue, not rewind to the original function entry.
                regs = updated
                assert updated == expected, (updated, expected)
                assert hook.count() == 1, hook.count()
                print("native counter executed once; registers and prologue verified")
            finally:
                hook.restore()
        finally:
            storage.close()
        after = call(0x0883bc20, [])
        assert before == after, (before, after)
        print('allocation/free round trip passed', hex(after))

finally:
    m.disconnect()
