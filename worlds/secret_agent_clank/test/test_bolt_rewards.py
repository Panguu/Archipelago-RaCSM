import unittest
from unittest.mock import Mock

from ..core.address_maps import BOLTS_ADDRESS
from ..core.bolt_rewards import MAX_BOLTS, MAX_BOLTS_PER_PACK, BoltRewards, reward_balance
from ..core.core import Core
from .test_runtime import Memory


class FakeServerStorage:
    """In-memory stand-in for the server's delivered/pending bolt storage keys."""
    def __init__(self):
        self.delivered = {"count": 0, "starting_delivered": False}
        self.pending = None

    def on_state_changed(self, delivered, pending):
        self.delivered, self.pending = delivered, pending

    def configure_kwargs(self, **extra):
        return {
            "delivered": self.delivered["count"],
            "starting_delivered": self.delivered["starting_delivered"],
            "pending": self.pending,
            **extra,
        }


class BoltRewardTests(unittest.TestCase):
    def setUp(self):
        self.p = Memory()
        self.p.write_int32 = lambda a, n: self.p.batch_write_int32([(a, n)])
        self.p.write_int32(BOLTS_ADDRESS, 1000)
        self.server = FakeServerStorage()
        self.r = BoltRewards(self.p, Mock(), on_state_changed=self.server.on_state_changed)
        self.r.configure(**self.server.configure_kwargs())

    def test_percentage_rounding_compounding_and_zero(self):
        self.assertEqual(reward_balance(1000, 2), 1440)
        self.assertEqual(reward_balance(491, 1), 589)
        self.assertEqual(reward_balance(0, 3), 0)

    def test_each_pack_is_capped(self):
        self.assertEqual(reward_balance(999_995, 1), 999_995 + 199_999)
        self.assertEqual(reward_balance(1_000_000, 1), 1_000_000 + MAX_BOLTS_PER_PACK)
        self.assertEqual(reward_balance(5_000_000, 2), 5_000_000 + 2 * MAX_BOLTS_PER_PACK)

    def test_rewards_are_capped(self):
        self.assertEqual(reward_balance(8_900_000, 1), MAX_BOLTS)
        self.assertEqual(reward_balance(MAX_BOLTS + 5, 1), MAX_BOLTS)
        self.p.write_int32(BOLTS_ADDRESS, 8_500_000)
        self.r.configure(**self.server.configure_kwargs(starting_bolts=100_000))
        self.r.received = 3
        self.r.deliver()
        self.assertEqual(self.p.read_int32(BOLTS_ADDRESS), MAX_BOLTS)

    def test_bolts_earned_in_game_are_clamped(self):
        self.r.deliver()
        self.p.write_int32(BOLTS_ADDRESS, MAX_BOLTS + 1234)
        self.r.deliver()
        self.assertEqual(self.p.read_int32(BOLTS_ADDRESS), MAX_BOLTS)

    def test_starting_grant_precedes_rewards_and_survives_restart(self):
        self.r.configure(**self.server.configure_kwargs(starting_bolts=5000))
        self.r.received = 1
        self.r.deliver()
        self.assertEqual(self.p.read_int32(BOLTS_ADDRESS), 7200)
        self.p.write_int32(BOLTS_ADDRESS, 200)
        r = BoltRewards(self.p, Mock(), on_state_changed=self.server.on_state_changed)
        r.configure(**self.server.configure_kwargs(starting_bolts=5000))
        r.received = 1
        r.deliver()
        self.assertEqual(self.p.read_int32(BOLTS_ADDRESS), 200)

    def test_starting_grant_lost_ack_recovers_after_restart(self):
        self.r.configure(**self.server.configure_kwargs(starting_bolts=5000))
        original = self.p.write_int32
        def lost_ack(a, n):
            original(a, n)
            raise OSError("Lost acknowledgement")
        self.p.write_int32 = lost_ack
        with self.assertRaises(OSError):
            self.r.deliver()
        self.p.write_int32 = original
        r = BoltRewards(self.p, Mock(), on_state_changed=self.server.on_state_changed)
        r.configure(**self.server.configure_kwargs(starting_bolts=5000))
        r.deliver()
        self.assertEqual(self.p.read_int32(BOLTS_ADDRESS), 6000)
        self.assertTrue(self.server.delivered["starting_delivered"])

    def test_existing_reward_journal_receives_missing_starting_grant(self):
        self.server.delivered = {"count": 2, "starting_delivered": False}
        r = BoltRewards(self.p, Mock(), on_state_changed=self.server.on_state_changed)
        r.configure(**self.server.configure_kwargs(starting_bolts=5000))
        r.received = 2
        r.deliver()
        self.assertEqual(self.p.read_int32(BOLTS_ADDRESS), 6000)
        self.assertEqual(self.server.delivered["count"], 2)

    def test_duplicate_packets_and_restart_do_not_reaward(self):
        self.r.received = 2
        self.r.deliver()
        self.r.deliver()
        self.assertEqual(self.p.read_int32(BOLTS_ADDRESS), 1440)
        r = BoltRewards(self.p, Mock(), on_state_changed=self.server.on_state_changed)
        r.configure(**self.server.configure_kwargs())
        self.p.write_int32(BOLTS_ADDRESS, 500)  # Purchased something.
        r.received = 2
        r.deliver()
        self.assertEqual(self.p.read_int32(BOLTS_ADDRESS), 500)
        r.received = 3
        r.deliver()
        self.assertEqual(self.p.read_int32(BOLTS_ADDRESS), 600)

    def test_delivery_waits_for_game_readiness(self):
        core = Core(self.p)
        core.bolt_rewards = self.r
        core.native_runtime.service = Mock(return_value=False)
        core.case.check_transition = Mock(return_value=False)
        core.apply_inventory(ratchet={}, clank={}, received_names=["Bolts", "Bolts"])
        core.tick()
        self.assertEqual(self.r.received, 2)
        self.assertEqual(self.p.read_int32(BOLTS_ADDRESS), 1000)
        # deliver() must not save anything before the runtime is ready.
        self.assertEqual(self.server.delivered, {"count": 0, "starting_delivered": False})
        self.assertIsNone(self.server.pending)

    def test_lost_write_ack_recovers_without_duplicate(self):
        original = self.p.write_int32
        def lost_ack(a, n):
            original(a, n)
            raise OSError("Lost acknowledgement")
        self.p.write_int32 = lost_ack
        self.r.received = 1
        with self.assertRaises(OSError):
            self.r.deliver()
        self.p.write_int32 = original
        self.r.deliver()
        self.assertEqual(self.p.read_int32(BOLTS_ADDRESS), 1200)
        self.assertEqual(self.server.delivered["count"], 1)

    def test_reconfigure_replaces_in_memory_state(self):
        # Switching slots: configure() replaces the old slot's state entirely.
        self.r.received = 1
        self.r.deliver()
        other = FakeServerStorage()
        self.r.on_state_changed = other.on_state_changed
        self.r.configure(**other.configure_kwargs())
        self.r.received = 1
        self.r.deliver()
        self.assertEqual(self.p.read_int32(BOLTS_ADDRESS), 1440)
