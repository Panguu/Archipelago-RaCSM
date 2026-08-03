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
from ..world import RACSizeMatterWorld
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
        self._filler_checkpoint_synced = False
        self._ap_loadout_restored = False
        self._starting_items_sent = False
        self._death_count = 0
        self._pending_item_apply = True
        self._already_hinted: set[int] = set()
        self._notification_item_index: int = 0
        self._last_mod_unlock_write: float = 0.0
        self._armour_set_checks_enabled = False

        self._last_weapon_state_push: float = 0.0
        self._pushed_weapon_state: dict[str, list[int]] = {}
        self._weapon_state_restored = False

        self._death_link_enabled = False
        self._last_death_link = 0.0
        self._debug_messages = False
        self._challenge_defaults_written = False

        self._wiring = Core(self.pine, log=self._log)

    async def _guarded_wiring_call(self, fn: Callable[[], None]) -> None:
        async with self._pine_lock:
            try:
                fn()
            except Exception as exc:
                logger.warning(f"[RAC] PINE call failed during wiring sync: {exc}. "
                                "If syncing stops working, use /reconnect.")
                self.pine_connected = False

    def _filler_applied_key(self) -> str:
        return f"racsm_filler_applied_{self.team}_{self.slot}"

    def _qs_storage_key(self) -> str:
        return f"racsm_quickselect_{self.team}_{self.slot}"

    def _armour_slots_storage_key(self) -> str:
        return f"racsm_armour_slots_{self.team}_{self.slot}"

    def _weapon_state_storage_key(self) -> str:
        return f"racsm_weapon_state_{self.team}_{self.slot}"

    def _try_restore_weapon_state(self) -> None:
        if self._weapon_state_restored or not self._wiring.planet.is_ready:
            return
        key = self._weapon_state_storage_key()
        data = self.stored_data.get(key)
        if isinstance(data, dict):
            self._wiring.planet.weapons.restore_level_experience(data)
            self._weapon_state_restored = True

    def _starting_items_key(self) -> str:
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

    async def _persist_weapon_state(self, data: dict) -> None:
        if self.slot is None:
            return
        await self.send_msgs([{
            "cmd": "Set",
            "key": self._weapon_state_storage_key(),
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

    def _launch_pcsx2_via_dynamic_pine(self) -> None:
        if not self.auth:
            return
        try:
            from worlds.dynamicpine import InstanceAlreadyRunningError, get_pine_port, launch_pcsx2
        except ImportError:
            return
        try:
            port = launch_pcsx2(GAME_NAME, self.auth)
        except InstanceAlreadyRunningError:
            # Already running (e.g. this client reconnecting) - reuse its
            # existing instance rather than treating that as a launch failure.
            port = get_pine_port(GAME_NAME, self.auth)
        except Exception as exc:
            logger.warning(f"[RAC] Dynamic Pine PCSX2 launch failed: {exc}")
            return
        if port is not None:
            self.pine.set_slot(port)

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
            self._weapon_state_restored = False
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
            self._wiring.weapon_level_checks_enabled = (
                int(self.slot_data.get("weapon_level_checks", 0)) >= 1
            )
            self._wiring.planet.weapons.experience_multiplier = (
                int(self.slot_data.get("weapon_experience_multiplier", 0)) or 1
            )
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
                on_equipped_armour_saved = self._on_equipped_armour_saved,
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
                self._launch_pcsx2_via_dynamic_pine()
                asyncio.create_task(self._attempt_pine_connect(), name="PCSX2 PINE connect")
            else:
                asyncio.create_task(self._send_map_page(self.current_planet))
            self._wiring.quick_select.on_save = (
                lambda data: asyncio.create_task(self._persist_quick_select(data))
            )
            for key in (
                self._filler_applied_key(),
                self._qs_storage_key(),
                self._armour_slots_storage_key(),
                self._starting_items_key(),
                self._weapon_state_storage_key(),
            ):
                self.set_notify(key)
            asyncio.create_task(self.send_msgs([{"cmd": "Get", "keys": [
                self._filler_applied_key(),
                self._qs_storage_key(),
                self._armour_slots_storage_key(),
                self._starting_items_key(),
                self._weapon_state_storage_key(),
            ]}]))
            return

        if cmd in ("Retrieved", "SetReply") and self.slot is not None:
            if not self._ap_loadout_restored:
                qs_key = self._qs_storage_key()
                if qs_key in self.stored_data and isinstance(self.stored_data[qs_key], dict):
                    self._wiring.quick_select.load(self.stored_data[qs_key])
                    if self._wiring.planet.is_ready:
                        self._wiring.quick_select.restore()
                armour_key = self._armour_slots_storage_key()
                if armour_key in self.stored_data and isinstance(self.stored_data[armour_key], dict):
                    if self._wiring.planet.is_ready:
                        self._wiring.armour.sync_equipped(self.stored_data[armour_key])
                self._ap_loadout_restored = True
            self._try_restore_weapon_state()
            starting_items_key = self._starting_items_key()
            if starting_items_key in self.stored_data:
                self._starting_items_sent = self._starting_items_sent or bool(self.stored_data[starting_items_key])
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
        version = RACSizeMatterWorld.world_version.as_simple_string()
        ui.base_title = f"Archipelago R&C: Size Matters Client v{version}"
        return ui
