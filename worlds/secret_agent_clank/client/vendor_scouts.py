"""AP-scouted vendor presentation, independent of native price and purchase ID."""
from dataclasses import dataclass

from ..constants.weapon_mods import WEAPON_MODS
from ..constants.weapon_progression import TITAN_LOCATIONS
from ..constants.weapons import CASE_BY_WEAPON_NAME, EQUIPMENT_INTERNAL_TO_DISPLAY
from ..core.inventories.weapons import WEAPON_ORDER
from ..core.patches.locations import VENDOR_LOCATIONS


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
    def title_color(self):
        return "orange" if self.progression else "white"

    @property
    def description(self):
        return f"{self.item_name}\nFor {self.recipient_name}"


class VendorScouts:
    def __init__(self, location_ids):
        display_names = EQUIPMENT_INTERNAL_TO_DISPLAY
        self.locations = {
            (0, int(slot)): location_ids[display_names.get(internal, internal)]
            for slot, internal in VENDOR_LOCATIONS.items()
            if display_names.get(internal, internal) in location_ids
        }
        self.locations.update({
            (3, mod.mod_id): location_ids[mod.location]
            for mod in WEAPON_MODS if mod.location in location_ids})
        self.locations.update({
            (4, WEAPON_ORDER.index(internal)): location_ids[name]
            for internal, name in TITAN_LOCATIONS.items() if name in location_ids})
        self.rewards = {}
        # (node_type, key) -> the case that must be unlocked before this row's
        # location may be scouted -- None for a row with no owning case (e.g.
        # a vendor-only weapon never found in any case), which is always
        # scoutable once the vendor itself is reached. See request()'s
        # owned_cases -- withholds a spoiler-y reveal of a case's vendor
        # contents before the player has actually unlocked that case.
        self.cases = {
            (0, int(slot)): CASE_BY_WEAPON_NAME.get(display_names.get(internal, internal))
            for slot, internal in VENDOR_LOCATIONS.items()
            if display_names.get(internal, internal) in location_ids
        }
        self.cases.update({
            (3, mod.mod_id): CASE_BY_WEAPON_NAME.get(mod.weapon)
            for mod in WEAPON_MODS if mod.location in location_ids})
        self.cases.update({
            (4, WEAPON_ORDER.index(internal)): CASE_BY_WEAPON_NAME.get(display_names.get(internal))
            for internal, name in TITAN_LOCATIONS.items() if name in location_ids})

    def request(self, server_locations, hint: bool = False, owned_cases: "frozenset[str] | None" = None):
        keys = self.locations if owned_cases is None else (
            key for key, case in self.cases.items()
            if case is None or case in owned_cases
        )
        eligible = {self.locations[key] for key in keys}
        locations = sorted(eligible & set(server_locations))
        # create_as_hint: 0 reveals contents locally only; 2 also sends the
        # scout out as a real AP hint (see options.py's SendScoutedLocations).
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
