import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from ..client.context import CommonContext, SACContext
from ..core.patches import mips as m
from ..core.patches.asm import packed
from ..core.patches.connection_warning import HEARTBEAT_FRAMES, ConnectionWarning
from .mips_cpu import CPU
from .test_native_capture_plans import CaptureMemory


class ConnectionWarningTests(unittest.TestCase):
    def setUp(self):
        self.p = CaptureMemory()
        self.p.write_int32 = lambda a, n: self.p.batch_write_int32([(a, n)])
        self.warning = ConnectionWarning(self.p)
        self.warning.entry, self.warning.heartbeat = 0x110000, 0x110100
        self.show, self.render, self.message, self.cooldown = 0x120000, 0x130000, 0x140000, 0x140100
        self.original = packed([m.addiu(m.SP, m.SP, -32), m.sd(m.RA, 16, m.SP)])
        self.warning.code = self.warning.routine(self.warning.heartbeat, self.message,
            self.show, self.render, self.original, self.cooldown)
        self.p.write_bytes(self.warning.entry, self.warning.code)

    def frame(self):
        cpu = CPU(self.p)
        cpu.r[m.SP] = 0x1F0000
        sp, ra = cpu.r[m.SP], cpu.r[m.RA]
        def show(cpu):
            self.assertEqual(cpu.r[m.A0], self.message)
            self.assertEqual(cpu.r[m.A1], 0)
            self.assertEqual(cpu.r[m.A2], 60)
            self.assertEqual(self.p.read_int32(self.cooldown), 0)
            for reg in (m.V0, m.V1, m.A0, m.A1, m.A2, m.T0, m.T1):
                cpu.r[reg] = 0xBAD
        cpu.run(self.warning.entry, stop=self.render + 8, stubs={self.show: show})
        self.assertEqual(cpu.r[m.SP], sp - 32)
        self.assertEqual(cpu.r[m.RA], ra)
        self.assertEqual(int.from_bytes(self.p.read_bytes(sp - 16, 8), 'little'), ra)
        return cpu.calls

    def test_client_loss_expires_and_warning_repeats_until_reconnected(self):
        self.warning.refresh(True)
        for _ in range(HEARTBEAT_FRAMES):
            self.assertEqual(self.frame(), [])
        for _ in range(3):
            self.p.write_int32(self.cooldown, 999)
            self.assertEqual(self.frame(), [self.show])
        self.warning.refresh(True)
        self.assertEqual(self.frame(), [])
        self.warning.refresh(False)
        self.assertEqual(self.frame(), [self.show])

    def test_changed_code_rejects_heartbeat_write(self):
        self.p.write_int32(self.warning.entry, 0)
        with self.assertRaisesRegex(RuntimeError, 'code changed'):
            self.warning.refresh(True)
        self.assertEqual(self.p.read_int32(self.warning.heartbeat), 0)

    def test_retail_prologue_replays_relocated_address_on_both_paths(self):
        # Read from the running USA game: register saves follow this LUI.
        original = packed([0x27BDFFE0, 0x3C020053])
        code = self.warning.routine(self.warning.heartbeat, self.message,
            self.show, self.render, original, self.cooldown)
        self.p.write_bytes(self.warning.entry, code)
        for heartbeat in (0, HEARTBEAT_FRAMES):
            with self.subTest(heartbeat=heartbeat):
                self.p.write_int32(self.warning.heartbeat, heartbeat)
                cpu = CPU(self.p)
                cpu.r[m.SP] = 0x1F0000
                sp, ra = cpu.r[m.SP], cpu.r[m.RA]
                def show(cpu):
                    cpu.r[m.V0] = 0xBAD
                cpu.run(self.warning.entry, stop=self.render + 8, stubs={self.show: show})
                self.assertEqual(cpu.r[m.SP], sp - 32)
                self.assertEqual(cpu.r[m.RA], ra)
                self.assertEqual(cpu.r[m.V0], 0x530000)
                self.assertEqual(cpu.calls, [self.show] if heartbeat == 0 else [])

    def test_prepare_accepts_retail_lui_but_rejects_unexpected_instructions(self):
        symbols = {'HUD_ShowOneLiner__FPCcbi': self.show, 'HUD_RenderOneLiner__Fv': self.render}
        with patch('worlds.secret_agent_clank.core.patches.connection_warning.triangle_storage',
                   return_value=(0x150000, bytes(352))), patch(
                   'worlds.secret_agent_clank.core.patches.connection_warning.ItemNotifications') as notifications:
            notifications.return_value.bind.return_value = True
            notifications.return_value.binding = (0, 0, self.cooldown)
            for high in (0x53, 0x60):
                original = packed([0x27BDFFE0, m.lui(m.V0, high)])
                self.p.write_bytes(self.render, original)
                edits = self.warning.prepare(symbols, SimpleNamespace(patches=[], extra_ranges=[]))
                self.assertEqual(edits[-1].original, original)
                self.assertEqual(self.p.read_bytes(self.render, 8), original)
            self.p.write_bytes(self.render, packed([0x27BDFFE0, m.jr(m.RA)]))
            with self.assertRaisesRegex(RuntimeError, 'render prologue changed'):
                self.warning.prepare(symbols, SimpleNamespace(patches=[], extra_ranges=[]))
            self.assertIsNone(self.warning.heartbeat)

    def test_prepare_fits_shared_storage_and_rejects_overlap(self):
        symbols = {'HUD_ShowOneLiner__FPCcbi': self.show, 'HUD_RenderOneLiner__Fv': self.render}
        self.p.write_bytes(self.render, self.original)
        hooks = SimpleNamespace(patches=[], extra_ranges=[])
        with patch('worlds.secret_agent_clank.core.patches.connection_warning.triangle_storage',
                   return_value=(0x150000, bytes(352))), patch(
                   'worlds.secret_agent_clank.core.patches.connection_warning.ItemNotifications') as notifications:
            notifications.return_value.bind.return_value = True
            notifications.return_value.binding = (0, 0, self.cooldown)
            edits = self.warning.prepare(symbols, hooks)
            self.assertLessEqual(max(x.address + len(x.replacement) for x in edits), 0x150000 + 352)
            hooks.patches = edits
            with self.assertRaisesRegex(RuntimeError, 'occupied'):
                self.warning.prepare(symbols, hooks)


class ConnectionLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_server_loss_marks_watchdog_offline(self):
        context = SACContext.__new__(SACContext)
        context._stealth_load_task = None
        context._worker = SimpleNamespace(request=AsyncMock())
        with patch.object(CommonContext, 'connection_closed', new_callable=AsyncMock) as closed:
            await context.connection_closed()
        closed.assert_awaited_once()
        import asyncio
        await asyncio.sleep(0)
        context._worker.request.assert_awaited_once_with("ap_connected", False)
