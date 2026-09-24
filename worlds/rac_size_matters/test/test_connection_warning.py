import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from ..client.context import CommonContext, RACContext
from ..core.native_runtime import NativeRuntime
from ..core.patches import connection_warning, item_toast
from .test_native_patches import CPU, Memory, plans


class ConnectionWarningTests(unittest.TestCase):
    def prepare(self):
        p = Memory()
        vendor, toast, _ = plans(p)
        warning = connection_warning.prepare(p, arena=vendor.arena, font=toast.font,
                                             colour=toast.colour, text=toast.text)
        vendor.install()
        warning.install()
        return p, vendor, toast, warning

    def test_warning_persists_without_client_and_clears_on_heartbeat(self):
        p, _, toast, warning = self.prepare()
        stubs = (toast.font, toast.colour, toast.text)
        connection_warning.refresh(warning, True)
        for _ in range(connection_warning.HEARTBEAT_FRAMES):
            cpu = CPU(p)
            cpu.run(warning.entry, stubs=stubs)
            self.assertEqual(cpu.calls, [])
        for _ in range(5):
            cpu = CPU(p)
            cpu.run(warning.entry, stubs=stubs)
            self.assertEqual(cpu.calls, list(stubs))
            self.assertEqual(p.read_int32(warning.heartbeat), 0)
        connection_warning.refresh(warning, True)
        cpu = CPU(p)
        cpu.run(warning.entry, stubs=stubs)
        self.assertEqual(cpu.calls, [])
        connection_warning.refresh(warning, False)
        cpu = CPU(p)
        cpu.run(warning.entry, stubs=stubs)
        self.assertEqual(cpu.calls, list(stubs))
        warning.restore()

    def test_warning_and_skin_hook_run_without_an_item_toast(self):
        for with_skin in (False, True):
            p, vendor, old_toast, warning = self.prepare()
            skin = vendor.arena + 0x100 if with_skin else None
            toast = item_toast.prepare(p, code_start=0xD00000,
                                      code=p.read_bytes(0xD00000, 0x400000),
                                      small_box=p.fixture["small_box"], starter=vendor.starter,
                                      frame_hook=skin, status_hook=warning.entry)
            toast.install()
            # Read native draw from the original prepared payload (before the hook).
            draw = (int.from_bytes(old_toast.edits[0].replacement[8:12], "little") & 0x3FFFFFF) << 2
            stubs = [draw, toast.font, toast.colour, toast.text]
            if skin is not None:
                stubs.append(skin)
            before = p.read_bytes(p.fixture["small_box"], 0x40)
            cpu = CPU(p)
            cpu.run(toast.edits[0].address, stubs=stubs)
            self.assertIn(toast.text, cpu.calls)
            if skin is not None:
                self.assertIn(skin, cpu.calls)
            self.assertEqual(p.read_int32(toast.timer), 0)
            self.assertEqual(p.read_bytes(p.fixture["small_box"], 0x40), before)
            item_toast.show(toast, "Received item")
            cpu = CPU(p)
            cpu.run(toast.edits[0].address, stubs=stubs)
            self.assertEqual(cpu.calls.count(toast.text), 2)
            self.assertEqual(p.read_int32(toast.timer), 179)

    def test_runtime_refreshes_only_current_module_and_warns_on_close(self):
        p, vendor, _, warning = self.prepare()
        runtime = NativeRuntime(p, SimpleNamespace(planet=SimpleNamespace(is_ready=False),
                                                  native_plan=None), lambda _: None, lambda _: None)
        runtime.connection_warning = warning
        runtime.module = 1
        p.write_int32(runtime.gate.STATE, 6)
        runtime.ap_connected = True
        runtime._poll()
        self.assertEqual(p.read_int32(warning.heartbeat), connection_warning.HEARTBEAT_FRAMES)
        runtime.ap_connected = False
        runtime._poll()
        self.assertEqual(p.read_int32(warning.heartbeat), 0)
        connection_warning.refresh(warning, True)
        runtime.close()
        self.assertEqual(p.read_int32(warning.heartbeat), 0)
        connection_warning.refresh(warning, True)
        p.write_int32(0x1F4C76C, 2)
        runtime.close()
        self.assertEqual(p.read_int32(warning.heartbeat), connection_warning.HEARTBEAT_FRAMES)


class ConnectionLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_common_client_disconnect_callback_marks_offline(self):
        # Invoke on a real class instance without opening sockets or initializing UI.
        context = RACContext.__new__(RACContext)
        context._wiring = SimpleNamespace(native=SimpleNamespace(ap_connected=True))
        with patch.object(CommonContext, "connection_closed", new_callable=AsyncMock) as closed:
            await context.connection_closed()
        closed.assert_awaited_once()
        self.assertFalse(context._wiring.native.ap_connected)
