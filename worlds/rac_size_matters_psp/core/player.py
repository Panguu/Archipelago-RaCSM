from __future__ import annotations

import struct
from enum import IntEnum
from typing import TYPE_CHECKING

from .address_maps import PLAYER_ADDRS

if TYPE_CHECKING:
    from ..pypsp import Psp

class PlayerMovementState(IntEnum):
    Alive           = 0x00
    FishDeath       = 0x29
    FadeDeath       = 0x2A
    Electrocution   = 0x2B
    VoidDeath       = 0x2C
    UnknownDeath    = 0x2D
    SwimDeath       = 0x2E
    MysteriousDeath = 0x2F
    Pickup          = 0x43

    @staticmethod
    def is_dead(state: int) -> bool:
        return PlayerMovementState.FishDeath <= state <= PlayerMovementState.MysteriousDeath


class PlayerMovementSlot:
    """Psp-backed accessor for the player's movement-state byte."""

    def __get__(self, instance, owner) -> PlayerMovementState | None:
        if instance is None or instance.movement_addr is None:
            return None
        try:
            return PlayerMovementState(instance.pine.read_int8(instance.movement_addr))
        except ValueError:
            return PlayerMovementState.Alive

    def __set__(self, instance, value: PlayerMovementState) -> None:
        if instance.movement_addr is None:
            return
        instance.pine.write_int8(instance.movement_addr, int(value))

    def __delete__(self, instance) -> None:
        if instance.movement_addr is None:
            return
        instance.pine.write_int8(instance.movement_addr, int(PlayerMovementState.Alive))


class PlayerHealthSlot:
    """Psp-backed accessor for the player's health (4-byte float32 on PSP)."""

    def __get__(self, instance, owner) -> float | None:
        if instance is None or instance.health_addr is None:
            return None
        return struct.unpack("<f", instance.pine.read_bytes(instance.health_addr, 4))[0]

    def __set__(self, instance, value: float) -> None:
        if instance.health_addr is None:
            return
        instance.pine.write_bytes(instance.health_addr, struct.pack("<f", value))

    def __delete__(self, instance) -> None:
        if instance.health_addr is None:
            return
        instance.pine.write_bytes(instance.health_addr, struct.pack("<f", 0.0))


class PlayerInventory:
    """Psp-backed live accessor for player movement/health, replacing PlayerState.

    Planet-dependent: both addresses live on a per-planet struct, so call
    set_base(planet_id) whenever the loaded planet changes, same as the other
    planet-dependent inventories (weapons/vendor/menu).
    """

    movement_state = PlayerMovementSlot()
    health         = PlayerHealthSlot()

    def __init__(self, pine: Psp) -> None:
        self.pine = pine
        self.movement_addr: int | None = None
        self.health_addr:   int | None = None

    def set_base(self, planet_id: int) -> None:
        addrs = PLAYER_ADDRS.get(planet_id)
        self.movement_addr = addrs[0] if addrs else None
        self.health_addr   = addrs[1] if addrs else None

    @property
    def is_dead(self) -> bool:
        state = self.movement_state
        return state is not None and PlayerMovementState.is_dead(int(state))

    @property
    def is_picking_up(self) -> bool:
        return self.movement_state == PlayerMovementState.Pickup

    def __repr__(self) -> str:
        return f"PlayerInventory(movement={self.movement_state}, health={self.health})"
