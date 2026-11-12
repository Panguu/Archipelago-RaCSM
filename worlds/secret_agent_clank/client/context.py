import asyncio
import time
from typing import Any

from CommonClient import logger
from NetUtils import ClientStatus
from Utils import async_start
from ..world import SecretAgentClankWorld

from ..constants import EQUIPMENT_DISPLAY_TO_INTERNAL
from ..items import CASE_GADGET_ITEM_TABLE, EFFECT_ITEMS, EQUIPMENT_ITEM_TABLE
from ..locations import LOCATION_NAME_TO_ID
from .command_processor import SACCommandProcessor
from .constants import GAME_NAME
from .deathlink import DeathLinkMixin
from .pine_mixin import PineMixin
from .ring_link import RingLinkMixin
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


class SACContext(PineMixin, DeathLinkMixin, RingLinkMixin, CommonContext):
    game = GAME_NAME
    command_processor = SACCommandProcessor
    items_handling = 0b111
    current_planet: str = ""
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
        self._scouted_location_ids: set[int] = set()
        self._locally_checked_locations: set[int] = set()
        self._warned_missing_locations: set[str] = set()

        self._death_link_enabled = False
        self._ring_link_enabled = False
        self._ring_link_source = time.time()
        self._ring_link_outgoing = 0
        self._ring_link_pending = 0
        self._ring_link_sent_at = 0.0
        self._processed_trap_count: int | None = None
        self._notification_count = None
        self._notification_slot = None
        self._stealth_identity = None
        self._stealth_load_task = None
        self.debug_logging = False

    def _worker_event(self, kind, value, identity=None):
        if identity is not None and identity != self._notification_slot:
            return
        if kind == "log":
            logger.info(value)
        elif kind == "debug":
            self._debug_log(value)
        elif kind == "location":
            self._append_location_by_name(value)
        elif kind == "goal":
            self._send_goal()
        elif kind == "death":
            self._send_death_link_from_sync(value)
        elif kind == "bolts":
            self._save_bolt_state(*value)
        elif kind == "stealth":
            async_start(self.send_msgs([{"cmd": "Set", "key": self._stealth_key(),
                "operations": [{"operation": "update", "value": value}]}]))

    def _debug_log(self, message):
        if self.debug_logging:
            logger.info(message)

    def _stealth_key(self):
        return f"secret_agent_clank_stealth_cases_{self.team}_{self.slot}"

    async def _load_stealth_state(self, identity):
        key = self._stealth_key()
        self.stored_data.pop(key, None)
        await self.send_msgs([{"cmd": "Set", "key": key, "default": {}, "want_reply": True,
                               "operations": [{"operation": "default", "value": {}}]}])
        while key not in self.stored_data:
            if identity != self._notification_slot or self.exit_event.is_set():
                return
            await asyncio.sleep(0.1)
        if identity == self._notification_slot:
            counts = self.stored_data[key]
            if type(counts) is int and counts == 0:
                counts = {}
                await self.send_msgs([{"cmd": "Set", "key": key,
                    "operations": [{"operation": "replace", "value": counts}]}])
            await self._worker.request("stealth", counts)

    async def _configure_game(self, identity, data, allowed):
        try:
            status = await self._worker.request("configure", (identity, data, allowed))
            if identity != self._notification_slot:
                return
            self.pine_connected = status["connected"]
            await self._worker.request("sync", self._checked_location_names())
            async_start(self._load_bolt_state())
            async_start(self._load_trap_state())
            if data.get("stealth_cases"):
                self._stealth_load_task = asyncio.create_task(self._load_stealth_state(identity))
                await self._stealth_load_task
                if identity != self._notification_slot or self.exit_event.is_set():
                    return
            if not self.pine_connected:
                self._dynamic_pine_port()
                await self._attempt_pine_connect()
            else:
                await self._apply_received_items()
        except Exception:
            logger.exception("[SAC] Game worker configuration failed")
            async with self._pine_lock:
                await self._teardown_pine_connection()

    def _bolt_storage_keys(self) -> tuple[str, str]:
        return (f"secret_agent_clank_delivered_bolts_{self.team}_{self.slot}",
                f"secret_agent_clank_pending_bolts_{self.team}_{self.slot}")

    async def _load_bolt_state(self) -> None:
        """Load bolt-reward state from the server, then enable delivery so rewards are never granted twice."""
        identity = self._notification_slot
        delivered_key, pending_key = self._bolt_storage_keys()
        self.stored_data.pop(delivered_key, None)
        self.stored_data.pop(pending_key, None)
        await self.send_msgs([
            {"cmd": "Set", "key": delivered_key, "default": {"count": 0, "starting_delivered": False},
             "want_reply": True, "operations": [
                {"operation": "default", "value": {"count": 0, "starting_delivered": False}}]},
            {"cmd": "Set", "key": pending_key, "default": None, "want_reply": True,
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
            delivered = {"count": int(delivered), "starting_delivered": False}
        await self._worker.request("bolts", dict(
            starting_bolts=int(self.slot_data.get("starting_bolts", 0)),
            delivered=delivered["count"],
            starting_delivered=delivered["starting_delivered"],
            pending=self.stored_data[pending_key],
        ))

    def _save_bolt_state(self, delivered: dict, pending: dict | None) -> None:
        delivered_key, pending_key = self._bolt_storage_keys()
        async_start(self.send_msgs([
            {"cmd": "Set", "key": delivered_key, "operations": [{"operation": "replace", "value": delivered}]},
            {"cmd": "Set", "key": pending_key, "operations": [{"operation": "replace", "value": pending}]},
        ]))

    def _trap_storage_key(self) -> str:
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
        async_start(self._apply_received_items())

    def _save_trap_state(self, count: int) -> None:
        async_start(self.send_msgs(
            [{"cmd": "Set", "key": self._trap_storage_key(), "operations": [{"operation": "replace", "value": count}]}]
        ))

    async def _apply_received_items(self) -> None:
        if self.slot is None or not self.pine_connected:
            return
        received_names = [
            self.item_names[self.game].get(network_item.item, "")
            for network_item in self.items_received
        ]
        ratchet = {
            EQUIPMENT_DISPLAY_TO_INTERNAL[name]: name in received_names
            for name in EQUIPMENT_ITEM_TABLE
        }
        clank   = {name: name in received_names for name in CASE_GADGET_ITEM_TABLE}
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
        """Apply each trap and XP filler received since the last processed index, stopping at one that can't apply yet."""
        if self._processed_trap_count is None:
            return
        async with self._pine_lock:
            try:
                for index in range(self._processed_trap_count, len(received_names)):
                    name = received_names[index]
                    if name in EFFECT_ITEMS and not await self._worker.request("effect", name):
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
        if self.slot is None or not self._game_state.get("vendor_active", False):
            return
        server_locations = getattr(self, "server_locations", None)
        if server_locations is None:
            return
        request = self.vendor_scouts.request(
            server_locations, hint=bool(self.slot_data.get("send_scouted_locations", True)),
            vendor_cases=self._game_state.get("vendor_cases", ()),
            vendor_locations=self._game_state.get("vendor_locations"),
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

        if cmd == "Bounced":
            self._on_ring_link(args)
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
            async_start(self.update_death_link(self._death_link_enabled))
            async_start(self._set_ring_link_enabled(bool(self.slot_data.get("ring_link", False))))
            allowed = {name for name, lid in self._location_name_to_id.items() if lid in self.server_locations}
            async_start(self._configure_game(identity, dict(self.slot_data), allowed))
            return

        if cmd in ("LocationInfo", "DataPackage", "RoomUpdate"):
            self.vendor_scouts.update(
                self.locations_info.values(), self.item_names.lookup_in_slot,
                lambda slot: self.player_names.get(slot, f"Player {slot}"))
            async_start(self._worker.request("scouts", dict(self.vendor_scouts.rewards)))

        if cmd == "ReceivedItems" and self._notification_count is None:
            self._notification_count = len(self.items_received)

        if cmd in ("ReceivedItems", "RoomUpdate"):
            self._resync_from_ap()
            return

        if cmd == "PrintJSON" and args.get("type") == "ItemSend":
            self._notify_sent_item(args)
            return

    def _notify_sent_item(self, args: dict[str, Any]) -> None:
        item, receiver = args["item"], args["receiving"]
        # Self-finds already show as received.
        if item.player != self.slot or receiver == self.slot:
            return
        name = self.item_names.lookup_in_slot(item.item, receiver)
        player = self.player_names.get(receiver, f"Player {receiver}")
        async_start(self._worker.request("sent", (name, player, bool(item.flags & 4))))

    def _resync_from_ap(self) -> None:
        checked = self._checked_location_names()
        async_start(self._worker.request("sync", checked))
        async_start(self._apply_received_items())

    def _send_goal(self):
        self.finished_game = True
        async_start(self.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}]))

    def make_gui(self):
        ui = super().make_gui()
        version = SecretAgentClankWorld.world_version.as_simple_string()
        base_name = "SAC" if tracker_loaded and dynamicpine_loaded else "Secret Agent Clank"
        ui.base_title = f"{base_name} v{version}"
        if dynamicpine_loaded:
            ui.base_title += f" | Dynamic Pine v{DYNAMIC_PINE_VERSION}"
        if tracker_loaded:
            ui.base_title += f" | Universal Tracker {UT_VERSION}"
        ui.base_title += " | Archipelago"
        return ui
