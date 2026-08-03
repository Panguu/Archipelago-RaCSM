from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from ..constants import Rac5GadgetKeys, Rac5ModVendorLocations
from ..locations import (
    GADGET_INTERNAL_TO_LOCATION,
    MOD_INTERNAL_TO_LOCATION,
    WEAPON_INTERNAL_TO_LOCATION,
    WEAPON_LEVEL_LOOKUP,
)
from .address_maps import PLANET_ADDRESSES, WEAPON_VENDOR_ITEMS, WEAPON_VENDOR_SLOTS
from .controller import GlobalButtonState, PauseSelectButtons
from .menu import MenuStateValue

if TYPE_CHECKING:
    from ..pypsp import Psp
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

# Planets whose mod vendor requires extra gadgets beyond the planet itself
# being AP-accessible — mirrors rules/challax.py's _base rule (Shrink Ray +
# Polarizer physically gate reaching Challax's mod vendor area, same as
# core/vendor.py's own _WEAPON_TO_PLANET_KEY-driven weapon vendor list would
# need if any other planet ever grew the same kind of gate).
_MOD_VENDOR_EXTRA_GADGETS: dict[str, tuple[str, ...]] = {
    "CHALLAX": (Rac5GadgetKeys.SHRINK_RAY, Rac5GadgetKeys.POLARIZER),
}

# WeaponAddresses ownership field ("mod_slot_N") -> the vendor's own
# "purchasable" flag field ("mod_unlock_N") for that same slot.
_SLOT_TO_UNLOCK_ATTR: dict[str, str] = {
    "mod_slot_one":   "mod_unlock_one",
    "mod_slot_two":   "mod_unlock_two",
    "mod_slot_three": "mod_unlock_three",
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
    """Psp-backed accessor for the vendor item list/size array
    (WEAPON_VENDOR_ITEMS/WEAPON_VENDOR_SLOTS).

    weapon_vendor()/mod_vendor() are the hooks fired when their respective
    menu opens — left empty for now, filled in as that logic is rebuilt.
    add_weapon() just tracks which rac5 weapon/gadget names belong in the
    vendor's item list; refresh() is what actually writes that list into
    game memory.
    """

    def __init__(
        self,
        pine: Psp,
        planet: PlanetInventory,
        planet_unlock: PlanetUnlockState,
        send_location: Callable[[str], None],
        log: Callable[[str], None] | None = None,
        is_weapon_ap_owned: Callable[[str], bool] | None = None,
        is_gadget_ap_owned: Callable[[str], bool] | None = None,
        is_weapon_level_checks_enabled: Callable[[], bool] | None = None,
    ) -> None:
        self.pine = pine
        self.planet = planet
        self.planet_unlock = planet_unlock
        self.send_location = send_location
        self._log = log or (lambda msg: None)
        # Whether AP has actually granted this weapon/gadget's item yet
        # (distinct from "was its vendor location bought" — a vendor
        # purchase only checks the location; it must not grant local
        # functionality on its own, since the item at that location may not
        # even be this weapon in a shuffled seed).
        self._is_weapon_ap_owned = is_weapon_ap_owned or (lambda name: False)
        self._is_gadget_ap_owned = is_gadget_ap_owned or (lambda name: False)
        # Gates the "levels" location-sends below — without this, a no-op
        # send_location() for a level whose location isn't in this seed's
        # pool (weapon_level_checks off) still logs a "not in server
        # locations" warning every time (see CommonClient's
        # _append_location_by_name), which fires constantly with the option
        # off since check_weapons() runs regardless of it.
        self._is_weapon_level_checks_enabled = is_weapon_level_checks_enabled or (lambda: False)
        self.weapons: WeaponInventory = planet.weapons
        self._items: list[str] = []

        # weapon_vendor()/mod_vendor() are called every tick while their menu
        # is open (not just once on open) so the D-pad toggle below can be
        # polled — this is all state that must survive between those calls.
        self._weapon_vendor_open:      bool = False
        self._mod_vendor_open:         bool = False
        self.show_purchasable_weapons: bool = True
        # Weapon levels while the weapons vendor is open — see
        # weapon_vendor()'s open block / close() below.
        self._level_snapshot: dict[str, int] = {}

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

    def _weapons_to_zero_for_vendor(self) -> frozenset[str]:
        """Weapons whose level zero_levels_for_vendor() should hide for the
        duration of this vendor visit.

        An AP-owned weapon only gets to show its real level once it's no
        longer purchasable here (i.e. this vendor's own location for it has
        already been bought) — at that point it has nothing left to hide
        behind a fake base price. Still-purchasable weapons must stay zeroed
        regardless of AP ownership: the weapon may already be functionally
        owned (granted from another location in a shuffled seed), but this
        vendor's own copy hasn't actually been bought yet, so its displayed
        price would otherwise be skewed by a level the player hasn't paid
        for at this vendor.
        """
        purchasable = set(self._purchasable_names())
        return frozenset(
            name for name in self.weapons.weapons
            if not (self._is_weapon_ap_owned(name) and name not in purchasable)
        )

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

    def purchasable_locations(self) -> list[str]:
        """AP location names for every weapon/gadget currently purchasable
        at the weapons vendor's default view — used to send hints the
        moment that vendor opens, so a purchasable check is hinted before
        the player has to browse for it."""
        locations: list[str] = []
        for name in self._purchasable_names():
            loc = WEAPON_INTERNAL_TO_LOCATION.get(name) or GADGET_INTERNAL_TO_LOCATION.get(name)
            if loc:
                locations.append(loc)
        return locations

    def mod_locations(self) -> list[str]:
        """AP location names for every mod slot currently reachable at the
        mod vendor — same hinting purpose as purchasable_locations(), for
        the mod vendor instead of the weapons vendor."""
        return [
            loc for (_weapon, _slot), loc in MOD_INTERNAL_TO_LOCATION.items()
            if self._is_mod_location_accessible(loc)
        ]

    def _is_mod_location_accessible(self, loc: str) -> bool:
        """Whether the mod vendor selling this location's planet is
        actually reachable — the planet itself being AP-accessible isn't
        enough where an extra gadget check gates the vendor's specific
        area (Challax's Shrink Ray + Polarizer, mirroring rules/challax.py's
        _base rule; see _MOD_VENDOR_EXTRA_GADGETS)."""
        planet_key = _MOD_LOCATION_TO_PLANET_KEY.get(loc)
        if not planet_key or not self.planet_unlock.is_vendor_accessible(planet_key):
            return False
        return all(
            self.weapons.gadgets.get(gadget, False)
            for gadget in _MOD_VENDOR_EXTRA_GADGETS.get(planet_key, ())
        )

    def _mod_vendor_weapons(self) -> list[str]:
        """Weapons that should appear in the mod vendor's selection list:
        at least one of their mod locations is actually reachable —
        regardless of whether the player owns the weapon yet, the mod
        itself is still browsable/listed. Every weapon returned here gets
        force-unlocked for display (see _refresh_mod_vendor()) since the
        game won't render an unlisted-as-unlocked weapon as a selection at
        all; real ownership only gates whether a slot is actually
        *purchasable* (mod_unlock_N, see _apply_mod_unlock_flags())."""
        weapons: list[str] = []
        for (weapon, _slot), loc in MOD_INTERNAL_TO_LOCATION.items():
            if self._is_mod_location_accessible(loc) and weapon not in weapons:
                weapons.append(weapon)
        return weapons

    def _apply_mod_unlock_flags(self) -> None:
        """Write mod_unlock_N — the mod vendor's own "purchasable" byte for
        that slot, distinct from mod_slot_N (does the player *own* the mod)
        — for every mod slot: 1 once its vendor location is actually
        reachable, 0 otherwise. Gated purely on reachability, matching every
        mod-vendor location's own world rule (see e.g. rules/quodrona.py's
        "purchasable without owning the weapon" comment, and
        rules/challax.py's _base gadget-only gate) — not on whether the
        player already owns that weapon. AP's own accessibility sweep
        assumes these locations are reachable independent of weapon
        ownership, so requiring it here too would leave a location that
        fill/hints treat as always gettable permanently unpurchasable
        in-game for a weapon the player hasn't received or bought yet.

        Making the mod purchasable without also forcing the weapon's own
        `unlocked` byte to match would leave a bad half-state (mod
        purchasable, weapon still reading as locked) — same display-unlock
        `_mod_vendor_weapons()`/apply_vendor_locations() already force for
        the weapon-selection list, done again here in lockstep with the
        per-slot reachability this method already computes. Temporary only:
        close() -> revert_unowned() zeros both the weapon and every mod slot
        back out for anything not truly AP-owned once the vendor closes, so
        nothing here leaks past this session the same way a real weapon-
        vendor purchase never grants local functionality by itself either.

        Covers every slot every call, not just newly-accessible ones, so
        anything that stops qualifying also gets correctly revoked.

        The weapon-level unlock below is "any slot reachable" (same OR
        semantics as _mod_vendor_weapons()), not the current slot's own
        reachable value — a weapon with multiple mod slots split across
        planets (one reachable, one not) must not have the later slot in
        iteration order lock the weapon back down after an earlier slot
        already unlocked it for display/purchase."""
        reachable_weapons = set(self._mod_vendor_weapons())
        for (weapon, slot), loc in MOD_INTERNAL_TO_LOCATION.items():
            reachable = self._is_mod_location_accessible(loc)
            unlock_attr = _SLOT_TO_UNLOCK_ATTR[slot]
            self.weapons.set_mod_unlock(weapon, unlock_attr, reachable)
            self.weapons.set(weapon, weapon in reachable_weapons)

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
            self._weapon_vendor_open = True
            # Zero level for the duration of this vendor visit — its
            # displayed price apparently derives from the level field, so an
            # already-leveled-but-still-purchasable-here weapon would show/
            # charge the wrong price otherwise, AP-owned or not (see
            # _weapons_to_zero_for_vendor()). Restored in close() (or, for
            # the purchasable view, re-derived on every left/right toggle
            # below). Core.tick() skips apply_progressive_leveling() while
            # this menu is open so it can't fight this zero-out back to the
            # real level mid-tick.
            self._level_snapshot = self.weapons.zero_levels_for_vendor(self._weapons_to_zero_for_vendor())
            purchasable = self._purchasable_names()
            if purchasable:
                # Default (left) view.
                self.show_purchasable_weapons = True
                self.weapons.apply_vendor_locations()
                self._set_items(purchasable)
            else:
                # Nothing left to buy — everything's already been
                # purchased, so open straight into the owned-inventory
                # (ammo) view instead of showing an empty left list.
                self.show_purchasable_weapons = False
                self.weapons.apply_vendor_locations(self._owned_names())
                self.weapons.restore_levels(self._level_snapshot)
                self._set_items(list(self._owned_names()))
            self.refresh(MenuStateValue.WEAPONS_VENDOR)
            # TEMP DEBUG: dump the vendor-id -> name mapping actually written
            # to game memory for this open, so a purchase can be cross-checked
            # against what slot/id the player actually clicked.
            self._log(
                "[RAC][vendor-debug] weapon vendor opened, items="
                + ", ".join(f"{name}=0x{WEAPON_VENDOR_IDS[name]:02X}" for name in self._items)
            )

        controller = self.controller()
        if controller is not None:
            if controller.pressed(PauseSelectButtons.D_PAD_RIGHT) and self.show_purchasable_weapons:
                self.weapons.apply_vendor_locations(self._owned_names())
                self.show_purchasable_weapons = False
                # Right-hand view browses the player's own owned weapons
                # (to buy ammo for them) — unlike the left view, ammo
                # price/capacity here genuinely depends on the weapon's
                # real level, so restore it for the duration of this view
                # instead of leaving it zeroed. Re-zeroed below the moment
                # the player flips back to the left view.
                self.weapons.restore_levels(self._level_snapshot)
                self._set_items(list(self._owned_names()))
                self.refresh(MenuStateValue.WEAPONS_VENDOR)

            # Only allow flipping back to the left (buy-new) view if there's
            # actually something purchasable to show there — with nothing
            # left to buy, the left/right toggle stops entirely and the
            # vendor stays in the owned-inventory (ammo) view for the rest
            # of this visit, same as it opened into.
            if (controller.pressed(PauseSelectButtons.D_PAD_LEFT) and not self.show_purchasable_weapons
                    and self._purchasable_names()):
                self.weapons.apply_vendor_locations()
                self.show_purchasable_weapons = True
                # Back to the left (buy-new) view — re-zero so an owned-
                # but-not-vendor-purchased weapon's displayed price isn't
                # skewed by its real level, same reasoning as the initial
                # zero on open. Re-snapshots from the just-restored real
                # levels above, so close() still restores the true value.
                self._level_snapshot = self.weapons.zero_levels_for_vendor(self._weapons_to_zero_for_vendor())
                self._set_items(self._purchasable_names())
                self.refresh(MenuStateValue.WEAPONS_VENDOR)

        changed = self.weapons.check()

        # TEMP DEBUG: log *any* struct-level change seen while this menu is
        # open, regardless of which view is active, so a purchase that
        # doesn't land on the expected internal weapon name still shows up.
        if changed["weapons"] or changed["gadgets"]:
            self._log(
                f"[RAC][vendor-debug] check() saw changed weapons={changed['weapons']!r} "
                f"gadgets={changed['gadgets']!r} "
                f"(show_purchasable={self.show_purchasable_weapons})"
            )

        # Weapon Level Checks — Core._check_vendor_purchases() never sees
        # this tick's check() result at all while either vendor menu is
        # open (it returns immediately once the vendor is active, since
        # this method owns weapons.check() while open), so a level newly
        # reached during a purchase (most commonly: buying a weapon at
        # level 0 for the first time) has to be sent from here instead —
        # in both views, since apply_progressive_leveling() runs from
        # Core.tick() independently of which view this menu is showing.
        # Gated on the option directly, same reasoning as Core's own
        # _check_vendor_purchases() — an unpooled location's no-op
        # send_location() still logs a warning every time otherwise.
        if self._is_weapon_level_checks_enabled():
            for name, level in changed["levels"]:
                loc = WEAPON_LEVEL_LOOKUP.get((name, level))
                if loc:
                    self.send_location(loc)

        # The re-lock below must run every tick regardless of which view is
        # active — check() above always runs regardless of view, and it
        # unconditionally baselines self.weapons/gadgets[name] = True the
        # instant it sees an unlocked bit in memory (dict entries never
        # regress on their own). An early return here for the right-hand
        # (AP-inventory/ammo) view used to skip this correction entirely: if
        # the game's own vendor UI ever re-asserts an unlocked bit while
        # browsing that view (e.g. still rendering the item you just bought
        # as "owned" for its own display purposes) with nothing to correct
        # it, that weapon/gadget stays permanently (and wrongly) marked
        # AP-owned even after leaving the vendor. Only the "is this a fresh
        # purchase to report as a location check" half is view-gated below —
        # nothing new is purchasable to report from the right-hand view, but
        # the correction itself must not depend on that.
        report_as_purchase = self.show_purchasable_weapons

        newly_purchased = False
        for name in changed["weapons"]:
            loc = WEAPON_INTERNAL_TO_LOCATION.get(name)
            self._log(f"[RAC][vendor-debug] weapon {name!r} newly unlocked -> loc={loc!r}")
            if report_as_purchase and loc:
                self.weapons.vendor_locations[loc] = True
                self.send_location(loc)
                newly_purchased = True
            # A vendor purchase only checks the location — it must not grant
            # local functionality by itself. Re-lock immediately unless AP
            # has already granted this weapon's actual item (e.g. it was
            # also a starting weapon, or arrived from another check).
            if not self._is_weapon_ap_owned(name):
                self.weapons.set(name, False)
                self.weapons.weapons[name] = False
        for name in changed["gadgets"]:
            loc = GADGET_INTERNAL_TO_LOCATION.get(name)
            self._log(f"[RAC][vendor-debug] gadget {name!r} newly unlocked -> loc={loc!r}")
            if report_as_purchase and loc:
                self.weapons.vendor_locations[loc] = True
                self.send_location(loc)
                newly_purchased = True
            if not self._is_gadget_ap_owned(name):
                self.weapons.set(name, False)
                self.weapons.gadgets[name] = False

        if not report_as_purchase:
            # Right-hand (AP inventory) view — nothing here can be reported
            # as a fresh purchase, and the post-purchase refresh below only
            # applies to the left (buy-new) view's own item list.
            return
        if newly_purchased:
            # Refresh right away so the just-bought item drops off the
            # purchasable list instead of waiting for the next open.
            purchasable = self._purchasable_names()
            if purchasable:
                self._set_items(purchasable)
            else:
                # That was the last purchasable item — nothing left to show
                # on the left, so drop straight into the owned-inventory
                # view instead of refreshing onto an empty list.
                self.show_purchasable_weapons = False
                self.weapons.apply_vendor_locations(self._owned_names())
                self.weapons.restore_levels(self._level_snapshot)
                self._set_items(list(self._owned_names()))
            self.refresh(MenuStateValue.WEAPONS_VENDOR)
            self._log(
                "[RAC][vendor-debug] post-purchase purchasable list="
                + ", ".join(self._items)
            )

    def close(self) -> None:
        """Called once when either vendor menu closes, resetting the
        open-edge/toggle state so the next open starts fresh."""
        was_mod_vendor = self._mod_vendor_open
        self._weapon_vendor_open      = False
        self._mod_vendor_open         = False
        self.show_purchasable_weapons = True
        if self._level_snapshot:
            self.weapons.restore_levels(self._level_snapshot)
            self._level_snapshot = {}
        if was_mod_vendor:
            # Undo _refresh_mod_vendor()'s temporary "give player the
            # weapon" display grant for anything not genuinely AP-owned —
            # it only exists so the weapon renders as a mod-vendor
            # selection while browsing; leaving it in place after closing
            # would mean walking away with a functional weapon (and its
            # mods) AP never actually granted.
            self.weapons.revert_unowned(self._is_weapon_ap_owned)

    def _refresh_mod_vendor(self) -> None:
        """(Re)build the mod vendor's weapon list and unlock flags. Shared by
        the open edge, the manual D_PAD_UP refresh, and the post-purchase
        refresh below — all three need the exact same sequence.

        apply_vendor_locations() zeroes every weapon's display bit then
        restores only vendor-purchased/allowed_extra ones — passing the
        *entire* weapons_sold list as allowed_extra here (not just the
        AP-owned subset) is deliberate: a weapon has to show as unlocked or
        the game won't render it as a mod-vendor selection at all, and
        that's true regardless of whether the player actually owns it yet.
        This only touches display memory, never weapons.weapons directly —
        but check() in mod_vendor() below will still see this unlock and
        baseline weapons.weapons[name] = True the instant it does (dict
        entries never regress on their own), so mod_vendor() corrects that
        dict back inline every tick for anything not truly AP-owned. That
        correction — not the vendor-close revert, and not apply_inventory()'s
        own re-apply, which is purely additive and can never un-set an
        already-True dict entry — is what actually keeps this from leaking
        past the current vendor visit if the session ends any way that
        doesn't cleanly trip close()/revert_unowned().
        """
        weapons_sold = self._mod_vendor_weapons()
        self.weapons.apply_vendor_locations(frozenset(weapons_sold))
        self._apply_mod_unlock_flags()
        self._set_items(weapons_sold)
        self.refresh(MenuStateValue.MOD_VENDOR)

    def mod_vendor(self) -> None:
        """Called every tick while the mod vendor menu is open."""
        if not self._mod_vendor_open:
            self._mod_vendor_open = True
            self._refresh_mod_vendor()

        controller = self.controller()
        if controller is not None and controller.pressed(PauseSelectButtons.D_PAD_UP):
            self._refresh_mod_vendor()

        changed = self.weapons.check()

        # Only a mod purchase counts as "purchased" here — changed["weapons"]
        # is never treated or reported as one: any weapon transition this
        # tick is just check() observing _refresh_mod_vendor()'s own
        # force-unlock writes above, never a real purchase (this vendor
        # doesn't sell whole weapons). But check() itself unconditionally
        # baselines self.weapons[name] = True the instant it sees that
        # display-only unlock in memory (dict entries never regress on their
        # own) — relying solely on close()'s revert_unowned() to undo that
        # later is a single point of failure if the session ever ends
        # without cleanly tripping close(). Correct the dict back inline
        # instead — memory must NOT be touched here (unlike weapon_vendor()'s
        # equivalent correction): the weapon has to stay unlocked in memory
        # for the whole visit or the game won't render it as a mod-vendor
        # selection at all; only the ownership bookkeeping needs fixing.
        for name in changed["weapons"]:
            if not self._is_weapon_ap_owned(name):
                self.weapons.weapons[name] = False

        newly_purchased = False
        for weapon, slot in changed["mods"]:
            loc = MOD_INTERNAL_TO_LOCATION.get((weapon, slot))
            if loc:
                self.weapons.vendor_locations[loc] = True
                self.send_location(loc)
                newly_purchased = True

        # Same reasoning as weapon_vendor() — Core never sees this tick's
        # check() while this menu is open, so a level reached in the
        # background (e.g. automatic mode catching up to a Progressive item
        # that arrived while browsing) must be sent from here too. Gated on
        # the option same as weapon_vendor()'s equivalent loop.
        if self._is_weapon_level_checks_enabled():
            for name, level in changed["levels"]:
                loc = WEAPON_LEVEL_LOOKUP.get((name, level))
                if loc:
                    self.send_location(loc)

        if newly_purchased:
            # Refresh right away, same as weapon_vendor() does after a
            # purchase, rather than waiting for the next menu open.
            self._refresh_mod_vendor()

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
