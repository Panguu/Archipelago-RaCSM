import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from ..client.ring_link import RingLinkMixin
from ..constants import RingLinkBehaviorOptions
from ..core.address_maps import BOLTS_ADDRESS
from ..core.bolt_rewards import MAX_BOLTS, BoltRewards
from ..core.ring_link import BASE_BOLTS_PER_RING, CHALLENGE_MODE_SCALE, RingLink
from .test_runtime import Memory


class RingLinkCoreTests(unittest.TestCase):
    def link(self, behavior=RingLinkBehaviorOptions.ITEMS, multiplier=1, balance=1000):
        self.memory = Memory()
        self.memory.write_int32(BOLTS_ADDRESS, balance)
        link = RingLink(self.memory)
        link.configure(behavior, multiplier)
        link.poll(balance)
        return link

    def test_play_changes_become_rings_and_keep_the_remainder(self):
        link = self.link()
        self.assertEqual(link.poll(1250), 2)
        self.assertEqual(link.poll(1300), 1)
        self.assertEqual(link.poll(1000), -3)

    def test_rate_follows_the_bolt_multiplier(self):
        link = self.link(multiplier=5)
        self.assertEqual(link.bolts_per_ring, BASE_BOLTS_PER_RING * 5)
        self.assertEqual(link.poll(2000), 2)

    def test_rate_follows_the_challenge_mode_tier(self):
        for tier, scale in enumerate(CHALLENGE_MODE_SCALE):
            with self.subTest(tier=tier):
                link = self.link(multiplier=5)
                link.challenge_mode = lambda: tier
                self.assertEqual(link.bolts_per_ring, BASE_BOLTS_PER_RING * 5 * scale)
                self.assertEqual(link.poll(1000 - 400_000), -400_000 // (BASE_BOLTS_PER_RING * 5 * scale))

    def test_first_poll_and_leaving_a_level_send_nothing(self):
        link = RingLink(Memory())
        self.assertEqual(link.poll(5000), 0)
        self.assertEqual(link.poll(None), 0)
        self.assertEqual(link.poll(9000), 0)

    def test_behavior_picks_which_received_changes_are_shared(self):
        for behavior, items, traps in ((RingLinkBehaviorOptions.ITEMS, 20, 0),
                                       (RingLinkBehaviorOptions.ITEMS_AND_TRAPS, 20, -8),
                                       (RingLinkBehaviorOptions.NEITHER, 0, 0)):
            with self.subTest(behavior=behavior):
                link = self.link(behavior)
                link.record("items", 2000)
                self.assertEqual(link.poll(3000), items)
                link.record("traps", -800)
                self.assertEqual(link.poll(2200), traps)

    def test_starting_bolts_are_never_shared(self):
        link = self.link(RingLinkBehaviorOptions.ITEMS_AND_TRAPS)
        link.record("starting", 500)
        self.assertEqual(link.poll(1500), 0)

    def test_received_rings_are_applied_and_not_sent_back(self):
        link = self.link(multiplier=5)
        link.receive(3)
        self.assertEqual(self.memory.read_int32(BOLTS_ADDRESS), 2500)
        self.assertEqual(link.poll(2500), 0)

    def test_received_losses_stop_at_zero(self):
        link = self.link(balance=40)
        link.receive(-10)
        self.assertEqual(self.memory.read_int32(BOLTS_ADDRESS), 0)
        self.assertEqual(link.poll(0), 0)

    def test_received_gains_stop_at_the_cap(self):
        link = self.link(balance=MAX_BOLTS - 5)
        link.receive(10)
        self.assertEqual(self.memory.read_int32(BOLTS_ADDRESS), MAX_BOLTS)

    def test_bolt_rewards_report_their_changes(self):
        memory = Memory()
        memory.write_int32(BOLTS_ADDRESS, 1000)
        rewards = BoltRewards(memory, lambda message: None)
        changes = []
        rewards.on_balance_changed = lambda kind, change: changes.append((kind, change))
        rewards.configure(starting_bolts=500)
        rewards.received = 1
        rewards.deliver()
        self.assertEqual(changes, [("starting", 500), ("items", 300)])


class Context(RingLinkMixin):
    def __init__(self):
        self.slot = 1
        self.tags = set()
        self.server = None
        self._ring_link_enabled = True
        self._ring_link_source = 1.0
        self._ring_link_outgoing = 0
        self._ring_link_pending = 0
        self._ring_link_sent_at = 0.0
        self._worker = SimpleNamespace(request=AsyncMock(return_value=True))
        self.send_msgs = AsyncMock()


class RingLinkClientTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        start = patch("worlds.secret_agent_clank.client.ring_link.async_start", side_effect=lambda task: task.close())
        start.start()
        self.addCleanup(start.stop)

    def amounts(self, ctx):
        return [call.args[0][0]["data"]["amount"] for call in ctx.send_msgs.call_args_list]

    async def test_changes_are_bounced(self):
        ctx = Context()
        await ctx._sync_ring_link(4)
        message = ctx.send_msgs.call_args.args[0][0]
        self.assertEqual(message["cmd"], "Bounce")
        self.assertEqual(message["tags"], ["RingLink"])
        self.assertEqual(message["data"]["amount"], 4)
        self.assertEqual(message["data"]["source"], 1.0)

    async def test_throttled_changes_are_added_up(self):
        ctx = Context()
        with patch("worlds.secret_agent_clank.client.ring_link.time.monotonic", side_effect=[10.0, 10.2, 10.6]):
            await ctx._sync_ring_link(1)
            await ctx._sync_ring_link(2)
            await ctx._sync_ring_link(-5)
        self.assertEqual(self.amounts(ctx), [1, -3])

    async def test_received_rings_are_applied(self):
        ctx = Context()
        ctx._on_ring_link({"tags": ["RingLink"], "data": {"source": 2.0, "amount": 3}})
        ctx._on_ring_link({"tags": ["RingLink"], "data": {"source": 3.0, "amount": -1}})
        await ctx._sync_ring_link(0)
        ctx._worker.request.assert_awaited_once_with("ring_link", 2)
        self.assertEqual(ctx._ring_link_pending, 0)

    async def test_own_and_other_bounces_are_ignored(self):
        ctx = Context()
        ctx._on_ring_link({"tags": ["RingLink"], "data": {"source": 1.0, "amount": 3}})
        ctx._on_ring_link({"tags": ["DeathLink"], "data": {"source": 2.0, "amount": 3}})
        self.assertEqual(ctx._ring_link_pending, 0)

    async def test_rings_wait_until_the_game_can_take_them(self):
        ctx = Context()
        ctx._worker.request.return_value = False
        ctx._on_ring_link({"tags": ["RingLink"], "data": {"source": 2.0, "amount": 3}})
        await ctx._sync_ring_link(0)
        self.assertEqual(ctx._ring_link_pending, 3)

    async def test_nothing_happens_when_off(self):
        ctx = Context()
        ctx._ring_link_enabled = False
        ctx._on_ring_link({"tags": ["RingLink"], "data": {"source": 2.0, "amount": 3}})
        await ctx._sync_ring_link(5)
        ctx.send_msgs.assert_not_called()
        ctx._worker.request.assert_not_called()
