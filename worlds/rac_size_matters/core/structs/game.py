from __future__ import annotations

import ctypes

from ..address_maps import (
    CHALLENGE_MODE_BASE,
    LOADING_PLANET_ADDRESS,
    PLANET_PROGRESS_BASE,
    QUICK_SELECT_BASE,
    SKIN_BASE,
    TRANSITION_GATE_ADDRESS,
)
from .base import MemoryStruct


class PlanetProgressStruct(MemoryStruct):

    BASE_ADDRESS = PLANET_PROGRESS_BASE
    _pack_ = 1
    _fields_ = [
        ("pokitaru",      ctypes.c_uint8),
        ("ryllus",        ctypes.c_uint8),
        ("kalidon",       ctypes.c_uint8),
        ("metalis",       ctypes.c_uint8),
        ("dreamtime",     ctypes.c_uint8),
        ("outpost_omega", ctypes.c_uint8),
        ("challax",       ctypes.c_uint8),
        ("dayni_moon",    ctypes.c_uint8),
        ("inside_clank",  ctypes.c_uint8),
        ("quodrona",      ctypes.c_uint8),
    ]

    PLANET_ORDER: tuple[str, ...] = (
        "pokitaru", "ryllus", "kalidon", "metalis", "dreamtime",
        "outpost_omega", "challax", "dayni_moon", "inside_clank", "quodrona",
    )
    PLANET_NAME_ORDER: tuple[str, ...] = tuple(n.upper() for n in PLANET_ORDER)


class QuickSelectStruct(MemoryStruct):
    BASE_ADDRESS = QUICK_SELECT_BASE
    _pack_ = 1
    _fields_ = [
        ("right",         ctypes.c_uint32),
        ("top_right",     ctypes.c_uint32),
        ("top_middle",    ctypes.c_uint32),
        ("top_left",      ctypes.c_uint32),
        ("left",          ctypes.c_uint32),
        ("bottom_left",   ctypes.c_uint32),
        ("bottom_middle", ctypes.c_uint32),
        ("bottom_right",  ctypes.c_uint32),
    ]

    SLOT_ORDER: tuple[str, ...] = (
        "right", "top_right", "top_middle", "top_left",
        "left", "bottom_left", "bottom_middle", "bottom_right",
    )


class SkinStruct(MemoryStruct):
    # +0x00 unlocked — bitmask; bit N = skin N is available.
    # +0x01 equipped — ID of the skin Ratchet is currently wearing.
    BASE_ADDRESS = SKIN_BASE
    _pack_ = 1
    _fields_ = [
        ("unlocked", ctypes.c_uint8),
        ("equipped", ctypes.c_uint8),
    ]


class ChallengeModeStruct(MemoryStruct):
    # Written once on connect from slot_data's challenge_mode — mirrors the AP
    # option into the game's own Challenge Mode (New Game Plus) tier.
    BASE_ADDRESS = CHALLENGE_MODE_BASE
    _pack_ = 1
    _fields_ = [("tier", ctypes.c_uint8)]


class VendorVisibilityStruct(MemoryStruct):

    BASE_ADDRESS = 0
    _pack_ = 1
    _fields_ = [("visibility", ctypes.c_int16)]

# Rests at TRANSITION_GATE_IDLE; any change away from idle means a transition has
# started and writes must stop until it returns to idle (fully settled).
TRANSITION_GATE_IDLE:    int = 0x000000FF
TRANSITION_GATE_ARRIVED: int = 0x00000100


class TransitionGateStruct(MemoryStruct):
    BASE_ADDRESS = TRANSITION_GATE_ADDRESS
    _pack_ = 1
    _fields_ = [("value", ctypes.c_uint32)]


# Sits right beside the gate (+0x10) and holds the planet ID being loaded — read
# this once the gate reaches TRANSITION_GATE_ARRIVED; CURRENT_PLANET_ADDRESS isn't reliable yet.
class LoadingPlanetStruct(MemoryStruct):
    BASE_ADDRESS = LOADING_PLANET_ADDRESS
    _pack_ = 1
    _fields_ = [("value", ctypes.c_uint32)]
