import asyncio
import time
import uuid

from ..core.player_bolts import MAX_PLAYER_BOLTS
from ..core.traps import traps_ready


class RingLinkMixin:
    """Exchange currency deltas, never absolute balances or AP bolt grants."""

    def _reset_ring_link(self) -> None:
        self._ring_link_source = uuid.uuid4().int & ((1 << 53) - 1)
        self._ring_link_remainder = 0
        self._last_ring_link_push = 0.0
        self._ring_link_seen = set()

    def _ring_link_ready(self) -> bool:
        return (self._ring_link_enabled and self.ap_connected and self.slot is not None
                and self.pine_connected and self._items_received_ready and self._save_data_received
                and not self._connection_sync_pending and not self._wiring.at_main_menu
                and self._wiring.planet.is_ready and not self._wiring.native.waiting
                and traps_ready(self.pine))

    def _bolts_per_ring(self) -> int:
        return 100 * max(1, self._wiring.player_bolts.multiplier)

    async def _set_ring_link_enabled(self, enabled: bool) -> None:
        async with self._pine_lock:
            self._ring_link_enabled = enabled
            self._ring_link_remainder = 0
            # Do not export changes collected while this link was disabled.
            self._wiring.player_bolts._prev = None
        await self._update_link_tag("RingLink", enabled)
        self._log(f"[RAC] RingLink {'enabled' if enabled else 'disabled'}.")

    def _record_ring_link_change(self, delta: int) -> None:
        """Called under the PINE lock by the ordinary bolt gain/boost tracker."""
        if not self._ring_link_ready():
            return
        self._ring_link_remainder += delta

    def _maybe_sync_ring_link(self) -> None:
        if not self._ring_link_ready():
            self._ring_link_remainder = 0
            return
        now = time.monotonic()
        if now - self._last_ring_link_push < 0.5:
            return
        ratio = self._bolts_per_ring()
        # Truncate toward zero: a partial negative ring must not round down.
        amount = abs(self._ring_link_remainder) // ratio
        if self._ring_link_remainder < 0:
            amount = -amount
        if not amount:
            return
        self._ring_link_remainder -= amount * ratio
        self._last_ring_link_push = now
        asyncio.create_task(self.send_msgs([{
            "cmd": "Bounce", "tags": ["RingLink"],
            "data": {"time": time.time(), "source": self._ring_link_source, "amount": amount},
        }]))

    async def _receive_ring_link(self, data: dict) -> None:
        amount, source, timestamp = data.get("amount"), data.get("source"), data.get("time")
        if (type(amount) is not int or type(source) is not int
                or type(timestamp) not in (int, float) or source == self._ring_link_source):
            return
        async with self._pine_lock:
            if not self._ring_link_ready():
                return
            key = (source, timestamp, amount)
            if key in self._ring_link_seen:
                return
            if len(self._ring_link_seen) >= 1024:
                self._ring_link_seen.clear()
            self._ring_link_seen.add(key)
            bolts = self._wiring.player_bolts
            # Account for pickups since the last tick before overwriting the baseline.
            bolts.apply_boost()
            value = max(0, min(MAX_PLAYER_BOLTS, bolts.get() + amount * self._bolts_per_ring()))
            bolts.set(value)
            bolts.rebaseline(value)
