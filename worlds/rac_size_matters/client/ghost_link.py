from __future__ import annotations

import asyncio
import time

from CommonClient import logger

# A peer's broadcast position is treated as gone once this long has passed
# since we last heard from them, regardless of their own configured
# interval (we have no way to know it) — generous enough to tolerate a
# couple of missed heartbeats without flickering the ghost on/off.
_GHOST_LINK_STALE_AFTER: float = 20.0

# Floor applied to a configured push interval below 1s, so a low (but
# nonzero) slider value can't spam data storage every poll tick.
_GHOST_LINK_MIN_PUSH_INTERVAL: float = 1.0


class GhostLinkMixin:
    """Shares live player position with every other connected player who
    also has Ghost Link enabled: each linked client periodically broadcasts
    its own X/Y/Z (see options.py's GhostLinkUpdateInterval) to a per-slot
    data storage key, and renders whichever other linked player is
    currently on the same planet as a static ghost clone — same underlying
    GhostRatchetInventory struct as the single-player /spawn_ghost debug
    command, but driven by follow()/stop_following() instead of
    spawn()/keep_alive() (see core/ghost_ratchet.py).

    Only one ghost struct exists per planet, so only one peer can ever be
    rendered at a time — if more than one linked player shares your planet,
    the lowest slot number among them wins, for a deterministic pick.
    """

    def _ghost_link_key(self, slot: int) -> str:
        return f"rsm_ghost_link_{self.team}_{slot}"

    async def _set_ghost_link_enabled(self, enabled: bool) -> None:
        self._ghost_link_enabled = enabled
        await self._update_link_tag("GhostLink", enabled)
        if enabled and self.slot is not None:
            self._refresh_ghost_link_slots()
            for slot in self._ghost_link_slots:
                self.set_notify(self._ghost_link_key(slot))
            if self._ghost_link_slots:
                await self.send_msgs([{"cmd": "Get", "keys": [
                    self._ghost_link_key(slot) for slot in self._ghost_link_slots
                ]}])
        else:
            self._wiring.ghost_ratchet.stop_following()
            self._ghost_link_peers.clear()
            self._ghost_link_following = None
        logger.info(f"[RAC] GhostLink {'enabled' if enabled else 'disabled'}.")

    def _refresh_ghost_link_slots(self) -> None:
        """Every other slot in this multiworld playing the same game — we
        can't tell ahead of time which of them have Ghost Link toggled on
        client-side (that's a runtime choice, not visible slot data), so
        this just watches all of them; a slot that never enables it simply
        never pushes anything to its key."""
        self._ghost_link_slots = [
            slot for slot, info in self.slot_info.items()
            if slot != self.slot and info.game == self.game
        ]
        # Unconditional (not gated behind /debug) — this only fires once per
        # enable, and an empty list here explains total silence downstream
        # far better than anything a later per-tick debug line could.
        logger.info(f"[RAC] GhostLink watching slots: {self._ghost_link_slots} "
                    f"(update interval: {self._ghost_link_interval}s)")

    def _maybe_sync_ghost_link(self) -> None:
        """Called every poll tick from PineMixin._poll_game(), which isn't
        wrapped in a try/except of its own here (unlike Core.tick()) — an
        uncaught exception escaping this method propagates up into
        game_watcher()'s broad except, which treats it as a dead PINE
        socket and stops polling entirely. Every raw pine read/write below
        is therefore guarded locally instead of trusted to behave."""
        if not self._ghost_link_enabled or self.slot is None or not self.pine_connected:
            return
        if not self._wiring.planet.is_ready:
            return

        try:
            self._maybe_push_ghost_link_position()
            self._follow_ghost_link_peer()
        except Exception as exc:
            logger.warning(f"[RAC] GhostLink tick failed: {exc}")

    def _maybe_push_ghost_link_position(self) -> None:
        # 0 means "as fast as possible" (every poll tick, no throttle) —
        # not "off". GhostLink only runs this at all while enabled, so
        # there's no separate "off" state to represent here.
        push_interval = self._ghost_link_interval
        if push_interval > 0:
            now = time.monotonic()
            if now - self._last_ghost_link_push < max(push_interval, _GHOST_LINK_MIN_PUSH_INTERVAL):
                return
            self._last_ghost_link_push = now
        planet_id = self._wiring.planet.planet_id
        pos = self._wiring.ghost_ratchet.read_own_position(planet_id) if planet_id is not None else None
        if pos is not None:
            self._log(f"[RAC] GhostLink push: planet=0x{planet_id:02X} pos={pos}")
            asyncio.create_task(self._push_ghost_link_position(planet_id, *pos))
        else:
            self._log(f"[RAC] GhostLink push skipped: planet 0x{planet_id:02X} not in GHOST_RATCHET_ADDRESSES"
                       if planet_id is not None else "[RAC] GhostLink push skipped: no planet_id")

    async def _push_ghost_link_position(self, planet_id: int, x: float, y: float, z: float) -> None:
        if self.slot is None:
            return
        await self.send_msgs([{
            "cmd": "Set",
            "key": self._ghost_link_key(self.slot),
            "default": {},
            "want_reply": False,
            "operations": [{"operation": "replace", "value": {
                "planet_id": planet_id, "x": x, "y": y, "z": z,
            }}],
        }])

    def _refresh_ghost_link_peers(self) -> None:
        """Pull the latest broadcast position for every watched slot out of
        stored_data — called from context.py's Retrieved/SetReply handler.
        Just updates a plain dict (no memory access), so needs no lock."""
        now = time.monotonic()
        for slot in self._ghost_link_slots:
            data = self.stored_data.get(self._ghost_link_key(slot))
            if not isinstance(data, dict):
                continue
            planet_id, x, y, z = data.get("planet_id"), data.get("x"), data.get("y"), data.get("z")
            if not isinstance(planet_id, int) or not all(isinstance(v, (int, float)) for v in (x, y, z)):
                self._log(f"[RAC] GhostLink: malformed data from slot {slot}: {data!r}", "warning")
                continue
            self._log(f"[RAC] GhostLink received: slot={slot} planet=0x{planet_id:02X} pos=({x}, {y}, {z})")
            self._ghost_link_peers[slot] = (planet_id, float(x), float(y), float(z), now)

    def _follow_ghost_link_peer(self) -> None:
        """Runs every poll tick while GhostLink is enabled — picks the
        lowest-slot fresh peer on the current planet and keeps the ghost
        struct pinned to their latest position, or stops following once
        nobody qualifies anymore."""
        planet_id = self._wiring.planet.planet_id
        if planet_id is None:
            self._wiring.ghost_ratchet.stop_following()
            return

        now = time.monotonic()
        candidate: tuple[int, float, float, float] | None = None
        for slot in sorted(self._ghost_link_peers):
            peer_planet, x, y, z, received_at = self._ghost_link_peers[slot]
            if peer_planet != planet_id:
                continue
            if now - received_at > _GHOST_LINK_STALE_AFTER:
                continue
            candidate = (slot, x, y, z)
            break

        if candidate is None:
            if self._ghost_link_following is not None:
                self._log(f"[RAC] GhostLink: stopped following slot {self._ghost_link_following}")
            self._ghost_link_following = None
            self._wiring.ghost_ratchet.stop_following()
            return

        slot, x, y, z = candidate
        if slot != self._ghost_link_following:
            self._log(f"[RAC] GhostLink: now following slot {slot} on planet 0x{planet_id:02X}")
            self._ghost_link_following = slot
        self._wiring.ghost_ratchet.follow(planet_id, x, y, z)
