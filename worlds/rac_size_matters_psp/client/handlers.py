from __future__ import annotations

import asyncio

from CommonClient import logger
from NetUtils import ClientStatus

from ..core import ARMOUR_SET_CHECKS
from ..core.address_maps import PLAYER_BOLT_COUNT
from ..core.player_bolts import MAX_PLAYER_BOLTS


class ChallengeHandlerMixin:
    def _on_challenge_armour_earned(self, loc_name: str) -> None:
        """Fired when a new armour piece is detected after a challenge completes."""
        self._pending_challenge_checks.append(loc_name)



class CutsceneHandlerMixin:
    async def _send_goal_status(self) -> None:
        if not self.finished_game:
            await self.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
            self.finished_game = True



class EventsHandlerMixin:
    async def _send_playing_status(self) -> None:
        """Tell the server we're actually in-game, not sitting at the main
        menu. Matches RAC3's pcsx2_sync_task, which sends CLIENT_PLAYING the
        moment its main_menu flag flips False -> True (i.e. a save was just
        loaded) — fired here from Core's on_initial_load hook, our
        equivalent edge."""
        await self.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_PLAYING}])

    def _on_planet_ready(self) -> None:
        """Fired every time a planet finishes loading (Core's on_planet_ready
        hook — every transition, not just the first). Re-applies received
        items as before, and also (re)attempts the starting-bolts grant:
        gated on a flag persisted to AP data storage rather than run once at
        PINE-connect time, since writing PLAYER_BOLT_COUNT before any planet
        has actually loaded doesn't reliably stick. Firing on every
        transition, not just the very first, gives it a free retry if an
        earlier attempt failed (e.g. a transient PINE error) without needing
        its own retry/backoff logic."""
        asyncio.create_task(self._apply_received_items())
        asyncio.create_task(self._grant_starting_items())
        # Retry weapon-state (level/experience) restore here too — the
        # "Retrieved"/"SetReply" handler in context.py only gets one shot at
        # it and may run before the planet is ready (see
        # _try_restore_weapon_state's docstring); this covers that race by
        # trying again on every subsequent planet-ready until it sticks.
        self._try_restore_weapon_state()

    async def _grant_starting_items(self) -> None:
        if self._starting_items_sent or not self.psp_connected:
            return
        # Claim the grant immediately, synchronously, before any await point
        # below — this can be scheduled from both _on_planet_ready (the
        # transition edge) and the "Retrieved"/"SetReply" handler (for when
        # the planet was already ready before AP connected), and on a fresh
        # connect both conditions are very often true at once. asyncio.
        # create_task() only schedules a coroutine, it doesn't start it, so
        # both calls could reach the check above before either had set this
        # flag — claiming it here, before the first await, closes that
        # window (the loser's check-at-top-of-function now always sees it
        # already claimed). Reset back to False on failure so a later retry
        # (e.g. next planet transition) can still attempt the grant.
        self._starting_items_sent = True
        starting_bolts = int(self.slot_data.get("starting_bolts", 0))
        if starting_bolts <= 0:
            asyncio.create_task(self._persist_starting_items_sent())
            return
        async with self._psp_lock:
            try:
                current = self.pine.read_int32(PLAYER_BOLT_COUNT)
                granted = min(current + starting_bolts, MAX_PLAYER_BOLTS)
                self.pine.write_int32(PLAYER_BOLT_COUNT, granted)
                # This is a one-shot AP grant, not organic gameplay gain —
                # rebaseline so Core's per-tick apply_boost() doesn't see it
                # as a "gain" and multiply it too.
                self._wiring.player_bolts.rebaseline(granted)
            except Exception as exc:
                logger.warning(f"[RAC] Could not grant starting bolts: {exc}")
                self.psp_connected = False
                self._starting_items_sent = False
                return
        asyncio.create_task(self._persist_starting_items_sent())

    def _on_vendor_close(self) -> None:
        """Fired when a weapons/mod vendor menu closes. While the vendor is
        open, memory only reflects that vendor's own restricted view
        (apply_vendor_locations() zeroes everything not purchased from it
        or explicitly allowed) — leaving the game that way after the player
        walks away would lock them out of AP-owned weapons/gadgets/mods
        that vendor never granted (e.g. received from another world).
        Re-applying the full AP inventory snapshot restores true ownership
        for actual gameplay."""
        self._on_menu_close_for_armour_sets()
        asyncio.create_task(self._apply_received_items())

    def _on_equipped_armour_saved(self, data: dict) -> None:
        """Fired every time the pause/equip menu closes (Core's
        on_equipped_armour_saved hook, wired from PlanetInventory.
        check_equipped_armour()) — the actual moment equipped armour can
        change, so the set-completion check belongs here, not on vendor
        close (that only ever runs it as a side effect of an unrelated
        menu, never on a normal equip)."""
        self._on_menu_close_for_armour_sets()
        asyncio.create_task(self._persist_armour_slots(data))

    def _on_menu_close_for_armour_sets(self) -> None:
        if not self._armour_set_checks_enabled:
            return
        equipped = self._wiring.armour.EquipedArmour
        for name, check in ARMOUR_SET_CHECKS.items():
            if check.matches(equipped):
                self._append_location_by_name(name)
