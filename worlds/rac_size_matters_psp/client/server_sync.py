from __future__ import annotations

from ..core.address_maps import CURRENT_PLANET_ADDRESS
from ..core.structs.game import TransitionGateStruct, TRANSITION_GATE_IDLE


class ServerSyncMixin:
    """Wait for fresh server snapshots before replacing the loaded save."""

    def _server_storage_keys(self) -> set[str]:
        return {self._filler_applied_key(), self._qs_storage_key(),
                self._armour_slots_storage_key(), self._starting_items_key(),
                self._weapon_state_storage_key()}

    def _reset_server_sync(self) -> None:
        self._items_received_ready = False
        self._fresh_storage_keys: set[str] = set()
        self._save_data_received = False
        self._filler_checkpoint_synced = False
        self._starting_checkpoint_synced = False
        self._starting_items_sent = False
        self._ap_loadout_restored = False
        self._weapon_state_restored = False
        self._processed_item_count = self._processed_trap_count = 0
        self._filler_persisted_checkpoint = None
        self._pushed_weapon_state = {}
        self._server_progress_synced = False

    @property
    def _server_state_ready(self) -> bool:
        return self._items_received_ready and self._save_data_received

    def _record_server_snapshot(self, cmd: str, args: dict) -> None:
        if cmd == "ReceivedItems" and args.get("index", 0) == 0:
            self._items_received_ready = True
        elif cmd == "Retrieved":
            # stored_data can still contain a previous connection's cache.
            # Only actual Get replies establish this connection's snapshot;
            # an unrelated SetReply must not complete restoration.
            self._fresh_storage_keys.update(self._server_storage_keys().intersection(args.get("keys", {})))
            self._save_data_received = self._server_storage_keys() <= self._fresh_storage_keys
        if not self._server_state_ready:
            return
        if not self._filler_checkpoint_synced:
            checkpoint = max(0, min(int(self.stored_data.get(self._filler_applied_key()) or 0),
                                    len(self.items_received)))
            self._processed_item_count = self._processed_trap_count = checkpoint
            self._filler_checkpoint_synced = True
        if not self._starting_checkpoint_synced:
            self._starting_items_sent = bool(self.stored_data.get(self._starting_items_key()))
            self._starting_checkpoint_synced = True

    def _restore_server_loadout(self) -> None:
        """Called under the PSP lock after the current overlay is ready."""
        if not self._server_state_ready or not self._game_memory_ready() or self._wiring.vendor_active:
            return
        if not self._ap_loadout_restored:
            self._wiring.skin.set_by_option(self._starting_skin_option)
            quick_select = self.stored_data.get(self._qs_storage_key())
            if isinstance(quick_select, dict):
                self._wiring.quick_select.load(quick_select)
                self._wiring.quick_select.restore()
            armour = self.stored_data.get(self._armour_slots_storage_key())
            if isinstance(armour, dict):
                self._wiring.armour.sync_equipped(armour)
            self._ap_loadout_restored = True
        self._try_restore_weapon_state()

    def _prepare_server_gameplay(self) -> None:
        if self._server_state_ready and not self._server_progress_synced:
            self._wiring.sync_from_ap(self._checked_location_names())
            self._server_progress_synced = True

    def _game_memory_ready(self) -> bool:
        return (self.psp_connected and self._wiring.planet.is_ready
                and self.pine.read_int32(TransitionGateStruct.BASE_ADDRESS) == TRANSITION_GATE_IDLE
                and self.pine.read_int8(CURRENT_PLANET_ADDRESS) == self._wiring.planet.planet_id)
