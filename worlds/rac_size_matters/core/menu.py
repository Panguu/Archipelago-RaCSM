from __future__ import annotations

import logging
from collections.abc import Callable
from enum import IntEnum
from typing import TYPE_CHECKING

from ..interface_orchestrator.memory.accessor import MemoryAccessor
from ..interface_orchestrator.state.base_state import BaseState
from ..interface_orchestrator.storage.local import LocalStorage
from ..interface_orchestrator.structs.address_map import AddressMap
from .structs.game import MenuStruct

logger = logging.getLogger("CommonClient")

if TYPE_CHECKING:
    from .planets import PlanetState
    from .vendor import ModVendorState, WeaponVendorState

class MenuStateValue(IntEnum):
    CLOSED            = 0x00
    PAUSE_MENU        = 0x03
    WEAPONS_VENDOR    = 0x09
    QUICK_SELECT_MENU = 0x0A
    MOD_VENDOR        = 0x0E
    PLANET_MENU       = 0x10
    SKYBOARD_MENU     = 0x15


class MenuState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
        log: Callable[..., None] | None = None,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self.current: MenuStateValue              = MenuStateValue.CLOSED
        self._weapon_vendor: WeaponVendorState | None = None
        self._mod_vendor: ModVendorState | None        = None
        self._planet: PlanetState | None          = None
        self._log                                 = log or logger.info
        self.on_pause_close:        Callable[[], None] = lambda: None
        self.on_travel_menu_close:  Callable[[], None] = lambda: None

    def bind(self, weapon_vendor: WeaponVendorState, mod_vendor: ModVendorState, planet: PlanetState) -> None:
        self._weapon_vendor = weapon_vendor
        self._mod_vendor    = mod_vendor
        self._planet        = planet

    def set_pause_close_callback(self, cb: Callable[[], None]) -> None:
        self.on_pause_close = cb

    def unbind(self) -> None:
        self._weapon_vendor = None
        self._mod_vendor    = None
        self._planet        = None

    def _vendor_for(self, value: MenuStateValue) -> WeaponVendorState | ModVendorState | None:
        if value == MenuStateValue.WEAPONS_VENDOR:
            return self._weapon_vendor
        if value == MenuStateValue.MOD_VENDOR:
            return self._mod_vendor
        return None

    def on_exit(self) -> None:
        if self.is_vendor:
            vendor = self._vendor_for(self.current)
            if vendor is not None:
                vendor.on_menu_close()
                vendor.deactivate()
        self.current = MenuStateValue.CLOSED
        self.unbind()

    def _register_handlers(self) -> None:
        menu_cls = self._menu_struct()
        if menu_cls is not None:
            self.accessor.on_struct_change(menu_cls, self._on_menu_change)

    def _unregister_handlers(self) -> None:
        menu_cls = self._menu_struct()
        if menu_cls is not None:
            self.accessor.remove_struct_handler(menu_cls, self._on_menu_change)

    def set_menu(self, value: MenuStateValue) -> None:
        """Request a menu change by writing to the update field (base+0x04),
        same offset on every planet's menu address."""
        menu_cls = self._menu_struct()
        if menu_cls is not None:
            self.accessor.write_field(menu_cls, "update", int(value))

    def _menu_struct(self) -> type[MenuStruct] | None:
        for cls in self.addresses.structs():
            if issubclass(cls, MenuStruct) and cls is not MenuStruct:
                return cls
        return None

    def _on_menu_change(self, address: int, new_bytes: bytes) -> None:
        del address
        raw = new_bytes[0] if new_bytes else 0
        try:
            new_state = MenuStateValue(raw)
        except ValueError:
            return
        prev = self.current
        self.current = new_state
        if new_state != prev:
            self._on_transition(prev, new_state)

    _TRAVEL_MENUS = frozenset({MenuStateValue.SKYBOARD_MENU, MenuStateValue.PLANET_MENU})

    def _on_transition(self, prev: MenuStateValue, current: MenuStateValue) -> None:
        if prev == MenuStateValue.PAUSE_MENU and current != MenuStateValue.PAUSE_MENU:
            self.on_pause_close()
        if prev in self._TRAVEL_MENUS and current not in self._TRAVEL_MENUS:
            self.on_travel_menu_close()

        if self._weapon_vendor is None or self._mod_vendor is None:
            return
        was_vendor = prev    in (MenuStateValue.WEAPONS_VENDOR, MenuStateValue.MOD_VENDOR)
        is_vendor  = current in (MenuStateValue.WEAPONS_VENDOR, MenuStateValue.MOD_VENDOR)

        if is_vendor and not was_vendor:
            self._log(f"[RAC] MenuState: vendor opened ({current.name}).")
            vendor = self._vendor_for(current)
            if vendor is None:
                return
            vendor.activate()
            vendor.on_menu_open()
            if self._planet is not None:
                if current == MenuStateValue.WEAPONS_VENDOR:
                    self._planet.on_weapon_vendor_open()
                else:
                    self._planet.on_mod_vendor_open()
            self.set_menu(current)
        elif was_vendor and not is_vendor:
            self._log(f"[RAC] MenuState: vendor closed ({prev.name} → {current.name}).")
            vendor = self._vendor_for(prev)
            if vendor is not None:
                vendor.on_menu_close()
                vendor.deactivate()
            if self._planet is not None:
                self._planet.on_menu_close()

    @property
    def is_vendor(self) -> bool:
        return self.current in (MenuStateValue.WEAPONS_VENDOR, MenuStateValue.MOD_VENDOR)

    @property
    def is_weapons_vendor(self) -> bool:
        return self.current == MenuStateValue.WEAPONS_VENDOR

    @property
    def is_mod_vendor(self) -> bool:
        return self.current == MenuStateValue.MOD_VENDOR

    @property
    def is_pause_menu(self) -> bool:
        return self.current == MenuStateValue.PAUSE_MENU

    @property
    def is_planet_menu(self) -> bool:
        return self.current == MenuStateValue.PLANET_MENU

    @property
    def is_quick_select_menu(self) -> bool:
        return self.current == MenuStateValue.QUICK_SELECT_MENU

    def __repr__(self) -> str:
        return f"MenuState(current={self.current.name})"
