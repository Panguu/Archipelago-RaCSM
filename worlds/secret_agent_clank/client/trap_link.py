import time

from CommonClient import logger
from Utils import async_start

from ..constants import TRAP_LINK_RECEIVE, TRAP_LINK_SEND

TRAP_LINK_TAG = "TrapLink"


class TrapLinkMixin:
    async def _set_trap_link_enabled(self, enabled: bool) -> None:
        old_tags = set(self.tags)
        self._enable_trap_link(enabled)
        await self._send_tags(old_tags)

    def _enable_trap_link(self, enabled: bool) -> None:
        self._trap_link_enabled = enabled
        self._trap_link_pending.clear()
        if enabled:
            self.tags.add(TRAP_LINK_TAG)
        else:
            self.tags.discard(TRAP_LINK_TAG)
        logger.info(f"[SAC] Trap Link {'enabled' if enabled else 'disabled'}.")

    def _trap_link_source(self) -> str:
        return self.player_names.get(self.slot, self.username or "")

    def _on_trap_link(self, args: dict) -> None:
        data = args.get("data", {})
        if (not self._trap_link_enabled or TRAP_LINK_TAG not in args.get("tags", ())
                or data.get("source") == self._trap_link_source()):
            return
        trap = TRAP_LINK_RECEIVE.get(data.get("trap_name"))
        if trap is not None:
            self._trap_link_pending.append(trap)
            logger.info(f"[SAC] Trap Link: {data.get('source', 'someone')} sent a {trap}.")

    def _send_trap_link(self, trap: str) -> None:
        """Share a trap received as an item. Linked traps aren't sent back out."""
        if not self._trap_link_enabled or self.slot is None:
            return
        async_start(self.send_msgs([{"cmd": "Bounce", "tags": [TRAP_LINK_TAG], "data": {
            "time": time.time(), "source": self._trap_link_source(), "trap_name": TRAP_LINK_SEND[trap]}}]))

    async def _apply_trap_link(self) -> None:
        """Apply linked traps in order, stopping at one that can't apply yet."""
        while self._trap_link_pending and await self._worker.request("effect", self._trap_link_pending[0]):
            self._trap_link_pending.pop(0)
