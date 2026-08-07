from __future__ import annotations

from collections.abc import Callable
from enum import IntEnum
from typing import TYPE_CHECKING

from .address_maps import WEAPON_CYCLER_ADDRS_BY_PLANET

if TYPE_CHECKING:
    from ..pypine import Pine


class WeaponCycleState(IntEnum):
    IDLE   = 0x00
    PICKUP = 0x0C

# Value current_weapon/stored_weapon hold when nothing is equipped/queued —
# not 0.
EMPTY_WEAPON_ID = 1


class WeaponCyclerField:
    """Pine-backed accessor for one 4-byte weapon-cycler field. `attr` names
    the instance attribute holding that field's address (None on a planet
    it isn't known for yet, in which case every read/write is a no-op)."""

    def __init__(self, attr: str) -> None:
        self.attr = attr

    def __get__(self, instance, owner) -> int | None:
        if instance is None:
            return None
        address = getattr(instance, self.attr)
        if address is None:
            return None
        return instance.pine.read_int32(address)

    def __set__(self, instance, value: int) -> None:
        address = getattr(instance, self.attr)
        if address is not None:
            instance.pine.write_int32(address, value)


class WeaponCyclerInventory:
    """Pine-backed live accessor + write gate for the per-planet weapon
    cycler — the mechanism cutscenes/kiosk pickups use to force a weapon
    into the player's hands via the apply-weapon trigger address.

    Planet-dependent (WEAPON_CYCLER_ADDRS_BY_PLANET), rebound via
    set_base(planet_id). Only Pokitaru's addresses are confirmed so far;
    other planets' fields read as None until filled in.

    There's no "we're in a cutscene" signal to gate writes on up front, so
    cutscene-forced weapons are handled the same way as the game's own
    forced unlocks elsewhere: let the write happen, then immediately clamp
    current_weapon/stored_weapon back to EMPTY_WEAPON_ID if AP hasn't
    actually granted it (see check()).
    """

    applied_weapon = WeaponCyclerField("apply_addr")
    cycle_state    = WeaponCyclerField("state_addr")
    current_weapon = WeaponCyclerField("current_addr")
    stored_weapon  = WeaponCyclerField("stored_addr")

    def __init__(self, pine: Pine) -> None:
        self.pine = pine
        self.apply_addr:   int | None = None
        self.state_addr:   int | None = None
        self.current_addr: int | None = None
        self.stored_addr:  int | None = None
        # Tracks vendor_active across calls so check() can detect the exact
        # close-edge tick and skip correcting on it too (see check()).
        self._prev_vendor_active: bool = False

    def set_base(self, planet_id: int) -> None:
        addrs = WEAPON_CYCLER_ADDRS_BY_PLANET.get(planet_id)
        if addrs is None:
            self.apply_addr = self.state_addr = self.current_addr = self.stored_addr = None
        else:
            self.apply_addr, self.state_addr, self.current_addr, self.stored_addr = addrs

    def initialize(self, fallback_weapon_id: Callable[[], int | None]) -> None:
        """Force cycle_state to 1 and set current_weapon/stored_weapon to
        whatever AP already owns (fallback_weapon_id(), or EMPTY_WEAPON_ID
        if nothing yet) — called once on the very first planet-ready of the
        session (see Core.tick()'s _initial_load_done branch), since the
        wheel otherwise starts in a state that blocks weapon application."""
        if not self.is_ready:
            return
        self.cycle_state = 1
        weapon_id = fallback_weapon_id() or EMPTY_WEAPON_ID
        self.applied_weapon = weapon_id  # actually changes current_weapon; a direct write doesn't take
        self.stored_weapon  = weapon_id

    @property
    def is_ready(self) -> bool:
        return self.apply_addr is not None

    @property
    def is_picking_up(self) -> bool:
        state = self.cycle_state
        return state is not None and state == WeaponCycleState.PICKUP

    def can_write(self, *, vendor_active: bool) -> bool:
        """Whether it's currently safe to write applied_weapon/current_weapon
        /stored_weapon — false during a pickup animation or while a vendor
        menu owns this same memory."""
        return self.is_ready and not self.is_picking_up and not vendor_active

    def apply(self, weapon_id: int, *, vendor_active: bool) -> bool:
        """Hand `weapon_id` to the player via the apply-weapon trigger
        address. No-ops (returns False) during a pickup animation or an
        open vendor menu."""
        if not self.can_write(vendor_active=vendor_active):
            return False
        self.applied_weapon = weapon_id
        return True

    def check(
        self, *, is_ap_owned: Callable[[int], bool], vendor_active: bool,
        fallback_weapon_id: Callable[[], int | None],
    ) -> None:
        """Pull-based: call every tick.

        Clamps current_weapon/stored_weapon back to EMPTY_WEAPON_ID the
        instant either reads as a weapon id AP hasn't granted — the only way
        this can happen outside apply() is the game itself forcing one on
        (e.g. a cutscene handing over a weapon/gadget it isn't supposed to,
        like Sprout-o-Matic before its own AP item has actually arrived).
        Skipped during a pickup animation or while a vendor is open, since
        both windows legitimately own this memory — and skipped for one
        extra tick right after the vendor closes too, so the vendor's own
        writes have a tick to settle before this starts checking again.

        If current_weapon ends up empty (EMPTY_WEAPON_ID, or a raw 0) — a
        fresh boot, or just cleared above — hands the player
        fallback_weapon_id() instead of leaving them with nothing equipped,
        provided AP actually owns at least one weapon yet.
        """
        just_closed_vendor = self._prev_vendor_active and not vendor_active
        self._prev_vendor_active = vendor_active

        if not self.is_ready or self.is_picking_up or vendor_active or just_closed_vendor:
            return

        # current_weapon is set through applied_weapon, not written directly
        # — a direct write to current_weapon doesn't actually change what
        # the player's holding; apply_weapon is the trigger the game itself
        # watches for that.
        current = self.current_weapon
        if current is not None and current not in (0, EMPTY_WEAPON_ID) and not is_ap_owned(current):
            self.applied_weapon = EMPTY_WEAPON_ID
            current = EMPTY_WEAPON_ID
        if not current or current == EMPTY_WEAPON_ID:
            fallback = fallback_weapon_id()
            if fallback:
                self.applied_weapon = fallback
            elif current != EMPTY_WEAPON_ID:
                self.applied_weapon = EMPTY_WEAPON_ID

        stored = self.stored_weapon
        if stored is not None and stored not in (0, EMPTY_WEAPON_ID) and not is_ap_owned(stored):
            self.stored_weapon = EMPTY_WEAPON_ID

    def __repr__(self) -> str:
        return (
            f"WeaponCyclerInventory(current={self.current_weapon!r}, "
            f"stored={self.stored_weapon!r}, state={self.cycle_state!r})"
        )
