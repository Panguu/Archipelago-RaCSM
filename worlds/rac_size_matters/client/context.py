from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

tracker_loaded: bool = False
try:
    from worlds.tracker.TrackerClient import TrackerGameContext as CommonContext
    tracker_loaded = True
except ImportError:
    from CommonClient import CommonContext
from CommonClient import logger

from ..core import TextColour, colored_text, set_trap_durations
from ..core.core import Core
from ..locations import ALL_LOCATIONS
from ..pypine import Pine
from .command_processor import RACCommandProcessor
from .constants import GAME_NAME
from .deathlink import DeathLinkMixin
from .handlers import CutsceneHandlerMixin, EventsHandlerMixin
from .pine_mixin import PineMixin
from .vendor import InventoryMixin, VendorHandlerMixin


class RACContext(
    PineMixin, CutsceneHandlerMixin, EventsHandlerMixin,
    DeathLinkMixin, VendorHandlerMixin, InventoryMixin, CommonContext,
):
    game = GAME_NAME
    command_processor = RACCommandProcessor
    items_handling = 0b111
    current_planet: str = "Galaxy"
    tags = CommonContext.tags - {"Tracker"}

    def __init__(self, server_address: str | None, password: str | None) -> None:
        super().__init__(server_address, password)

        self.pine = Pine()
        self.pine_connected = False
        self._pine_lock = asyncio.Lock()
        self.slot_data: dict[str, Any] = {}

        self._location_name_to_id = {name: data.code for name, data in ALL_LOCATIONS.items()}
        self._locally_checked_locations: set[int] = set()

        self._pending_armour_pickup_locs: list[str] = []
        self._processed_item_count = 0
        self._processed_trap_count = 0
        # Whether the persisted "how many items_received have already had
        # their bolts/traps granted to the live PS2 memory" checkpoint has
        # been fetched from the AP server's data storage yet (see
        # _filler_applied_key). items_received alone can't tell us what's
        # actually been written to the game, since a fresh client process
        # always replays the entire history from index 0 — without this, a
        # client restart would either re-grant every historical bolt/trap (no
        # local counter survives the restart) or, with the old "assume a full
        # resync means everything already happened" heuristic, silently skip
        # ones that were received but never actually applied (e.g. PCSX2
        # wasn't connected yet). Granting is gated on this being True so we
        # never grant against the wrong (zero) starting point.
        self._filler_checkpoint_synced = False
        # Guards quick-select/armour restore-from-AP so it only applies once
        # per reconnect — without this, set_notify echoing our own later
        # push_save()/push_slots_save() writes back as SetReply would
        # re-trigger restore_equipped_slots() on every in-game change.
        self._ap_loadout_restored = False
        # Whether starting bolts have already been granted, per a flag
        # persisted to AP data storage (racsm_starting_items_sent_*) — NOT a
        # local bool, so a client restart or reconnect doesn't re-grant them.
        # Starts False (unset key reads as 0/falsy); flipped True only after
        # a confirmed successful grant.
        self._starting_items_sent = False
        self._death_count = 0
        self._pending_item_apply = True
        self._already_hinted: set[int] = set()
        self._notification_item_index: int = 0
        self._last_mod_unlock_write: float = 0.0
        self._armour_set_checks_enabled = False

        self._death_link_enabled = False
        self._last_death_link = 0.0
        self._debug_messages = False
        self._challenge_defaults_written = False

        self._wiring = Core(self.pine, log=self._log)

    async def _guarded_wiring_call(self, fn: Callable[[], None]) -> None:
        """Runs a synchronous Core call under the PINE lock so it can't
        interleave PINE requests with game_watcher's poll loop.

        Does NOT skip when PCSX2 isn't connected — callers include pure
        in-memory bookkeeping (e.g. sync_from_ap, which never touches
        self.pine) that must still run before the first PINE connect attempt
        completes, since that's now triggered from the same "Connected"
        handler that calls this. A connection drop mid-call is still treated
        as a soft flag, not a crash, same as game_watcher's poll loop.

        Runs fn() in-line rather than via run_in_executor — same reasoning as
        PineMixin._attempt_pine_connect: a thread-pool worker stuck inside a
        slow/timing-out PINE call would hold _pine_lock for the entire 5s
        socket timeout, freezing every other PINE consumer (poll loop, vendor
        sync, deathlink) behind it for that whole window. RAC3's equivalent
        calls are all in-line on its single coroutine for the same reason.
        """
        async with self._pine_lock:
            try:
                fn()
            except Exception as exc:
                # Not a full disconnect — game_watcher's poll loop (which drives
                # Core.tick() independently) keeps running regardless of this
                # failing, so pickup/location detection isn't affected by this
                # alone. This just stops this particular sync call until the
                # next successful one.
                logger.warning(f"[RAC] PINE call failed during wiring sync: {exc}. "
                                "If syncing stops working, use /reconnect.")
                self.pine_connected = False

    def _filler_applied_key(self) -> str:
        """AP data-storage key for the persisted bolts/traps-applied checkpoint,
        scoped per team+slot so it survives client process restarts."""
        return f"racsm_filler_applied_{self.team}_{self.slot}"

    def _qs_storage_key(self) -> str:
        return f"racsm_quickselect_{self.team}_{self.slot}"

    def _armour_slots_storage_key(self) -> str:
        return f"racsm_armour_slots_{self.team}_{self.slot}"

    def _starting_items_key(self) -> str:
        """AP data-storage key marking whether starting bolts have already
        been granted (0/unset = not yet, 1 = granted) — persisted so a
        client restart or reconnect never re-grants them."""
        return f"racsm_starting_items_sent_{self.team}_{self.slot}"

    async def _persist_starting_items_sent(self) -> None:
        if self.slot is None:
            return
        await self.send_msgs([{
            "cmd": "Set",
            "key": self._starting_items_key(),
            "default": 0,
            "want_reply": False,
            "operations": [{"operation": "replace", "value": 1}],
        }])

    async def _persist_quick_select(self, data: dict) -> None:
        if self.slot is None:
            return
        await self.send_msgs([{
            "cmd": "Set",
            "key": self._qs_storage_key(),
            "default": {},
            "want_reply": False,
            "operations": [{"operation": "replace", "value": data}],
        }])

    async def _persist_armour_slots(self, data: dict) -> None:
        if self.slot is None:
            return
        await self.send_msgs([{
            "cmd": "Set",
            "key": self._armour_slots_storage_key(),
            "default": {},
            "want_reply": False,
            "operations": [{"operation": "replace", "value": data}],
        }])

    def _checked_location_names(self) -> set[str]:
        id_to_name = {v: k for k, v in self._location_name_to_id.items()}
        return {
            id_to_name[lid]
            for lid in (self.checked_locations | self._locally_checked_locations)
            if lid in id_to_name
        }

    def _log(self, msg: str, level: str = "info") -> None:
        if not self._debug_messages:
            return
        if level == "warning":
            logger.warning(msg)
        else:
            logger.info(msg)

    async def server_auth(self, password_requested: bool = False) -> None:
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        await self.get_username()
        await self.send_connect(game=self.game)

    def on_package(self, cmd: str, args: dict[str, Any]) -> None:
        super().on_package(cmd, args)

        if cmd == "Connected":
            self.slot_data = args.get("slot_data", {})
            self._already_hinted.clear()
            self._ap_loadout_restored = False
            self._death_link_enabled = bool(self.slot_data.get("death_link", False))
            self._armour_set_checks_enabled = bool(self.slot_data.get("armour_set_checks", False))
            clank_mode = int(self.slot_data.get("clank_challenges", 1))
            self._wiring.clank_enabled        = clank_mode >= 1
            self._wiring.clank_all_challenges = clank_mode >= 2
            self._wiring.skyboard_enabled     = int(self.slot_data.get("skyboard_challenges", 0)) >= 1
            self._wiring.skill_points_enabled = (
                int(self.slot_data.get("skill_points", 0)) >= 1
                or bool(self.slot_data.get("enable_clank_challenge_skill_points", False))
                or bool(self.slot_data.get("enable_skyboard_challenge_skill_points", False))
            )
            # Option encodes "off" as 0 — `or 1` maps that straight to a 1x
            # (no-op) multiplier instead of a bogus 0x.
            self._wiring.planet.weapons.experience_multiplier = (
                int(self.slot_data.get("weapon_experience_multiplier", 0)) or 1
            )
            # 0/1/2 = off/manual/automatic — matches PROGRESSIVE_OFF/
            # PROGRESSIVE_MANUAL/PROGRESSIVE_AUTOMATIC in core/weapons.py.
            self._wiring.planet.weapons.progressive_mode = (
                int(self.slot_data.get("progressive_weapons", 0))
            )
            self._wiring.player_bolts.multiplier = (
                int(self.slot_data.get("bolt_multiplier", 0)) or 1
            )
            trap_duration = self.slot_data.get("trap_duration")
            if isinstance(trap_duration, dict):
                set_trap_durations(trap_duration)
            self._wiring.skin.set_by_option(int(self.slot_data.get("starting_skin", 0)))
            if self._death_link_enabled:
                asyncio.create_task(self.send_msgs([{"cmd": "ConnectUpdate", "tags": ["DeathLink"]}]))
            self._wiring.wire(
                send_location      = self._append_location_by_name,
                send_deathlink     = self._send_death_link_from_sync,
                death_amnesty      = lambda: int(self.slot_data.get("death_amnesty", 1)),
                death_link_enabled = lambda: self._death_link_enabled,
                on_goal            = lambda: asyncio.create_task(self._send_goal_status()),
                on_vendor_open     = lambda: asyncio.create_task(self._send_vendor_hints()),
                on_vendor_close    = self._on_vendor_close,
                on_equipped_armour_saved = lambda data: asyncio.create_task(self._persist_armour_slots(data)),
                on_bonus_weapon_pickup = self._grant_random_bonus_item,
                on_scripted_gadget_pickup = self._handle_scripted_gadget_pickup,
                on_planet_ready    = self._on_planet_ready,
                on_initial_load    = lambda: asyncio.create_task(self._send_playing_status()),
            )
            checked = self._checked_location_names()
            asyncio.create_task(self._guarded_wiring_call(
                lambda: self._wiring.sync_from_ap(checked)
            ))
            self._pending_item_apply = True
            asyncio.create_task(self._apply_received_items())
            self._write_notification_text(colored_text(
                "Connected to ", TextColour.YELLOW, "Archipelago", TextColour.WHITE,
            ))
            if not self.pine_connected:
                asyncio.create_task(self._attempt_pine_connect(), name="PCSX2 PINE connect")
            else:
                # PCSX2 never dropped, so _attempt_pine_connect's own
                # _send_map_page call (which only fires on a PINE reconnect)
                # won't run here. current_planet is always kept fresh by the
                # independent PINE poll loop regardless of the AP server
                # connection, so re-push it now rather than leaving the
                # server's stored value stuck at whatever it was before this
                # AP (re)connect — it's not something to persist and trust,
                # it's something to always re-check and re-send on connect.
                asyncio.create_task(self._send_map_page(self.current_planet))
            # Wire the quick-select save callback — pushed to AP data storage on
            # pause-menu close (Core wires PlanetInventory.on_pause_close to
            # quick_select.push_save() internally), not on every poll-detected
            # change. Armour's equivalent is on_equipped_armour_saved, passed
            # directly to wire() above since it's fired the same way.
            self._wiring.quick_select.on_save = (
                lambda data: asyncio.create_task(self._persist_quick_select(data))
            )
            # Fetch persisted state from AP server. team/slot are only known now
            # (after super().on_package() set them), so registration must happen here.
            # set_notify keeps values current for the rest of the connection;
            # the explicit Get is needed because the set_notify batch already
            # fired before these keys were registered.
            for key in (
                self._filler_applied_key(),
                self._qs_storage_key(),
                self._armour_slots_storage_key(),
                self._starting_items_key(),
            ):
                self.set_notify(key)
            asyncio.create_task(self.send_msgs([{"cmd": "Get", "keys": [
                self._filler_applied_key(),
                self._qs_storage_key(),
                self._armour_slots_storage_key(),
                self._starting_items_key(),
            ]}]))
            return

        if cmd in ("Retrieved", "SetReply") and self.slot is not None:
            if not self._ap_loadout_restored:
                qs_key = self._qs_storage_key()
                if qs_key in self.stored_data and isinstance(self.stored_data[qs_key], dict):
                    self._wiring.quick_select.load(self.stored_data[qs_key])
                armour_key = self._armour_slots_storage_key()
                if armour_key in self.stored_data and isinstance(self.stored_data[armour_key], dict):
                    if self._wiring.planet.is_ready:
                        self._wiring.armour.sync_equipped(self.stored_data[armour_key])
                self._ap_loadout_restored = True
            starting_items_key = self._starting_items_key()
            if starting_items_key in self.stored_data:
                self._starting_items_sent = bool(self.stored_data[starting_items_key])
                # Otherwise this only ever gets attempted from _on_planet_ready
                # (a transition edge) — if PCSX2 was already connected with a
                # planet loaded before this AP (re)connect, no new transition
                # fires, so the grant would silently wait for the player to
                # next travel somewhere. PLAYER_BOLT_COUNT is a global address
                # (safe to write any time a planet is ready), so fire the
                # attempt now instead of waiting for that.
                if not self._starting_items_sent and self._wiring.planet.is_ready:
                    asyncio.create_task(self._grant_starting_items())
            if not self._filler_checkpoint_synced:
                key = self._filler_applied_key()
                if key in self.stored_data:
                    checkpoint = min(int(self.stored_data[key] or 0), len(self.items_received))
                    self._processed_item_count = checkpoint
                    self._processed_trap_count = checkpoint
                    self._filler_checkpoint_synced = True
                    self._pending_item_apply = True
                    asyncio.create_task(self._apply_received_items())
            return

        if cmd == "ReceivedItems":
            if args.get("index", 0) == 0:
                # Full resync (initial connect or reconnect). The base handler
                # just rebuilt items_received from scratch with the player's
                # entire history — none of these are newly received this
                # session, so baseline the notification index past them to
                # avoid replaying old notifications. Bolts/traps are NOT
                # baselined here — _filler_checkpoint_synced gates their
                # granting until the real server-persisted checkpoint (above)
                # arrives, instead of guessing.
                self._notification_item_index = len(self.items_received)
            checked = self._checked_location_names()
            asyncio.create_task(self._guarded_wiring_call(
                lambda: self._wiring.sync_from_ap(checked)
            ))
            self._pending_item_apply = True
            asyncio.create_task(self._apply_received_items())
            return

        if cmd == "Bounced" and self._death_link_enabled and "DeathLink" in args.get("tags", []):
            data = args.get("data", {})
            if data.get("source") != self.auth:
                asyncio.create_task(self._receive_death_link(data))

    def on_connection_closed(self) -> None:
        super().on_connection_closed()
        self._write_notification_text(colored_text(
            "Disconnected from ", TextColour.YELLOW, "Archipelago", TextColour.WHITE,
        ))

    def make_gui(self):
        ui = super().make_gui()
        ui.base_title = "Archipelago R&C: Size Matters Client"
        return ui
