from __future__ import annotations

import asyncio
import time

from CommonClient import logger

from ..core import TextColour, colored_text, reconcile_traps
from ..universal_tracker import PLANET_ID_TO_REGION
from .constants import EXPECTED_GAME_ID, POLL_INTERVAL
from .other_ratchet_games import GAME_ID_TO_OTHER_RATCHET

# Throttle for pushing weapon level/experience to AP data storage; only
# actually sent when the snapshot differs from the last push (see
# _maybe_persist_weapon_state).
_WEAPON_STATE_PUSH_INTERVAL: float = 5.0


class PspMixin:
    """Owns the connection to PPSSPP (procmem/transport.py's ProcMemTransport,
    exposed as self.pine): connect/reconnect/teardown, and the poll loop that
    drives Core.tick() every cycle.

    The game id is only checked once, at connect() time, so a game swapped
    inside an already-running PPSSPP process won't be noticed until the next
    /reconnect. Any PPSSPP error in this file is caught and turned into a
    clean disconnect + log line.
    """

    async def _teardown_psp_connection(self) -> None:
        """Drop the process handle (and any still-open bootstrap socket).
        Safe to call even if it's already down."""
        self.psp_connected = False
        try:
            self.pine.disconnect()
        except Exception:
            logger.debug("[RAC] psp.disconnect() raised during teardown", exc_info=True)

    async def reconnect_psp(self) -> None:
        async with self._psp_lock:
            await self._teardown_psp_connection()
        await self._attempt_psp_connect(is_reconnect=True)

    async def _reject_wrong_game(self, game_id: str, *, is_disconnect: bool) -> None:
        known_game = GAME_ID_TO_OTHER_RATCHET.get(game_id)
        if is_disconnect:
            msg = (
                f"PPSSPP is now running {known_game or game_id} — Size Matters client disconnected. "
                "Use /reconnect once R&C: Size Matters is loaded again."
            )
            # handle_connection_loss() reads sys.exc_info(), so it must be called
            # from inside an except block — raise+catch our own signal exception.
            try:
                raise ConnectionError(msg)
            except ConnectionError:
                self.handle_connection_loss(f"[RAC] {msg}")
        elif known_game:
            logger.warning(
                f"[RAC] Wrong game in PPSSPP: detected {known_game} [{game_id}]. This client is for "
                f"Ratchet & Clank: Size Matters [{EXPECTED_GAME_ID}]. Connection rejected."
            )
        else:
            logger.warning(f"[RAC] Wrong game in PPSSPP: {game_id!r} (expected {EXPECTED_GAME_ID!r}). "
                            "Connection rejected.")
        async with self._psp_lock:
            await self._teardown_psp_connection()

    async def _attempt_psp_connect(self, is_reconnect: bool = False) -> None:
        # Called in-line, not via run_in_executor: a blocked thread-pool worker
        # would hold _psp_lock and freeze every other consumer (poll loop,
        # vendor sync, deathlink) behind it.
        async with self._psp_lock:
            def _connect_and_get_game_id() -> str:
                self.pine.connect()
                return self.pine.get_game_id()
            try:
                game_id = _connect_and_get_game_id()
            except Exception as exc:
                logger.warning(
                    f"[RAC] Could not connect to PPSSPP: {exc}. Use /reconnect once the emulator is running."
                )
                await self._teardown_psp_connection()
                return

        if game_id != EXPECTED_GAME_ID:
            await self._reject_wrong_game(game_id, is_disconnect=False)
            return

        async with self._psp_lock:
            logger.info(
                "[RAC] Reconnected to PPSSPP - R&C: Size Matters detected."
                if is_reconnect else
                "[RAC] Connected to PPSSPP - R&C: Size Matters detected."
            )
            self.psp_connected = True
            try:
                self._read_initial_state_sync()
                # Trap bookkeeping (core/traps.py's _active_deadlines) isn't persisted
                # and starts empty each restart — reconcile now so a trap stuck in
                # game memory from a prior crash doesn't linger.
                reconcile_traps(self.pine)
                # on_package's "Connected"/"ReceivedItems" handlers skip pushing
                # skin/vendor state while psp_connected is False, so do it here instead.
                if self.slot is not None:
                    self._wiring.skin.set_by_option(self._starting_skin_option)
                    self._wiring.sync_from_ap(self._checked_location_names())
            except Exception as exc:
                logger.warning(
                    f"[RAC] Initial state read failed: {exc}. Use /reconnect once the game is fully loaded."
                )
                await self._teardown_psp_connection()
                return
            # Confirm the connection in-game now, before the steps below that can
            # still fail transiently without the connection itself being lost.
            self._write_notification_text(colored_text(
                "Reconnected to " if is_reconnect else "Connected to ", TextColour.YELLOW,
                "PPSSPP", TextColour.WHITE,
            ))

        try:
            # Baseline first so the catch-up batch of already-received items
            # doesn't pop a notification.
            self._notification_item_index = len(self.items_received)
            await self._apply_received_items()
            await self._send_map_page(self.current_planet)
        except Exception as exc:
            logger.warning(f"[RAC] Lost PPSSPP connection while starting up: {exc}. Use /reconnect.")
            async with self._psp_lock:
                await self._teardown_psp_connection()

    async def _read_initial_state(self) -> None:
        try:
            async with self._psp_lock:
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
            if not self.psp_connected:
                continue
            try:
                await self._poll_game()
            except Exception as exc:
                # Soft flag only; /reconnect remains available. Logs the full
                # traceback since str(exc) can be empty for some exception types.
                logger.warning(
                    f"[RAC] Lost PPSSPP connection or poll failed: {type(exc).__name__}: {exc}",
                    exc_info=True,
                )
                self.psp_connected = False

    async def _poll_game(self) -> None:
        prev_planet = self.current_planet
        async with self._psp_lock:
            self._wiring.tick()
        self.current_planet = PLANET_ID_TO_REGION.get(self._wiring.planet.planet_id, "Galaxy")
        if self.current_planet != prev_planet:
            await self._send_map_page(self.current_planet)

        # Re-applied every cycle (not just at event boundaries) to self-heal drift;
        # safe to call unconditionally since apply_inventory() no-ops writes it
        # must not make mid-vendor/mid-death/mid-pickup-animation, and everything
        # else here is checkpoint-based and idempotent.
        await self._apply_received_items()
        self._maybe_persist_weapon_state()

    def _maybe_persist_weapon_state(self) -> None:
        """Push the weapon level/experience snapshot to AP data storage, throttled
        and skipped if unchanged. Weapon XP isn't tracked by any AP item, so it
        must be saved explicitly or a reconnect's wipe() loses it for good.
        """
        if self.slot is None or not self.psp_connected or not self._wiring.planet.is_ready:
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
        """Wired as Core.wire(send_location=...) — dispatches async immediately."""
        loc_id = self._location_name_to_id.get(name)
        if loc_id is None:
            logger.warning(f"[RAC] unknown location {name!r} — not in location table")
            return
        if loc_id in self._locally_checked_locations or loc_id in self.checked_locations:
            return
        server_locations = getattr(self, "server_locations", None)
        if server_locations is not None and loc_id not in server_locations:
            logger.warning(f"[RAC] {name!r} (id={loc_id}) not in server locations"
                           " — was game generated with the current options?")
            return
        self._locally_checked_locations.add(loc_id)
        self._log(f"[RAC] Location checked: {name}")
        # Refresh the vendor-purchase cache immediately rather than waiting for the
        # next ReceivedItems/Connected packet, since the vendor menu reads it live.
        self._wiring.planet.weapons.sync_from_ap(self._checked_location_names())
        asyncio.create_task(self.check_locations({loc_id}))
