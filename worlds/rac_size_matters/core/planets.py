from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING, NamedTuple

from ..constants import Rac5CutsceneLocations, Rac5Infobots, Rac5Locations
from .address_maps import (
    CURRENT_PLANET_ADDRESS,
    MENU_ADDR_BY_PLANET_ID,
    NEW_PLANET_START_LOAD_ADDR,
    PLANET_LOAD_IDLE_VALUE,
    PLANET_STATE_OFFSET,
    PLANET_UNLOCK_ADDRESSES,
    WEAPON_ARRAY_BASE_BY_PLANET,
)
from .armour import EQUIPPED_SLOT_TO_PIECE, ArmourPiece, ArmourStruct
from .controller import GlobalButtonState
from .display_text import multi_line_text_box_inventory, small_text_box_inventory
from .menu import MenuInventory, MenuStateValue
from .player import PlayerInventory, PlayerMovementState
from .states.base_state import BaseState
from .structs.game import (
    TRANSITION_GATE_ARRIVED,
    TRANSITION_GATE_IDLE,
    LoadingPlanetStruct,
    PlanetProgressStruct,
    TransitionGateStruct,
)
from .traps import activate_trap as _activate_trap
from .weapon_cycler import WeaponCyclerInventory
from .weapons import WeaponInventory

if TYPE_CHECKING:
    from ..pypine import Pine
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
    # Special vanilla sub-modes entered from Metalis/Challax, not normal AP regions.
    GIANT_CLANK_METALIS = Planet("Giant Clank (Metalis)", 0x0F)
    GIANT_CLANK_CHALLAX = Planet("Giant Clank (Challax)", 0x15)
    # Kalidon's skyboard race sub-level has no addresses of its own; only the
    # fixed/global skyboard completion bits are safe to read while it's loaded.
    KALIDON_RACE    = Planet("Kalidon Race Track",    0x16)
    OUTPOST_OMEGA_2 = Planet("Outpost Omega 2",       0x17, menu_addr=MENU_ADDR_BY_PLANET_ID[0x17])


BY_ID: dict[int, Planet] = {
    p.planet_id: p
    for p in vars(Planets).values()
    if isinstance(p, Planet)
}

@dataclass(frozen=True)
class PlanetUnlock:
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
# Infobots are AP items; receiving one sets the planet's unlock-status address
# to INFOBOT_UNLOCK_VALUE (3). Dreamtime/Inside Clank are auto-unlocked instead.

INFOBOT_UNLOCK_VALUE = 3  # value written to the planet status address

# Display name -> planet key(s). Pokitaru's infobot also unlocks Ryllus since
# the two share one merged item.
INFOBOT_ITEM_TO_PLANET: dict[str, tuple[str, ...]] = {
    Rac5Infobots.POKITARU:     ("pokitaru", "ryllus"),
    Rac5Infobots.KALIDON:      ("kalidon",),
    Rac5Infobots.METALIS:      ("metalis",),
    Rac5Infobots.OUTPOST_OMEGA: ("outpost_omega",),
    Rac5Infobots.CHALLAX:      ("challax",),
    Rac5Infobots.DAYNI_MOON:   ("dayni_moon",),
    Rac5Infobots.QUODRONA:     ("quodrona",),
}

PLANET_STATE_ADDRESSES: dict[str, int] = {
    "pokitaru":          PLANET_UNLOCK_ADDRESSES["POKITARU"],
    "ryllus":            PLANET_UNLOCK_ADDRESSES["RYLLUS"],
    "kalidon":           PLANET_UNLOCK_ADDRESSES["KALIDON"],
    "metalis":           PLANET_UNLOCK_ADDRESSES["METALIS"],
    "outpost_omega":     PLANET_UNLOCK_ADDRESSES["OUTPOST_OMEGA"],
    "outpost_omega_oo2": 0x21F4C677,  # secondary state set alongside Outpost Omega
    "challax":           PLANET_UNLOCK_ADDRESSES["CHALLAX"],
    "dayni_moon":        PLANET_UNLOCK_ADDRESSES["DAYNI_MOON"],
    "inside_clank":      PLANET_UNLOCK_ADDRESSES["INSIDE_CLANK"],  # unlocked via Dayni Moon infobot
    "quodrona":          PLANET_UNLOCK_ADDRESSES["QUODRONA"],
}

# Planet unlock addresses always forced to INFOBOT_UNLOCK_VALUE because
# these planets have no collectible infobot in the AP item pool.
AUTO_UNLOCK_ADDRESSES: list[int] = [
    0x21F4C665,  # Dreamtime -- auto-unlocked via Outpost Omega
]


# Planet state (runtime)

logger = logging.getLogger("CommonClient")

_METALIS_ID: int = 0x04
_CHALLAX_ID: int = 0x07

# Giant Clank Metalis/Challax are self-contained vanilla sequences, not normal AP
# regions — detected purely by planet id, completed via an armour-piece pickup.
_GIANT_CLANK_METALIS_ID:  int = 0x0F
_GIANT_CLANK_CHALLAX_ID:  int = 0x15


class GiantClankConfig(NamedTuple):
    origin_id:        int            # planet the sequence is entered from
    armour_set:       str            # ArmourStruct.SET_FIELDS name (e.g. "electroshock")
    piece:            ArmourPiece    # piece bit that signals completion when it appears
    pickup_locations: tuple[str, ...]  # AP location(s) fired the moment that bit appears
    # redirect_to forces NEW_PLANET_START_LOAD_ADDR back to origin_id when the game
    # scripts an exit to a different planet (Metalis); None/None if it returns on its own.
    redirect_to:      int | None = None
    escape_location:  str | None = None


GIANT_CLANK_CONFIGS: dict[int, GiantClankConfig] = {
    _GIANT_CLANK_METALIS_ID: GiantClankConfig(
        origin_id=_METALIS_ID,
        armour_set="electroshock", piece=ArmourPiece.GLOVES,
        pickup_locations=(Rac5Locations.METALIS_GLOVES,),
        redirect_to=_METALIS_ID, escape_location=Rac5CutsceneLocations.METALIS_ESCAPE,
    ),
    _GIANT_CLANK_CHALLAX_ID: GiantClankConfig(
        origin_id=_CHALLAX_ID,
        armour_set="electroshock", piece=ArmourPiece.CHESTPLATE,
        pickup_locations=(Rac5Locations.CHALLAX_CHESTPLATE, Rac5CutsceneLocations.CHALLAX_CLANK),
    ),
}


class PlanetInventory:
    """Single home for planet-specific runtime logic. Owns every planet-dependent
    Inventory and rebinds them via set_planet(); never pokes memory directly itself."""

    def __init__(
        self,
        pine: Pine,
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
        self.weapon_cycler    = WeaponCyclerInventory(pine)
        self.small_text       = small_text_box_inventory(pine)
        self.multi_line_text  = multi_line_text_box_inventory(pine)

        self.planet_id: int | None = None
        # True once every planet-dependent Inventory has its address rebound;
        # False mid-transition, gating every read/write below.
        self.is_ready: bool = False
        self._pending_planet_id: int | None = None
        self._prev_gate: int = TRANSITION_GATE_IDLE

        # Random Starting Planet: the game always boots a fresh save into Pokitaru,
        # so the first arrival must be redirected once. None (option off) is vanilla.
        self.starting_planet_id: int | None = None
        self._start_redirect_pending: bool = False
        # Quick select starts frozen; zeroed on the first ready planet, restored after.
        self._quick_select_primed: bool = False

        # Giant Clank Metalis/Challax: self-contained vanilla sequences with no AP
        # items/notifications. Defaults True so standalone/test usage isn't locked out.
        self.giant_clank_allowed: bool = True
        self.giant_clank_active: bool = False
        self._giant_clank_config: GiantClankConfig | None = None
        self._giant_clank_had_piece: bool = False
        self._giant_clank_escape_sent: bool = False

        # equipped_armour only ever updates on pause-menu-close (check_equipped_armour()).
        self.equipped_armour:  dict[str, int] = dict.fromkeys(ArmourStruct.SLOT_FIELDS, 0)
        # Gated to the pickup-animation window so an AP inventory resync (which writes
        # the same bytes outside any animation) is never misread as a genuine pickup.
        self._was_picking_up:    bool = False
        # Snapshot equipped slots at pickup-start and restore at pickup-end, since a
        # pickup can auto-equip a piece and must not silently change the loadout.
        self._equipped_pickup_baseline: dict[str, int] | None = None

        self.on_death:                 Callable[[], None]              = lambda: None
        self.on_respawn:               Callable[[], None]              = lambda: None
        self.on_equipped_armour_saved: Callable[[dict[str, int]], None] = lambda _: None
        # Fires on pause-menu-close alongside the equipped-armour save, so other
        # pause-close-only state (e.g. quick select) can hook the same edge.
        self.on_pause_close:           Callable[[], None]              = lambda: None

        self._prev_dead: bool = False
        self._prev_menu: MenuStateValue | None = None
        # Set by check_death() and reused by check_collected_armour() the same tick,
        # so the two don't each take their own movement read.
        self._cached_movement: PlayerMovementState | None = None

    def set_starting_planet(self, planet_id: int | None) -> None:
        """Set once from slot_data: the planet id the first Pokitaru arrival should be
        redirected to. None (option off, or already Pokitaru) leaves it untouched."""
        self.starting_planet_id = planet_id
        self._start_redirect_pending = planet_id is not None and planet_id != Planets.POKITARU.planet_id

    def set_planet(self, planet_id: int) -> None:
        """Rebind every planet-dependent Inventory to the newly loaded planet, including
        unbinding for an unrecognized planet_id — otherwise it'd keep stale addresses."""
        self.planet_id = planet_id
        self.player.set_base(planet_id)
        self.menu.set_base(planet_id)
        self.small_text.set_base(planet_id)
        self.multi_line_text.set_base(planet_id)
        self.weapons.set_base(WEAPON_ARRAY_BASE_BY_PLANET.get(planet_id))
        self.weapon_cycler.set_base(planet_id)

    def check_transition(self) -> bool:
        """Pull-based transition detector — call every tick. Primary signal is the
        transition gate; falls back to a raw CURRENT_PLANET_ADDRESS comparison for a
        planet swap that never touches the gate. Returns True once, when ready."""
        gate = self.pine.read_int32(TransitionGateStruct.BASE_ADDRESS)
        if gate != self._prev_gate:
            prev = self._prev_gate
            self._prev_gate = gate
            left_idle    = prev == TRANSITION_GATE_IDLE and gate != TRANSITION_GATE_IDLE
            back_to_idle = prev != TRANSITION_GATE_IDLE and gate == TRANSITION_GATE_IDLE

            if left_idle:
                self.is_ready = False
                self.quick_select.freeze()

            if gate == TRANSITION_GATE_ARRIVED:
                planet_id = self.pine.read_int8(LoadingPlanetStruct.BASE_ADDRESS)
                if planet_id != 0:
                    self._pending_planet_id = planet_id

            if back_to_idle and self._pending_planet_id:
                self._ready_on_planet(self._pending_planet_id)
                self._pending_planet_id = None
                return True

            return False

        # Fallback: an out-of-band planet change that never touched the gate.
        current_id = self.pine.read_int8(CURRENT_PLANET_ADDRESS)
        if current_id != 0 and current_id != self.planet_id and self._pending_planet_id is None:
            self._ready_on_planet(current_id)
            return True

        return False

    def _ready_on_planet(self, planet_id: int) -> None:
        if self._start_redirect_pending and planet_id == Planets.POKITARU.planet_id:
            # Redirect the hardcoded first Pokitaru boot-in; one-shot so a later
            # legitimate visit is never redirected again.
            self._start_redirect_pending = False
            self.pine.write_int32(NEW_PLANET_START_LOAD_ADDR, self.starting_planet_id)
            return

        config = GIANT_CLANK_CONFIGS.get(planet_id)
        if config is not None and not self.giant_clank_allowed:
            # Option off: force an immediate load back to origin_id. is_ready is
            # left False so nothing runs against this half-loaded state.
            self.pine.write_int32(NEW_PLANET_START_LOAD_ADDR, config.origin_id)
            return

        self.set_planet(planet_id)
        self.is_ready = True
        if not self._quick_select_primed:
            self._quick_select_primed = True
            self.quick_select.zero()
        else:
            self.quick_select.unfreeze()
        # Called unconditionally so both branches converge: applies the loaded
        # loadout (or zero()'s default) on first ready, the normal restore after.
        self.quick_select.restore()

        if config is not None:
            self._enter_giant_clank(config)
        elif self.giant_clank_active:
            self._exit_giant_clank()

    def _enter_giant_clank(self, config: GiantClankConfig) -> None:
        """Strip armour on entry so nothing AP-granted shows during the
        sequence, and so the completion pickup (checked live via
        check_giant_clank()) is a clean 0->1 transition."""
        self.giant_clank_active = True
        self._giant_clank_config = config
        self._giant_clank_had_piece = False
        self._giant_clank_escape_sent = False
        self.armour.clear_unlocked()

    def _exit_giant_clank(self) -> None:
        """Restore true AP armour ownership once back on a regular planet."""
        self.giant_clank_active = False
        self._giant_clank_config = None
        self.armour.apply_full()

    def check_giant_clank(self) -> list[str]:
        """Poll-based: call every tick regardless of is_ready/transition state so a
        redirect lands ASAP. No-ops unless giant_clank_active. Returns
        pickup_locations on a genuine armour pickup, and escape_location once
        when redirecting the game's own scripted exit back to origin_id."""
        config = self._giant_clank_config
        if not self.giant_clank_active or config is None:
            return []

        to_send: list[str] = []

        unlocked = self.armour.read()
        has_piece = bool(getattr(unlocked, config.armour_set) & config.piece)
        if has_piece and not self._giant_clank_had_piece:
            to_send.extend(config.pickup_locations)
        self._giant_clank_had_piece = has_piece

        if config.redirect_to is not None:
            load_value = self.pine.read_int32(NEW_PLANET_START_LOAD_ADDR)
            if load_value != PLANET_LOAD_IDLE_VALUE:
                self.pine.write_int32(NEW_PLANET_START_LOAD_ADDR, config.redirect_to)
                if not self._giant_clank_escape_sent:
                    self._giant_clank_escape_sent = True
                    if config.escape_location:
                        to_send.append(config.escape_location)

        return to_send

    # Text chat — the entry point external code calls to show a message.
    # Deciding *when* to call it is entirely external.
    def show_text(self, text: bytes | str, *, multi_line: bool = False) -> None:
        if not self.is_ready:
            return
        box = self.multi_line_text if multi_line else self.small_text
        box.set(text)

    # Death — pull-based, call whenever you want to check for a transition.
    def check_death(self) -> bool:
        """Also refreshes self._cached_movement, the single PlayerInventory read this
        and check_collected_armour() both need this tick, avoiding a second read."""
        if not self.is_ready:
            return False
        movement = self.player.movement_state
        self._cached_movement = movement
        is_dead = movement is not None and PlayerMovementState.is_dead(int(movement))
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
        if buttons is not None and buttons.opens_planet_menu:
            self.menu.set(MenuStateValue.PLANET_MENU)

    # Quick select / traps
    def activate_trap(self, trap_name: str) -> None:
        if not self.is_ready:
            return
        _activate_trap(self.pine, trap_name)

    # Armour
    def check_collected_armour(self) -> None:
        """Detect a genuine pickup via the pickup-animation window, not by polling
        continuously (apply_inventory()'s AP resync writes the same bytes and would
        look like a pickup). Zeroes every set on entry so whatever's back to 1 on exit
        is fresh, masking out bits for pieces already equipped going in."""
        if not self.is_ready:
            return
        is_picking_up = self._cached_movement == PlayerMovementState.Pickup
        if is_picking_up and not self._was_picking_up:
            equipped = self.armour.read()
            self._equipped_pickup_baseline = {
                name: int(getattr(equipped, name) or 0)
                for name in ArmourStruct.SLOT_FIELDS
            }
            self.armour.clear_unlocked()
        elif not is_picking_up and self._was_picking_up:
            equipped_mask_by_set: dict[str, int] = {}
            if self._equipped_pickup_baseline:
                for slot_name, piece in EQUIPPED_SLOT_TO_PIECE.items():
                    raw_set = self._equipped_pickup_baseline.get(slot_name, 0)
                    if raw_set:
                        set_key = ArmourStruct.SET_FIELDS[raw_set - 1]
                        equipped_mask_by_set[set_key] = equipped_mask_by_set.get(set_key, 0) | int(piece)

            unlocked = self.armour.read()
            new_pieces: dict[str, ArmourPiece] = {}
            for name in ArmourStruct.SET_FIELDS:
                raw = int(getattr(unlocked, name))
                raw &= ~equipped_mask_by_set.get(name, 0)
                already = int(getattr(self.armour.game_armour, name) or 0)
                new_bits = raw & ~already
                if new_bits:
                    new_pieces[name] = ArmourPiece(new_bits)
            if new_pieces:
                self.armour.record_pickup(new_pieces)
            self.armour.apply_full()

            if self._equipped_pickup_baseline is not None:
                self.armour.sync_equipped(self._equipped_pickup_baseline)
                self._equipped_pickup_baseline = None
        self._was_picking_up = is_picking_up

    def check_equipped_armour(self) -> bool:
        """Pull-based: call whenever you want to check for a pause-menu-close
        transition. Only then does it snapshot + save EquipedArmour."""
        if not self.is_ready:
            return False
        current = self.menu.get()
        left_pause_menu = self._prev_menu == MenuStateValue.PAUSE_MENU and current != MenuStateValue.PAUSE_MENU
        self._prev_menu = current
        if left_pause_menu:
            equipped = self.armour.read()
            for name in ArmourStruct.SLOT_FIELDS:
                self.equipped_armour[name] = int(getattr(equipped, name) or 0)
            self.on_equipped_armour_saved(dict(self.equipped_armour))
            self.on_pause_close()
        return left_pause_menu

    # Weapons
    def check_weapons(self) -> dict[str, list]:
        if not self.is_ready:
            return {"weapons": [], "gadgets": [], "mods": [], "levels": []}
        return self.weapons.check()

    def check_weapon_cycler(
        self, *, is_ap_owned: Callable[[int], bool], vendor_active: bool,
        fallback_weapon_id: Callable[[], int | None],
    ) -> None:
        if not self.is_ready:
            return
        self.weapon_cycler.check(
            is_ap_owned=is_ap_owned, vendor_active=vendor_active, fallback_weapon_id=fallback_weapon_id,
        )

    def __repr__(self) -> str:
        return f"PlanetInventory(planet_id={self.planet_id})"


# Planet unlock state (runtime)

PLANET_UNLOCK_BASE: int = PlanetProgressStruct.BASE_ADDRESS

class PlanetLockValue(IntEnum):
    LOCKED   = 0x00
    UNLOCKED = 0x03

PLANET_UNLOCK_ORDER: list[str] = list(PlanetProgressStruct.PLANET_NAME_ORDER)

_AUTO_UNLOCK_NAMES: frozenset[str] = frozenset({
    "DREAMTIME",
})

# Planets whose unlock byte the game manages entirely on its own — never read,
# written, or forced by AP (Inside Clank opens naturally via Dayni Moon progress).
_NATURAL_UNLOCK_NAMES: frozenset[str] = frozenset({"INSIDE_CLANK"})

# Maps an auto-unlocked planet -> the planet whose AP status gates its vendor access.
_VENDOR_PLANET_GATE: dict[str, str] = {
    "DREAMTIME":    "OUTPOST_OMEGA",  # reachable only once Outpost Omega infobot received
    "INSIDE_CLANK": "DAYNI_MOON",    # reachable only once Dayni Moon infobot received
}

_COUNT = len(PLANET_UNLOCK_ORDER)

class PlanetUnlockState(BaseState):

    def __init__(self, pine: Pine) -> None:
        super().__init__()
        self.pine = pine
        self.unlocked: dict[str, bool] = dict.fromkeys(PLANET_UNLOCK_ORDER, False)
        self._desired: dict[str, bool] = {p: p in _AUTO_UNLOCK_NAMES for p in PLANET_UNLOCK_ORDER}
        self._desired["RYLLUS"]        = True
        self._enforce_active: bool     = True
        self._ryllus_released: bool    = False
        self._infobot_planets: set[str] = set()
        # False (option off) keeps Ryllus force-opened until its intro cutscene ends,
        # matching vanilla. True gates it purely by infobot ownership from tick one.
        self._random_start: bool = False

    def _read_struct(self) -> PlanetProgressStruct:
        raw = self.pine.read_bytes(PlanetProgressStruct.BASE_ADDRESS, PlanetProgressStruct.size())
        return PlanetProgressStruct.from_bytes(raw)

    def check(self) -> None:
        """Pull-based: re-check + enforce planet unlock state, firing
        on_planet_unlocked/on_planet_locked for whatever changed."""
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
        """Unconditionally re-assert every non-natural planet's lock state every call,
        since _write_desired()'s second state_addr byte can silently drift out of sync."""
        if not self._enforce_active:
            return
        names = [n for n in PLANET_UNLOCK_ORDER if n not in _NATURAL_UNLOCK_NAMES]
        self._write_desired(names)
        for name in names:
            self.unlocked[name] = self._desired[name]

    def _write_desired(self, names: list[str]) -> None:
        # Per-field writes, not one packed write, so _NATURAL_UNLOCK_NAMES planets are
        # never touched — a bulk write would clobber their live game-managed byte.
        for field, name in zip(PlanetProgressStruct.PLANET_ORDER, PLANET_UNLOCK_ORDER, strict=False):
            if name not in names:
                continue
            unlock_val = PlanetLockValue.UNLOCKED if self._desired[name] else PlanetLockValue.LOCKED
            self.pine.write_int8(PlanetProgressStruct.address_of(field), int(unlock_val))
            pu = PLANET_UNLOCKS.get(name)
            if pu is not None:
                state_val = max(int(unlock_val), pu.default_state)
                self.pine.write_int8(pu.state_addr, state_val)

    def set_random_start(self, enabled: bool) -> None:
        self._random_start = enabled

    def set_unlocked_planets(self, planets: set[str]) -> None:
        self._infobot_planets = set(planets)
        for name in PLANET_UNLOCK_ORDER:
            self._desired[name] = name in planets or name in _AUTO_UNLOCK_NAMES
        if not self._random_start and not self._ryllus_released:
            self._desired["RYLLUS"] = True

    def on_ryllus_cutscene_ended(self) -> None:
        if self._random_start or self._ryllus_released:
            return
        self._ryllus_released = True
        self._desired["RYLLUS"] = "RYLLUS" in self._infobot_planets

    def reset_session(self) -> None:
        self._ryllus_released = False
        if not self._random_start:
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
