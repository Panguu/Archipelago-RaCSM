import time
from typing import Any

from CommonClient import logger
from Utils import async_start


class DeathLinkMixin:
    async def _set_death_link_enabled(self, enabled: bool) -> None:
        self._death_link_enabled = enabled
        await self._worker.request("death_enabled", enabled)
        await self.update_death_link(enabled)
        logger.info(f"[SAC] DeathLink {'enabled' if enabled else 'disabled'}.")

    def _send_death_link_from_sync(self, death: dict[str, str | None]) -> None:
        if death['planet']:
            self.current_planet = death['planet']
        if not self._death_link_enabled:
            return
        if time.time() - self.last_death_link < 1:  # one death can be reported more than once
            return
        message = f"{self.auth or 'Ratchet'} {death['cause'] or 'died'} on {self.current_planet or 'an unknown planet'}."
        async_start(self.send_death(message))
        async_start(self._worker.request("death_sent", message))

    def on_deathlink(self, data: dict[str, Any]) -> None:
        if data.get("time", 0) <= self.last_death_link:  # old, or one we sent
            return
        super().on_deathlink(data)
        if self._death_link_enabled:
            async_start(self._receive_death_link(data))

    async def _receive_death_link(self, data: dict[str, Any]) -> None:
        if not self.pine_connected:
            return
        source = data.get("source", "Unknown")
        cause = data.get("cause") or f"{source} died"
        async with self._pine_lock:
            await self._worker.request("death", (source, cause))
