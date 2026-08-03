from __future__ import annotations

import asyncio
import time

from CommonClient import logger

from ..core import TextColour, colored_text, reconcile_traps
from ..universal_tracker import PLANET_ID_TO_REGION
from .constants import EXPECTED_GAME_ID, POLL_INTERVAL
from .other_ratchet_games import GAME_ID_TO_OTHER_RATCHET

# How often weapon level/experience gets persisted to AP data storage — a
# throttle, not a poll rate: experience changes continuously during combat,
# so pushing every POLL_INTERVAL tick would spam the server for no benefit.
# Only actually pushed when the snapshot differs from what was last sent
# anyway (see _maybe_persist_weapon_state), so this just bounds how often
# that comparison can turn into a real Set call.
_WEAPON_STATE_PUSH_INTERVAL: float = 5.0


class PspMixin:
    """Owns the connection to PPSSPP (procmem/transport.py's ProcMemTransport,
    exposed as self.pine): connect/reconnect/teardown, and the poll loop that
    drives Core.tick() every cycle.

    self.pine.connect() briefly uses PPSSPP's debugger WebSocket under the
    hood for a one-time bootstrap only (see procmem/transport.py); every
    other call on self.pine, including get_game_id(), is either a raw
    ReadProcessMemory/WriteProcessMemory into PPSSPP's own process or a
    value cached from that bootstrap, so this mixin's logic (poll cadence,
    reconnect, wrong-game handling) doesn't need to know or care which
    transport is underneath.

    The game's disc id is only checked once, at connect() time — a wrong
    game is caught right here before Core.tick() ever runs, so Core never
    has to reason about connection health or which game is loaded, but a
    game swapped inside an already-running PPSSPP process without
    restarting it won't be noticed until the next /reconnect. Any PPSSPP
    error anywhere in this file is caught and turned into a clean disconnect
    + log line; nothing here lets an exception reach the caller.
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
                f"[RAC] Wrong game in PPSSPP: detected {known_game} [{game_id}]. This client is for "
                f"Ratchet & Clank: Size Matters [{EXPECTED_GAME_ID}]. Connection rejected."
            )
        else:
            logger.warning(f"[RAC] Wrong game in PPSSPP: {game_id!r} (expected {EXPECTED_GAME_ID!r}). "
                            "Connection rejected.")
        async with self._psp_lock:
            await self._teardown_psp_connection()

    async def _attempt_psp_connect(self, is_reconnect: bool = False) -> None:
        # PPSSPP debugger calls run in-line on the event loop thread, never
        # via run_in_executor — a thread-pool worker blocked inside a
        # 5s-timeout debugger call would hold _psp_lock for that whole
        # window, freezing every other consumer (poll loop, vendor sync,
        # deathlink) behind it. Calling in-line means a slow PPSSPP response
        # only stalls this one coroutine.
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
                # This process's own trap bookkeeping (core/traps.py's
                # _active_deadlines) is never persisted, so it starts empty
                # on every client restart — reconcile now, while the PPSSPP
                # connection is confirmed up, so a trap left stuck in game
                # memory from before (crash, or a drop racing a reconcile)
                # doesn't linger for the rest of this session.
                reconcile_traps(self.pine)
                # Skin/vendor-purchase state can only be pushed to PPSSPP
                # now that the connection is confirmed up — on_package's
                # "Connected"/"ReceivedItems" handlers skip these while
                # psp_connected is False and leave it to this success path
                # instead of racing the connect attempt.
                if self.slot is not None:
                    self._wiring.skin.set_by_option(self._starting_skin_option)
                    self._wiring.sync_from_ap(self._checked_location_names())
            except Exception as exc:
                logger.warning(
                    f"[RAC] Initial state read failed: {exc}. Use /reconnect once the game is fully loaded."
                )
                await self._teardown_psp_connection()
                return
            # Confirm the connection in-game immediately — PPSSPP has connected, the
            # right game is loaded, and initial state read succeeded, so show this
            # now rather than after the steps below, which can still fail
            # transiently (e.g. a response timeout) without the connection itself being lost.
            self._write_notification_text(colored_text(
                "Reconnected to " if is_reconnect else "Connected to ", TextColour.YELLOW,
                "PPSSPP", TextColour.WHITE,
            ))

        try:
            # Baseline before applying so the catch-up batch of items already
            # received before this PPSSPP connection doesn't pop a notification.
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
                # Soft flag only — a genuinely dead socket keeps failing every
                # subsequent poll too, so /reconnect remains available; no
                # need to tear anything else down from here.
                logger.warning(f"[RAC] Lost PPSSPP connection or poll failed: {exc}")
                self.psp_connected = False

    async def _poll_game(self) -> None:
        # The game id is only checked once, at connect() time (see
        # ProcMemTransport.get_game_id()) — no periodic re-verification here,
        # so a game swapped inside an already-running PPSSPP process without
        # restarting it won't be noticed until the next /reconnect.
        prev_planet = self.current_planet
        async with self._psp_lock:
            self._wiring.tick()
        self.current_planet = PLANET_ID_TO_REGION.get(self._wiring.planet.planet_id, "Galaxy")
        if self.current_planet != prev_planet:
            await self._send_map_page(self.current_planet)

        # Continuously re-apply AP state every cycle rather than only at
        # specific event boundaries (item received, planet ready, vendor
        # close) — self-heals any drift immediately during normal
        # gameplay. Safe to call unconditionally: apply_inventory() itself
        # (called from within here) already no-ops the memory writes it
        # must not make mid-vendor/mid-death/mid-pickup-animation, and
        # everything else this triggers (bolt/trap filler grants, item
        # notifications) is checkpoint-based and idempotent against being
        # called far more often than something new actually arrived.
        await self._apply_received_items()
        self._maybe_persist_weapon_state()

    def _maybe_persist_weapon_state(self) -> None:
        """Push the current weapon level/experience snapshot to AP data
        storage, throttled to _WEAPON_STATE_PUSH_INTERVAL and skipped
        entirely if nothing's actually changed since the last push — real
        gameplay progress (no AP item records it), so it has to be saved
        explicitly or a reconnect's wipe() (core/core.py's tick()) loses it
        for good instead of just resetting check()'s diff baseline like
        it's meant to.
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
        # Refresh the vendor-purchase cache immediately, rather than waiting
        # for the next ReceivedItems/Connected packet — apply_vendor_locations
        # reads WeaponInventory.vendor_locations live whenever the vendor menu
        # opens, so a check made just before opening it must be visible right away.
        self._wiring.planet.weapons.sync_from_ap(self._checked_location_names())
        asyncio.create_task(self.check_locations({loc_id}))
