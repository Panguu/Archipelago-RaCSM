from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING

from CommonClient import logger

from ..interface_orchestrator.memory.accessor import MemoryAccessor
from ..interface_orchestrator.state.base_state import BaseState
from ..interface_orchestrator.storage.local import LocalStorage
from ..interface_orchestrator.structs.address_map import AddressMap
from ..items import GADGET_DISPLAY_TO_INTERNAL, WEAPON_DISPLAY_TO_INTERNAL
from ..pypine.pypine.pine import Pine
from .address_maps import (
    PLANET_ADDRESSES,
    WEAPON_VENDOR_ITEMS,
    WEAPON_VENDOR_SLOTS,
)
from .display_text import SmallTextBox, SmallTextBoxAddrs
from .memory import GADGETS, WEAPONS, MemoryItemState, restore_tracked_weapon_state, zero_weapon
from .planets import BY_ID
from .states.game_state import GameState
from .weapons import GADGET_ORDER, WEAPON_MOD_COUNTS, WEAPON_ORDER

if TYPE_CHECKING:
    from .planets import PlanetUnlockState
    from .weapons import WeaponState


# ── Menu snapshot (single-read, used by VendorPoller) ────────────────────────────

class MenuStateValue(IntEnum):
    CLOSED         = 0x00
    PAUSE_MENU     = 0x03
    WEAPONS_VENDOR = 0x09
    MOD_VENDOR     = 0x0E
    PLANET_MENU    = 0x10
    PRELOAD_READY  = 0x13


class MenuState:
    """Single-read snapshot of the current menu state for a planet."""

    def __init__(self, value: int, menu_addr: int | None) -> None:
        self._value     = value
        self._menu_addr = menu_addr

    @classmethod
    def read(cls, ipc: Pine, planet_id: int) -> MenuState:
        planet_obj = BY_ID.get(planet_id)
        menu_addr  = planet_obj.menu_addr if planet_obj else None
        value      = ipc.read_int8(menu_addr) if menu_addr else 0
        return cls(value, menu_addr)

    def write(self, ipc: Pine, state: MenuStateValue) -> bool:
        """Write state to the menu address."""
        if not self._menu_addr:
            return False
        ipc.write_int8(self._menu_addr, state)
        return True

    # ── raw ───────────────────────────────────────────────────────────────────

    @property
    def raw(self) -> int:
        return self._value

    # ── named states ─────────────────────────────────────────────────────────

    @property
    def is_weapons_vendor(self) -> bool:
        return self._value == MenuStateValue.WEAPONS_VENDOR

    @property
    def is_mod_vendor(self) -> bool:
        return self._value == MenuStateValue.MOD_VENDOR

    @property
    def is_vendor(self) -> bool:
        return self._value in (MenuStateValue.WEAPONS_VENDOR, MenuStateValue.MOD_VENDOR)

    @property
    def is_planet_menu(self) -> bool:
        return self._value == MenuStateValue.PLANET_MENU

    @property
    def is_pause_menu(self) -> bool:
        return self._value == MenuStateValue.PAUSE_MENU

    @property
    def is_open(self) -> bool:
        return self._value in MenuStateValue._value2member_map_

    # ── repr ──────────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        try:
            name = MenuStateValue(self._value).name
        except ValueError:
            name = f"UNKNOWN({self._value:#04x})"
        return f"MenuState({name})"


# ── Vendor state (runtime BaseState) ─────────────────────────────────────────────

class VendorSessionState(IntEnum):
    CLOSED     = 0
    PRELOADING = 1
    OPEN       = 2

class VendorState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self.session: VendorSessionState        = VendorSessionState.CLOSED
        self.vendor_type: MenuStateValue | None = None
        self.vendor_locations: dict[str, bool]  = {}

    def activate(self, vendor_type: MenuStateValue) -> None:
        self.vendor_type = vendor_type
        self.session = VendorSessionState.OPEN

    def deactivate(self) -> None:
        self.vendor_type = None
        self.session = VendorSessionState.CLOSED

    def start_menu_preload(self) -> None:
        self.session = VendorSessionState.PRELOADING

    def exit_menu_preload(self) -> None:
        pass

    def on_menu_open(self) -> None:
        pass

    def on_menu_close(self) -> None:
        pass

    def sync_from_ap(self, checked_location_names: set[str]) -> None:
        self.vendor_locations.clear()
        for loc_name in checked_location_names:
            if loc_name.startswith("Purchase "):
                self.vendor_locations[loc_name] = True

    def on_purchase(self, kind: str, name: str, slot: str | None) -> None:
        del kind, name, slot

    def __repr__(self) -> str:
        t = self.vendor_type.name if self.vendor_type else "None"
        return f"VendorState(session={self.session.name}, type={t})"


# ── Vendor session / poller (legacy memory-poll path) ────────────────────────────

_TEXTBOX_BY_PLANET: dict[int, SmallTextBox] = {tb.planet_id: tb for tb in SmallTextBoxAddrs}

_MOD_SLOT_ATTRS = ("mod_slot_one", "mod_slot_two", "mod_slot_three")
_SLOT_NAMES = {1: "one", 2: "two", 3: "three"}


def _build_vendor_weapon_addresses() -> dict[str, int]:
    addrs: dict[str, int] = {}
    for name, w in WEAPONS.items():
        addrs[name] = w.unlocked
        for i, attr in enumerate(_MOD_SLOT_ATTRS, 1):
            if i <= WEAPON_MOD_COUNTS.get(name, 0):
                addrs[f"{name}_mod_{i}"] = getattr(w, attr)
    return addrs


def _build_vendor_gadget_addresses() -> dict[str, int]:
    return {name: g.unlocked for name, g in GADGETS.items()}


@dataclass
class VendorSession:
    purchased_weapons:  list[str]                              = field(default_factory=list)
    purchased_gadgets:  list[str]                              = field(default_factory=list)
    purchased_mods:     list[tuple[str, str]]                  = field(default_factory=list)
    mods_randomized:    bool                                   = field(default=True)
    log:                Callable[[str], None]                  = field(default=logger.info, repr=False, compare=False)
    on_purchase:        Callable[[str, str, str | None], None] | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        self.weapon_state = MemoryItemState({}, name="VendorWeaponState", debug_log=self.log)
        self.gadget_state = MemoryItemState({}, name="VendorGadgetState", debug_log=self.log)

    def refresh(
        self,
        tracked_vendor_weapons: dict[str, int],
        tracked_vendor_gadgets: dict[str, int],
        tracked_vendor_mods:    dict[str, set[str]],
    ) -> None:
        if WEAPONS:
            self.weapon_state.update_addresses(_build_vendor_weapon_addresses())
            for name in WEAPONS:
                self.weapon_state.add(name, 1 if name in tracked_vendor_weapons else 0)
                for i in range(1, WEAPON_MOD_COUNTS.get(name, 0) + 1):
                    slot = _SLOT_NAMES[i]
                    purchased = slot in tracked_vendor_mods.get(name, set())
                    self.weapon_state.add(f"{name}_mod_{i}", 1 if purchased else 0)
        if GADGETS:
            self.gadget_state.update_addresses(_build_vendor_gadget_addresses())
            for name in GADGETS:
                self.gadget_state.add(name, 1 if name in tracked_vendor_gadgets else 0)
        self.purchased_weapons.clear()
        self.purchased_gadgets.clear()
        self.purchased_mods.clear()

    def apply(self, ipc) -> None:
        for w in WEAPONS.values():
            zero_weapon(ipc, w)
        for g in GADGETS.values():
            ipc.write_int8(g.unlocked, 0)
        self.weapon_state.give(ipc)
        self.gadget_state.give(ipc)

    def detect_purchases(self, ipc, gs: GameState) -> None:
        for name, w in WEAPONS.items():
            if self.weapon_state.get(name) == 0 and ipc.read_int8(w.unlocked):
                self._add_weapon(name, gs)
                self.weapon_state.add(name, 1)
            if self.mods_randomized:
                for i in range(1, WEAPON_MOD_COUNTS.get(name, 0) + 1):
                    attr = _MOD_SLOT_ATTRS[i - 1]
                    if self.weapon_state.get(f"{name}_mod_{i}") == 0 and ipc.read_int8(getattr(w, attr)):
                        slot = _SLOT_NAMES[i]
                        self._add_mod(name, slot, gs)
                        self.weapon_state.add(f"{name}_mod_{i}", 1)
        for name, g in GADGETS.items():
            if self.gadget_state.get(name) == 0 and ipc.read_int8(g.unlocked):
                self._add_gadget(name, gs)
                self.gadget_state.add(name, 1)

    def enforce(self, ipc) -> None:
        for name, w in WEAPONS.items():
            expected_unlocked = self.weapon_state.get(name)
            if ipc.read_int8(w.unlocked) != expected_unlocked:
                if expected_unlocked == 0:
                    zero_weapon(ipc, w)
                else:
                    ipc.write_int8(w.unlocked, 1)
            if self.mods_randomized:
                for i in range(1, WEAPON_MOD_COUNTS.get(name, 0) + 1):
                    attr = _MOD_SLOT_ATTRS[i - 1]
                    exp_mod = self.weapon_state.get(f"{name}_mod_{i}")
                    if ipc.read_int8(getattr(w, attr)) != exp_mod:
                        ipc.write_int8(getattr(w, attr), exp_mod)
        for name, g in GADGETS.items():
            exp = self.gadget_state.get(name)
            if ipc.read_int8(g.unlocked) != exp:
                ipc.write_int8(g.unlocked, exp)

    def total(self) -> int:
        return len(self.purchased_weapons) + len(self.purchased_gadgets) + len(self.purchased_mods)


    def _add_weapon(self, name: str, gs: GameState) -> None:
        if name not in self.purchased_weapons:
            self.purchased_weapons.append(name)
            gs.tracked_vendor_weapons[name] = 1
            self.log(f"  Purchase detected: weapon {name}")
            if self.on_purchase:
                self.on_purchase("weapon", name, None)

    def _add_gadget(self, name: str, gs: GameState) -> None:
        if name not in self.purchased_gadgets:
            self.purchased_gadgets.append(name)
            gs.tracked_vendor_gadgets[name] = 1
            self.log(f"  Purchase detected: gadget {name}")
            if self.on_purchase:
                self.on_purchase("gadget", name, None)

    def _add_mod(self, weapon: str, slot: str, gs: GameState) -> None:
        if (weapon, slot) not in self.purchased_mods:
            self.purchased_mods.append((weapon, slot))
            gs.tracked_vendor_mods.setdefault(weapon, set()).add(slot)
            self.log(f"  Purchase detected: mod {weapon} slot {slot}")
            if self.on_purchase:
                self.on_purchase("mod", weapon, slot)


class VendorPoller:

    def __init__(self, gs: GameState, log: Callable[[str], None] | None = None) -> None:
        self._gs  = gs
        self._log = log or logger.info

    def tick(self, ipc) -> None:
        gs           = self._gs
        ms           = MenuState.read(ipc, gs.current_planet)
        textbox      = _TEXTBOX_BY_PLANET.get(gs.current_planet)
        pa           = PLANET_ADDRESSES.get(gs.current_planet)
        if textbox and pa is not None and pa.vendor_prompt_id is not None:
            raw        = ipc.read_int16(textbox.message_str_pointer)
            msg_val    = ((raw & 0xFF) << 8) | (raw >> 8)
            is_visible = bool(ipc.read_int16(textbox.is_visible))
            is_preloaded = msg_val == pa.vendor_prompt_id and is_visible
        else:
            is_visible   = False
            is_preloaded = False
        is_in_menu    = ms.is_vendor
        was_preloaded = gs.is_preloaded
        was_in_menu   = gs.is_in_menu

        # Stage 1: preload rising edge — player entered vendor proximity
        if is_preloaded and not was_preloaded and not is_in_menu and not gs.is_dead and not gs.is_picking_up:
            if not WEAPONS or not gs.weapons_ready:
                self._log("Vendor preload: weapon addresses not ready yet — waiting for planet load.")
            else:
                gs.vendor_session.refresh(gs.tracked_vendor_weapons, gs.tracked_vendor_gadgets, gs.tracked_vendor_mods)
                self._log("Vendor preload detected.")
                gs.vendor_session.apply(ipc)
                self._log(
                    f"Vendor state applied: {gs.vendor_session.weapon_state!r}  "
                    f"{gs.vendor_session.gadget_state!r}"
                )

        # Stage 1: falling edge — player left without opening menu
        if was_preloaded and not is_visible and not is_in_menu and not was_in_menu:
            restore_tracked_weapon_state(gs)
            self._log("Vendor preload exit. State restored.")

        # Stage 2: menu opened
        if is_in_menu and not was_in_menu and not gs.is_dead and not gs.is_picking_up:
            self._log(f"Vendor menu opened ({ms!r}).")
            if not WEAPONS or not gs.weapons_ready:
                self._log("Vendor menu: weapon addresses not ready yet.")
            else:
                gs.vendor_session.apply(ipc)
                ms.write(ipc, MenuStateValue.CLOSED)
                ms.write(ipc, MenuStateValue(ms.raw))
                self._log("Vendor menu refreshed.")

        # Stage 2: ongoing purchase detection — fires on_purchase immediately per item
        if is_in_menu and not gs.is_dead:
            gs.vendor_session.detect_purchases(ipc, gs)

        # Stage 3: menu closed
        if was_in_menu and not is_in_menu:
            self._process_close(gs, ipc)

        gs.is_preloaded = is_preloaded
        gs.is_in_menu   = is_in_menu

    def _process_close(self, gs: GameState, ipc) -> None:
        vs = gs.vendor_session
        # Final sweep in case anything was missed during the pickup animation.
        vs.detect_purchases(ipc, gs)
        total = vs.total()
        self._log(f"Vendor closed. {total} purchase(s) processed.")
        restore_tracked_weapon_state(gs)
        self._log("Vendor state restored.")
        if gs.on_vendor_close:
            gs.on_vendor_close()


# ── Vendor unlock state ──────────────────────────────────────────────────────────

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


    def apply(self, accessor: MemoryAccessor) -> None:
        ws        = self._ws
        pu        = self._pu
        purchased = _purchased_names(ws)
        seen: set[int] = set()
        items: list[int] = []

        def _add(name: str) -> None:
            vid = WEAPON_VENDOR_IDS.get(name)
            if vid is not None and vid not in seen:
                seen.add(vid)
                items.append(vid)

        # Ammo-refill slots: player owns the weapon AND
        #   (a) its vendor planet is not yet accessible — remove from inventory would be wrong, or
        #   (b) the purchase location was already checked (bought from vendor before).
        for name in _WEAPON_DISPLAY_ORDER:
            if name not in _WEAPON_TO_PLANET_KEY or not ws.weapons.get(name, False):
                continue
            planet_key = _WEAPON_TO_PLANET_KEY[name]
            if not pu.is_vendor_accessible(planet_key) or name in purchased:
                _add(name)

        for name in _GADGET_DISPLAY_ORDER:
            if name not in _GADGET_TO_PLANET_KEY or not ws.gadgets.get(name, False):
                continue
            planet_key = _GADGET_TO_PLANET_KEY[name]
            if not pu.is_vendor_accessible(planet_key) or name in purchased:
                _add(name)

        # Purchasable slots: planet accessible AND location not yet checked.
        for name, planet_key in _WEAPON_TO_PLANET_KEY.items():
            if pu.is_vendor_accessible(planet_key) and name not in purchased:
                _add(name)
        for name, planet_key in _GADGET_TO_PLANET_KEY.items():
            if pu.is_vendor_accessible(planet_key) and name not in purchased:
                _add(name)

        accessor.write_raw(WEAPON_VENDOR_SLOTS, len(items).to_bytes(4, "little"))
        for i, item_id in enumerate(items):
            accessor.write_raw(WEAPON_VENDOR_ITEMS + i * 4, item_id.to_bytes(4, "little"))

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
