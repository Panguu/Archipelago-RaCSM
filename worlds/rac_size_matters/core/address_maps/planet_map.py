from __future__ import annotations

from ...interface_orchestrator.structs.address_map import AddressMap
from ..display_text import SmallTextBoxAddrs
from ..structs.game import (
    make_countdown_cls,
    make_menu_cls,
    make_player_movement_cls,
    make_vendor_visibility_cls,
)
from ..structs.pickups import make_gadget_struct_cls, make_weapon_struct_cls
from ..weapons import build_weapons
from .ps2 import PLANET_ADDRESSES

_TEXTBOX_BY_PLANET = {tb.planet_id: tb for tb in SmallTextBoxAddrs}

_PLANET_ID_TO_NAME: dict[int, str] = {
    pid: pa.name.replace(" ", "") for pid, pa in PLANET_ADDRESSES.items()
}


def build_planet_address_map(planet_id: int) -> AddressMap:
    planet_name = _PLANET_ID_TO_NAME.get(planet_id, f"Planet{planet_id:02X}")
    address_map = AddressMap(interface_id=f"planet_{planet_id:#04x}")

    pa = PLANET_ADDRESSES.get(planet_id)
    if pa is not None:
        address_map.register(make_player_movement_cls(planet_name, pa.player_state))

        if pa.menu is not None:
            address_map.register(make_menu_cls(planet_name, pa.menu))

        if pa.weapon_array is not None:
            weapon_addrs, gadget_addrs = build_weapons(pa.weapon_array)
            for name, addrs in weapon_addrs.items():
                address_map.register(make_weapon_struct_cls(name, addrs.base))
            for name, addrs in gadget_addrs.items():
                address_map.register(make_gadget_struct_cls(name, addrs.base))

    tb = _TEXTBOX_BY_PLANET.get(planet_id)
    if tb is not None:
        address_map.register(make_countdown_cls(planet_name, tb.countdown_timer))
        address_map.register(make_vendor_visibility_cls(planet_name, tb.message_str_pointer))

    return address_map


def build_combined_address_map(planet_id: int, global_map: AddressMap) -> AddressMap:
    combined = AddressMap(interface_id=f"combined_{planet_id:#04x}")
    for struct_cls in global_map.structs():
        combined.register(struct_cls)
    for struct_cls in build_planet_address_map(planet_id).structs():
        combined.register(struct_cls)
    return combined
