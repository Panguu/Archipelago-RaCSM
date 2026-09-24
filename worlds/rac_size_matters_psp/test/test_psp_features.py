import json
import asyncio
import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from ..client.links import ResourceLinkMixin
from ..core.nanotech import NanotechChecks
from ..core.patches import CodePlan, Patch
from ..core.player import PlayerInventory
from ..pypsp.psp import Psp
from .test_psp_runtime import Memory


class TestNanotech(unittest.TestCase):
    def test_catchup_deduplicates_and_preserves_server_checks(self):
        checks = NanotechChecks()
        checks.sync_from_ap({"Nanotech Level: 7"})
        self.assertEqual(checks.check(8), ["Nanotech Level: 6", "Nanotech Level: 8"])
        self.assertEqual(checks.check(5), [])
        self.assertEqual(checks.check(8), [])

    def test_bad_memory_never_reports_checks(self):
        checks = NanotechChecks()
        for value in (None, float("nan"), float("inf"), -1, 0, 76, 7.2, "8", True):
            with self.subTest(value=value):
                self.assertEqual(checks.check(value), [])
        self.assertEqual(checks.check(6), ["Nanotech Level: 6"])

    def test_interval_and_maximum(self):
        checks = NanotechChecks()
        checks.interval, checks.maximum = 5, 16
        self.assertEqual(checks.check(75), ["Nanotech Level: 10", "Nanotech Level: 15"])

    def test_player_field_and_unbound_state(self):
        memory = Mock()
        memory.read_float.return_value = 8.0
        player = PlayerInventory(memory)
        self.assertIsNone(player.max_health)
        player.set_base(1)
        self.assertEqual(player.max_health, 8.0)
        memory.read_float.assert_called_once_with(0x09473BA8)
        player.set_base(255)
        self.assertIsNone(player.max_health)


class LinkContext(ResourceLinkMixin):
    def __init__(self):
        self._init_resource_links()
        self.team, self.slot = 2, 3
        self.tags = {"AP", "DeathLink"}
        self.psp_connected = True
        self.stored_data = {}
        self.send_msgs = AsyncMock()
        self.set_notify = Mock()
        self.ammo = {"Lacerator": 50, "Scorcher": 20}
        weapons = SimpleNamespace(weapons={"Lacerator": True, "Scorcher": False},
                                  get_ammo=lambda name: self.ammo[name],
                                  set_ammo=Mock(side_effect=lambda name, value: self.ammo.update({name: value})))
        bolts = Mock()
        bolts.get.return_value = 100
        bolts.set.side_effect = lambda value: setattr(bolts.get, "return_value", value)
        self._wiring = SimpleNamespace(planet=SimpleNamespace(is_ready=True, weapons=weapons),
                                       vendor_active=False, player_bolts=bolts)


class TestResourceLinks(unittest.IsolatedAsyncioTestCase):
    async def enable(self, context, kind):
        await context._set_resource_link(kind, True)
        context._resource_link_packet("Retrieved", {"keys": {context._resource_link_key(kind): None}})
        context.send_msgs.reset_mock()

    async def test_tags_are_additive(self):
        ctx = LinkContext()
        await self.enable(ctx, "ammo")
        await self.enable(ctx, "bolt")
        self.assertEqual(ctx.tags, {"AP", "DeathLink", "AmmoLink", "BoltLink"})
        await ctx._set_resource_link("ammo", False)
        self.assertEqual(ctx.tags, {"AP", "DeathLink", "BoltLink"})

    async def test_bolt_remote_is_rebaselined_and_not_echoed(self):
        ctx = LinkContext()
        await self.enable(ctx, "bolt")
        ctx.stored_data[ctx._resource_link_key("bolt")] = 150
        ctx._poll_resource_links()
        ctx._poll_resource_links()
        ctx._wiring.player_bolts.set.assert_called_once_with(150)
        ctx._wiring.player_bolts.rebaseline.assert_called_once_with(150)
        ctx.send_msgs.assert_not_called()

    async def test_ammo_rejects_invalid_values_and_unowned_weapons(self):
        ctx = LinkContext()
        await self.enable(ctx, "ammo")
        key = ctx._resource_link_key("ammo")
        for invalid in (-1, True, 10000, "20"):
            ctx.stored_data[key] = {"Lacerator": invalid, "Scorcher": 10}
            ctx._poll_resource_links()
        ctx._wiring.planet.weapons.set_ammo.assert_not_called()
        ctx.stored_data[key] = {"Lacerator": 30, "Scorcher": 10}
        ctx._wiring.vendor_active = True
        ctx._poll_resource_links()
        ctx._wiring.planet.weapons.set_ammo.assert_not_called()
        ctx._wiring.vendor_active = False
        ctx._poll_resource_links()
        ctx._wiring.planet.weapons.set_ammo.assert_called_once_with("Lacerator", 30)

    async def test_no_access_before_ready(self):
        ctx = LinkContext()
        await ctx._set_resource_link("bolt", True)
        ctx._poll_resource_links()
        ctx._wiring.player_bolts.get.assert_not_called()
        ctx._link_ready.add(ctx._resource_link_key("bolt"))
        ctx._wiring.planet.is_ready = False
        ctx._poll_resource_links()
        ctx._wiring.player_bolts.get.assert_not_called()

    async def test_own_bolt_echo_does_not_undo_a_new_pickup(self):
        ctx = LinkContext()
        await self.enable(ctx, "bolt")
        ctx._poll_resource_links()
        await asyncio.sleep(0)
        payload = ctx.send_msgs.call_args.args[0][0]
        self.assertEqual(payload["key"], "rsm_bolt_link_2")
        self.assertEqual(payload["operations"], [{"operation": "replace", "value": 100}])
        ctx._wiring.player_bolts.get.return_value = 110
        ctx.stored_data[ctx._resource_link_key("bolt")] = 100
        ctx._poll_resource_links()
        ctx._wiring.player_bolts.set.assert_not_called()

    async def test_ammo_echo_preserves_new_local_shot(self):
        ctx = LinkContext()
        await self.enable(ctx, "ammo")
        ctx._poll_resource_links()
        await asyncio.sleep(0)
        ctx.ammo["Lacerator"] = 49
        ctx.stored_data[ctx._resource_link_key("ammo")] = {"Lacerator": 50}
        ctx._poll_resource_links()
        self.assertEqual(ctx.ammo["Lacerator"], 49)
        ctx._wiring.planet.weapons.set_ammo.assert_not_called()


class TestControlReplies(unittest.TestCase):
    def test_stale_ticket_and_non_object_are_skipped(self):
        control = Psp()
        control._ws = Mock()
        control._ws.recv.side_effect = [json.dumps(x) for x in (
            [], {"event": "cpu.status", "ticket": "old", "pc": 1},
            {"event": "cpu.status", "ticket": "1", "pc": 2})]
        self.assertEqual(control._request("cpu.status")["pc"], 2)

    def test_unticketed_step_completion(self):
        control = Psp()
        control._ws = Mock()
        control._ws.recv.return_value = '{"event":"cpu.stepping"}'
        self.assertEqual(control._request("cpu.runUntil", response_event="cpu.stepping")["event"], "cpu.stepping")


class TestCodePatches(unittest.TestCase):
    def test_cpu_stays_stopped_through_write_and_restore(self):
        memory = Memory()
        events = []
        @contextmanager
        def paused():
            events.append("pause")
            try:
                yield
            finally:
                events.append("resume")
        memory.paused = paused
        memory.invalidate_code = lambda: events.append("clear")
        write = memory.write_bytes
        def checked_write(address, data):
            self.assertEqual(events[-1], "clear")
            write(address, data)
        memory.write_bytes = checked_write
        plan = CodePlan(memory, [Patch(0x08800000, b"abcd", b"wxyz")], name="code")
        plan.install()
        plan.restore()
        self.assertEqual(events, ["pause", "clear", "resume"] * 2)
        self.assertEqual(memory.data, b"abcd")

    def test_instruction_alignment_required(self):
        with self.assertRaises(ValueError):
            CodePlan(Memory(), [Patch(0x08800001, b"abcd", b"wxyz")], name="bad")
