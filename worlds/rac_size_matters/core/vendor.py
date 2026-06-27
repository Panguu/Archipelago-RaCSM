from __future__ import annotations

import time
from enum import IntEnum
from typing import TYPE_CHECKING

from ..interface_orchestrator.memory.accessor import MemoryAccessor
from ..interface_orchestrator.state.base_state import BaseState
from ..interface_orchestrator.storage.local import LocalStorage
from ..interface_orchestrator.structs.address_map import AddressMap
from ..items import GADGET_DISPLAY_TO_INTERNAL, WEAPON_DISPLAY_TO_INTERNAL
from .address_maps import WEAPON_VENDOR_ITEMS, WEAPON_VENDOR_SLOTS
from .weapons import GADGET_ORDER, WEAPON_ORDER

# WEAPON_VENDOR_ITEMS is a flat array immediately followed in memory by
# WEAPON_VENDOR_SLOTS (the count). The gap between them is the array's full
# capacity — slots beyond the written count must be zeroed too, otherwise
# stale entries from a previous, longer write (e.g. the inventory view) keep
# showing up in the vendor menu instead of disappearing.
MAX_VENDOR_SLOTS = (WEAPON_VENDOR_SLOTS - WEAPON_VENDOR_ITEMS) // 4

if TYPE_CHECKING:
    from .planets import PlanetUnlockState
    from .weapons import WeaponState


class MenuStateValue(IntEnum):
    CLOSED         = 0x00
    PAUSE_MENU     = 0x03
    WEAPONS_VENDOR = 0x09
    MOD_VENDOR     = 0x0E
    PLANET_MENU    = 0x10


# Vendor state (runtime BaseState)
#
# Split into two independent states rather than one generic vendor_type-
# branching class: the weapons vendor owns the vendor list/size array
# (WEAPON_VENDOR_ITEMS/WEAPON_VENDOR_SLOTS, via VendorUnlockState.apply), the
# mod vendor only needs the mod_unlock_N "purchasable" bytes on the weapon
# structs themselves kept correct (handled by the existing inventory-sync
# logic) — there's no separate list/size array for mods. Keeping them as
# separate classes makes it obvious which one is responsible for what when
# debugging.

class WeaponVendorState(BaseState):
    """Weapons vendor menu (sells weapons/gadgets)."""

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self.active = False
        # True while D_PAD_RIGHT has swapped the vendor list to show the
        # player's full AP inventory (for ammo purchase) instead of the
        # default vendor-unlock ("left view") view.
        self.showing_inventory = False
        # Monotonic deadline until which deactivate() should NOT reset
        # showing_inventory. The toggle's own menu.set_menu() refresh can make
        # the game briefly cycle the menu closed->open, which would otherwise
        # look like a real exit and wrongly reset showing_inventory mid-toggle.
        # Set a short window (see game_orchestrator's toggle) rather than a
        # plain bool that depends on something else clearing it — relying on
        # on_weapon_vendor_open() re-firing to clear a sticky flag is fragile:
        # if that speculative re-trigger never happens, the flag gets stuck
        # forever, the next *real* close silently skips its reset, and every
        # later open re-asserts the inventory view without ever calling
        # _wire_vendor_purchase_callbacks() again — permanently breaking
        # vendor-purchase location tracking for the rest of the session. A
        # deadline always expires on its own, even if nothing clears it.
        self.refresh_deadline = 0.0

    def activate(self) -> None:
        self.active = True

    def deactivate(self) -> None:
        self.active = False
        if time.monotonic() >= self.refresh_deadline:
            # A real exit (not a refresh-induced blip) — always default back
            # to the left/purchasable view for the next open.
            self.showing_inventory = False

    def on_menu_open(self) -> None:
        pass

    def on_menu_close(self) -> None:
        pass

    def __repr__(self) -> str:
        return f"WeaponVendorState(active={self.active}, showing_inventory={self.showing_inventory})"


class ModVendorState(BaseState):
    """Weapon mod vendor menu (sells mod slots)."""

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self.active = False

    def activate(self) -> None:
        self.active = True

    def deactivate(self) -> None:
        self.active = False

    def on_menu_open(self) -> None:
        pass

    def on_menu_close(self) -> None:
        pass

    def __repr__(self) -> str:
        return f"ModVendorState(active={self.active})"


# Vendor unlock state

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


_DISPLAY_TO_PLANET_KEY: dict[str, str] = {
    "Pokitaru":      "POKITARU",
    "Ryllus":        "RYLLUS",
    "Kalidon":       "KALIDON",
    "Metalis":       "METALIS",
    "Dreamtime":     "DREAMTIME",
    "Outpost Omega": "OUTPOST_OMEGA",
    "Challax":       "CHALLAX",
    "Dayni Moon":    "DAYNI_MOON",
    "Inside Clank":  "INSIDE_CLANK",
    "Quodrona":      "QUODRONA",
}


def is_mod_region_accessible(planet_unlock: PlanetUnlockState, region: str) -> bool:
    """True if ``region`` (a display name like "Kalidon", as used in
    MOD_UNLOCK_PLANET) has an AP-accessible vendor right now."""
    planet_key = _DISPLAY_TO_PLANET_KEY.get(region)
    return bool(planet_key) and planet_unlock.is_vendor_accessible(planet_key)

# internal weapon/gadget name → PlanetUnlockState key
_WEAPON_TO_PLANET_KEY: dict[str, str] = {
    WEAPON_DISPLAY_TO_INTERNAL["Lacerator"]:      "POKITARU",
    WEAPON_DISPLAY_TO_INTERNAL["Acid Bomb Glove"]: "POKITARU",
    WEAPON_DISPLAY_TO_INTERNAL["Concussion Gun"]:  "POKITARU",
    WEAPON_DISPLAY_TO_INTERNAL["Agents of Doom"]:  "RYLLUS",
    WEAPON_DISPLAY_TO_INTERNAL["Scorcher"]:        "KALIDON",
    WEAPON_DISPLAY_TO_INTERNAL["Suck Cannon"]:     "DREAMTIME",
    WEAPON_DISPLAY_TO_INTERNAL["Bee Mine Glove"]:  "OUTPOST_OMEGA",
    WEAPON_DISPLAY_TO_INTERNAL["Sniper Mine"]:     "CHALLAX",
    WEAPON_DISPLAY_TO_INTERNAL["Shock Rocket"]:    "DAYNI_MOON",
    WEAPON_DISPLAY_TO_INTERNAL["Static Barrier"]:  "INSIDE_CLANK",
    WEAPON_DISPLAY_TO_INTERNAL["Laser Tracer"]:    "QUODRONA",
}

_GADGET_TO_PLANET_KEY: dict[str, str] = {
    GADGET_DISPLAY_TO_INTERNAL["Hypershot"]:    "POKITARU",
    GADGET_DISPLAY_TO_INTERNAL["PDA"]:          "CHALLAX",
    GADGET_DISPLAY_TO_INTERNAL["Map-O-Matic"]:  "DAYNI_MOON",
    GADGET_DISPLAY_TO_INTERNAL["Bolt Grabber"]: "CHALLAX",
    GADGET_DISPLAY_TO_INTERNAL["Box Breaker"]:  "OUTPOST_OMEGA",
}

# Ordered display lists (None gaps stripped) for deterministic slot order.
_WEAPON_DISPLAY_ORDER: list[str] = [n for n in WEAPON_ORDER if n is not None]
_GADGET_DISPLAY_ORDER: list[str] = [n for n in GADGET_ORDER if n is not None]


def _purchased_names(ws: WeaponState) -> frozenset[str]:
    """Return internal names of weapons/gadgets purchased from the vendor."""
    from .weapons import VENDOR_GADGET_LOC, VENDOR_WEAPON_LOC
    result: set[str] = set()
    for loc_name, bought in ws.vendor_locations.items():
        if not bought:
            continue
        if loc_name in VENDOR_WEAPON_LOC:
            result.add(VENDOR_WEAPON_LOC[loc_name])
        elif loc_name in VENDOR_GADGET_LOC:
            result.add(VENDOR_GADGET_LOC[loc_name])
    return frozenset(result)


class VendorUnlockState:

    def __init__(self, weapon_state: WeaponState, planet_unlock: PlanetUnlockState) -> None:
        self._ws = weapon_state
        self._pu = planet_unlock


    def unlock_items(self) -> list[int]:
        """Vendor item IDs for the default (purchasable-only) vendor view.

        Only currently-purchasable slots: planet accessible AND location not
        yet checked. No ammo-refill slots here regardless of ownership — an
        owned-but-already-purchased (or owned-but-not-vendor-gated, e.g.
        Ryno) weapon shows ammo only via the D_PAD_RIGHT inventory view.
        """
        pu        = self._pu
        purchased = _purchased_names(self._ws)
        seen: set[int] = set()
        items: list[int] = []

        def _add(name: str) -> None:
            vid = WEAPON_VENDOR_IDS.get(name)
            if vid is not None and vid not in seen:
                seen.add(vid)
                items.append(vid)

        for name, planet_key in _WEAPON_TO_PLANET_KEY.items():
            if pu.is_vendor_accessible(planet_key) and name not in purchased:
                _add(name)
        for name, planet_key in _GADGET_TO_PLANET_KEY.items():
            if pu.is_vendor_accessible(planet_key) and name not in purchased:
                _add(name)

        return items

    def owned_names(self) -> frozenset[str]:
        """Internal names of every weapon/gadget currently owned in the AP
        inventory, regardless of vendor-unlock state. Passed to
        WeaponState.apply_vendor_locations() while the inventory view is
        showing, so the in-game `unlocked` bit matches what's listed —
        otherwise a listed-but-not-actually-unlocked slot can't sell ammo."""
        ws = self._ws
        owned: set[str] = set()
        for name in _WEAPON_DISPLAY_ORDER:
            if ws.weapons.get(name, False):
                owned.add(name)
        for name in _GADGET_DISPLAY_ORDER:
            if ws.gadgets.get(name, False):
                owned.add(name)
        return frozenset(owned)

    def inventory_items(self) -> list[int]:
        """Vendor item IDs for every weapon/gadget the player currently owns in
        their AP inventory, regardless of vendor-unlock state — lets the
        player buy ammo for anything they own (e.g. a Ryno picked up as an AP
        item on a planet whose vendor hasn't unlocked it yet)."""
        owned = self.owned_names()
        seen: set[int] = set()
        items: list[int] = []

        def _add(name: str) -> None:
            vid = WEAPON_VENDOR_IDS.get(name)
            if vid is not None and vid not in seen:
                seen.add(vid)
                items.append(vid)

        for name in _WEAPON_DISPLAY_ORDER + _GADGET_DISPLAY_ORDER:
            if name in owned:
                _add(name)

        return items

    def _write_items(self, accessor: MemoryAccessor, items: list[int]) -> None:
        accessor.write_raw(WEAPON_VENDOR_SLOTS, len(items).to_bytes(4, "little"))
        for i, item_id in enumerate(items):
            accessor.write_raw(WEAPON_VENDOR_ITEMS + i * 4, item_id.to_bytes(4, "little"))
        # Zero every slot past the new count, up to the array's full capacity,
        # so leftover IDs from a previous (longer) write don't linger in the menu.
        for i in range(len(items), MAX_VENDOR_SLOTS):
            accessor.write_raw(WEAPON_VENDOR_ITEMS + i * 4, (0).to_bytes(4, "little"))

    def apply(self, accessor: MemoryAccessor) -> None:
        self._write_items(accessor, self.unlock_items())

    def apply_inventory(self, accessor: MemoryAccessor) -> None:
        self._write_items(accessor, self.inventory_items())

    def apply_mod_vendor_weapons(self, accessor: MemoryAccessor) -> None:
        """Write the vendor list/size array with the weapons that have a
        purchasable mod here — the mod vendor's weapon-selection list reads
        from the same WEAPON_VENDOR_ITEMS/SLOTS array the weapons vendor
        does, it just isn't populated by anything when only on_mod_vendor_open's
        struct writes run."""
        names = self.mod_vendor_unlock_weapons()
        seen: set[int] = set()
        items: list[int] = []
        for name in _WEAPON_DISPLAY_ORDER:
            if name not in names:
                continue
            vid = WEAPON_VENDOR_IDS.get(name)
            if vid is not None and vid not in seen:
                seen.add(vid)
                items.append(vid)
        self._write_items(accessor, items)

    def mod_vendor_unlock_weapons(self) -> frozenset[str]:
        """Weapons that should show `unlocked` while the mod vendor is open.

        A weapon's mod slot won't render at all if the weapon itself shows
        as locked, so this can't be gated on having bought that weapon from
        its own weapons vendor (mods are frequently sold on a different
        planet than the weapon itself) — just whether one of its mod
        locations is currently purchasable from this vendor.
        """
        from ..locations import MOD_INTERNAL_TO_LOCATION
        pu = self._pu
        allowed: set[str] = set()
        for (weapon, _slot), loc in MOD_INTERNAL_TO_LOCATION.items():
            planet_display = loc.split(":")[0].strip()
            planet_key      = _DISPLAY_TO_PLANET_KEY.get(planet_display)
            if planet_key and pu.is_vendor_accessible(planet_key):
                allowed.add(weapon)
        return frozenset(allowed)

    def purchasable_loc_names(self, vendor_type: MenuStateValue | None = None) -> list[str]:
        """Return AP location names for items currently purchasable from a vendor.

        Includes weapons and gadgets whose planet vendor is accessible and not yet
        purchased, plus weapon mods whose vendor planet is accessible and whose
        parent weapon is owned by the player.

        ``vendor_type`` narrows the result to match what that specific vendor
        menu actually sells: WEAPONS_VENDOR -> weapons/gadgets only, MOD_VENDOR ->
        mods only. Pass None (default) to return everything, regardless of vendor.
        """
        from ..locations import (
            GADGET_INTERNAL_TO_LOCATION,
            MOD_INTERNAL_TO_LOCATION,
            WEAPON_INTERNAL_TO_LOCATION,
        )
        ws        = self._ws
        pu        = self._pu
        purchased = _purchased_names(ws)
        result:   list[str] = []

        if vendor_type in (None, MenuStateValue.WEAPONS_VENDOR):
            for internal, planet_key in _WEAPON_TO_PLANET_KEY.items():
                if pu.is_vendor_accessible(planet_key) and internal not in purchased:
                    loc = WEAPON_INTERNAL_TO_LOCATION.get(internal)
                    if loc:
                        result.append(loc)

            for internal, planet_key in _GADGET_TO_PLANET_KEY.items():
                if pu.is_vendor_accessible(planet_key) and internal not in purchased:
                    loc = GADGET_INTERNAL_TO_LOCATION.get(internal)
                    if loc:
                        result.append(loc)

        if vendor_type in (None, MenuStateValue.MOD_VENDOR):
            for (weapon, _), loc in MOD_INTERNAL_TO_LOCATION.items():
                planet_display = loc.split(":")[0].strip()
                planet_key     = _DISPLAY_TO_PLANET_KEY.get(planet_display)
                if planet_key and pu.is_vendor_accessible(planet_key) and ws.weapons.get(weapon):
                    result.append(loc)

        return result

    def allowed_weapons_for_inventory(self) -> frozenset[str]:
        ws        = self._ws
        pu        = self._pu
        purchased = _purchased_names(ws)
        allowed: set[str] = set()

        for name in _WEAPON_DISPLAY_ORDER:
            if not ws.weapons.get(name, False):
                continue
            planet_key = _WEAPON_TO_PLANET_KEY.get(name)
            if planet_key is None or not pu.is_vendor_accessible(planet_key) or name in purchased:
                allowed.add(name)

        for name in _GADGET_DISPLAY_ORDER:
            if not ws.gadgets.get(name, False):
                continue
            planet_key = _GADGET_TO_PLANET_KEY.get(name)
            if planet_key is None or not pu.is_vendor_accessible(planet_key) or name in purchased:
                allowed.add(name)

        return frozenset(allowed)

    def debug_lines(self) -> list[str]:
        ws        = self._ws
        pu        = self._pu
        purchased = _purchased_names(ws)
        lines: list[str] = ["[RAC] Vendor unlock state:"]

        accessible = [k for k in _DISPLAY_TO_PLANET_KEY.values() if pu.is_vendor_accessible(k)]
        lines.append(f"  Accessible planets : {', '.join(accessible) or 'none'}")
        lines.append(f"  Purchased          : {', '.join(sorted(purchased)) or 'none'}")

        for display_planet, planet_key in _DISPLAY_TO_PLANET_KEY.items():
            if not pu.is_vendor_accessible(planet_key):
                continue
            w_here = [n for n, pk in _WEAPON_TO_PLANET_KEY.items() if pk == planet_key and n not in purchased]
            g_here = [n for n, pk in _GADGET_TO_PLANET_KEY.items() if pk == planet_key and n not in purchased]
            available = w_here + g_here
            if available:
                lines.append(f"  {display_planet:<14} → available: {', '.join(available)}")

        # Weapons owned but planet accessible and not purchased — removed from
        # inventory so vendor shows them as purchasable rather than ammo-refill.
        pending_purchase = [
            n for n in _WEAPON_DISPLAY_ORDER + _GADGET_DISPLAY_ORDER
            if (ws.weapons.get(n) or ws.gadgets.get(n))
            and (n in _WEAPON_TO_PLANET_KEY or n in _GADGET_TO_PLANET_KEY)
            and pu.is_vendor_accessible((_WEAPON_TO_PLANET_KEY | _GADGET_TO_PLANET_KEY).get(n, ""))
            and n not in purchased
        ]
        if pending_purchase:
            lines.append(f"  Owned → purchasable slot (removed from inv): {', '.join(pending_purchase)}")

        return lines

    def __repr__(self) -> str:
        pu = self._pu
        purchased = len(_purchased_names(self._ws))
        accessible = sum(1 for pk in _DISPLAY_TO_PLANET_KEY.values() if pu.is_vendor_accessible(pk))
        return f"VendorUnlockState(accessible_planets={accessible}, purchased={purchased})"
