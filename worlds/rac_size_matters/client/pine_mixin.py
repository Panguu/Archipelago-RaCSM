from __future__ import annotations

import asyncio

from CommonClient import logger

from ..core import TextColour, colored_text, reconcile_traps
from ..universal_tracker import PLANET_ID_TO_REGION
from .constants import EXPECTED_GAME_ID, POLL_INTERVAL
from .other_ratchet_games import GAME_ID_TO_OTHER_RATCHET


class PineMixin:
    """Owns the raw PINE socket: connect/reconnect/teardown, and the poll
    loop that drives Core.tick() every cycle.

    The game's SCUS id is re-verified on every single poll, not just at
    connect time — a wrong or missing game disconnects right here, before
    Core.tick() ever runs, so Core never has to reason about connection
    health or which game is loaded. Any PINE error anywhere in this file is
    caught and turned into a clean disconnect + log line; nothing here lets
    an exception reach the caller.
    """

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
            # handle_connection_loss() logs and pops a GUI error messagebox,
            # but reads sys.exc_info() to do it — it must actually be called
            # from inside an except block, so raise+catch our own signal
            # exception here rather than just logging a plain warning.
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
        # PINE calls run in-line on the event loop thread, never via
        # run_in_executor — a thread-pool worker blocked inside a 5s-timeout
        # PINE call would hold _pine_lock for that whole window, freezing
        # every other PINE consumer (poll loop, vendor sync, deathlink)
        # behind it. Calling in-line means a slow PCSX2 response only stalls
        # this one coroutine.
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

        async with self._pine_lock:
            logger.info(
                "[RAC] Reconnected to PCSX2 - R&C: Size Matters detected."
                if is_reconnect else
                "[RAC] Connected to PCSX2 - R&C: Size Matters detected."
            )
            self.pine_connected = True
            try:
                self._read_initial_state_sync()
                # This process's own trap bookkeeping (core/traps.py's
                # _active_deadlines) is never persisted, so it starts empty
                # on every client restart — reconcile now, while PINE is
                # confirmed up, so a trap left stuck in game memory from
                # before (crash, or a revert racing a PINE drop) doesn't
                # linger for the rest of this session.
                reconcile_traps(self.pine)
            except Exception as exc:
                logger.warning(
                    f"[RAC] Initial state read failed: {exc}. Use /reconnect once the game is fully loaded."
                )
                await self._teardown_pine_connection()
                return
            # Confirm the connection in-game immediately — PINE has connected, the
            # right game is loaded, and initial state read succeeded, so show this
            # now rather than after the steps below, which can still fail
            # transiently (e.g. a response timeout) without PINE itself being lost.
            self._write_notification_text(colored_text(
                "Reconnected to " if is_reconnect else "Connected to ", TextColour.YELLOW,
                "PCSX2", TextColour.WHITE,
            ))

        try:
            # Baseline before applying so the catch-up batch of items already
            # received before this PCSX2 connection doesn't pop a notification.
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
                # Soft flag only — a genuinely dead socket keeps failing every
                # subsequent poll too, so /reconnect remains available; no
                # need to tear anything else down from here.
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
        # Refresh the vendor-purchase cache immediately, rather than waiting
        # for the next ReceivedItems/Connected packet — apply_vendor_locations
        # reads WeaponInventory.vendor_locations live whenever the vendor menu
        # opens, so a check made just before opening it must be visible right away.
        self._wiring.planet.weapons.sync_from_ap(self._checked_location_names())
        asyncio.create_task(self.check_locations({loc_id}))
