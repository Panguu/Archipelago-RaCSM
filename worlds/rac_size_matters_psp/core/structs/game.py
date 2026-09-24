from __future__ import annotations

import ctypes

from .base import MemoryStruct

PLANET_PROGRESS_BASE = 0x088C2621  # computed, in-range — PS2 was 0x21F4C661, not yet live-verified

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
    # CONFIRMED live — the original PS2-offset guess (0x088C1324) read as
    # garbage. The real struct sits at 0x088C1344, right after ARMOUR_BASE's
    # 13-byte struct (0x088C1334-0x088C1340) plus 3 bytes of alignment
    # padding. Live read on a real save returned 0x10, 0x08, 0x0A, 0x02,
    # 0x04, 0, 0, 0 — every non-zero value is a valid entry in vendor.py's
    # WEAPON_VENDOR_IDS table (hypershot, shock_rocket, scorcher, lacerator,
    # acid_bomb_glove), the same ID scheme used elsewhere in this game, with
    # the remaining 3 wheel slots empty. PS2 was 0x21F4B364.
    BASE_ADDRESS = 0x088C1344
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
    BASE_ADDRESS = 0x088C141A  # CONFIRMED (user-verified: 0x088C141A is the unlock address, 0x088C141B is the currently-active skin) — PS2 was 0x21F4B45A
    _pack_ = 1
    _fields_ = [
        ("unlocked", ctypes.c_uint8),
        ("equipped", ctypes.c_uint8),
    ]


class VendorVisibilityStruct(MemoryStruct):

    BASE_ADDRESS = 0
    _pack_ = 1
    _fields_ = [("visibility", ctypes.c_int16)]

# CONFIRMED live on PSP (user-supplied, live-verified: idle reads exactly
# 0xFFFFFFFF). Rests at TRANSITION_GATE_IDLE. Any change away from idle means
# a level transition has started — writes must stop immediately. Unlike PS2,
# there's no distinct "arrived" value to watch for on PSP — the destination
# planet id at _LOADING_PLANET_ADDR isn't valid until ~5 seconds after the
# gate leaves idle, so the transition handler waits out that window on a
# wall-clock timer before reading it, rather than polling for a specific gate
# value. Returning to idle means the transition is fully settled.
_TRANSITION_GATE_ADDR: int = 0x088C0744  # CONFIRMED live — PS2 was 0x1EDDAD4 (no longer a valid PS2->PSP offset relationship; found via direct discovery, not translation)

TRANSITION_GATE_IDLE: int = 0xFFFFFFFF
# No PSP equivalent of PS2's TRANSITION_GATE_ARRIVED sentinel — see the
# gate-address comment above. Kept as a named constant only for any leftover
# PS2-shaped reference; the PSP transition path (core/planets.py's
# check_transition()) does not use it.
TRANSITION_GATE_ARRIVED: int = 0x00000100


class TransitionGateStruct(MemoryStruct):
    BASE_ADDRESS = _TRANSITION_GATE_ADDR
    _pack_ = 1
    _fields_ = [("value", ctypes.c_uint32)]


# CONFIRMED live on PSP (user-supplied) — sits +0x04 after the gate (not
# PS2's +0x10). Only meaningful ~5 seconds after the gate leaves idle; at
# rest it can hold a stale value from a previous transition, not the
# currently-loaded planet (use CURRENT_PLANET_ADDRESS for that instead).
_LOADING_PLANET_ADDR: int = 0x088C0748  # CONFIRMED live — PS2 was 0x1EDDAE4


class LoadingPlanetStruct(MemoryStruct):
    BASE_ADDRESS = _LOADING_PLANET_ADDR
    _pack_ = 1
    _fields_ = [("value", ctypes.c_uint32)]
