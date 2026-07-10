from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from ..constants import Rac5ModVendorLocations
from ..locations import GADGET_INTERNAL_TO_LOCATION, MOD_INTERNAL_TO_LOCATION, WEAPON_INTERNAL_TO_LOCATION
from .address_maps import PLANET_ADDRESSES, WEAPON_VENDOR_ITEMS, WEAPON_VENDOR_SLOTS
from .controller import GlobalButtonState, PauseSelectButtons
from .menu import MenuStateValue

if TYPE_CHECKING:
    from ..pypine import Pine
    from .planets import PlanetInventory, PlanetUnlockState
    from .weapons import WeaponInventory

# WEAPON_VENDOR_ITEMS is a flat array immediately followed in memory by
# WEAPON_VENDOR_SLOTS (the count). The gap between them is the array's full
# capacity — slots beyond the written count must be zeroed too, otherwise
# stale entries from a previous, longer write keep showing up in the vendor
# menu instead of disappearing.
MAX_VENDOR_SLOTS = (WEAPON_VENDOR_SLOTS - WEAPON_VENDOR_ITEMS) // 4

# Vendor item IDs written to WEAPON_VENDOR_ITEMS.
# Each 4-byte entry identifies one slot in the vendor menu UI.
# Derivation: combined weapon+gadget array slot index + 2 offset.
# lacerator (slot 0) = 0x02 is the only in-game confirmed value.
# All others are inferred from array layout — verify in-game.
WEAPON_VENDOR_IDS: dict[str, int] = {
    # weapons (WEAPON_ORDER slots 0-13; slot 12 is None gap → 0x0E skipped)
    "lacerator":        0x02,  # confirmed
    "concussion_gun":   0x03,
    "acid_bomb_glove":  0x04,
    "agents_of_doom":   0x05,
    "bee_mine_glove":   0x06,
    "static_barrier":   0x07,
    "shock_rocket":     0x08,
    "sniper_mine":      0x09,
    "scorcher":         0x0A,
    "laser_tracer":     0x0B,
    "suck_cannon":      0x0C,
    "mootator":         0x0D,
    # slot 12 gap → 0x0E (no weapon)
    "ryno":             0x0F,
    # gadgets (GADGET_ORDER slots 0-8; slot 6 is None gap → 0x16 skipped)
    "hypershot":        0x10,
    "sprout_o_matic":   0x11,
    "polarizer":        0x12,
    "pda":              0x13,
    "shrink_ray":       0x14,
    "bolt_grabber":     0x15,
    # slot 6 gap → 0x16 (no gadget)
    "map_o_matic":      0x17,
    "box_breaker":      0x18,
}

# internal weapon/gadget name -> PlanetUnlockState key, for deciding which
# items are currently purchasable (their vendor planet is AP-accessible).
# Ryno/mootator/sprout_o_matic/polarizer/shrink_ray aren't sold at any
# weapons vendor, so they're deliberately absent here.
_WEAPON_TO_PLANET_KEY: dict[str, str] = {
    "lacerator":       "POKITARU",
    "acid_bomb_glove": "POKITARU",
    "concussion_gun":  "POKITARU",
    "agents_of_doom":  "RYLLUS",
    "scorcher":        "KALIDON",
    "suck_cannon":     "DREAMTIME",
    "bee_mine_glove":  "OUTPOST_OMEGA",
    "sniper_mine":     "CHALLAX",
    "shock_rocket":    "DAYNI_MOON",
    "static_barrier":  "INSIDE_CLANK",
    "laser_tracer":    "QUODRONA",
}

_GADGET_TO_PLANET_KEY: dict[str, str] = {
    "hypershot":    "POKITARU",
    "pda":          "CHALLAX",
    "map_o_matic":  "DAYNI_MOON",
    "bolt_grabber": "CHALLAX",
    "box_breaker":  "OUTPOST_OMEGA",
}

# Mod vendor AP location -> PlanetUnlockState key, one entry per
# Rac5ModVendorLocations constant.
_MOD_LOCATION_TO_PLANET_KEY: dict[str, str] = {
    Rac5ModVendorLocations.KALIDON_LACERATOR_LOCK:     "KALIDON",
    Rac5ModVendorLocations.KALIDON_CONCUSSION_SPLIT:   "KALIDON",
    Rac5ModVendorLocations.CHALLAX_LACERATOR_DOUBLE:   "CHALLAX",
    Rac5ModVendorLocations.CHALLAX_ACID_BURN:          "CHALLAX",
    Rac5ModVendorLocations.CHALLAX_ACID_EPOXY:         "CHALLAX",
    Rac5ModVendorLocations.CHALLAX_CONCUSSION_LOCK:    "CHALLAX",
    Rac5ModVendorLocations.CHALLAX_CONCUSSION_CHARGE:  "CHALLAX",
    Rac5ModVendorLocations.CHALLAX_BEE_WORKER:         "CHALLAX",
    Rac5ModVendorLocations.QUODRONA_AGENTS_LAUNCHER:   "QUODRONA",
    Rac5ModVendorLocations.QUODRONA_SCORCHER_SPITFIRE: "QUODRONA",
    Rac5ModVendorLocations.QUODRONA_SNIPER_SPLIT:      "QUODRONA",
    Rac5ModVendorLocations.QUODRONA_SHOCK_LOCK:        "QUODRONA",
    Rac5ModVendorLocations.QUODRONA_SHOCK_AFTER:       "QUODRONA",
}


class WeaponVendorMenu:
    """Weapons vendor menu (sells weapons/gadgets) open/close toggle."""

    def __init__(self) -> None:
        self.active = False

    def activate(self) -> None:
        self.active = True

    def deactivate(self) -> None:
        self.active = False

    def __repr__(self) -> str:
        return f"WeaponVendorMenu(active={self.active})"


class ModVendorMenu:
    """Weapon mod vendor menu (sells mod slots) open/close toggle."""

    def __init__(self) -> None:
        self.active = False

    def activate(self) -> None:
        self.active = True

    def deactivate(self) -> None:
        self.active = False

    def __repr__(self) -> str:
        return f"ModVendorMenu(active={self.active})"


class VendorInventory:
    """Pine-backed accessor for the vendor item list/size array
    (WEAPON_VENDOR_ITEMS/WEAPON_VENDOR_SLOTS).

    weapon_vendor()/mod_vendor() are the hooks fired when their respective
    menu opens — left empty for now, filled in as that logic is rebuilt.
    add_weapon() just tracks which rac5 weapon/gadget names belong in the
    vendor's item list; refresh() is what actually writes that list into
    game memory.
    """

    def __init__(
        self,
        pine: Pine,
        planet: PlanetInventory,
        planet_unlock: PlanetUnlockState,
        send_location: Callable[[str], None],
    ) -> None:
        self.pine = pine
        self.planet = planet
        self.planet_unlock = planet_unlock
        self.send_location = send_location
        self.weapons: WeaponInventory = planet.weapons
        self._items: list[str] = []

        # weapon_vendor()/mod_vendor() are called every tick while their menu
        # is open (not just once on open) so the D-pad toggle below can be
        # polled — this is all state that must survive between those calls.
        self._weapon_vendor_open:      bool = False
        self._mod_vendor_open:         bool = False
        self.show_purchasable_weapons: bool = True

    def controller(self) -> GlobalButtonState | None:
        """Current controller/pause-select button state for whichever planet
        is loaded, or None if no planet is loaded yet, or its
        controller_pause_select_v2 address isn't mapped — GlobalButtonState.read()
        raises rather than returning None for that, so it must be checked first."""
        planet_id = self.planet.planet_id
        if planet_id is None:
            return None
        planet = PLANET_ADDRESSES.get(planet_id)
        if planet is None or planet.controller_pause_select_v2 is None:
            return None
        return GlobalButtonState.read(self.pine, planet_id)

    def _owned_names(self) -> frozenset[str]:
        owned = {name for name, unlocked in self.weapons.weapons.items() if unlocked}
        owned |= {name for name, unlocked in self.weapons.gadgets.items() if unlocked}
        return frozenset(owned)

    def _is_purchased(self, name: str) -> bool:
        loc = WEAPON_INTERNAL_TO_LOCATION.get(name) or GADGET_INTERNAL_TO_LOCATION.get(name)
        return bool(loc and self.weapons.vendor_locations.get(loc, False))

    def _purchasable_names(self) -> list[str]:
        """Weapons/gadgets whose vendor planet is currently AP-accessible and
        haven't been bought yet — the default (left) view's item list."""
        names: list[str] = []
        for name, planet_key in _WEAPON_TO_PLANET_KEY.items():
            if self.planet_unlock.is_vendor_accessible(planet_key) and not self._is_purchased(name):
                names.append(name)
        for name, planet_key in _GADGET_TO_PLANET_KEY.items():
            if self.planet_unlock.is_vendor_accessible(planet_key) and not self._is_purchased(name):
                names.append(name)
        return names

    def _mod_vendor_weapons(self) -> list[str]:
        """Weapons that should appear in the mod vendor's selection list: at
        least one of their mod locations is on an AP-accessible planet."""
        weapons: list[str] = []
        for (weapon, _slot), loc in MOD_INTERNAL_TO_LOCATION.items():
            planet_key = _MOD_LOCATION_TO_PLANET_KEY.get(loc)
            if planet_key and self.planet_unlock.is_vendor_accessible(planet_key) and weapon not in weapons:
                weapons.append(weapon)
        return weapons

    def _set_items(self, names: list[str]) -> None:
        self._items = []
        for name in names:
            self.add_weapon(name)

    def weapon_vendor(self) -> None:
        """Called every tick while the weapons vendor menu is open.

        D_PAD_RIGHT swaps the vendor list to the player's full AP inventory
        (so ammo can be bought for owned-but-not-vendor-unlocked weapons);
        D_PAD_LEFT swaps back to the default purchasable view.

        WeaponInventory.check() diffs against its own raw-memory baseline
        (not the sticky ownership dict), so it correctly reports a purchase
        even for a weapon already owned via an earlier AP item — see
        check()'s docstring in weapons.py.
        """
        if not self._weapon_vendor_open:
            # Just opened — reset to the default purchasable view.
            self._weapon_vendor_open      = True
            self.show_purchasable_weapons = True
            self.weapons.apply_vendor_locations()
            self._set_items(self._purchasable_names())
            self.refresh(MenuStateValue.WEAPONS_VENDOR)

        controller = self.controller()
        if controller is not None:
            if controller.pressed(PauseSelectButtons.D_PAD_RIGHT) and self.show_purchasable_weapons:
                self.weapons.apply_vendor_locations(self._owned_names())
                self.show_purchasable_weapons = False
                self._set_items(list(self._owned_names()))
                self.refresh(MenuStateValue.WEAPONS_VENDOR)

            if controller.pressed(PauseSelectButtons.D_PAD_LEFT) and not self.show_purchasable_weapons:
                self.weapons.apply_vendor_locations()
                self.show_purchasable_weapons = True
                self._set_items(self._purchasable_names())
                self.refresh(MenuStateValue.WEAPONS_VENDOR)

        changed = self.weapons.check()

        if not self.show_purchasable_weapons:
            # Right-hand (AP inventory) view — browsing ammo for already-owned
            # weapons, nothing here can be a fresh purchase.
            return

        newly_purchased = False
        for name in changed["weapons"]:
            loc = WEAPON_INTERNAL_TO_LOCATION.get(name)
            if loc:
                self.weapons.vendor_locations[loc] = True
                self.send_location(loc)
                newly_purchased = True
        for name in changed["gadgets"]:
            loc = GADGET_INTERNAL_TO_LOCATION.get(name)
            if loc:
                self.weapons.vendor_locations[loc] = True
                self.send_location(loc)
                newly_purchased = True
        if newly_purchased:
            # Refresh right away so the just-bought item drops off the
            # purchasable list instead of waiting for the next open.
            self._set_items(self._purchasable_names())
            self.refresh(MenuStateValue.WEAPONS_VENDOR)

    def close(self) -> None:
        """Called once when either vendor menu closes, resetting the
        open-edge/toggle state so the next open starts fresh."""
        self._weapon_vendor_open      = False
        self._mod_vendor_open         = False
        self.show_purchasable_weapons = True

    def mod_vendor(self) -> None:
        """Called every tick while the mod vendor menu is open."""
        if not self._mod_vendor_open:
            # Just opened — populate the vendor's weapon-selection list.
            self._mod_vendor_open = True
            self.weapons.apply_vendor_locations()
            self._set_items(self._mod_vendor_weapons())
            self.refresh(MenuStateValue.MOD_VENDOR)

        changed = self.weapons.check()

        for weapon, slot in changed["mods"]:
            loc = MOD_INTERNAL_TO_LOCATION.get((weapon, slot))
            if loc:
                self.weapons.vendor_locations[loc] = True
                self.send_location(loc)

    def add_weapon(self, weapon: str) -> None:
        """Add a rac5 weapon/gadget (internal name, e.g. "lacerator") to the
        vendor's unlocked-item list."""
        if weapon in WEAPON_VENDOR_IDS and weapon not in self._items:
            self._items.append(weapon)

    def force_refresh(self) -> None:
        """Debug/manual command hook: rebuild the item list for whichever
        vendor is currently open (matching whatever weapon_vendor()/
        mod_vendor() would compute) and rewrite it immediately, without
        waiting for the next natural tick — for verifying the
        WEAPON_VENDOR_ITEMS/WEAPON_VENDOR_SLOTS write directly against a
        memory viewer. No-ops if neither vendor is open."""
        if self._weapon_vendor_open:
            if self.show_purchasable_weapons:
                self._set_items(self._purchasable_names())
            else:
                self._set_items(list(self._owned_names()))
            self.refresh(MenuStateValue.WEAPONS_VENDOR)
        elif self._mod_vendor_open:
            self._set_items(self._mod_vendor_weapons())
            self.refresh(MenuStateValue.MOD_VENDOR)

    def refresh(self, menu_value: MenuStateValue) -> None:
        """Write the current item list into game memory, then poke the menu
        update field (the same address self.planet.menu.set() writes to
        request a menu change) so the game actually redraws the vendor with
        the new list instead of showing whatever it already had on screen."""
        item_ids = [WEAPON_VENDOR_IDS[name] for name in self._items]
        self.pine.write_bytes(WEAPON_VENDOR_SLOTS, len(item_ids).to_bytes(4, "little"))
        for i, item_id in enumerate(item_ids):
            self.pine.write_bytes(WEAPON_VENDOR_ITEMS + i * 4, item_id.to_bytes(4, "little"))
        # Zero every slot past the new count, up to the array's full capacity,
        # so leftover IDs from a previous (longer) write don't linger in the menu.
        for i in range(len(item_ids), MAX_VENDOR_SLOTS):
            self.pine.write_bytes(WEAPON_VENDOR_ITEMS + i * 4, (0).to_bytes(4, "little"))
        self.planet.menu.set(menu_value)

    def __repr__(self) -> str:
        return (
            f"VendorInventory(items={list(self._items)}, "
            f"weapon_open={self._weapon_vendor_open}, mod_open={self._mod_vendor_open}, "
            f"show_purchasable={self.show_purchasable_weapons}, "
            f"planet_id={self.planet.planet_id!r}, controller={self.controller()!r})"
        )
