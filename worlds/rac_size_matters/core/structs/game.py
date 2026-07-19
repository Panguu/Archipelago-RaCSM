from __future__ import annotations

import ctypes

from .base import MemoryStruct

PLANET_PROGRESS_BASE = 0x21F4C661

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
    BASE_ADDRESS = 0x21F4B364
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
    BASE_ADDRESS = 0x21F4B45A
    _pack_ = 1
    _fields_ = [
        ("unlocked", ctypes.c_uint8),
        ("equipped", ctypes.c_uint8),
    ]


class VendorVisibilityStruct(MemoryStruct):

    BASE_ADDRESS = 0
    _pack_ = 1
    _fields_ = [("visibility", ctypes.c_int16)]

# Rests at TRANSITION_GATE_IDLE (0x000000FF). Any change away from idle means a
# level transition has started — writes must stop immediately. It passes through
# TRANSITION_GATE_ARRIVED (0x00000100) once the new planet is known (safe to swap
# the address map then — that's a local bookkeeping change, not a memory write).
# Returning to idle means the transition is fully settled and writes may resume.
_TRANSITION_GATE_ADDR: int = 0x1EDDAD4

TRANSITION_GATE_IDLE:    int = 0x000000FF
TRANSITION_GATE_ARRIVED: int = 0x00000100


class TransitionGateStruct(MemoryStruct):
    BASE_ADDRESS = _TRANSITION_GATE_ADDR
    _pack_ = 1
    _fields_ = [("value", ctypes.c_uint32)]


# Sits right beside the gate (+0x10) and holds the planet ID being loaded —
# read this once the gate reaches TRANSITION_GATE_ARRIVED, instead of
# CURRENT_PLANET_ADDRESS, which isn't reliable yet during the load itself.
_LOADING_PLANET_ADDR: int = 0x1EDDAE4


class LoadingPlanetStruct(MemoryStruct):
    BASE_ADDRESS = _LOADING_PLANET_ADDR
    _pack_ = 1
    _fields_ = [("value", ctypes.c_uint32)]
