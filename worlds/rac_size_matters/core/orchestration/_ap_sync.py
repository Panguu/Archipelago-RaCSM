from __future__ import annotations

from typing import Any


class APSyncMixin:
    """Syncs game state with Archipelago server events."""

    def on_ap_connected(
        self,
        slot_data: dict[str, Any],
        checked_location_names: set[str],
    ) -> None:
        self._checked_locations = checked_location_names
        self.clank.sync_from_ap(checked_location_names)
        self.skyboard.sync_from_ap(checked_location_names)
        self.weapons.sync_from_ap(checked_location_names)
        self.skill_points.sync_from_ap(checked_location_names)
        self.armour.sync_from_ap(checked_location_names)
        self.armour_sets.sync_from_ap(checked_location_names)
        self.missions.sync_from_ap(checked_location_names)

    def on_ap_received_items(self, checked_location_names: set[str]) -> None:
        self._checked_locations = checked_location_names
        self.clank.sync_from_ap(checked_location_names)
        self.skyboard.sync_from_ap(checked_location_names)
        self.weapons.sync_from_ap(checked_location_names)
        self.skill_points.sync_from_ap(checked_location_names)
        self.armour.sync_from_ap(checked_location_names)
        self.armour_sets.sync_from_ap(checked_location_names)
        self.missions.sync_from_ap(checked_location_names)
        self._reapply_inv()
