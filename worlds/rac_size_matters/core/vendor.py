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
from .weapons import TITAN_ELIGIBLE_WEAPONS

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
# Confirmed in-game.
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

# Challenge Mode 1+ Titan variant purchases reuse the base weapon's own
# vendor slot/item id (WEAPON_VENDOR_IDS) and its owned/unlocked address —
# there is no separate Titan vendor item id. Buying a weapon a second time,
# once it's already sitting at the level-4 floor set below, is what the game
# treats as the Titan purchase; see _is_titan_pending() and
# weapon_vendor()'s purchase-detection loop.

# Lookup used everywhere the vendor item list resolves a weapon/gadget name
# to its menu item id.
_ITEM_IDS: dict[str, int] = WEAPON_VENDOR_IDS

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
    # Challenge Mode 1+ only — RYNO has no vendor listing in vanilla.
    "ryno":            "POKITARU",
}

# Weapons requiring Challenge Mode 1+ before their vendor listing appears at
# all, on top of the usual planet-accessibility gate above.
_CHALLENGE_MODE_ONLY_WEAPONS: frozenset[str] = frozenset({"ryno"})

# internal weapon name -> PlanetUnlockState key for its Titan variant vendor
# listing (Challenge Mode 1+, every weapon except RYNO). Mootator has no
# normal-weapon vendor listing at all, hence its own entry here rather than
# reusing _WEAPON_TO_PLANET_KEY.
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

# Planets whose mod vendor requires extra gadgets beyond the planet itself
# being AP-accessible — mirrors rules/challax.py's _base rule (Shrink Ray +
# Polarizer physically gate reaching Challax's mod vendor area).
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
        # Whether AP has actually granted this weapon/gadget's item yet —
        # distinct from "was its vendor location bought", since a vendor
        # purchase only checks the location and must not grant local
        # functionality on its own (the item there may differ in a shuffled seed).
        self._is_weapon_ap_owned = is_weapon_ap_owned or (lambda name: False)
        self._is_gadget_ap_owned = is_gadget_ap_owned or (lambda name: False)
        # Gates the "levels" location-sends below to avoid an unpooled
        # location's no-op send_location() logging a warning every time.
        self._is_weapon_level_checks_enabled = is_weapon_level_checks_enabled or (lambda: False)
        self.weapons: WeaponInventory = planet.weapons
        self._items: list[str] = []

        # Challenge Mode option (options.py's ChallengeMode Range 0-2): 0 =
        # off. Set directly by the client from slot_data. Gates RYNO, the
        # Challenge-Mode-only mods, and every Titan variant purchase below.
        self.challenge_mode: int = 0

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
        is loaded, or None if no planet is loaded or its
        controller_pause_select_v2 address isn't mapped (checked first since
        GlobalButtonState.read() raises rather than returning None)."""
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
        """Weapons whose level zero_levels_for_vendor() should force to 0
        for the vendor's default (left, buy-new) view.

        The vendor's own displayed level is binary — every weapon currently
        shown for purchase there is at either 0 (still needs its base
        purchase) or 0x03 (base purchase done, re-listed for the Titan
        purchase — see _is_titan_pending()), nothing else. So this is
        simply every currently-purchasable weapon that ISN'T already
        Titan-pending; a Titan-pending one must never be zeroed back, or it
        would silently turn back into the base listing on every vendor
        open/toggle.
        """
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
        """True once `name`'s vendor slot should show at the level-4 floor
        (0x03) for its Titan purchase, as opposed to the plain base-weapon
        purchase (level 0): its base vendor location has actually been
        bought AT THIS VENDOR. Deliberately NOT satisfied by AP ownership
        alone — apply_vendor_locations() zeroes `unlocked` for the left
        view unless vendor_locations[loc] is true, precisely so a weapon
        already AP-owned via some other location still shows as
        purchasable here and its OWN base location can actually be sent;
        gating this on AP ownership too would skip that location
        permanently for anyone who receives the item before ever visiting
        this vendor. Mootator has no base listing at all, so it goes by its
        real live level instead — once that's organically reached the
        level-4 floor through play/Progressive Weapons.
        """
        if not self._is_titan_eligible(name):
            return False
        base_loc = WEAPON_INTERNAL_TO_LOCATION.get(name)
        if base_loc is None:
            return self.weapons.get_level(name) >= 3
        return self._is_purchased(name)

    def _apply_titan_pending_levels(self, purchasable: list[str]) -> None:
        """Force the level-4 floor (0x03) for every currently Titan-pending
        weapon in `purchasable` — the companion to zero_levels_for_vendor()
        zeroing everything else. Needed as an explicit step (called at
        vendor open/D-pad-left-toggle time) rather than left to whatever
        the real level happens to be, since _is_titan_pending() can now be
        true purely from AP ownership, without the weapon ever having gone
        through a purchase event at this vendor to set its level itself.

        Deliberately does NOT touch _level_snapshot: that's the player's
        real, organically-earned level (could genuinely be below 3 — the
        Titan floor only trims EXCESS level, see _titan_bound(), it never
        forces a minimum), and it must stay that way so restore_levels()
        shows the true level on the right-hand (ammo) view / on close. This
        0x03 write is a left-view-only display fake; overwriting the
        snapshot with it would leak that fake value into the right view and
        into what's restored on close too.
        """
        for name in purchasable:
            if self._is_titan_pending(name):
                self.weapons.set_level(name, 3)

    def _purchasable_names(self) -> list[str]:
        """Weapons/gadgets currently shown on the vendor's default (left,
        buy-new) view.

        A Titan-eligible weapon stays in this list for as long as its Titan
        variant hasn't been bought: first at level 0 (the base purchase),
        then — once that's done — explicitly re-set to level 4 and
        re-locked so the SAME vendor slot re-lists as the Titan purchase
        (see weapon_vendor()'s purchase-detection loop). No separate
        pseudo name or vendor item id for the Titan variant. Mootator has no
        base vendor listing at all, so it only ever appears in this
        Titan-pending state. Every other weapon/gadget drops out for good
        once its one-time vendor location is bought.
        """
        names: list[str] = []
        for name, planet_key in _WEAPON_TO_PLANET_KEY.items():
            if name in _CHALLENGE_MODE_ONLY_WEAPONS and self.challenge_mode < 1:
                continue
            if not self.planet_unlock.is_vendor_accessible(planet_key):
                continue
            if self._is_titan_eligible(name) or not self._is_purchased(name):
                names.append(name)
        if self._is_titan_eligible("mootator") and self.weapons.get_level("mootator") >= 3:
            # Mootator has no base vendor listing/purchase to gate this on
            # (unlike every other Titan-eligible weapon, which only starts
            # showing its Titan purchase once its OWN base purchase has
            # actually happened) — it must instead wait for its real level
            # to organically reach the level-4 floor through play/Progressive
            # Weapons before appearing here at all, or it would show up
            # looking exactly like a buyable base weapon (level 0) despite
            # never having any base purchase behind it.
            mootator_planet_key = _TITAN_TO_PLANET_KEY["mootator"]
            if self.planet_unlock.is_vendor_accessible(mootator_planet_key):
                names.append("mootator")
        for name, planet_key in _GADGET_TO_PLANET_KEY.items():
            if self.planet_unlock.is_vendor_accessible(planet_key) and not self._is_purchased(name):
                names.append(name)
        return names

    def purchasable_locations(self) -> list[str]:
        """AP location names for every weapon/gadget/Titan variant currently
        purchasable at the weapons vendor's default view — used to send
        hints the moment that vendor opens, so a purchasable check is
        hinted before the player has to browse for it."""
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
        """AP location names for every mod slot currently reachable at the
        mod vendor — same hinting purpose as purchasable_locations(), for
        the mod vendor instead of the weapons vendor."""
        return [
            loc for (_weapon, _slot), loc in MOD_INTERNAL_TO_LOCATION.items()
            if self._is_mod_location_accessible(loc)
        ]

    def _is_mod_location_accessible(self, loc: str) -> bool:
        """Whether the mod vendor selling this location's planet is
        actually reachable — planet AP-accessibility alone isn't enough
        where an extra gadget check gates the vendor's area (see
        _MOD_VENDOR_EXTRA_GADGETS), or where the mod itself is Challenge
        Mode 1+ only (see _CHALLENGE_MODE_MOD_LOCATIONS)."""
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
        """Weapons that should appear in the mod vendor's selection list: at
        least one of their mod locations is reachable, regardless of
        ownership. Every weapon returned here gets force-unlocked for
        display (see _refresh_mod_vendor()) since the game won't render an
        unlisted weapon as a selection; real ownership only gates whether a
        slot is *purchasable* (mod_unlock_N, see _apply_mod_unlock_flags())."""
        weapons: list[str] = []
        for (weapon, _slot), loc in MOD_INTERNAL_TO_LOCATION.items():
            if self._is_mod_location_accessible(loc) and weapon not in weapons:
                weapons.append(weapon)
        return weapons

    def _apply_mod_unlock_flags(self) -> None:
        """Write mod_unlock_N — the mod vendor's "purchasable" byte for that
        slot, distinct from mod_slot_N (does the player *own* the mod) — 1
        once its vendor location is reachable, 0 otherwise. Gated purely on
        reachability, not ownership: AP's accessibility sweep assumes these
        locations are reachable independent of weapon ownership, so gating
        on ownership too would leave an always-gettable location permanently
        unpurchasable in-game.

        Also forces the weapon's own `unlocked` byte to match (same
        display-unlock `_mod_vendor_weapons()` already forces for the
        selection list) to avoid a bad half-state. Temporary only — close()
        -> revert_unowned() zeros both back out once the vendor closes.

        Covers every slot every call so anything that stops qualifying is
        correctly revoked. The weapon-level unlock is "any slot reachable"
        (OR semantics), not the current slot's own value, so a weapon with
        mod slots split across planets doesn't get locked back down by a
        later not-yet-reachable slot in iteration order."""
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
            # displayed price derives from the level field (see
            # _weapons_to_zero_for_vendor()). Restored in close() (or
            # re-derived on every left/right toggle below). Core.tick()
            # skips apply_progressive_leveling() while this menu is open so
            # it can't fight this zero-out back mid-tick.
            self._level_snapshot = self.weapons.zero_levels_for_vendor(self._weapons_to_zero_for_vendor())
            purchasable = self._purchasable_names()
            self._apply_titan_pending_levels(purchasable)
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

        # Weapon Level Checks — Core._check_vendor_purchases() never sees
        # this tick's check() result while either vendor menu is open (it
        # returns immediately, since this method owns weapons.check() while
        # open), so a level newly reached during a purchase has to be sent
        # from here instead — this catches a genuine organic level-up that
        # happens to land while the vendor is open (apply_experience_boost()
        # runs every tick regardless of vendor state, unlike
        # apply_progressive_leveling() which is skipped while it's active).
        # Excludes any weapon in changed["titans"] this tick, but only when
        # Challenge Mode is actually active: that's the game's own level
        # 4 -> 5 jump firing purely because the player just bought its
        # Titan variant here, not something earned by play, and already has
        # its own dedicated Titan-purchase location sent below. With
        # Challenge Mode off there's no Titan purchase to duplicate — a
        # weapon can still organically reach level 5 there (Progressive
        # Weapons imposes no titan ceiling without it), and that's a
        # genuine level-up that must still be reported normally.
        # Gated on the option to avoid an unpooled location's no-op
        # send_location() logging a warning every time.
        if self._is_weapon_level_checks_enabled():
            titan_names = frozenset(changed["titans"]) if self.challenge_mode >= 1 else frozenset()
            for name, level in changed["levels"]:
                if name in titan_names:
                    continue
                loc = WEAPON_LEVEL_LOOKUP.get((name, level))
                if loc:
                    self.send_location(loc)

        # The re-lock below must run every tick regardless of which view is
        # active — check() unconditionally baselines self.weapons/gadgets
        # [name] = True the instant it sees an unlocked bit (dict entries
        # never regress on their own), so skipping this correction on the
        # right-hand view would leave a weapon permanently (and wrongly)
        # marked AP-owned if the game's UI re-asserts its unlocked bit while
        # browsing. Only the "report as a fresh purchase" half is view-gated.
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
                    # Set to the level-4 floor — the in-game prerequisite
                    # for the Titan purchase to appear at this same vendor
                    # slot — and force this weapon PERMANENTLY unlocked
                    # (memory + tracking dict), bypassing the normal
                    # AP-ownership relock below entirely. Without this, the
                    # relock zeroes both the moment AP hasn't granted the
                    # real item yet; on the next vendor open,
                    # apply_vendor_locations() then can't restore `unlocked`
                    # either (it also reads that same zeroed tracking dict),
                    # so the base purchase looks entirely undone and the
                    # player can buy it again instead of only ever seeing
                    # the Titan purchase from here on.
                    #
                    # _level_snapshot is deliberately left untouched — it
                    # holds the player's real, organically-earned level
                    # (could be below 3), which restore_levels() needs to
                    # show correctly on the right-hand (ammo) view and on
                    # close; this 0x03 is a left-view-only display fake.
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

        # Titan purchase: the game itself bumps a Titan-eligible weapon's
        # level from the 4 floor set above straight to 5 (addr.level 3 -> 4)
        # the moment the player actually buys the Titan variant — see
        # WeaponInventory.check()'s "titans" derivation. Runs regardless of
        # which view is showing (unlike the base purchase above): the
        # weapon is genuinely owned and visible on both, so the purchase
        # can happen from either.
        for name in changed["titans"]:
            titan_loc = TITAN_INTERNAL_TO_LOCATION.get(name)
            self._log(f"[RAC][vendor-debug] titan {name!r} purchased -> loc={titan_loc!r}")
            if titan_loc:
                self.weapons.titan_purchased[name] = True
                self.send_location(titan_loc)
                newly_purchased = True
                # Drop any stale snapshot entry from the earlier
                # base-weapon purchase: restore_levels() on close() would
                # otherwise write that pre-Titan value back over the game's
                # own (already-correct) post-Titan level.
                self._level_snapshot.pop(name, None)
                # Reset the vendor's own display level back to 0 — purely
                # for consistency with the binary 0/0x03 model; titan_purchased
                # above already excludes this weapon from
                # _purchasable_names() for good, so it can never be
                # re-offered regardless of this value. Safe even though
                # this is also the REAL level field: titan_purchased being
                # true floors it straight back up to the actual Titan tier
                # via apply_progressive_leveling() (skipped only while this
                # menu stays open) the moment the vendor closes.
                self.weapons.set_level(name, 0)

        # D-Pad view toggle — deliberately handled here, AFTER all purchase
        # processing above has fully settled this tick (locations sent,
        # levels/ownership/snapshot updated), not before it. Handling it
        # first (the original position, before check()) meant pressing
        # D-Pad Right on the exact same tick as a purchase would apply the
        # toggle using stale pre-purchase state: report_as_purchase would
        # already reflect the switched-to view instead of the one the
        # purchase actually happened under, and apply_vendor_locations()/
        # restore_levels() would run before this tick's level/ownership
        # writes above landed — showing wrong data (e.g. a Titan purchase
        # that hadn't actually been recorded yet) on the view being
        # switched to.
        if controller is not None:
            if controller.pressed(PauseSelectButtons.D_PAD_RIGHT) and self.show_purchasable_weapons:
                self.weapons.apply_vendor_locations(self._owned_names())
                self.show_purchasable_weapons = False
                # Right-hand view browses owned weapons for ammo — ammo
                # price/capacity depends on the real level, so restore it
                # here (re-zeroed below when flipping back to the left view).
                self.weapons.restore_levels(self._level_snapshot)
                self._set_items(list(self._owned_names()))
                self.refresh(MenuStateValue.WEAPONS_VENDOR)

            # Only allow flipping back to the left (buy-new) view if there's
            # still something purchasable — otherwise the toggle stops and
            # the vendor stays in the owned-inventory view for this visit.
            still_purchasable = self._purchasable_names()
            if (controller.pressed(PauseSelectButtons.D_PAD_LEFT) and not self.show_purchasable_weapons
                    and still_purchasable):
                self.weapons.apply_vendor_locations()
                self.show_purchasable_weapons = True
                # Re-zero so an owned-but-not-vendor-purchased weapon's price
                # isn't skewed by its real level, same as the initial zero
                # on open. Re-snapshots from the just-restored real levels.
                self._level_snapshot = self.weapons.zero_levels_for_vendor(self._weapons_to_zero_for_vendor())
                self._apply_titan_pending_levels(still_purchasable)
                self._set_items(still_purchasable)
                self.refresh(MenuStateValue.WEAPONS_VENDOR)

        if not report_as_purchase:
            # Wasn't browsing the buy-new view when this tick's purchases
            # (if any) happened — a Titan purchase above still registers
            # either way, but nothing here can be reported as a fresh BASE
            # purchase. Any D-Pad Left toggle just above already rebuilt
            # the left-view list fresh on its own if it fired.
            return

        if newly_purchased and self.show_purchasable_weapons:
            # Refresh right away so the just-bought item drops off (or, for
            # a Titan-eligible weapon, re-lists as) the purchasable list
            # instead of waiting for the next open. Skipped if the D-Pad
            # Right toggle just above already switched away from this view
            # this same tick — that already wrote the correct (right-view)
            # item list, and refreshing here would clobber it back to the
            # left-view one.
            purchasable = self._purchasable_names()
            if purchasable:
                self._apply_titan_pending_levels(purchasable)
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

        Passes the *entire* weapons_sold list to apply_vendor_locations()'s
        allowed_extra (not just the AP-owned subset), since a weapon has to
        show as unlocked or the game won't render it as a mod-vendor
        selection at all. This only touches display memory — mod_vendor()
        corrects weapons.weapons back to false every tick for anything not
        truly AP-owned, since check() would otherwise baseline it True and
        dict entries never regress on their own.
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

        # Only a mod purchase counts as "purchased" here — any weapon
        # transition in changed["weapons"] is just check() observing
        # _refresh_mod_vendor()'s own force-unlock writes, never a real
        # purchase. check() still baselines self.weapons[name] = True when it
        # sees that display-only unlock, so correct the dict back inline
        # rather than relying solely on close()'s revert_unowned(). Memory
        # itself must NOT be touched here (unlike weapon_vendor()'s
        # equivalent) — the weapon has to stay unlocked in memory for the
        # whole visit or it won't render as a mod-vendor selection.
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
        """Add a rac5 weapon/gadget/Titan-variant pseudo name (internal name,
        e.g. "lacerator" or "lacerator_titan") to the vendor's unlocked-item
        list."""
        if weapon in _ITEM_IDS and weapon not in self._items:
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
