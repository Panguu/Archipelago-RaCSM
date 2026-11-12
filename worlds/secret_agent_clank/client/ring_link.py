import time

from CommonClient import logger
from Utils import async_start

RING_LINK_TAG = "RingLink"
SEND_INTERVAL = 0.5


class RingLinkMixin:
    async def _set_ring_link_enabled(self, enabled: bool) -> None:
        self._ring_link_enabled = enabled
        self._ring_link_outgoing = 0
        self._ring_link_pending = 0
        old_tags = set(self.tags)
        if enabled:
            self.tags.add(RING_LINK_TAG)
        else:
            self.tags.discard(RING_LINK_TAG)
        if self.server and self.server.socket and self.tags != old_tags:
            await self.send_msgs([{"cmd": "ConnectUpdate", "tags": list(self.tags)}])
        logger.info(f"[SAC] Ring Link {'enabled' if enabled else 'disabled'}.")

    def _on_ring_link(self, args: dict) -> None:
        data = args.get("data", {})
        if (not self._ring_link_enabled or RING_LINK_TAG not in args.get("tags", ())
                or data.get("source") == self._ring_link_source):
            return
        amount = data.get("amount")
        if isinstance(amount, int):
            self._ring_link_pending += amount

    async def _sync_ring_link(self, rings: int) -> None:
        """Called after every game tick with the rings this game's bolt change is worth."""
        if not self._ring_link_enabled or self.slot is None:
            return
        self._ring_link_outgoing += rings
        now = time.monotonic()
        if self._ring_link_outgoing and now - self._ring_link_sent_at >= SEND_INTERVAL:
            self._ring_link_sent_at = now
            amount, self._ring_link_outgoing = self._ring_link_outgoing, 0
            async_start(self.send_msgs([{"cmd": "Bounce", "tags": [RING_LINK_TAG], "data": {
                "time": time.time(), "source": self._ring_link_source, "amount": amount}}]))
        pending = self._ring_link_pending
        if pending and await self._worker.request("ring_link", pending):
            self._ring_link_pending -= pending
