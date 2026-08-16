from __future__ import annotations

import asyncio
import time

from CommonClient import logger

# Throttle for both detecting local ammo changes and pushing them to AP data
# storage — ammo can tick down every shot, so pushing every poll tick would
# spam the server for no benefit.
_AMMO_LINK_PUSH_INTERVAL: float = 0.5


class AmmoLinkMixin:
    """Mirrors weapon ammo counts across every connected player who also has
    AmmoLink enabled: whenever any linked player's ammo for a weapon
    changes, every other linked player's ammo for that same weapon is
    overwritten to match. Not a shared/depleting pool — a straight mirror,
    same model as DeathLink's Bounce, but built on data storage (a single
    absolute value) instead of an event.

    Players don't need matching weapon inventories: only the weapons a
    given player currently owns are ever read from or written to on their
    side, keyed by internal weapon name so weapons neither player owns are
    simply absent from the diff.
    """

    def _ammo_link_key(self) -> str:
        return f"rsm_ammo_link_{self.team}"

    async def _set_ammo_link_enabled(self, enabled: bool) -> None:
        self._ammo_link_enabled = enabled
        await self._update_link_tag("AmmoLink", enabled)
        if enabled and self.slot is not None:
            self.set_notify(self._ammo_link_key())
            await self.send_msgs([{"cmd": "Get", "keys": [self._ammo_link_key()]}])
        logger.info(f"[RAC] AmmoLink {'enabled' if enabled else 'disabled'}.")

    def _maybe_sync_ammo_link(self) -> None:
        if not self._ammo_link_enabled or self.slot is None or not self.pine_connected:
            return
        if not self._wiring.planet.is_ready:
            return
        now = time.monotonic()
        if now - self._last_ammo_link_push < _AMMO_LINK_PUSH_INTERVAL:
            return
        weapons = self._wiring.planet.weapons
        current = {name: weapons.get_ammo(name) for name, owned in weapons.weapons.items() if owned}
        if current == self._pushed_ammo_link:
            return
        self._last_ammo_link_push = now
        self._pushed_ammo_link = current
        asyncio.create_task(self._push_ammo_link(current))

    async def _push_ammo_link(self, data: dict[str, int]) -> None:
        if self.slot is None:
            return
        await self.send_msgs([{
            "cmd": "Set",
            "key": self._ammo_link_key(),
            "default": {},
            "want_reply": False,
            # "update" (dict.update, server-side) merges just our own
            # weapon entries into the shared key — NOT "replace", which
            # would blow away every other linked player's entries whenever
            # we push, since players routinely own different weapon sets
            # and each push here only ever carries our own subset.
            "operations": [{"operation": "update", "value": data}],
        }])

    def _apply_ammo_link_update(self) -> None:
        """Runs under _pine_lock (see context.py's Retrieved/SetReply
        handler) — writes memory directly, so never call this loose."""
        if not self._ammo_link_enabled or not self._wiring.planet.is_ready:
            return
        data = self.stored_data.get(self._ammo_link_key())
        if not isinstance(data, dict) or data == self._applied_ammo_link:
            return
        self._applied_ammo_link = dict(data)
        weapons = self._wiring.planet.weapons
        for name, value in data.items():
            if not isinstance(value, int) or not weapons.weapons.get(name):
                continue
            if weapons.get_ammo(name) != value:
                weapons.set_ammo(name, value)
        # Rebaseline the push-side cache too, to whatever our own weapons
        # actually read now — otherwise _maybe_sync_ammo_link would see a
        # "change" (the value we just wrote in from a peer) it never
        # pushed itself, and immediately echo it straight back out.
        self._pushed_ammo_link = {
            name: weapons.get_ammo(name) for name, owned in weapons.weapons.items() if owned
        }
