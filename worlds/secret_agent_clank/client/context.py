import asyncio
from typing import Any

from CommonClient import logger
from NetUtils import ClientStatus
from Utils import async_start

from ..constants.weapons import EQUIPMENT_DISPLAY_TO_INTERNAL
from ..items import GADGET_ITEM_TABLE, TRAP_ITEM_TABLE, WEAPON_ITEM_TABLE
from ..locations import LOCATION_NAME_TO_ID
from .command_processor import SACCommandProcessor
from .constants import GAME_NAME
from .deathlink import DeathLinkMixin
from .item_names import canonical_item_name
from .pine_mixin import PineMixin
from .vendor_scouts import VendorScouts
from .worker_bridge import GameWorker

tracker_loaded = False
try:
    from worlds.tracker.TrackerClient import UT_VERSION
    from worlds.tracker.TrackerClient import TrackerGameContext as CommonContext
    tracker_loaded = True
except ImportError:
    from CommonClient import CommonContext

dynamicpine_loaded = False
try:
    from worlds.dynamicpine import DYNAMIC_PINE_VERSION, get_pending_auth, get_pine_port, launched_via_hub
    dynamicpine_loaded = True
except ImportError:
    DYNAMIC_PINE_VERSION = None


class SACContext(PineMixin, DeathLinkMixin, CommonContext):
    game = GAME_NAME
    command_processor = SACCommandProcessor
    items_handling = 0b111
    current_planet: str = "Galaxy"
    # A real game client, so drop the "Tracker" tag UT's context would otherwise add.
    tags = CommonContext.tags - {"Tracker"}

    def __init__(self, server_address: str | None, password: str | None) -> None:
        super().__init__(server_address, password)

        self._pine_port = 28011
        self._game_state = {}
        self._worker = GameWorker(self._worker_event)
        self.pine_connected = False
        self._pine_lock = asyncio.Lock()
        self.slot_data: dict[str, Any] = {}

        self._location_name_to_id = dict(LOCATION_NAME_TO_ID)
        self.vendor_scouts = VendorScouts(self._location_name_to_id)
        # Location ids already scouted this connection (see _maybe_scout_vendor()).
        self._scouted_location_ids: set[int] = set()
        self._locally_checked_locations: set[int] = set()
        # Rejected location names already logged; detectors retry them every tick.
        self._warned_missing_locations: set[str] = set()

        self._death_link_enabled = False
        self._last_death_link = 0.0
        # None until _load_trap_state() has read the count from the server.
        self._processed_trap_count: int | None = None
        self._notification_count = None
        self._notification_slot = None
        self._stealth_identity = None
        self._stealth_load_task = None

    def _worker_event(self, kind, value, identity=None):
        if identity is not None and identity != self._notification_slot:
            return
        if kind == "log":
            logger.info(value)
        elif kind == "location":
            self._append_location_by_name(value)
        elif kind == "goal":
            self._send_goal()
        elif kind == "death":
            self._send_death_link_from_sync(value)
        elif kind == "bolts":
            self._save_bolt_state(*value)
        elif kind == "stealth":
            key = f"secret_agent_clank_stealth_{self.team}_{self.slot}"
            async_start(self.send_msgs([{"cmd": "Set", "key": key,
                "operations": [{"operation": "max", "value": value}]}]))

    async def _load_stealth_state(self, identity):
        key = f"secret_agent_clank_stealth_{self.team}_{self.slot}"
        self.stored_data.pop(key, None)
        await self.send_msgs([{"cmd": "Set", "key": key, "want_reply": True,
                               "operations": [{"operation": "default", "value": 0}]}])
        while key not in self.stored_data:
            await asyncio.sleep(0.1)
        if identity == self._notification_slot:
            await self._worker.request("stealth", self.stored_data[key])

    async def _configure_game(self, identity, data, allowed):
        try:
            status = await self._worker.request("configure", (identity, data, allowed))
            if identity != self._notification_slot:
                return
            self.pine_connected = status["connected"]
            await self._worker.request("sync", self._checked_location_names())
            async_start(self._load_bolt_state())
            async_start(self._load_trap_state())
            if int(data.get("stealth_takedown_checks", 0)):
                self._stealth_load_task = asyncio.create_task(self._load_stealth_state(identity))
            if not self.pine_connected:
                self._dynamic_pine_port()
                await self._attempt_pine_connect()
            else:
                await self._apply_received_items()
        except Exception:
            logger.exception("[SAC] Game worker configuration failed")
            self.pine_connected = False

    def _bolt_storage_keys(self) -> tuple[str, str]:
        """Server data-storage keys for this slot's delivered and pending bolt rewards."""
        return (f"secret_agent_clank_delivered_bolts_{self.team}_{self.slot}",
                f"secret_agent_clank_pending_bolts_{self.team}_{self.slot}")

    async def _load_bolt_state(self) -> None:
        """Load bolt-reward state from the server, then enable delivery so rewards are never granted twice."""
        identity = self._notification_slot
        delivered_key, pending_key = self._bolt_storage_keys()
        # Drop cached values from an earlier connection so the wait below sees fresh ones.
        self.stored_data.pop(delivered_key, None)
        self.stored_data.pop(pending_key, None)
        await self.send_msgs([
            {"cmd": "Set", "key": delivered_key, "want_reply": True, "operations": [
                {"operation": "default", "value": {"count": 0, "starting_delivered": False}}]},
            {"cmd": "Set", "key": pending_key, "want_reply": True,
             "operations": [{"operation": "default", "value": None}]},
        ])
        while delivered_key not in self.stored_data or pending_key not in self.stored_data:
            if identity != self._notification_slot or self.exit_event.is_set():
                return
            await asyncio.sleep(0.1)
        if identity != self._notification_slot:
            return
        delivered = self.stored_data[delivered_key]
        if not isinstance(delivered, dict):
            # Older clients stored a bare count here.
            delivered = {"count": int(delivered), "starting_delivered": False}
        await self._worker.request("bolts", dict(
            starting_bolts=int(self.slot_data.get("starting_bolts", 0)),
            delivered=delivered["count"],
            starting_delivered=delivered["starting_delivered"],
            pending=self.stored_data[pending_key],
        ))

    def _save_bolt_state(self, delivered: dict, pending: "dict | None") -> None:
        """Persist bolt-reward state to server data storage."""
        delivered_key, pending_key = self._bolt_storage_keys()
        async_start(self.send_msgs([
            {"cmd": "Set", "key": delivered_key, "operations": [{"operation": "replace", "value": delivered}]},
            {"cmd": "Set", "key": pending_key, "operations": [{"operation": "replace", "value": pending}]},
        ]))

    def _trap_storage_key(self) -> str:
        """Server data-storage key for how many received items have been processed for traps."""
        return f"secret_agent_clank_processed_traps_{self.team}_{self.slot}"

    async def _load_trap_state(self) -> None:
        """Load the processed-trap count, so reconnecting doesn't replay every trap ever received."""
        identity = self._notification_slot
        key = self._trap_storage_key()
        self.stored_data.pop(key, None)
        await self.send_msgs([
            {"cmd": "Set", "key": key, "want_reply": True, "operations": [{"operation": "default", "value": 0}]},
        ])
        while key not in self.stored_data:
            if identity != self._notification_slot or self.exit_event.is_set():
                return
            await asyncio.sleep(0.1)
        if identity != self._notification_slot:
            return
        self._processed_trap_count = self.stored_data[key]
        # Traps are only applied on item events, so apply any that arrived while loading.
        async_start(self._apply_received_items())

    def _save_trap_state(self, count: int) -> None:
        async_start(self.send_msgs(
            [{"cmd": "Set", "key": self._trap_storage_key(), "operations": [{"operation": "replace", "value": count}]}]
        ))

    async def _apply_received_items(self) -> None:
        """Pass every received item to Core, queue receipt notifications, then fire new traps."""
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
                notifications = []
                if self._notification_count is not None:
                    for index in range(self._notification_count, len(received_names)):
                        item = self.items_received[index]
                        sender = self.player_names.get(item.player, f"Player {item.player}")
                        notifications.append((received_names[index], sender, bool(item.flags & 4)))
                await self._worker.request("items", (
                    dict(ratchet=ratchet, clank=clank, received_names=received_names), notifications))
                if self._notification_count is not None or received_names:
                    self._notification_count = max(self._notification_count or 0, len(received_names))
            except Exception as exc:
                logger.warning(f"[SAC] PINE call failed while applying items: {exc}. "
                                "If syncing stops working, use /reconnect.")
                self.pine_connected = False
                return
        await self._apply_new_traps(received_names)

    async def _apply_new_traps(self, received_names: list[str]) -> None:
        """Activate each trap received since the last processed index, stopping at one that can't fire yet."""
        if self._processed_trap_count is None:
            return
        async with self._pine_lock:
            try:
                for index in range(self._processed_trap_count, len(received_names)):
                    name = received_names[index]
                    if name in TRAP_ITEM_TABLE and not await self._worker.request("trap", name):
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
        """Scout the seed's vendor catalog once the shared shop is opened."""
        if self.slot is None or not self._game_state.get("vendor_active", False):
            return
        server_locations = getattr(self, "server_locations", None)
        if server_locations is None:
            return
        request = self.vendor_scouts.request(
            server_locations, hint=bool(self.slot_data.get("send_scouted_locations", True)),
            owned_cases=self._game_state.get("owned_cases", ()),
        )
        new_ids = [lid for lid in request["locations"] if lid not in self._scouted_location_ids]
        if not new_ids:
            return
        self._scouted_location_ids.update(new_ids)
        async_start(self.send_msgs([{**request, "locations": new_ids}]))

    def _dynamic_pine_auth(self) -> None:
        """Use the slot name the Dynamic Pine hub launched us with."""
        if self.auth or not dynamicpine_loaded:
            return
        if not launched_via_hub():
            return
        pending = get_pending_auth()
        if pending:
            self.auth = pending

    def _dynamic_pine_port(self) -> None:
        """Connect to the PCSX2 instance the Dynamic Pine hub started for this slot."""
        if not self.auth or not dynamicpine_loaded:
            return
        if not launched_via_hub():
            return
        port = get_pine_port(GAME_NAME, self.auth)
        if port is not None:
            self._pine_port = port

    async def server_auth(self, password_requested: bool = False) -> None:
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        self._dynamic_pine_auth()
        await self.get_username()
        await self.send_connect(game=self.game)

    async def connection_closed(self) -> None:
        if self._stealth_load_task is not None:
            self._stealth_load_task.cancel()
        async def offline():
            try:
                await self._worker.request("ap_connected", False)
            except Exception:
                logger.debug("[SAC] Worker unavailable while disconnecting", exc_info=True)
        async_start(offline())
        await super().connection_closed()

    def on_package(self, cmd: str, args: dict[str, Any]) -> None:
        super().on_package(cmd, args)

        if cmd == "RoomInfo":
            self.seed_name = args["seed_name"]
            return

        if cmd == "Connected":
            self.pine_connected = False
            self._processed_trap_count = None
            identity = (self.seed_name, self.team, self.slot)
            if self._stealth_load_task is not None:
                self._stealth_load_task.cancel()
            if identity != self._notification_slot:
                self._notification_slot = identity
                self._notification_count = None
                self._locally_checked_locations.clear()
            self.slot_data = args.get("slot_data", {})
            self.vendor_scouts.rewards.clear()
            self._scouted_location_ids.clear()
            self._death_link_enabled = bool(self.slot_data.get("death_link", False))
            if self._death_link_enabled:
                self.tags |= {"DeathLink"}
                async_start(self.send_msgs([{"cmd": "ConnectUpdate", "tags": list(self.tags)}]))
            allowed = {name for name, lid in self._location_name_to_id.items() if lid in self.server_locations}
            async_start(self._configure_game(identity, dict(self.slot_data), allowed))
            return

        if cmd in ("LocationInfo", "DataPackage", "RoomUpdate"):
            self.vendor_scouts.update(
                self.locations_info.values(), self.item_names.lookup_in_slot,
                lambda slot: self.player_names.get(slot, f"Player {slot}"))
            async_start(self._worker.request("scouts", dict(self.vendor_scouts.rewards)))

        if cmd == "ReceivedItems" and self._notification_count is None:
            # Initial sync is historical inventory, not a burst of new receipts.
            self._notification_count = len(self.items_received)

        if cmd in ("ReceivedItems", "RoomUpdate"):
            self._resync_from_ap()
            return

        if cmd == "Bounced" and self._death_link_enabled and "DeathLink" in args.get("tags", []):
            data = args.get("data", {})
            if data.get("source") != self.auth:
                async_start(self._receive_death_link(data))

    def _resync_from_ap(self) -> None:
        """Push AP's checked locations into the game, then re-apply received items."""
        checked = self._checked_location_names()
        async_start(self._worker.request("sync", checked))
        async_start(self._apply_received_items())

    def _send_goal(self):
        self.finished_game = True
        async_start(self.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}]))

    def make_gui(self):
        ui = super().make_gui()
        ui.base_title = "Secret Agent Clank Client"
        if dynamicpine_loaded:
            ui.base_title += f" | Dynamic Pine v{DYNAMIC_PINE_VERSION}"
        if tracker_loaded:
            ui.base_title += f" | Universal Tracker {UT_VERSION}"
        ui.base_title += " | Archipelago"
        return ui
