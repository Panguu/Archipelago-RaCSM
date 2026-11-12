from dataclasses import dataclass

from ..constants import (
    EQUIPMENT_INTERNAL_TO_DISPLAY,
    TITAN_LOCATIONS,
    VENDOR_LOCATIONS,
    VENDOR_ROW_CASES,
    WEAPON_MODS,
    WEAPON_ORDER,
    vendor_location_name,
)


@dataclass(frozen=True)
class VendorReward:
    location_id: int
    item_id: int
    recipient_slot: int
    item_name: str
    recipient_name: str
    flags: int

    @property
    def progression(self):
        return bool(self.flags & 1)

    @property
    def description(self):
        return f"{self.item_name}\nFor {self.recipient_name}"


class VendorScouts:
    def __init__(self, location_ids):
        display_names = EQUIPMENT_INTERNAL_TO_DISPLAY
        self.locations = {
            (0, int(slot)): location_ids[vendor_location_name(display_names.get(internal, internal))]
            for slot, internal in VENDOR_LOCATIONS.items()
            if vendor_location_name(display_names.get(internal, internal)) in location_ids
        }
        self.locations.update({
            (3, mod.mod_id): location_ids[mod.location]
            for mod in WEAPON_MODS if mod.location in location_ids})
        self.locations.update({
            (4, WEAPON_ORDER.index(internal)): location_ids[name]
            for internal, name in TITAN_LOCATIONS.items() if name in location_ids})
        self.rewards = {}
        self.location_ids = location_ids

    def request(self, server_locations, hint: bool = False, vendor_cases=(), vendor_locations=None):
        if vendor_locations is not None:
            locations = sorted({self.location_ids[name] for name in vendor_locations
                                if name in self.location_ids} & set(server_locations))
            return {"cmd": "LocationScouts", "locations": locations, "create_as_hint": 2 if hint else 0}
        locations = sorted({location for row, location in self.locations.items()
                            if VENDOR_ROW_CASES[row] in vendor_cases}
                           & set(server_locations))
        return {"cmd": "LocationScouts", "locations": locations, "create_as_hint": 2 if hint else 0}

    def update(self, items, item_name, player_name):
        allowed = set(self.locations.values())
        for item in items:
            if item.location in allowed:
                self.rewards[item.location] = VendorReward(
                    item.location, item.item, item.player,
                    item_name(item.item, item.player), player_name(item.player), item.flags)

    def for_row(self, row):
        key = row.mod_id if row.node_type == 3 else row.weapon_id
        return self.rewards.get(self.locations.get((row.node_type, key)))
