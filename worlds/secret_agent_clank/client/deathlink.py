import asyncio
import time
from typing import Any

from CommonClient import logger


class DeathLinkMixin:
    async def _set_death_link_enabled(self, enabled: bool) -> None:
        self._death_link_enabled = enabled
        await self.update_death_link(enabled)
        logger.info(f"[SAC] DeathLink {'enabled' if enabled else 'disabled'}.")

    def _send_death_link_from_sync(self, cause_state: int) -> None:
        if not self._death_link_enabled:
            return
        now = time.time()
        if now - self._last_death_link < 1:
            return
        self._last_death_link = now
        source = self.auth or "Ratchet"
        planet_name = self.current_planet or "an unknown planet"
        logger.info("[SAC] DeathLink sent.")
        asyncio.create_task(
            self.send_msgs([{
                "cmd": "Bounce",
                "tags": ["DeathLink"],
                "data": {
                    "time": now,
                    "source": source,
                    "cause": f"{source} died on {planet_name}.",
                },
            }])
        )

    async def _receive_death_link(self, data: dict[str, Any]) -> None:
        if not self.pine_connected:
            return
        timestamp = float(data.get("time", 0))
        if timestamp and timestamp <= self._last_death_link:
            return
        self._last_death_link = max(timestamp, time.time())
        source = data.get("source", "Unknown")
        cause = data.get("cause") or f"{source} died"
        logger.info(f"[SAC] DeathLink received: {cause}")
        async with self._pine_lock:
            self._kill_player_sync()

    def _kill_player_sync(self) -> None:
        """TODO: no confirmed death-state value exists yet (see core/player.py's CharacterState.DEAD_STATE_VALUES) — zeroing health is the best available approximation until one is found live."""
        self._wiring.case.ratchet.health = 0.0
