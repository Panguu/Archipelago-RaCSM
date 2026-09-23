from __future__ import annotations

import asyncio
import math
import random
import time
from typing import Any

from CommonClient import logger

from ..core import (
    PlayerMovementState as PlayerState,
    TextColour,
    colored_text,
)
from ..core.address_maps import CURRENT_PLANET_ADDRESS
from ..core.structs.game import TransitionGateStruct, TRANSITION_GATE_IDLE

_DEATH_CAUSES: dict[PlayerState, list[str]] = {
    PlayerState.FishDeath: [
        "got eaten by a fish",
        "tried to swim with the fishes",
        "became an aquatic creature's lunch",
        "found out fish bite back",
    ],
    PlayerState.FadeDeath: [
        "was faded out of existence",
        "ceased to exist, briefly",
        "got erased from reality",
        "found the off switch for themselves",
    ],
    PlayerState.Electrocution: [
        "got electrocuted",
        "touched the wrong wire",
        "became a lightning rod",
        "found out electricity is not their friend",
    ],
    PlayerState.VoidDeath: [
        "fell out of the world",
        "discovered the world has edges",
        "took a step too far",
        "found a shortcut to the void",
    ],
    PlayerState.UnknownDeath: [
        "met an untimely end",
        "had a very bad day",
        "encountered something unfortunate",
        "lost a fight with the universe",
    ],
    PlayerState.SwimDeath: [
        "tried to swim in lava",
        "thought lava was just spicy water",
        "went for a relaxing lava bath",
        "underestimated the temperature of magma",
    ],
    PlayerState.MysteriousDeath: [
        "died under mysterious circumstances",
        "departed this world inexplicably",
        "achieved death through unknown means",
        "was claimed by forces beyond comprehension",
    ],
}


def _dead(player_state: int) -> bool:
    return PlayerState.is_dead(player_state)


def _death_cause(player_state: int) -> str:
    causes = _DEATH_CAUSES.get(player_state)
    return random.choice(causes) if causes else "died"


class DeathLinkMixin:
    async def _set_death_link_enabled(self, enabled: bool) -> None:
        """Toggle DeathLink at runtime: updates the local gating flag and the
        server-side "DeathLink" connection tag."""
        self._death_link_enabled = enabled
        if not enabled:
            self._death_link_pending = False
        await self.update_death_link(enabled)
        logger.info(f"[RAC] DeathLink {'enabled' if enabled else 'disabled'}.")

    def _send_death_link_from_sync(self, player_state: int) -> None:
        if not self._death_link_enabled or getattr(self, '_death_link_applied', False):
            return
        now = time.time()
        if now - self._last_death_link < 1:
            return
        self._last_death_link = now
        logger.info("[RAC] DeathLink sent.")
        source = self.auth or "Ratchet"
        planet_name = self.current_planet or "an unknown planet"
        cause_text = _death_cause(player_state)
        self._write_notification_text(colored_text(
            TextColour.RED, "Deathlink: ", source, TextColour.WHITE, " ", cause_text,
        ))
        asyncio.create_task(
            self.send_msgs([
                {
                    "cmd": "Bounce",
                    "tags": ["DeathLink"],
                    "data": {
                        "time": now,
                        "source": source,
                        "cause": f"{source} {cause_text} on {planet_name}.",
                    },
                }
            ])
        )

    async def _receive_death_link(self, data: dict[str, Any]) -> None:
        if not self.psp_connected or not self._death_link_enabled:
            return
        try:
            timestamp = float(data.get("time", 0))
        except (TypeError, ValueError):
            return
        if not math.isfinite(timestamp):
            return
        if timestamp and timestamp <= self._last_death_link:
            return
        self._last_death_link = max(timestamp, time.time())
        source = data.get("source", "Unknown")
        cause  = data.get("cause") or f"{source} died"
        self._log(f"[RAC] DeathLink received: {cause}")
        self._write_notification_text(colored_text(
            TextColour.RED, "Deathlink: ", source, TextColour.WHITE, " ", cause,
        ))
        async with self._psp_lock:
            self._death_link_pending = True
            self._poll_death_link()

    def _poll_death_link(self) -> None:
        """Called under the PSP lock; defer incoming deaths until gameplay resumes."""
        planet = self._wiring.planet
        if not self.psp_connected or not planet.is_ready:
            return
        if getattr(self, '_death_link_applied', False) and not planet.player.is_dead:
            self._death_link_applied = False
        if getattr(self, '_death_link_pending', False) and self._death_link_enabled:
            if self._kill_player_sync():
                self._death_link_pending = False

    def _kill_player_sync(self) -> bool:
        planet = self._wiring.planet
        player = planet.player
        if (not self.psp_connected or not planet.is_ready or self._wiring.vendor_active
                or player.health_addr is None or player.movement_addr is None):
            return False
        self.pine.validate_session()
        if (self.pine.read_int32(TransitionGateStruct.BASE_ADDRESS) != TRANSITION_GATE_IDLE
                or self.pine.read_int8(CURRENT_PLANET_ADDRESS) != planet.planet_id):
            return False
        if player.is_dead:
            return True
        # PSP health is a float32 and movement is one byte. Never fall back
        # to Pokitaru addresses while another overlay is loading.
        player.health = 0.0
        player.movement_state = PlayerState.VoidDeath
        self._death_link_applied = True
        return True
