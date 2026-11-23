from collections.abc import Callable

from .address_maps import BOLTS_ADDRESS
from .bolt_rewards import MAX_BOLTS
from ..constants import RingLinkBehaviorOptions

# Shop items cost ~20,000 base bolts, about one level's worth of rings in a ring-based game.
BASE_BOLTS_PER_RING = 100
# Challenge Mode shop items cost ~400,000, so a typical purchase is the same number of rings in every tier.
CHALLENGE_MODE_SCALE = (1, 20, 20)


class RingLink:
    def __init__(self, pine, challenge_mode: Callable[[], int] = lambda: 0):
        self.pine = pine
        self.challenge_mode = challenge_mode
        self.share_items = False
        self.share_traps = False
        self.bolt_multiplier = 1
        self.last: int | None = None
        self.unshared = 0
        self.remainder = 0

    @property
    def bolts_per_ring(self) -> int:
        # Earned bolts are multiplied, so a ring stands for the same play at any multiplier.
        return BASE_BOLTS_PER_RING * self.bolt_multiplier * CHALLENGE_MODE_SCALE[self.challenge_mode()]

    def configure(self, behavior: int, bolt_multiplier: int) -> None:
        self.share_items = behavior in (RingLinkBehaviorOptions.ITEMS, RingLinkBehaviorOptions.ITEMS_AND_TRAPS)
        self.share_traps = behavior == RingLinkBehaviorOptions.ITEMS_AND_TRAPS
        self.bolt_multiplier = max(1, bolt_multiplier)
        self.remainder = 0

    def record(self, kind: str, change: int) -> None:
        """Note a bolt change the game didn't make, so it's only shared when the behavior allows it."""
        if not (kind == "items" and self.share_items or kind == "traps" and self.share_traps):
            self.unshared += change

    def poll(self, balance: int | None) -> int:
        """Rings to send for the bolt change since the last poll, or 0 while no level is loaded."""
        if balance is None or self.last is None:
            self.last, self.unshared = balance, 0
            return 0
        total = self.remainder + balance - self.last - self.unshared
        self.last, self.unshared = balance, 0
        rate = self.bolts_per_ring
        rings = abs(total) // rate * (1 if total >= 0 else -1)
        self.remainder = total - rings * rate
        return rings

    def receive(self, rings: int) -> None:
        before = self.pine.read_int32(BOLTS_ADDRESS)
        after = max(0, min(MAX_BOLTS, before + rings * self.bolts_per_ring))
        if after != before:
            self.pine.write_int32(BOLTS_ADDRESS, after)
        self.unshared += after - before
