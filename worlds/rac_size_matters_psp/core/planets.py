from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING

from ..constants import Rac5Infobots
from .address_maps import (
    CURRENT_PLANET_ADDRESS,
    MENU_ADDR_BY_PLANET_ID,
    PLANET_MISSION_ADDRESSES,
    PLANET_STATE_OFFSET,
    PLANET_UNLOCK_ADDRESSES,
    WEAPON_ARRAY_BASE_BY_PLANET,
)
from .armour import ARMOUR_SET_TO_KEY, EQUIPPED_SLOT_TO_PIECE, ArmourUnlocks, EquippedArmour
from .controller import GlobalButtonState
from .menu import MenuInventory, MenuStateValue
from .player import PlayerInventory
from .states.base_state import BaseState
from .structs.game import (
    TRANSITION_GATE_IDLE,
    LoadingPlanetStruct,
    PlanetProgressStruct,
    TransitionGateStruct,
)
from .traps import activate_trap as _activate_trap
from .weapons import WeaponInventory
from ..pypsp import Psp

if TYPE_CHECKING:
    from .armour import ArmourInventory
    from .quick_select import QuickSelectState


@dataclass(frozen=True)
class Planet:
    name:      str
    planet_id: int
    menu_addr: int | None = None


class Planets:
    POKITARU        = Planet("Pokitaru",              0x01, menu_addr=MENU_ADDR_BY_PLANET_ID[0x01])
    RYLLUS          = Planet("Ryllus",                0x02, menu_addr=MENU_ADDR_BY_PLANET_ID[0x02])
    KALIDON         = Planet("Kalidon",               0x03, menu_addr=MENU_ADDR_BY_PLANET_ID[0x03])
    METALIS         = Planet("Metalis",               0x04, menu_addr=MENU_ADDR_BY_PLANET_ID[0x04])
    DREAMTIME       = Planet("Dreamtime",             0x05, menu_addr=MENU_ADDR_BY_PLANET_ID[0x05])
    # OUTPOST_OMEGA_1 = Planet("Outpost Omega 1",       0x06)
    CHALLAX         = Planet("Challax",               0x07, menu_addr=MENU_ADDR_BY_PLANET_ID[0x07])
    DAYNI_MOON      = Planet("Dayni Moon",            0x08, menu_addr=MENU_ADDR_BY_PLANET_ID[0x08])
    INSIDE_CLANK    = Planet("Inside Clank",          0x09)
    QUODRONA        = Planet("Quodrona",              0x0A, menu_addr=MENU_ADDR_BY_PLANET_ID[0x0A])
    # GIANT_CLANK_META = Planet("Giant Clank (Metalis)", 0x0F)
    # GIANT_CLANK_CHAL = Planet("Giant Clank (Challax)", 0x15)
    # KALIDON_RACE    = Planet("Kalidon Race Track",    0x16)
    OUTPOST_OMEGA_2 = Planet("Outpost Omega 2",       0x17, menu_addr=MENU_ADDR_BY_PLANET_ID[0x17])


BY_ID: dict[int, Planet] = {
    p.planet_id: p
    for p in vars(Planets).values()
    if isinstance(p, Planet)
}

@dataclass(frozen=True)
class PlanetUnlock:
    """
    Data record for a planet's unlock information.
    This is used for monitoring and modifying planet unlock states in the game.
    """

    unlock_addr:   int
    state_addr:    int
    default_state: int = 0  # minimum value always written to state_addr


_DEFAULT_STATES: dict[str, int] = {
    "DREAMTIME":     3,
    "OUTPOST_OMEGA": 3,
}

PLANET_UNLOCKS: dict[str, PlanetUnlock] = {
    name: PlanetUnlock(
        unlock_addr=addr,
        state_addr=addr + PLANET_STATE_OFFSET,
        default_state=_DEFAULT_STATES.get(name, 0),
    )
    for name, addr in PLANET_UNLOCK_ADDRESSES.items()
}


# Infobots / planet state
# Infobots are AP items given to the player.  When received they set the
# corresponding planet's unlock-status address to INFOBOT_UNLOCK_VALUE (3),
# which allows Ratchet to travel to (or enter) that planet.
#
# Planets that are auto-unlocked from the start (no infobot item):
#   Dreamtime    -- unlocked through Outpost Omega automatically
#   Inside Clank -- entrance only accessible from Dayni Moon; requires Shrink Ray

INFOBOT_UNLOCK_VALUE = 3  # value written to the planet status address

# Display name -> planet key used in PLANET_STATE_ADDRESSES
INFOBOT_ITEM_TO_PLANET: dict[str, str] = {
    Rac5Infobots.POKITARU:     "pokitaru",
    Rac5Infobots.RYLLUS:       "ryllus",
    Rac5Infobots.KALIDON:      "kalidon",
    Rac5Infobots.METALIS:      "metalis",
    Rac5Infobots.OUTPOST_OMEGA: "outpost_omega",
    Rac5Infobots.CHALLAX:      "challax",
    Rac5Infobots.DAYNI_MOON:   "dayni_moon",
    Rac5Infobots.QUODRONA:     "quodrona",
}

PLANET_STATE_ADDRESSES: dict[str, int] = {
    "pokitaru":          PLANET_UNLOCK_ADDRESSES["POKITARU"],
    "ryllus":            PLANET_UNLOCK_ADDRESSES["RYLLUS"],
    "kalidon":           PLANET_UNLOCK_ADDRESSES["KALIDON"],
    "metalis":           PLANET_UNLOCK_ADDRESSES["METALIS"],
    "outpost_omega":     PLANET_UNLOCK_ADDRESSES["OUTPOST_OMEGA"],
    "outpost_omega_oo2": PLANET_UNLOCK_ADDRESSES["OUTPOST_OMEGA"] + PLANET_STATE_OFFSET,  # secondary state set alongside Outpost Omega
    "challax":           PLANET_UNLOCK_ADDRESSES["CHALLAX"],
    "dayni_moon":        PLANET_UNLOCK_ADDRESSES["DAYNI_MOON"],
    "inside_clank":      PLANET_UNLOCK_ADDRESSES["INSIDE_CLANK"],  # unlocked via Dayni Moon infobot
    "quodrona":          PLANET_UNLOCK_ADDRESSES["QUODRONA"],
}

# Planet unlock addresses always forced to INFOBOT_UNLOCK_VALUE because
# these planets have no collectible infobot in the AP item pool.
AUTO_UNLOCK_ADDRESSES: list[int] = [
    PLANET_UNLOCK_ADDRESSES["POKITARU"],   # mandatory starting planet, always accessible
    PLANET_UNLOCK_ADDRESSES["DREAMTIME"],  # auto-unlocked via Outpost Omega
]


# Planet state (runtime)

logger = logging.getLogger("CommonClient")

# How long after the transition gate leaves idle before _LOADING_PLANET_ADDR
# is trustworthy — user-supplied/live-verified on PSP. See check_transition()
# and structs/game.py's gate-address comment.
TRANSITION_ARRIVAL_DELAY_S: float = 5.0

_METALIS_ID: int = 0x04

# Giant Clank on Metalis is unreachable/disabled (no AP location for it — see
# locations.py). Tracked via a bit on the Challax mission address (the game
# shares that progress word between the two Giant Clank sequences); forcing
# it set on every Metalis entry stops the game from triggering the sequence.
_GIANT_CLANK_ADDR: int = PLANET_MISSION_ADDRESSES["Challax"]
_GIANT_CLANK_MASK: int = 0x0010


class PlanetInventory:
    """Single home for planet-specific runtime logic.

    Owns every planet-dependent Inventory (player, menu, weapons, text boxes)
    and rebinds them via set_base()/set_planet() on planet_enter(). Only ever
    calls the get/set/delete/check methods already implemented on each
    Inventory — never pokes memory directly itself.
    """

    def __init__(
        self,
        pine: Psp,
        armour: ArmourInventory,
        quick_select: QuickSelectState,
    ) -> None:
        self.pine         = pine
        self.armour       = armour
        self.quick_select = quick_select

        # Planet-specific — owned and rebound here, not passed in.
        self.player           = PlayerInventory(pine)
        self.menu             = MenuInventory(pine)
        self.weapons          = WeaponInventory(pine)

        self.planet_id: int | None = None
        # True once the current planet has fully loaded and every
        # planet-dependent Inventory has its base address rebound. False
        # while a planet transition is in flight — every read/write below
        # is gated on this, since addresses are stale/unbound until then.
        self.is_ready: bool = False
        self._prev_gate: int = TRANSITION_GATE_IDLE
        # Wall-clock timestamp (time.monotonic()) of the tick the gate was
        # last seen leaving idle, or None when no transition is in flight.
        # PSP has no "arrived" sentinel value to poll for like PS2 did —
        # _LOADING_PLANET_ADDR simply isn't valid until roughly this long
        # after the gate leaves idle, so the wait is timed instead of
        # value-driven. See structs/game.py's gate-address comment.
        self._transition_started: float | None = None
        # Quick select starts frozen; the first time a planet becomes ready
        # it's zeroed (fresh boot), every time after that it's restored from
        # the in-memory snapshot — same start/restore split QuickSelectState
        # itself already exposes.
        self._quick_select_primed: bool = False

        # Armour tracking: collected_armour is what's been picked up in-game
        # this session, unlock_armour is what Archipelago has granted — kept
        # separate the same way ArmourState used to split world/ap armour.
        # equipped_armour only ever updates when the pause menu closes (see
        # check_equipped_armour()) — never on any other tick.
        self.collected_armour: dict[str, int] = dict.fromkeys(ArmourUnlocks._OFFSETS, 0)
        self.unlock_armour:    dict[str, int] = dict.fromkeys(ArmourUnlocks._OFFSETS, 0)
        self.equipped_armour:  dict[str, int] = dict.fromkeys(EquippedArmour._OFFSETS, 0)
        # Armour-pickup detection is gated to the player's pickup-animation
        # window (see check_collected_armour()) so an AP inventory resync —
        # which writes the same UnlockedArmour bytes outside of any pickup
        # animation, e.g. on every planet load — is never misread as a
        # genuine in-game pickup. There's no separate "this specific pickup
        # was collected" flag available to read (the per-set byte is the
        # only signal that exists, and AP's own grant already writes that
        # same byte), so an already-AP-owned piece would otherwise look
        # identical to one that was never picked up. check_collected_armour()
        # works around that by zeroing the bytes for the duration of the
        # animation window instead of merely snapshotting them.
        self._was_picking_up:    bool = False
        # Picking up a new armour piece can auto-equip it for the pickup
        # animation — snapshot the equipped slots at pickup-start and
        # restore them at pickup-end so a mere pickup never silently changes
        # what the player has equipped; equipping stays a deliberate action
        # (quick select / pause menu).
        self._equipped_pickup_baseline: dict[str, int] | None = None

        self.on_death:                 Callable[[], None]              = lambda: None
        self.on_respawn:               Callable[[], None]              = lambda: None
        self.on_equipped_armour_saved: Callable[[dict[str, int]], None] = lambda _: None
        # Fires whenever the pause menu closes — alongside the equipped-armour
        # save above, so anything else that should only persist on pause-close
        # (e.g. quick select) can hook the same edge without its own tracking.
        self.on_pause_close:           Callable[[], None]              = lambda: None

        self._prev_dead: bool = False
        self._prev_menu: MenuStateValue | None = None

    def set_planet(self, planet_id: int) -> None:
        """Rebind every planet-dependent Inventory to the newly loaded planet
        — including unbinding them (base/array None, every read/write on
        them becomes a no-op) for a planet_id not in PLANET_ADDRESSES. Every
        sub-inventory here must always be explicitly rebound on every call,
        never left alone, or an unrecognized planet would keep whatever
        addresses the last recognized planet had bound: player/menu/weapons
        would then read/write a totally unrelated planet's memory instead of
        just leaving those addresses untouched, and only truly global
        addresses (bolts, skill points, missions, ...) would be safe."""
        self.planet_id = planet_id
        self.player.set_base(planet_id)
        self.menu.set_base(planet_id)
        self.weapons.set_base(WEAPON_ARRAY_BASE_BY_PLANET.get(planet_id))

    def check_transition(self) -> bool:
        """Pull-based transition detector — call every tick.

        Primary signal is the transition gate (structs/game.py's
        _TRANSITION_GATE_ADDR): any change away from TRANSITION_GATE_IDLE
        (0xFFFFFFFF) means a level transition has started, and blocks writes
        immediately (is_ready False). Unlike PS2, PSP has no distinct
        "arrived" gate value to poll for — _LOADING_PLANET_ADDR (the
        destination planet id, right next to the gate) isn't valid until
        roughly TRANSITION_ARRIVAL_DELAY_S seconds after the gate leaves
        idle, so that read is timed on a wall-clock deadline
        (time.monotonic()) rather than value-driven. Once the deadline
        passes, the planet id there is read and — if non-zero — that's the
        moment set_planet() actually rebinds every planet-dependent
        Inventory and is_ready goes back to True.

        Backed up — independent of the gate entirely — by a raw
        CURRENT_PLANET_ADDRESS comparison, checked unconditionally every
        tick (not just when the gate path stays quiet): catches the rare
        planet swap that never touches the gate at all (e.g. the scripted
        Outpost Omega 1 -> 2 area change), a gate address that's ever
        unreadable, and the general case of the gate-based detection above
        simply missing a transition for any other reason. Also lets a
        gate-detected transition resolve early if the real planet id updates
        before the timed wait above elapses, rather than always sitting out
        the full delay.

        Quick select is frozen the moment writes are blocked, and restored
        (or zeroed, the very first time) the moment the new planet is ready
        — same lifecycle QuickSelectState.freeze()/restore()/zero() already
        implements, just called at the right transition edges.

        Planet ID 0x00 is never treated as ready, no matter what else reads
        true, since there's nothing valid to bind addresses to.

        Returns True exactly once, the tick the new planet becomes ready.
        """
        try:
            gate = self.pine.read_int32(TransitionGateStruct.BASE_ADDRESS)
        except Psp.RequestError:
            gate = None

        if gate is not None and gate != self._prev_gate:
            prev = self._prev_gate
            self._prev_gate = gate
            left_idle = prev == TRANSITION_GATE_IDLE and gate != TRANSITION_GATE_IDLE

            if left_idle:
                self.is_ready = False
                self.quick_select.freeze()
                self._transition_started = time.monotonic()

        # Timed wait for _LOADING_PLANET_ADDR to become valid — independent
        # of whether the gate itself changed *this* tick, since the deadline
        # can (and usually does) land on a later tick than the one that set it.
        if self._transition_started is not None:
            if time.monotonic() - self._transition_started >= TRANSITION_ARRIVAL_DELAY_S:
                planet_id = self.pine.read_int8(LoadingPlanetStruct.BASE_ADDRESS)
                self._transition_started = None
                if planet_id != 0:
                    self._ready_on_planet(planet_id)
                    return True

        # Backup: plain planet-id-changed check, always evaluated regardless
        # of gate/timer state above (see docstring) — this is the one signal
        # that doesn't depend on the gate address working at all.
        current_id = self.pine.read_int8(CURRENT_PLANET_ADDRESS)
        if current_id != 0 and current_id != self.planet_id:
            self._transition_started = None
            self._ready_on_planet(current_id)
            return True

        return False

    def _ready_on_planet(self, planet_id: int) -> None:
        self.set_planet(planet_id)
        self.is_ready = True
        if not self._quick_select_primed:
            self._quick_select_primed = True
            self.quick_select.zero()
        else:
            self.quick_select.unfreeze()
        # zero()'s own docstring already promises this: the in-memory
        # snapshot survives the zero-out specifically so a previously
        # restored AP loadout can be written back right after — but nothing
        # actually called restore() on this first-time branch, so a loadout
        # already loaded via context.py's Retrieved/SetReply handler (see
        # QuickSelectState.load()) sat in memory doing nothing until the
        # player's *next* planet transition ever wrote it out. Calling it
        # unconditionally here closes that gap for both branches: on the
        # very first ready it applies whatever's already been loaded (or
        # harmlessly re-applies the same all-zero default zero() just
        # wrote), and on every later one it's the same restore the old
        # code already ran in the else branch above.
        self.quick_select.restore()
        if planet_id == _METALIS_ID:
            self._suppress_giant_clank()

    def _suppress_giant_clank(self) -> None:
        """Force the Giant Clank trigger bit already set so the game treats
        it as done and never starts the (unreachable) sequence."""
        value = self.pine.read_int16(_GIANT_CLANK_ADDR)
        if not value & _GIANT_CLANK_MASK:
            self.pine.write_int16(_GIANT_CLANK_ADDR, value | _GIANT_CLANK_MASK)

    # Death — pull-based, call whenever you want to check for a transition.
    def check_death(self) -> bool:
        if not self.is_ready:
            return False
        is_dead = self.player.is_dead
        newly_dead    = is_dead and not self._prev_dead
        newly_revived = self._prev_dead and not is_dead
        self._prev_dead = is_dead
        if newly_dead:
            self.on_death()
        elif newly_revived:
            self.on_respawn()
        return newly_dead

    # Controller — force the planet menu open while the hotkey combo is held.
    def check_controller(self) -> None:
        if not self.is_ready or self.planet_id is None:
            return
        buttons = GlobalButtonState.read(self.pine, self.planet_id)
        if buttons.opens_planet_menu:
            self.menu.set(MenuStateValue.PLANET_MENU)

    # Quick select / traps
    def activate_trap(self, trap_name: str) -> None:
        if not self.is_ready:
            return
        _activate_trap(self.pine, trap_name)

    # Armour
    def check_collected_armour(self) -> None:
        """Detect a genuine in-game armour pickup by watching the player's
        pickup-animation window (player.is_picking_up), not by polling
        UnlockedArmour continuously — apply_inventory() writes those same
        bytes any time AP-owned armour gets re-synced (e.g. on every planet
        load), completely outside of any pickup animation, and treating
        every appeared bit as "new" would misreport that resync as a real
        pickup the first time each session it happens.

        A snapshot-and-diff wouldn't be enough on its own though: if AP
        already granted a piece before its own vanilla pickup was ever
        visited, apply_inventory() has already written that same bit, so it
        would sit in the "baseline" too and the game re-writing the
        identical bit during the pickup would never look like a change.
        There's no separate per-pickup "collected" flag to fall back on
        (the per-set byte is the only signal that exists, and it's the same
        one AP writes) — so instead of snapshotting, entering the animation
        zeroes every set's bytes outright. Whatever's back to 1 on exit is
        fresh from this pickup — except a piece already equipped going into
        the animation, whose bit the game re-asserts on its own regardless
        of any new pickup (e.g. the default starting armour, worn before AP
        has granted it), so those bits are masked out of the diff using the
        pre-pickup equipped-slot baseline before the result is OR'd into
        collected_armour (so it's never reported twice), then
        immediately rewrite memory for every set back to only what
        Archipelago has actually granted (unlock_armour) — a local pickup
        only proves the *location* was visited, it doesn't grant ownership,
        so the raw bits the game just wrote must not be left sitting in
        memory as if they were owned. Never touches unlock_armour itself —
        that's only ever set by sync_unlock_armour() from AP data.

        Also snapshots/restores the equipped-slot bytes across the same
        window — picking up a piece can auto-equip it for the animation,
        which must not silently change the player's actual loadout."""
        if not self.is_ready:
            return
        is_picking_up = self.player.is_picking_up
        if is_picking_up and not self._was_picking_up:
            self._equipped_pickup_baseline = {
                name: int(getattr(self.armour.EquipedArmour, name) or 0)
                for name in EquippedArmour._OFFSETS
            }
            self.armour.sync_unlocked(dict.fromkeys(ArmourUnlocks._OFFSETS, 0))
        elif not is_picking_up and self._was_picking_up:
            equipped_mask_by_set: dict[str, int] = {}
            if self._equipped_pickup_baseline:
                for slot_name, piece in EQUIPPED_SLOT_TO_PIECE.items():
                    set_key = ARMOUR_SET_TO_KEY.get(self._equipped_pickup_baseline.get(slot_name, 0))
                    if set_key:
                        equipped_mask_by_set[set_key] = equipped_mask_by_set.get(set_key, 0) | int(piece)

            changed: dict[str, int] = {}
            for name in ArmourUnlocks._OFFSETS:
                raw = int(getattr(self.armour.UnlockedArmour, name))
                raw &= ~equipped_mask_by_set.get(name, 0)
                new_bits = raw & ~self.collected_armour[name]
                if new_bits:
                    self.collected_armour[name] |= new_bits
                changed[name] = self.unlock_armour.get(name, 0)
            self.armour.sync_unlocked(changed)

            if self._equipped_pickup_baseline is not None:
                self.armour.sync_equipped(self._equipped_pickup_baseline)
                self._equipped_pickup_baseline = None
        self._was_picking_up = is_picking_up

    def sync_unlock_armour(self, ap_armour: dict[str, int]) -> None:
        """Record what Archipelago has granted, separate from collected_armour.
        Not gated on is_ready — this only touches the in-memory dict, not the game."""
        self.unlock_armour.update(ap_armour)

    def check_equipped_armour(self) -> bool:
        """Pull-based: call whenever you want to check for a pause-menu-close
        transition. Only then does it snapshot + save EquipedArmour."""
        if not self.is_ready:
            return False
        current = self.menu.get()
        left_pause_menu = self._prev_menu == MenuStateValue.PAUSE_MENU and current != MenuStateValue.PAUSE_MENU
        self._prev_menu = current
        if left_pause_menu:
            for name in EquippedArmour._OFFSETS:
                self.equipped_armour[name] = int(getattr(self.armour.EquipedArmour, name) or 0)
            self.on_equipped_armour_saved(dict(self.equipped_armour))
            self.on_pause_close()
        return left_pause_menu

    # Weapons
    def check_weapons(self) -> dict[str, list]:
        if not self.is_ready:
            return {"weapons": [], "gadgets": [], "mods": [], "levels": []}
        return self.weapons.check()

    def __repr__(self) -> str:
        return f"PlanetInventory(planet_id={self.planet_id})"


# Planet unlock state (runtime)

PLANET_UNLOCK_BASE: int = PlanetProgressStruct.BASE_ADDRESS

class PlanetLockValue(IntEnum):
    LOCKED   = 0x00
    UNLOCKED = 0x03

PLANET_UNLOCK_ORDER: list[str] = list(PlanetProgressStruct.PLANET_NAME_ORDER)

_AUTO_UNLOCK_NAMES: frozenset[str] = frozenset({
    "POKITARU",
    "DREAMTIME",
})

# Planets whose unlock byte the game manages entirely on its own — never
# read, written, or forced by AP. Inside Clank's entrance naturally opens
# once Dayni Moon's own in-game progress (Shrink Ray) allows it; forcing it
# here used to fight that, either locking it back before it should open or
# needlessly rewriting a byte the game already set correctly.
_NATURAL_UNLOCK_NAMES: frozenset[str] = frozenset({"INSIDE_CLANK"})

# Planets auto-unlocked in memory but gated behind different AP progress.
# Maps auto-unlock planet → the planet whose AP status we check for vendor access.
_VENDOR_PLANET_GATE: dict[str, str] = {
    "DREAMTIME":    "OUTPOST_OMEGA",  # reachable only once Outpost Omega infobot received
    "INSIDE_CLANK": "DAYNI_MOON",    # reachable only once Dayni Moon infobot received
}

_COUNT = len(PLANET_UNLOCK_ORDER)

class PlanetUnlockState(BaseState):

    def __init__(self, pine: Psp) -> None:
        super().__init__()
        self.pine = pine
        self.unlocked: dict[str, bool] = dict.fromkeys(PLANET_UNLOCK_ORDER, False)
        self._desired: dict[str, bool] = {p: p in _AUTO_UNLOCK_NAMES for p in PLANET_UNLOCK_ORDER}
        self._desired["RYLLUS"]        = True
        self._enforce_active: bool     = True
        self._ryllus_released: bool    = False
        self._infobot_planets: set[str] = set()

    def _read_struct(self) -> PlanetProgressStruct:
        raw = self.pine.read_bytes(PlanetProgressStruct.BASE_ADDRESS, PlanetProgressStruct.size())
        return PlanetProgressStruct.from_bytes(raw)

    def check(self) -> None:
        """Pull-based: call whenever you want to re-check + enforce planet
        unlock state, firing on_planet_unlocked/on_planet_locked for whatever
        changed since the last call."""
        instance = self._read_struct()
        prev = dict(self.unlocked)
        for field, name in zip(PlanetProgressStruct.PLANET_ORDER, PLANET_UNLOCK_ORDER, strict=False):
            self.unlocked[name] = getattr(instance, field) == PlanetLockValue.UNLOCKED

        self._enforce_desired()

        for name in PLANET_UNLOCK_ORDER:
            if self.unlocked[name] and not prev[name]:
                self.on_planet_unlocked(name)
            elif not self.unlocked[name] and prev[name]:
                self.on_planet_locked(name)

    def sync(self) -> None:
        instance = self._read_struct()
        for field, name in zip(PlanetProgressStruct.PLANET_ORDER, PLANET_UNLOCK_ORDER, strict=False):
            self.unlocked[name] = getattr(instance, field) == PlanetLockValue.UNLOCKED
        self._enforce_desired()

    def _enforce_desired(self) -> None:
        """Unconditionally re-assert every non-natural planet's lock state
        every call, rather than only when self.unlocked (mirroring just the
        PlanetProgressStruct byte) looks out of sync with _desired.

        _write_desired() also writes a second, independent byte per planet
        (PLANET_UNLOCKS[name].state_addr — the one that actually gates ship
        travel/selection) alongside the PlanetProgressStruct field this
        class reads back for self.unlocked. Those two bytes can drift apart
        without ever showing up as a mismatch here (e.g. a stale save/prior
        session leaves state_addr unlocked while the struct field reads
        locked) — a mismatch-gated write would then never touch state_addr
        again, silently leaving a planet travelable despite never having
        received its infobot. Writing every tick regardless closes that gap
        instead of trusting a single derived signal to catch every case.
        """
        if not self._enforce_active:
            return
        names = [n for n in PLANET_UNLOCK_ORDER if n not in _NATURAL_UNLOCK_NAMES]
        self._write_desired(names)
        for name in names:
            self.unlocked[name] = self._desired[name]

    def _write_desired(self, names: list[str]) -> None:
        # Per-field writes rather than one packed write, so planets in
        # _NATURAL_UNLOCK_NAMES (e.g. Inside Clank) are never touched at all
        # — a bulk write would clobber their live game-managed byte with
        # whatever this instance's default/desired value happened to be.
        for field, name in zip(PlanetProgressStruct.PLANET_ORDER, PLANET_UNLOCK_ORDER, strict=False):
            if name not in names:
                continue
            unlock_val = PlanetLockValue.UNLOCKED if self._desired[name] else PlanetLockValue.LOCKED
            self.pine.write_int8(PlanetProgressStruct.address_of(field), int(unlock_val))
            pu = PLANET_UNLOCKS.get(name)
            if pu is not None:
                state_val = max(int(unlock_val), pu.default_state)
                self.pine.write_int8(pu.state_addr, state_val)

    def set_unlocked_planets(self, planets: set[str]) -> None:
        self._infobot_planets = set(planets)
        for name in PLANET_UNLOCK_ORDER:
            self._desired[name] = name in planets or name in _AUTO_UNLOCK_NAMES
        if not self._ryllus_released:
            self._desired["RYLLUS"] = True

    def on_ryllus_cutscene_ended(self) -> None:
        if self._ryllus_released:
            return
        self._ryllus_released = True
        self._desired["RYLLUS"] = "RYLLUS" in self._infobot_planets

    def reset_session(self) -> None:
        self._ryllus_released = False
        self._desired["RYLLUS"] = True

    def unlock(self, planet: str) -> None:
        self._desired[planet] = True

    def lock(self, planet: str) -> None:
        if planet not in _AUTO_UNLOCK_NAMES:
            self._desired[planet] = False

    def is_unlocked(self, planet: str) -> bool:
        return self._desired.get(planet, False)

    def is_vendor_accessible(self, planet: str) -> bool:
        gate = _VENDOR_PLANET_GATE.get(planet, planet)
        return self._desired.get(gate, False)

    def on_planet_unlocked(self, _planet: str) -> None:
        del _planet

    def on_planet_locked(self, _planet: str) -> None:
        del _planet

    def __repr__(self) -> str:
        count = sum(self.unlocked.values())
        return f"PlanetUnlockState(unlocked={count}/{_COUNT})"
