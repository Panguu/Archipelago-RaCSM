from __future__ import annotations

import asyncio
import time

from CommonClient import logger

from ..core import TextColour, colored_text, reconcile_traps
from ..universal_tracker import PLANET_ID_TO_REGION
from .constants import EXPECTED_GAME_ID, PINE_CONNECT_SETTLE_DELAY_S, POLL_INTERVAL
from .other_ratchet_games import GAME_ID_TO_OTHER_RATCHET

# Throttle weapon level/experience pushes — experience changes continuously during combat,
# so pushing every poll tick would spam the server for no benefit.
_WEAPON_STATE_PUSH_INTERVAL: float = 5.0


class PineMixin:
    """Owns the raw PINE socket and poll loop that drives Core.tick(). The game's SCUS id is
    re-verified every poll, not just at connect, so Core never has to reason about connection health."""

    async def _teardown_pine_connection(self) -> None:
        """Drop the raw socket. Safe to call even if it's already down."""
        self.pine_connected = False
        try:
            self.pine.disconnect()
        except Exception:
            logger.debug("[RAC] pine.disconnect() raised during teardown", exc_info=True)

    async def reconnect_pine(self) -> None:
        async with self._pine_lock:
            await self._teardown_pine_connection()
        await self._attempt_pine_connect(is_reconnect=True)

    async def _reject_wrong_game(self, game_id: str, *, is_disconnect: bool) -> None:
        known_game = GAME_ID_TO_OTHER_RATCHET.get(game_id)
        if is_disconnect:
            msg = (
                f"PCSX2 is now running {known_game or game_id} — Size Matters client disconnected. "
                "Use /reconnect once R&C: Size Matters is loaded again."
            )
            # handle_connection_loss() reads sys.exc_info(), so it must be
            # called from inside an except block.
            try:
                raise ConnectionError(msg)
            except ConnectionError:
                self.handle_connection_loss(f"[RAC] {msg}")
        elif known_game:
            logger.warning(
                f"[RAC] Wrong game in PCSX2: detected {known_game} [{game_id}]. This client is for "
                f"Ratchet & Clank: Size Matters [{EXPECTED_GAME_ID}]. Connection rejected."
            )
        else:
            logger.warning(f"[RAC] Wrong game in PCSX2: {game_id!r} (expected {EXPECTED_GAME_ID!r}). "
                            "Connection rejected.")
        async with self._pine_lock:
            await self._teardown_pine_connection()

    async def _attempt_pine_connect(self, is_reconnect: bool = False) -> None:
        # PINE calls run in-line on the event loop, never via run_in_executor — a blocked
        # thread-pool worker would hold _pine_lock and freeze every other PINE consumer.
        async with self._pine_lock:
            def _connect_and_get_game_id() -> str:
                self.pine.connect()
                return self.pine.get_game_id()
            try:
                game_id = _connect_and_get_game_id()
            except Exception:
                logger.warning("[RAC] Could not connect to PCSX2. Use /reconnect once the emulator is running.")
                await self._teardown_pine_connection()
                return

        if game_id != EXPECTED_GAME_ID:
            await self._reject_wrong_game(game_id, is_disconnect=False)
            return

        # Dynamic Pine boots PCSX2 straight into the ISO, so gameplay state may not be valid
        # yet even though PINE is reachable — give it a moment before the first real read.
        await asyncio.sleep(PINE_CONNECT_SETTLE_DELAY_S)

        async with self._pine_lock:
            logger.info(
                "[RAC] Reconnected to PCSX2 - R&C: Size Matters detected."
                if is_reconnect else
                "[RAC] Connected to PCSX2 - R&C: Size Matters detected."
            )
            self.pine_connected = True
            try:
                self._read_initial_state_sync()
                # Trap bookkeeping isn't persisted, so reconcile now to clear any trap left
                # stuck in game memory from before (crash, PINE drop).
                reconcile_traps(self.pine)
            except Exception as exc:
                logger.warning(
                    f"[RAC] Initial state read failed: {exc}. Use /reconnect once the game is fully loaded."
                )
                await self._teardown_pine_connection()
                return
            # Confirm the connection in-game now, before the steps below that
            # can still fail transiently without PINE itself being lost.
            self._write_notification_text(colored_text(
                "Reconnected to " if is_reconnect else "Connected to ", TextColour.YELLOW,
                "PCSX2", TextColour.WHITE,
            ))

        try:
            # Baseline first so the catch-up batch of already-received items
            # doesn't pop a notification.
            self._notification_item_index = len(self.items_received)
            await self._apply_received_items()
            await self._send_map_page(self.current_planet)
        except Exception as exc:
            logger.warning(f"[RAC] Lost PCSX2 connection while starting up: {exc}. Use /reconnect.")
            async with self._pine_lock:
                await self._teardown_pine_connection()

    async def _read_initial_state(self) -> None:
        try:
            async with self._pine_lock:
                self._read_initial_state_sync()
        except Exception as exc:
            self._log(f"[RAC] Initial state read failed: {exc}", "warning")

    def _read_initial_state_sync(self) -> None:
        self._wiring.tick()
        planet_id = self._wiring.planet.planet_id
        self.current_planet = PLANET_ID_TO_REGION.get(planet_id, "Galaxy")

    async def game_watcher(self) -> None:
        while not self.exit_event.is_set():
            await asyncio.sleep(POLL_INTERVAL)
            if not self.pine_connected:
                continue
            try:
                await self._poll_game()
            except Exception as exc:
                # Soft flag only — a dead socket keeps failing every
                # subsequent poll, so /reconnect remains available.
                logger.warning(f"[RAC] Lost PINE connection or poll failed: {exc}")
                self.pine_connected = False

    async def _poll_game(self) -> None:
        async with self._pine_lock:
            game_id = self.pine.get_game_id()
        if game_id != EXPECTED_GAME_ID:
            await self._reject_wrong_game(game_id, is_disconnect=True)
            return

        prev_planet = self.current_planet
        async with self._pine_lock:
            self._wiring.tick()
        self.current_planet = PLANET_ID_TO_REGION.get(self._wiring.planet.planet_id, "Galaxy")
        if self.current_planet != prev_planet:
            await self._send_map_page(self.current_planet)

        # Re-applied every cycle rather than only at event boundaries, to self-heal drift — safe
        # since apply_inventory() already no-ops writes it must not make mid-vendor/mid-death.
        await self._apply_received_items()
        self._maybe_persist_weapon_state()
        self._maybe_sync_ammo_link()
        self._maybe_sync_bolt_link()
        self._maybe_sync_ghost_link()

    def _maybe_persist_weapon_state(self) -> None:
        """Push the weapon level/experience snapshot to AP data storage, throttled and skipped
        if unchanged, since no AP item records this progress and a reconnect's wipe() would lose it."""
        if self.slot is None or not self.pine_connected or not self._wiring.planet.is_ready:
            return
        now = time.monotonic()
        if now - self._last_weapon_state_push < _WEAPON_STATE_PUSH_INTERVAL:
            return
        snapshot = self._wiring.planet.weapons.level_experience_snapshot()
        if snapshot == self._pushed_weapon_state:
            return
        self._last_weapon_state_push = now
        self._pushed_weapon_state = snapshot
        asyncio.create_task(self._persist_weapon_state(snapshot))

    async def _send_map_page(self, planet: str) -> None:
        if self.slot is None:
            return
        team = getattr(self, "team", 0)
        await self.send_msgs([{
            "cmd": "Set",
            "key": f"rsm_current_planet_{self.slot}_{team}",
            "default": "Galaxy",
            "want_reply": False,
            "operations": [{"operation": "replace", "value": planet}],
        }])

    def _append_location_by_name(self, name: str) -> None:
        """Wired as Core.wire(send_location=...). Silently no-ops for a name outside the location
        table, already checked, or excluded from this seed's pool (e.g. an option-gated location)."""
        loc_id = self._location_name_to_id.get(name)
        if loc_id is None:
            return
        if loc_id in self._locally_checked_locations or loc_id in self.checked_locations:
            return
        server_locations = getattr(self, "server_locations", None)
        if server_locations is not None and loc_id not in server_locations:
            return
        self._locally_checked_locations.add(loc_id)
        self._log(f"[RAC] Location checked: {name}")
        # Refresh the vendor-purchase cache immediately, since a check made just before opening
        # the vendor menu must be visible right away.
        self._wiring.planet.weapons.sync_from_ap(self._checked_location_names())
        asyncio.create_task(self.check_locations({loc_id}))
