import struct
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from ..client.trap_link import TrapLinkMixin
from ..constants import ALL_TRAPS, DAMAGE_PERCENT, TRAP_LINK_RECEIVE, TRAP_LINK_SEND, SACTraps
from ..core import Core
from ..core.player import ActivePlayer
from .test_runtime import Memory

PLAYER = 0x120000


class DamageTrapTests(unittest.TestCase):
    def player(self, health, maximum=20.0):
        memory = Memory()
        player = ActivePlayer(memory)
        player._health = Mock(return_value=None if health is None else (PLAYER, health, maximum))
        return memory, player

    def health(self, memory):
        return struct.unpack_from("<f", memory.data, PLAYER + 0x274)[0]

    def test_takes_a_share_of_max_health(self):
        memory, player = self.player(20.0)
        self.assertTrue(player.damage(25))
        self.assertEqual(self.health(memory), 15.0)

    def test_never_goes_below_one(self):
        memory, player = self.player(3.0)
        self.assertTrue(player.damage(25))
        self.assertEqual(self.health(memory), 1.0)
        memory, player = self.player(1.0)
        self.assertTrue(player.damage(25))
        self.assertEqual(memory.writes, [])

    def test_no_player_defers(self):
        _, player = self.player(None)
        self.assertFalse(player.damage(25))

    def test_dispatch(self):
        player = Mock(damage=Mock(return_value=True))
        core = SimpleNamespace(case=SimpleNamespace(is_ready=True, active_player=player),
                               _inventory_initialized=True, _log=Mock())
        self.assertTrue(Core.activate_effect(core, SACTraps.DAMAGE))
        player.damage.assert_called_once_with(DAMAGE_PERCENT)


class Context(TrapLinkMixin):
    def __init__(self):
        self.slot = 1
        self.username = "Me"
        self.player_names = {1: "Me", 2: "Them"}
        self.tags = set()
        self.server = None
        self._trap_link_enabled = True
        self._trap_link_pending = []
        self._worker = SimpleNamespace(request=AsyncMock(return_value=True))
        self.send_msgs = AsyncMock()


class TrapLinkTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        start = patch("worlds.secret_agent_clank.client.trap_link.async_start", side_effect=lambda task: task.close())
        start.start()
        self.addCleanup(start.stop)

    def test_every_trap_round_trips(self):
        for trap in ALL_TRAPS:
            with self.subTest(trap):
                self.assertEqual(TRAP_LINK_RECEIVE[TRAP_LINK_SEND[trap]], trap)

    def test_unique_traps_keep_their_own_names(self):
        for trap in (SACTraps.BIG_HEADED, SACTraps.BOLT_CONFUSION):
            with self.subTest(trap):
                self.assertEqual(TRAP_LINK_SEND[trap], trap)

    def test_received_traps_go_out_under_the_shared_name(self):
        ctx = Context()
        ctx._send_trap_link(SACTraps.MIRRORED_LEVELS)
        message = ctx.send_msgs.call_args.args[0][0]
        self.assertEqual(message["cmd"], "Bounce")
        self.assertEqual(message["tags"], ["TrapLink"])
        self.assertEqual(message["data"]["trap_name"], "Mirror Trap")
        self.assertEqual(message["data"]["source"], "Me")

    def test_nothing_is_sent_while_disabled(self):
        ctx = Context()
        ctx._trap_link_enabled = False
        ctx._send_trap_link(SACTraps.DAMAGE)
        ctx.send_msgs.assert_not_called()

    async def test_known_traps_are_applied_in_order(self):
        ctx = Context()
        for name in ("Screen Flip Trap", "Damage Trap", "Unknown Trap"):
            ctx._on_trap_link({"tags": ["TrapLink"], "data": {"source": "Them", "trap_name": name}})
        await ctx._apply_trap_link()
        self.assertEqual([call.args for call in ctx._worker.request.await_args_list],
                         [("effect", SACTraps.MIRRORED_LEVELS), ("effect", SACTraps.DAMAGE)])
        self.assertEqual(ctx._trap_link_pending, [])

    async def test_a_trap_that_cant_apply_yet_waits(self):
        ctx = Context()
        ctx._worker.request.return_value = False
        ctx._on_trap_link({"tags": ["TrapLink"], "data": {"source": "Them", "trap_name": "One Hit KO"}})
        await ctx._apply_trap_link()
        self.assertEqual(ctx._trap_link_pending, [SACTraps.ONE_HP])

    def test_own_and_untagged_bounces_are_ignored(self):
        ctx = Context()
        ctx._on_trap_link({"tags": ["TrapLink"], "data": {"source": "Me", "trap_name": "Mirror Trap"}})
        ctx._on_trap_link({"tags": ["RingLink"], "data": {"source": "Them", "trap_name": "Mirror Trap"}})
        self.assertEqual(ctx._trap_link_pending, [])
