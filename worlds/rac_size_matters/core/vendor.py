from collections.abc import Callable
from typing import TYPE_CHECKING

from ..constants import Rac5GadgetKeys, Rac5ModVendorLocations
from ..locations import (
    GADGET_INTERNAL_TO_LOCATION,
    MOD_INTERNAL_TO_LOCATION,
    TITAN_INTERNAL_TO_LOCATION,
    WEAPON_INTERNAL_TO_LOCATION,
    WEAPON_LEVEL_LOOKUP,
)
from .address_maps import PLANET_ADDRESSES, WEAPON_VENDOR_ITEMS, WEAPON_VENDOR_SLOTS
from .controller import GlobalButtonState, PauseSelectButtons
from .menu import MenuStateValue
from .weapons import TITAN_ELIGIBLE_WEAPONS, WEAPON_VENDOR_DISPLAY_AMMO

if TYPE_CHECKING:
    from ..pypine import Pine
    from .planets import PlanetInventory, PlanetUnlockState
    from .weapons import WeaponInventory

# The gap between WEAPON_VENDOR_ITEMS and WEAPON_VENDOR_SLOTS (the count) is the array's
# full capacity — slots beyond the written count must be zeroed or stale entries linger.
MAX_VENDOR_SLOTS = (WEAPON_VENDOR_SLOTS - WEAPON_VENDOR_ITEMS) // 4

# Vendor item IDs written to WEAPON_VENDOR_ITEMS: combined weapon+gadget
# array slot index + 2 offset. Confirmed in-game.
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

# Titan purchases reuse the base weapon's own vendor slot/item id — there is no
# separate Titan item id; see _is_titan_pending() and weapon_vendor()'s purchase loop.

# Lookup used everywhere the vendor item list resolves a weapon/gadget name
# to its menu item id.
_ITEM_IDS: dict[str, int] = WEAPON_VENDOR_IDS

# internal weapon/gadget name -> PlanetUnlockState key, for gating purchasability.
# Ryno/mootator/sprout_o_matic/polarizer/shrink_ray aren't sold at any weapons vendor.
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
    # Challenge Mode 1+ only — RYNO has no vendor listing in vanilla.
    "ryno":            "POKITARU",
}

# Weapons requiring Challenge Mode 1+ before their vendor listing appears at
# all, on top of the usual planet-accessibility gate above.
_CHALLENGE_MODE_ONLY_WEAPONS: frozenset[str] = frozenset({"ryno"})

# internal weapon name -> PlanetUnlockState key for its Titan variant vendor
# listing. Mootator has no normal listing, hence its own entry here.
_TITAN_TO_PLANET_KEY: dict[str, str] = {
    **_WEAPON_TO_PLANET_KEY,
    "mootator": "DAYNI_MOON",
}
del _TITAN_TO_PLANET_KEY["ryno"]

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
    # Challenge Mode 1+ only — see _CHALLENGE_MODE_MOD_LOCATIONS below.
    Rac5ModVendorLocations.KALIDON_AGENTS_EXPLOSIVE:       "KALIDON",
    Rac5ModVendorLocations.KALIDON_SCORCHER_SUNFLARE:      "KALIDON",
    Rac5ModVendorLocations.KALIDON_SUCK_CANNON_BOUNCE:     "KALIDON",
    Rac5ModVendorLocations.KALIDON_BEE_HIVE_BOMB:          "KALIDON",
    Rac5ModVendorLocations.CHALLAX_SNIPER_SMART_REFLECTOR: "CHALLAX",
    Rac5ModVendorLocations.CHALLAX_SHOCK_MULTI_LAUNCHER:   "CHALLAX",
    Rac5ModVendorLocations.KALIDON_STATIC_REFLECTION:      "KALIDON",
    Rac5ModVendorLocations.QUODRONA_STATIC_MIRAGE:         "QUODRONA",
    Rac5ModVendorLocations.CHALLAX_LASER_PIERCE:           "CHALLAX",
    Rac5ModVendorLocations.QUODRONA_LASER_RICOCHET:        "QUODRONA",
}

# Mod vendor locations that only exist at Challenge Mode 1+, on top of the
# usual planet-accessibility gate above.
_CHALLENGE_MODE_MOD_LOCATIONS: frozenset[str] = frozenset({
    Rac5ModVendorLocations.KALIDON_AGENTS_EXPLOSIVE,
    Rac5ModVendorLocations.KALIDON_SCORCHER_SUNFLARE,
    Rac5ModVendorLocations.KALIDON_SUCK_CANNON_BOUNCE,
    Rac5ModVendorLocations.KALIDON_BEE_HIVE_BOMB,
    Rac5ModVendorLocations.CHALLAX_SNIPER_SMART_REFLECTOR,
    Rac5ModVendorLocations.CHALLAX_SHOCK_MULTI_LAUNCHER,
    Rac5ModVendorLocations.KALIDON_STATIC_REFLECTION,
    Rac5ModVendorLocations.QUODRONA_STATIC_MIRAGE,
    Rac5ModVendorLocations.CHALLAX_LASER_PIERCE,
    Rac5ModVendorLocations.QUODRONA_LASER_RICOCHET,
})

# Planets whose mod vendor requires extra gadgets beyond planet accessibility;
# mirrors rules/challax.py's _base rule.
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
    """Pine-backed accessor for the vendor item list/size array. add_weapon() tracks
    which names belong in the vendor's item list; refresh() writes that list to memory."""

    def __init__(
        self,
        pine: "Pine",
        planet: "PlanetInventory",
        planet_unlock: "PlanetUnlockState",
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
        # Whether AP has actually granted this item, distinct from "was its vendor
        # location bought" — a purchase only checks the location, not local functionality.
        self._is_weapon_ap_owned = is_weapon_ap_owned or (lambda name: False)
        self._is_gadget_ap_owned = is_gadget_ap_owned or (lambda name: False)
        # Gates the "levels" location-sends below to avoid an unpooled
        # location's no-op send_location() logging a warning every time.
        self._is_weapon_level_checks_enabled = is_weapon_level_checks_enabled or (lambda: False)
        self.weapons: WeaponInventory = planet.weapons
        self._items: list[str] = []

        # Gates RYNO, the Challenge-Mode-only mods, and every Titan variant purchase below.
        self.challenge_mode: int = 0

        # Called every tick while their menu is open so the D-pad toggle can be polled;
        # this is all state that must survive between those calls.
        self._weapon_vendor_open:      bool = False
        self._mod_vendor_open:         bool = False
        self.show_purchasable_weapons: bool = True
        # Weapon levels while the weapons vendor is open — see
        # weapon_vendor()'s open block / close() below.
        self._level_snapshot: dict[str, int] = {}
        # Real ammo for weapons showing fake display ammo; same lifecycle as
        # _level_snapshot. Non-empty exactly when ammo_link_paused should be true.
        self._ammo_snapshot: dict[str, int] = {}

    def controller(self) -> GlobalButtonState | None:
        """Current controller/pause-select button state, or None if no planet is loaded
        or its address isn't mapped (checked first since read() raises otherwise)."""
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
        """Weapons whose level should force to 0 for the vendor's default (left,
        buy-new) view: every purchasable weapon that isn't already Titan-pending,
        since zeroing a Titan-pending one would revert it to the base listing."""
        return frozenset(
            name for name in self._purchasable_names()
            if not self._is_titan_pending(name)
        )

    def _is_purchased(self, name: str) -> bool:
        loc = WEAPON_INTERNAL_TO_LOCATION.get(name) or GADGET_INTERNAL_TO_LOCATION.get(name)
        return bool(loc and self.weapons.vendor_locations.get(loc, False))

    def _is_titan_eligible(self, name: str) -> bool:
        """Whether `name` still has an unbought Titan variant to offer:
        Challenge Mode 1+, one of TITAN_ELIGIBLE_WEAPONS, not yet bought."""
        return (self.challenge_mode >= 1 and name in TITAN_ELIGIBLE_WEAPONS
                and not self.weapons.titan_purchased.get(name, False))

    def _is_titan_pending(self, name: str) -> bool:
        """True once `name`'s vendor slot should show the level-4 floor for its Titan
        purchase; requires the base location to be bought AT THIS VENDOR (not just AP
        ownership), so its own base location can still be sent. Mootator goes by real level."""
        if not self._is_titan_eligible(name):
            return False
        base_loc = WEAPON_INTERNAL_TO_LOCATION.get(name)
        if base_loc is None:
            return self.weapons.get_level(name) >= 3
        return self._is_purchased(name)

    def _apply_titan_pending_levels(self, purchasable: list[str]) -> None:
        """Force the level-4 floor and `unlocked=True` for Titan-pending weapons in
        `purchasable`. Deliberately doesn't touch _level_snapshot — that's the real level
        restore_levels() must show later; this write is a left-view-only display fake."""
        for name in purchasable:
            if self._is_titan_pending(name):
                self.weapons.set_level(name, 3)
                self.weapons.set(name, True)
                self.weapons.weapons[name] = True

    @property
    def ammo_link_paused(self) -> bool:
        """True while the left-view's fake display ammo is showing, so AmmoLink must not
        push or overwrite it with a real value. Mirrors _ammo_snapshot's lifecycle."""
        return bool(self._ammo_snapshot)

    def _apply_display_ammo(self, purchasable: list[str]) -> None:
        """Overwrite ammo for weapons in `purchasable` with the display base/titan count.
        Only snapshots a weapon's real ammo the FIRST time it's faked this visit, or a
        later re-entry would capture the fake value and lose the true ammo for good."""
        weapon_names = frozenset(purchasable) & frozenset(self.weapons._weapon_addrs)
        to_snapshot = weapon_names - self._ammo_snapshot.keys()
        if to_snapshot:
            self._ammo_snapshot.update(self.weapons.snapshot_ammo(to_snapshot))
        for name in weapon_names:
            display = WEAPON_VENDOR_DISPLAY_AMMO.get(name)
            if display is None:
                continue
            value = display.titan if (self._is_titan_pending(name) and display.titan is not None) else display.base
            self.weapons.set_ammo(name, value)

    def _restore_ammo(self) -> None:
        """Write back real ammo from _ammo_snapshot and clear it, the counterpart to
        _apply_display_ammo(), whenever the left-hand view is left."""
        if not self._ammo_snapshot:
            return
        self.weapons.restore_ammo(self._ammo_snapshot)
        self._ammo_snapshot = {}

    def _purchasable_names(self) -> list[str]:
        """Weapons/gadgets shown on the vendor's default (left, buy-new) view. A
        Titan-eligible weapon stays listed (reusing the same slot) until its Titan
        variant is bought; Mootator has no base listing, so it only appears Titan-pending."""
        names: list[str] = []
        for name, planet_key in _WEAPON_TO_PLANET_KEY.items():
            if name in _CHALLENGE_MODE_ONLY_WEAPONS and self.challenge_mode < 1:
                continue
            if not self.planet_unlock.is_vendor_accessible(planet_key):
                continue
            if self._is_titan_eligible(name) or not self._is_purchased(name):
                names.append(name)
        if self._is_titan_eligible("mootator") and self.weapons.get_level("mootator") >= 3:
            # Mootator has no base listing/purchase to gate on, so it waits for its
            # real level to reach the floor organically instead.
            mootator_planet_key = _TITAN_TO_PLANET_KEY["mootator"]
            if self.planet_unlock.is_vendor_accessible(mootator_planet_key):
                names.append("mootator")
        for name, planet_key in _GADGET_TO_PLANET_KEY.items():
            if self.planet_unlock.is_vendor_accessible(planet_key) and not self._is_purchased(name):
                names.append(name)
        return names

    def purchasable_locations(self) -> list[str]:
        """AP location names for every weapon/gadget/Titan variant currently purchasable
        at the vendor's default view, used to hint before the player has to browse."""
        locations: list[str] = []
        for name in self._purchasable_names():
            if self._is_titan_pending(name):
                loc = TITAN_INTERNAL_TO_LOCATION.get(name)
            else:
                loc = WEAPON_INTERNAL_TO_LOCATION.get(name) or GADGET_INTERNAL_TO_LOCATION.get(name)
            if loc:
                locations.append(loc)
        return locations

    def mod_locations(self) -> list[str]:
        """AP location names for every mod slot currently reachable, same hinting
        purpose as purchasable_locations() but for the mod vendor."""
        return [
            loc for (_weapon, _slot), loc in MOD_INTERNAL_TO_LOCATION.items()
            if self._is_mod_location_accessible(loc)
        ]

    def _is_mod_location_accessible(self, loc: str) -> bool:
        """Whether this location's mod vendor is actually reachable — planet
        accessibility alone isn't enough where an extra gadget or Challenge Mode gates it."""
        if loc in _CHALLENGE_MODE_MOD_LOCATIONS and self.challenge_mode < 1:
            return False
        planet_key = _MOD_LOCATION_TO_PLANET_KEY.get(loc)
        if not planet_key or not self.planet_unlock.is_vendor_accessible(planet_key):
            return False
        return all(
            self.weapons.gadgets.get(gadget, False)
            for gadget in _MOD_VENDOR_EXTRA_GADGETS.get(planet_key, ())
        )

    def _mod_vendor_weapons(self) -> list[str]:
        """Weapons that should appear in the mod vendor's selection list: at least one of
        their mod locations is reachable, regardless of ownership (which only gates purchasability)."""
        weapons: list[str] = []
        for (weapon, _slot), loc in MOD_INTERNAL_TO_LOCATION.items():
            if self._is_mod_location_accessible(loc) and weapon not in weapons:
                weapons.append(weapon)
        return weapons

    def _apply_mod_unlock_flags(self) -> None:
        """Write mod_unlock_N — gated purely on reachability, not ownership, since AP's
        accessibility sweep assumes these locations are reachable regardless. Also forces
        the weapon's `unlocked` byte to match; temporary, undone by close()'s revert_unowned()."""
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
        """Called every tick while the weapons vendor menu is open. D_PAD_RIGHT swaps
        to the player's full AP inventory view; D_PAD_LEFT swaps back to the default
        purchasable view. check() diffs against raw memory, so a purchase is
        correctly reported even for a weapon already owned via an earlier AP item."""
        if not self._weapon_vendor_open:
            self._weapon_vendor_open = True
            # Zero level for the visit since displayed price derives from it;
            # Core.tick() skips apply_progressive_leveling() while this menu is open.
            self._level_snapshot = self.weapons.zero_levels_for_vendor(self._weapons_to_zero_for_vendor())
            purchasable = self._purchasable_names()
            self._apply_titan_pending_levels(purchasable)
            if purchasable:
                # Default (left) view.
                self.show_purchasable_weapons = True
                self.weapons.apply_vendor_locations()
                self._apply_display_ammo(purchasable)
                self._set_items(purchasable)
            else:
                # Nothing left to buy — open straight into the owned-inventory view.
                self.show_purchasable_weapons = False
                self.weapons.apply_vendor_locations(self._owned_names())
                self.weapons.restore_levels(self._level_snapshot)
                self._set_items(list(self._owned_names()))
            self.refresh(MenuStateValue.WEAPONS_VENDOR)
            # TEMP DEBUG: vendor-id -> name mapping written for this open.
            self._log(
                "[RAC][vendor-debug] weapon vendor opened, items="
                + ", ".join(f"{name}=0x{_ITEM_IDS[name]:02X}" for name in self._items)
            )

        controller = self.controller()

        changed = self.weapons.check()

        # TEMP DEBUG: log any struct-level change seen while open.
        if changed["weapons"] or changed["gadgets"]:
            self._log(
                f"[RAC][vendor-debug] check() saw changed weapons={changed['weapons']!r} "
                f"gadgets={changed['gadgets']!r} "
                f"(show_purchasable={self.show_purchasable_weapons})"
            )

        # Core never sees this tick's check() while a vendor menu is open, so a
        # level newly reached during a purchase must be sent from here instead.
        # Excludes changed["titans"] when Challenge Mode is active, since that jump
        # is the dedicated Titan-purchase location sent below, not organic play.
        if self._is_weapon_level_checks_enabled():
            titan_names = frozenset(changed["titans"]) if self.challenge_mode >= 1 else frozenset()
            for name, level in changed["levels"]:
                if name in titan_names:
                    continue
                loc = WEAPON_LEVEL_LOOKUP.get((name, level))
                if loc:
                    self.send_location(loc)

        # The re-lock below must run regardless of view, since check() baselines
        # ownership permanently; only "report as a fresh purchase" is view-gated.
        report_as_purchase = self.show_purchasable_weapons

        newly_purchased = False
        for name in changed["weapons"]:
            loc = WEAPON_INTERNAL_TO_LOCATION.get(name)
            self._log(f"[RAC][vendor-debug] weapon {name!r} newly unlocked -> loc={loc!r}")
            if report_as_purchase and loc and not self._is_purchased(name):
                # Base purchase.
                self.weapons.vendor_locations[loc] = True
                self.send_location(loc)
                newly_purchased = True
                if self._is_titan_eligible(name):
                    # Force the level-4 floor and PERMANENT unlock, bypassing the normal
                    # AP-ownership relock — otherwise the base purchase would look undone.
                    # _level_snapshot is left untouched; this 0x03 is a display-only fake.
                    self.weapons.set_level(name, 3)
                    self.weapons.set(name, True)
                    self.weapons.weapons[name] = True
                    continue
            # A vendor purchase only checks the location; re-lock immediately
            # unless AP has already granted this weapon's actual item.
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

        # Titan purchase: the game bumps level 4->5 the moment the player buys the
        # Titan variant. Runs regardless of view, unlike the base purchase above.
        for name in changed["titans"]:
            titan_loc = TITAN_INTERNAL_TO_LOCATION.get(name)
            self._log(f"[RAC][vendor-debug] titan {name!r} purchased -> loc={titan_loc!r}")
            if titan_loc:
                self.weapons.titan_purchased[name] = True
                self.send_location(titan_loc)
                newly_purchased = True
                # Drop any stale snapshot so close()'s restore_levels() doesn't
                # write the pre-Titan value back over the correct post-Titan level.
                self._level_snapshot.pop(name, None)
                # Reset display level to 0; safe since apply_progressive_leveling()
                # floors it back to the real Titan tier once the vendor closes.
                self.weapons.set_level(name, 0)

        # D-Pad view toggle — handled AFTER purchase processing settles this tick,
        # or a same-tick D-Pad press would apply the toggle against stale pre-purchase state.
        if controller is not None:
            if controller.pressed(PauseSelectButtons.D_PAD_RIGHT) and self.show_purchasable_weapons:
                self.weapons.apply_vendor_locations(self._owned_names())
                self.show_purchasable_weapons = False
                # Ammo price/capacity depends on the real level, so restore it here
                # (re-zeroed if flipping back to the left view).
                self.weapons.restore_levels(self._level_snapshot)
                # Same for the real ammo count faked by the left view; re-enables AmmoLink too.
                self._restore_ammo()
                self._set_items(list(self._owned_names()))
                self.refresh(MenuStateValue.WEAPONS_VENDOR)

            # Only allow flipping back to the left view if something is still purchasable.
            still_purchasable = self._purchasable_names()
            if (controller.pressed(PauseSelectButtons.D_PAD_LEFT) and not self.show_purchasable_weapons
                    and still_purchasable):
                self.weapons.apply_vendor_locations()
                self.show_purchasable_weapons = True
                # Re-zero so an owned-but-unpurchased weapon's price isn't skewed by its real level.
                self._level_snapshot = self.weapons.zero_levels_for_vendor(self._weapons_to_zero_for_vendor())
                self._apply_titan_pending_levels(still_purchasable)
                self._apply_display_ammo(still_purchasable)
                self._set_items(still_purchasable)
                self.refresh(MenuStateValue.WEAPONS_VENDOR)

        if not report_as_purchase:
            # Wasn't browsing the buy-new view, so nothing here can be reported as
            # a fresh BASE purchase (a Titan purchase above still registers either way).
            return

        if newly_purchased and self.show_purchasable_weapons:
            # Refresh right away so the just-bought item drops off/re-lists, unless a
            # D-Pad Right toggle above already switched views and wrote the right list.
            purchasable = self._purchasable_names()
            # A weapon fully purchased this tick drops out of `purchasable` for good,
            # but isn't restored to real ammo yet — that happens at the usual exit points.
            dropped_out = self._ammo_snapshot.keys() - set(purchasable)
            for name in dropped_out:
                display = WEAPON_VENDOR_DISPLAY_AMMO.get(name)
                if display is not None:
                    self.weapons.set_ammo(name, display.base)
            if purchasable:
                self._apply_titan_pending_levels(purchasable)
                self._apply_display_ammo(purchasable)
                self._set_items(purchasable)
            else:
                # Last purchasable item gone — drop straight into the owned-inventory view.
                self.show_purchasable_weapons = False
                self.weapons.apply_vendor_locations(self._owned_names())
                self.weapons.restore_levels(self._level_snapshot)
                self._restore_ammo()
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
        self._restore_ammo()
        if was_mod_vendor:
            # Undo _refresh_mod_vendor()'s temporary display grant for anything not
            # genuinely AP-owned, or the player walks away with an ungranted weapon.
            self.weapons.revert_unowned(self._is_weapon_ap_owned)

    def _refresh_mod_vendor(self) -> None:
        """(Re)build the mod vendor's weapon list and unlock flags, shared by the open
        edge, D_PAD_UP refresh, and post-purchase refresh. Passes the entire weapons_sold
        list as allowed_extra since a weapon must show unlocked to render as a selection."""
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

        # Only a mod purchase counts as "purchased" — a weapon transition here is just
        # check() observing _refresh_mod_vendor()'s own force-unlock, so correct the
        # tracking dict inline but leave memory untouched (must stay unlocked to render).
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

        # Same reasoning as weapon_vendor() — Core never sees this tick's check() while
        # this menu is open, so a background level-up must be sent from here too.
        if self._is_weapon_level_checks_enabled():
            for name, level in changed["levels"]:
                loc = WEAPON_LEVEL_LOOKUP.get((name, level))
                if loc:
                    self.send_location(loc)

        if newly_purchased:
            # Refresh right away rather than waiting for the next menu open.
            self._refresh_mod_vendor()

    def add_weapon(self, weapon: str) -> None:
        """Add a rac5 weapon/gadget/Titan-variant pseudo name to the vendor's
        unlocked-item list."""
        if weapon in _ITEM_IDS and weapon not in self._items:
            self._items.append(weapon)

    def force_refresh(self) -> None:
        """Debug/manual command hook: rebuild and rewrite the open vendor's item list
        immediately, for verifying the write directly against a memory viewer."""
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
        """Write the current item list into game memory, then poke the menu update
        field so the game redraws the vendor instead of showing stale contents."""
        item_ids = [_ITEM_IDS[name] for name in self._items]
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
