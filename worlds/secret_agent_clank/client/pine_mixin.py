"""Owns the raw PINE socket to PCSX2: connect/reconnect/teardown, plus the poll loop that drives Core.tick() every cycle."""
import asyncio

from CommonClient import logger

from .constants import EXPECTED_GAME_ID, PINE_CONNECT_SETTLE_DELAY_S, POLL_INTERVAL


class PineMixin:

    async def _teardown_pine_connection(self) -> None:
        self.pine_connected = False
        try:
            self._wiring.close()
        except Exception:
            logger.warning("[SAC] Could not restore the loader barrier. Restart the game before continuing if loading is held.", exc_info=True)
        try:
            self.pine.disconnect()
        except Exception:
            logger.debug("[SAC] pine.disconnect() raised during teardown", exc_info=True)

    async def reconnect_pine(self) -> None:
        async with self._pine_lock:
            await self._teardown_pine_connection()
        await self._attempt_pine_connect(is_reconnect=True)

    async def _reject_wrong_game(self, game_id: str, *, is_disconnect: bool) -> None:
        if is_disconnect:
            msg = (
                f"PCSX2 is now running {game_id} — Secret Agent Clank client disconnected. "
                "Use /reconnect once Secret Agent Clank is loaded again."
            )
            try:
                raise ConnectionError(msg)
            except ConnectionError:
                self.handle_connection_loss(f"[SAC] {msg}")
        else:
            logger.warning(
                f"[SAC] Wrong game in PCSX2: {game_id!r} (expected {EXPECTED_GAME_ID!r}). Connection rejected."
            )
        async with self._pine_lock:
            await self._teardown_pine_connection()

    async def _attempt_pine_connect(self, is_reconnect: bool = False) -> None:
        async with self._pine_lock:
            def _connect_and_get_game_id() -> str:
                self.pine.connect()
                return self.pine.get_game_id()
            try:
                game_id = _connect_and_get_game_id()
            except Exception:
                logger.warning("[SAC] Could not connect to PCSX2. Use /reconnect once the emulator is running.")
                await self._teardown_pine_connection()
                return

        if game_id != EXPECTED_GAME_ID:
            await self._reject_wrong_game(game_id, is_disconnect=False)
            return

        await asyncio.sleep(PINE_CONNECT_SETTLE_DELAY_S)

        async with self._pine_lock:
            logger.info(
                "[SAC] Reconnected to PCSX2 - Secret Agent Clank detected."
                if is_reconnect else
                "[SAC] Connected to PCSX2 - Secret Agent Clank detected."
            )
            self.pine_connected = True
            try:
                self._wiring.tick()
            except Exception as exc:
                logger.warning(
                    f"[SAC] Initial state read failed: {exc}. Use /reconnect once the game is fully loaded."
                )
                await self._teardown_pine_connection()
                return

        self._maybe_scout_vendor()
        try:
            await self._apply_received_items()
        except Exception as exc:
            logger.warning(f"[SAC] Lost PCSX2 connection while starting up: {exc}. Use /reconnect.")
            async with self._pine_lock:
                await self._teardown_pine_connection()

    async def game_watcher(self) -> None:
        while not self.exit_event.is_set():
            await asyncio.sleep(POLL_INTERVAL)
            if not self.pine_connected:
                continue
            try:
                await self._poll_game()
            except Exception as exc:
                logger.warning(f"[SAC] Lost PINE connection or poll failed: {exc}")
                async with self._pine_lock:
                    await self._teardown_pine_connection()

    async def _poll_game(self) -> None:
        async with self._pine_lock:
            game_id = self.pine.get_game_id()
        if game_id != EXPECTED_GAME_ID:
            await self._reject_wrong_game(game_id, is_disconnect=True)
            return

        async with self._pine_lock:
            self._wiring.tick()

        self._maybe_scout_vendor()
        await self._apply_received_items()

    def _append_location_by_name(self, name: str) -> bool:
        """Queue an AP location check, if -- and only if -- `name` is actually a location that exists in THIS seed."""
        loc_id = self._location_name_to_id.get(name)
        if loc_id is None:
            if name not in self._warned_missing_locations:
                self._warned_missing_locations.add(name)
                logger.warning(f"[SAC] unknown location {name!r} — not in location table")
            return False
        if loc_id in self._locally_checked_locations or loc_id in self.checked_locations:
            return True
        server_locations = getattr(self, "server_locations", None)
        if server_locations is not None and loc_id not in server_locations:
            if name not in self._warned_missing_locations:
                self._warned_missing_locations.add(name)
                logger.warning(f"[SAC] {name!r} (id={loc_id}) not in server locations"
                               " — was game generated with the current options?")
            return False
        self._locally_checked_locations.add(loc_id)
        asyncio.create_task(self.check_locations({loc_id}))
        return True
