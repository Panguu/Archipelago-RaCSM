from __future__ import annotations

import ctypes

from ...interface_orchestrator.structs.base import MemoryStruct
from ..address_maps import (
    CONTROLLER_BUTTONS_ADDRESS,
    CONTROLLER_PAUSE_SELECT_ADDRESS,
    NEW_PLANET_START_LOAD_ADDR,
    PLANET_MISSION_ADDRESSES,
    PLAYER_BOLT_COUNT,
)

# ── Player ─────────────────────────────────────────────────────────────────────

class PlayerMovementStruct(MemoryStruct):

    BASE_ADDRESS = 0
    _pack_ = 1
    _fields_ = [
        ("state", ctypes.c_uint8),
    ]

def make_player_movement_cls(planet_name: str, movement_addr: int) -> type[PlayerMovementStruct]:
    return type(
        f"PlayerMovementStruct_{planet_name}",
        (PlayerMovementStruct,),
        {"BASE_ADDRESS": movement_addr},
    )


# ── Game status / controller ───────────────────────────────────────────────────

class GameStatusStruct(MemoryStruct):

    BASE_ADDRESS = PLAYER_BOLT_COUNT
    _pack_ = 1
    _fields_ = [
        ("bolt_count",     ctypes.c_uint32),
        ("current_planet", ctypes.c_uint8),
        ("_pad1",          ctypes.c_uint8 * 3),
        ("planet_load",    ctypes.c_uint8),
        ("_pad2",          ctypes.c_uint8 * 7),
        ("challenge_mode", ctypes.c_uint8),
    ]

class ControllerStruct(MemoryStruct):

    BASE_ADDRESS = CONTROLLER_PAUSE_SELECT_ADDRESS
    _pack_ = 1
    _fields_ = [
        ("pause_select", ctypes.c_uint8),
        ("buttons",      ctypes.c_uint8),
    ]

    assert BASE_ADDRESS + 1 == CONTROLLER_BUTTONS_ADDRESS


# ── Menu ───────────────────────────────────────────────────────────────────────

class MenuStruct(MemoryStruct):

    BASE_ADDRESS = 0
    _pack_ = 1
    _fields_ = [
        ("state", ctypes.c_uint8),
    ]

class PreloadMenuStruct(MemoryStruct):

    BASE_ADDRESS = 0
    _pack_ = 1
    _fields_ = [
        ("state", ctypes.c_uint8),
    ]

def make_menu_cls(planet_name: str, menu_addr: int) -> type[MenuStruct]:
    return type(
        f"MenuStruct_{planet_name}",
        (MenuStruct,),
        {"BASE_ADDRESS": menu_addr},
    )

def make_preload_menu_cls(planet_name: str, preload_addr: int) -> type[PreloadMenuStruct]:
    return type(
        f"PreloadMenuStruct_{planet_name}",
        (PreloadMenuStruct,),
        {"BASE_ADDRESS": preload_addr},
    )


# ── Planet load ────────────────────────────────────────────────────────────────

class PlanetLoadStruct(MemoryStruct):
    """Two consecutive uint32 values that signal planet load lifecycle events.

    start_load    (0x21F4A744): becomes non-zero when a new planet begins loading.
    load_complete (0x21F4A748): becomes non-zero when loading has finished.
    """

    BASE_ADDRESS = NEW_PLANET_START_LOAD_ADDR
    _pack_ = 1
    _fields_ = [
        ("start_load",    ctypes.c_uint32),
        ("load_complete", ctypes.c_uint32),
    ]


# ── Planet progress ────────────────────────────────────────────────────────────

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


# ── Quick select ───────────────────────────────────────────────────────────────

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


# ── Skins ──────────────────────────────────────────────────────────────────────

class SkinStruct(MemoryStruct):
    # +0x00 unlocked — bitmask; bit N = skin N is available.
    # +0x01 equipped — ID of the skin Ratchet is currently wearing.
    BASE_ADDRESS = 0x21F4B45A
    _pack_ = 1
    _fields_ = [
        ("unlocked", ctypes.c_uint8),
        ("equipped", ctypes.c_uint8),
    ]


# ── Display text ───────────────────────────────────────────────────────────────

class CountdownTimerStruct(MemoryStruct):

    BASE_ADDRESS = 0
    _pack_ = 1
    _fields_ = [("timer", ctypes.c_float)]

class VendorVisibilityStruct(MemoryStruct):

    BASE_ADDRESS = 0
    _pack_ = 1
    _fields_ = [("visibility", ctypes.c_int16)]

def make_countdown_cls(planet_name: str, countdown_addr: int) -> type[CountdownTimerStruct]:
    return type(
        f"CountdownTimerStruct_{planet_name}",
        (CountdownTimerStruct,),
        {"BASE_ADDRESS": countdown_addr},
    )

def make_vendor_visibility_cls(planet_name: str, is_visible_addr: int) -> type[VendorVisibilityStruct]:
    return type(
        f"VendorVisibilityStruct_{planet_name}",
        (VendorVisibilityStruct,),
        {"BASE_ADDRESS": is_visible_addr},
    )


# ── Transition gate ────────────────────────────────────────────────────────────
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


# ── Missions ───────────────────────────────────────────────────────────────────

MISSIONS_BASE = PLANET_MISSION_ADDRESSES["Pokitaru"]  # 0x21F4B3C4


class MissionsStruct(MemoryStruct):
    """2-byte mission progress value for each planet, contiguous from Pokitaru."""

    BASE_ADDRESS = MISSIONS_BASE
    _pack_ = 1
    _fields_ = [
        ("pokitaru",        ctypes.c_uint16),  # +0x00  0x21F4B3C4
        ("ryllus",          ctypes.c_uint16),  # +0x02  0x21F4B3C6
        ("kalidon",         ctypes.c_uint16),  # +0x04  0x21F4B3C8
        ("metalis",         ctypes.c_uint16),  # +0x06  0x21F4B3CA
        ("dreamtime",       ctypes.c_uint16),  # +0x08  0x21F4B3CC
        ("outpost_omega",   ctypes.c_uint16),  # +0x0A  0x21F4B3CE
        ("challax",         ctypes.c_uint16),  # +0x0C  0x21F4B3D0
        ("dayni_moon",      ctypes.c_uint16),  # +0x0E  0x21F4B3D2
        ("inside_clank",    ctypes.c_uint16),  # +0x10  0x21F4B3D4
        ("quodrona",        ctypes.c_uint16),  # +0x12  0x21F4B3D6
        ("outpost_omega_2", ctypes.c_uint16),  # +0x14  0x21F4B3D8
    ]
