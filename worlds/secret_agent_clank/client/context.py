import asyncio
from typing import Any

from NetUtils import ClientStatus
from rule_builder.rules import False_

tracker_loaded = False
try:
    from worlds.tracker.TrackerClient import UT_VERSION
    from worlds.tracker.TrackerClient import TrackerGameContext as CommonContext
    tracker_loaded = True
except ImportError:
    from CommonClient import CommonContext
from CommonClient import logger

dynamicpine_loaded = False
try:
    from worlds.dynamicpine import DYNAMIC_PINE_VERSION, get_pending_auth, get_pine_port, launched_via_hub
    dynamicpine_loaded = True
except ImportError:
    DYNAMIC_PINE_VERSION = None

from ..constants.weapons import EQUIPMENT_DISPLAY_TO_INTERNAL
from ..core.core import Core
from ..items import GADGET_ITEM_TABLE, TRAP_ITEM_TABLE, WEAPON_ITEM_TABLE

from ..locations import ALL_LOCATIONS
from ..pypine import Pine
from ..rules.vendor_access import VENDOR_REQUIREMENTS
from .command_processor import SACCommandProcessor
from .constants import GAME_NAME
from .deathlink import DeathLinkMixin
from .pine_mixin import PineMixin
from .vendor_scouts import VendorScouts
from .item_names import canonical_item_name


class SACContext(PineMixin, DeathLinkMixin, CommonContext):
    game = GAME_NAME
    command_processor = SACCommandProcessor
    items_handling = 0b111
    current_planet: str = "Galaxy"
    # This is a real game client (syncs live PCSX2 memory), not the passive
    # "Tracker" connection UT's own headless client uses -- dropping this
    # tag keeps the server from treating this connection as tracker-only
    # when worlds.tracker's TrackerGameContext is the resolved base above.
    tags = CommonContext.tags - {"Tracker"}

    def __init__(self, server_address: str | None, password: str | None) -> None:
        super().__init__(server_address, password)

        self.pine = Pine()
        self.pine_connected = False
        self._pine_lock = asyncio.Lock()
        self.slot_data: dict[str, Any] = {}

        self._location_name_to_id = {name: data.code for name, data in ALL_LOCATIONS.items()}
        self.vendor_scouts = VendorScouts(self._location_name_to_id)
        # Location ids already sent in a LocationScouts request this
        # connection -- see _maybe_scout_vendor() (pine_mixin.py's poll
        # loop): scouting is withheld until the native vendor screen is
        # actually open, and even then only for cases already unlocked, so
        # this tracks what's gone out so far rather than re-sending the same
        # ids every tick while the vendor stays open.
        self._scouted_location_ids: set[int] = set()
        self._locally_checked_locations: set[int] = set()
        # Names already warned about via _append_location_by_name (pine_mixin.py)
        # -- native detectors retry a rejected name every tick (see
        # core/case_events.py's confirm() docstring for why that retry
        # matters), but a name genuinely absent from this seed (e.g. a
        # disabled character's case) will never stop being rejected, so
        # only the first rejection is logged to avoid spamming the console.
        self._warned_missing_locations: set[str] = set()

        self._death_link_enabled = False
        self._last_death_link = 0.0
        # None (not just 0) until _load_trap_state() actually hears back
        # from AP -- see that method's docstring for why a fresh client
        # process can't just assume 0 without asking the server first.
        self._processed_trap_count: int | None = None
        self._notification_count = None
        self._notification_slot = None

        self._wiring = Core(self.pine, log=logger.info)
        self._wiring.vendor_rewards.scouts = self.vendor_scouts
        self._wiring.native_runtime.configure_vendors(
            name for name, rule in VENDOR_REQUIREMENTS.items() if not isinstance(rule, False_))

    def _bolt_storage_keys(self) -> tuple[str, str]:
        """AP data-storage keys for this connection's bolt-reward delivery state -- never a local file (see core/bolt_rewards.py's docstring): an external file can't follow the player across machines or survive a wipe, and AP already provides durable per-slot server storage built for exactly this."""
        return (f"secret_agent_clank_delivered_bolts_{self.team}_{self.slot}",
                f"secret_agent_clank_pending_bolts_{self.team}_{self.slot}")

    async def _load_bolt_state(self) -> None:
        """Fetch this slot's delivered/pending bolt state from the AP server (initializing it server-side via "default" if this is the first connection ever) and only then let BoltRewards.deliver() start running -- it stays disabled (see its `enabled` flag) until configure() below actually has real, authoritative values instead of assuming zero and potentially re-granting an already-delivered reward."""
        delivered_key, pending_key = self._bolt_storage_keys()
        # Discard any stale cache from a previous connection this session
        # (e.g. a different slot) so the wait below can't be satisfied by
        # values that were never actually confirmed for THIS connection.
        self.stored_data.pop(delivered_key, None)
        self.stored_data.pop(pending_key, None)
        await self.send_msgs([
            {"cmd": "Set", "key": delivered_key, "want_reply": True, "operations": [
                {"operation": "default", "value": {"count": 0, "starting_delivered": False}}]},
            {"cmd": "Set", "key": pending_key, "want_reply": True,
             "operations": [{"operation": "default", "value": None}]},
        ])
        while delivered_key not in self.stored_data or pending_key not in self.stored_data:
            await asyncio.sleep(0.1)
        delivered = self.stored_data[delivered_key]
        if not isinstance(delivered, dict):
            # Pre-dict-schema leftover from an older client version stored a bare
            # count at this key -- treat it as that count with nothing yet marked
            # as the starting-bolts grant, rather than crashing this task forever.
            delivered = {"count": int(delivered), "starting_delivered": False}
        self._wiring.bolt_rewards.configure(
            starting_bolts=int(self.slot_data.get("starting_bolts", 0)),
            delivered=delivered["count"],
            starting_delivered=delivered["starting_delivered"],
            pending=self.stored_data[pending_key],
        )

    def _save_bolt_state(self, delivered: dict, pending: "dict | None") -> None:
        """BoltRewards.on_state_changed -- persists to AP's server-side data storage, never a local file."""
        delivered_key, pending_key = self._bolt_storage_keys()
        asyncio.create_task(self.send_msgs([
            {"cmd": "Set", "key": delivered_key, "operations": [{"operation": "replace", "value": delivered}]},
            {"cmd": "Set", "key": pending_key, "operations": [{"operation": "replace", "value": pending}]},
        ]))

    def _trap_storage_key(self) -> str:
        """AP data-storage key for how many of items_received's entries have already had activate_trap() fired for them -- never a local file, same reasoning as _bolt_storage_keys()."""
        return f"secret_agent_clank_processed_traps_{self.team}_{self.slot}"

    async def _load_trap_state(self) -> None:
        """Fetch this slot's processed-trap-count from the AP server before _apply_new_traps() is allowed to run -- items_received is the full historical list every time a client (re)connects, so without this a fresh client process would start counting from 0 again and replay activate_trap() for every trap item ever received this seed."""
        key = self._trap_storage_key()
        self.stored_data.pop(key, None)
        await self.send_msgs([
            {"cmd": "Set", "key": key, "want_reply": True, "operations": [{"operation": "default", "value": 0}]},
        ])
        while key not in self.stored_data:
            await asyncio.sleep(0.1)
        self._processed_trap_count = self.stored_data[key]
        # _apply_new_traps() is event-driven (ReceivedItems/RoomUpdate/pine
        # reconnect -- see its call sites), not polled every tick like
        # BoltRewards.deliver(), so if nothing else triggers it before this
        # load finishes, any trap already sitting in items_received would
        # otherwise never get activated. Re-run it now that the count is real.
        asyncio.create_task(self._apply_received_items())

    def _save_trap_state(self, count: int) -> None:
        asyncio.create_task(self.send_msgs(
            [{"cmd": "Set", "key": self._trap_storage_key(), "operations": [{"operation": "replace", "value": count}]}]
        ))

    async def _apply_received_items(self) -> None:
        """Rebuild the per-character AP-ownership snapshot from items_received and hand it to Core.apply_inventory(), which writes it into game memory (gated on the current case being ready)."""
        if self.slot is None or not self.pine_connected:
            return
        received_names = [
            canonical_item_name(self.item_names[self.game].get(network_item.item, ""))
            for network_item in self.items_received
        ]
        ratchet = {
            EQUIPMENT_DISPLAY_TO_INTERNAL[name]: name in received_names
            for name in WEAPON_ITEM_TABLE
        }
        clank   = {name: name in received_names for name in GADGET_ITEM_TABLE}
        async with self._pine_lock:
            try:
                self._wiring.apply_inventory(ratchet=ratchet, clank=clank, received_names=received_names)
                if self._notification_count is not None:
                    for index in range(self._notification_count, len(received_names)):
                        item = self.items_received[index]
                        sender = self.player_names.get(item.player, f"Player {item.player}")
                        self._wiring.notifications.enqueue(received_names[index], sender, bool(item.flags & 4))
                if self._notification_count is not None or received_names:
                    self._notification_count = max(self._notification_count or 0, len(received_names))
            except Exception as exc:
                logger.warning(f"[SAC] PINE call failed while applying items: {exc}. "
                                "If syncing stops working, use /reconnect.")
                self.pine_connected = False
                return
        await self._apply_new_traps(received_names)

    async def _apply_new_traps(self, received_names: list[str]) -> None:
        """Fires activate_trap() once per trap item beyond what's already been processed -- received_names is index-ordered, so slicing from _processed_trap_count only sees genuinely new items."""
        if self._processed_trap_count is None:
            return
        async with self._pine_lock:
            try:
                for index in range(self._processed_trap_count, len(received_names)):
                    name = received_names[index]
                    if name in TRAP_ITEM_TABLE and not self._wiring.activate_trap(name):
                        break
                    self._processed_trap_count = index + 1
                    self._save_trap_state(self._processed_trap_count)
            except Exception as exc:
                logger.warning(f"[SAC] Trap activation deferred: {exc}")

    def _checked_location_names(self) -> set[str]:
        id_to_name = {v: k for k, v in self._location_name_to_id.items()}
        return {
            id_to_name[lid]
            for lid in (self.checked_locations | self._locally_checked_locations)
            if lid in id_to_name
        }

    def _maybe_scout_vendor(self) -> None:
        """Send a LocationScouts request for whatever vendor rows are newly eligible --
        only once the native vendor screen is actually open (Core.vendor.active), and
        even then only for rows whose owning case is already unlocked (Core.owned_cases)
        -- so opening the vendor never reveals/hints a case's contents before the player
        has actually reached that case. Cheap and idempotent to call every poll tick
        while the vendor is open: _scouted_location_ids means already-sent ids are
        never re-requested, and a newly-unlocked case's rows go out the next tick."""
        if self.slot is None or not self._wiring.vendor.active:
            return
        server_locations = getattr(self, "server_locations", None)
        if server_locations is None:
            return
        request = self.vendor_scouts.request(
            server_locations, hint=bool(self.slot_data.get("send_scouted_locations", True)),
            owned_cases=self._wiring.owned_cases,
        )
        new_ids = [lid for lid in request["locations"] if lid not in self._scouted_location_ids]
        if not new_ids:
            return
        self._scouted_location_ids.update(new_ids)
        asyncio.create_task(self.send_msgs([{**request, "locations": new_ids}]))

    def _dynamic_pine_auth(self) -> None:
        """Pre-fills auth from whatever slot name the hub's /launch command was given, so the player isn't asked to retype it -- and so it can't drift from what _dynamic_pine_port() later looks the PCSX2 instance's port up under."""
        if self.auth or not dynamicpine_loaded:
            return
        if not launched_via_hub():
            return
        pending = get_pending_auth()
        if pending:
            self.auth = pending

    def _dynamic_pine_port(self) -> None:
        """This world uses launcher_options="simple" -- the hub's Launch button always starts PCSX2 itself before spawning this client, so this only ever resolves the already-assigned port, never launches anything."""
        if not self.auth or not dynamicpine_loaded:
            return
        if not launched_via_hub():
            return
        port = get_pine_port(GAME_NAME, self.auth)
        if port is not None:
            self.pine.set_slot(port)

    async def server_auth(self, password_requested: bool = False) -> None:
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        self._dynamic_pine_auth()
        await self.get_username()
        await self.send_connect(game=self.game)

    def on_package(self, cmd: str, args: dict[str, Any]) -> None:
        super().on_package(cmd, args)

        if cmd == "RoomInfo":
            self.seed_name = args["seed_name"]
            return

        if cmd == "Connected":
            identity = (self.seed_name, self.team, self.slot)
            if identity != self._notification_slot:
                self._notification_slot = identity
                self._notification_count = None
                self._wiring.notifications.queue.clear()
            self.slot_data = args.get("slot_data", {})
            self.vendor_scouts.rewards.clear()
            self._scouted_location_ids.clear()
            self._wiring.native_runtime.starting_case.configure(self.slot_data)
            asyncio.create_task(self._load_bolt_state())
            asyncio.create_task(self._load_trap_state())
            self._wiring.progression.configure(self.slot_data)
            self._wiring.weapon_mods.configure(self.slot_data)
            self._wiring.wrench.enabled = bool(self.slot_data.get("progressive_wrench", False))
            self._wiring.progressive_planets = self.slot_data.get("progressive_planets")
            self._wiring.character_unlocks = int(self.slot_data.get("infobots", 1)) == 3
            self._wiring.traps.durations.update(self.slot_data.get("trap_duration", {}))
            self._wiring.goal = int(self.slot_data.get("goal", 0))
            self._wiring._goal_sent = False  # Resend after reconnect if the earlier status was lost.
            self._death_link_enabled = bool(self.slot_data.get("death_link", False))
            if self._death_link_enabled:
                self.tags |= {"DeathLink"}
                asyncio.create_task(self.send_msgs([{"cmd": "ConnectUpdate", "tags": list(self.tags)}]))

            self._wiring.wire(
                send_location      = self._append_location_by_name,
                send_deathlink     = self._send_death_link_from_sync,
                death_amnesty      = lambda: int(self.slot_data.get("death_amnesty", 1)),
                death_link_enabled = lambda: self._death_link_enabled,
                on_case_ready      = lambda: None,
                on_goal            = self._send_goal,
                # slot_data's "all_missions" is options.py's Missions
                # value (0 = level_completion, 1 = all -- see world.py's
                # fill_slot_data()).
                missions_all       = lambda: self.slot_data.get("all_missions", 0) == 1,
                on_bolt_state_changed = self._save_bolt_state,
            )
            checked = self._checked_location_names()
            asyncio.create_task(self._pine_guarded(lambda: self._wiring.sync_from_ap(checked)))
            asyncio.create_task(self._apply_received_items())

            if not self.pine_connected:
                self._dynamic_pine_port()
                asyncio.create_task(self._attempt_pine_connect(), name="PCSX2 PINE connect")
            return

        if cmd in ("LocationInfo", "DataPackage", "RoomUpdate"):
            self.vendor_scouts.update(
                self.locations_info.values(), self.item_names.lookup_in_slot,
                lambda slot: self.player_names.get(slot, f"Player {slot}"))

        if cmd == "ReceivedItems" and self._notification_count is None:
            # Initial sync is historical inventory, not a burst of new receipts.
            self._notification_count = len(self.items_received)

        if cmd in ("ReceivedItems", "RoomUpdate"):
            checked = self._checked_location_names()
            asyncio.create_task(self._pine_guarded(lambda: self._wiring.sync_from_ap(checked)))
            asyncio.create_task(self._apply_received_items())
            return

        if cmd == "Bounced" and self._death_link_enabled and "DeathLink" in args.get("tags", []):
            data = args.get("data", {})
            if data.get("source") != self.auth:
                asyncio.create_task(self._receive_death_link(data))

    async def _pine_guarded(self, fn) -> None:
        async with self._pine_lock:
            try:
                fn()
            except Exception as exc:
                logger.warning(f"[SAC] PINE call failed during wiring sync: {exc}. "
                                "If syncing stops working, use /reconnect.")
                self.pine_connected = False

    def _send_goal(self):
        self.finished_game = True
        asyncio.create_task(self.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}]))

    def make_gui(self):
        ui = super().make_gui()
        ui.base_title = "Secret Agent Clank Client"
        if dynamicpine_loaded:
            ui.base_title += f" | Dynamic Pine v{DYNAMIC_PINE_VERSION}"
        if tracker_loaded:
            ui.base_title += f" | Universal Tracker {UT_VERSION}"
        ui.base_title += " | Archipelago"
        return ui
