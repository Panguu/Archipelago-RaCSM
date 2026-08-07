from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from ..constants import Rac5Traps
from .address_maps import (
    BRIGHTNESS_ADDRESS,
    CHEATS,
    CURRENT_PLANET_ADDRESS,
    DREAMTIME_EFFECT,
    NEW_PLANET_START_LOAD_ADDR,
)

if TYPE_CHECKING:
    from ..pypine import Pine

# Direct memory-flag traps: write 1 to activate, write 0 to revert.
_DIRECT_ADDRESSES: dict[str, int] = {
    Rac5Traps.TRAP_FEVERDREAMTIME: DREAMTIME_EFFECT,
    Rac5Traps.TRAP_BRIGHTNESS:     BRIGHTNESS_ADDRESS,
}

# Cheat-flag traps: bits OR'd into CHEATS (0x21F4C440) so multiple cheat traps
# can be active at once; reverted by clearing only this trap's bit.
MIRROR_LEVEL_CHEAT_BIT:     int = 0x10
REVERSE_CONTROLS_CHEAT_BIT: int = 0x40
WEAPON_SWITCHING_CHEAT_BIT: int = 0x80

_CHEAT_BITS: dict[str, int] = {
    Rac5Traps.TRAP_MIRROR_LEVEL:     MIRROR_LEVEL_CHEAT_BIT,
    Rac5Traps.TRAP_REVERSE_CONTROLS: REVERSE_CONTROLS_CHEAT_BIT,
    Rac5Traps.TRAP_WEAPON_SWITCHING: WEAPON_SWITCHING_CHEAT_BIT,
}

# Default seconds each trap stays active before auto-reverting; also the
# TrapDuration option's default. Never mutated — _trap_durations below is
# the live copy activate_trap() reads from.
TRAP_DURATIONS: dict[str, float] = {
    Rac5Traps.TRAP_FEVERDREAMTIME:   70,
    Rac5Traps.TRAP_BRIGHTNESS:       70,
    Rac5Traps.TRAP_MIRROR_LEVEL:     70,
    Rac5Traps.TRAP_REVERSE_CONTROLS: 70,
    Rac5Traps.TRAP_WEAPON_SWITCHING: 70,
    # Reset Level is instantaneous (see activate_trap()) — this entry exists
    # only so it gets an item id (items.py's TRAP_ITEM_TABLE enumerates this
    # dict) and shows up in the TrapWeight/TrapDuration options. Appended
    # last so existing traps' enumerated item ids don't shift.
    Rac5Traps.TRAP_RESET_LEVEL:      1,
}

ALL_TRAPS: frozenset[str] = frozenset(TRAP_DURATIONS)

# Live durations activate_trap() uses — copy of the defaults above,
# overwritten once from slot_data on connect (see set_trap_durations()).
_trap_durations: dict[str, float] = dict(TRAP_DURATIONS)


def set_trap_durations(overrides: dict[str, float]) -> None:
    """Apply the TrapDuration option's per-trap seconds, called once by the
    client right after connecting. Only overwrites known trap names —
    anything absent/unrecognized keeps its existing (default) duration."""
    for trap_name, seconds in overrides.items():
        if trap_name in _trap_durations:
            _trap_durations[trap_name] = seconds

# Per-trap-name bookkeeping so repeated activations of the same trap extend
# the revert deadline instead of racing independent timers.
_active_deadlines: dict[str, float] = {}
_revert_handles: dict[str, asyncio.TimerHandle] = {}


def activate_trap(pine: Pine, trap_name: str) -> None:
    """Activate a trap by name and schedule it to automatically revert.

    Re-activating a still-active trap extends its revert deadline by another
    full duration (stacking) rather than reverting at the first deadline.
    Unknown/unimplemented traps are silently ignored.
    """
    if trap_name == Rac5Traps.TRAP_RESET_LEVEL:
        # One-shot, no revert: force-reload whatever planet the player is
        # currently on by writing its own id back into the same forced-load
        # address the Giant Clank redirect and menu travel use (see
        # planets.py's check_giant_clank() and NEW_PLANET_START_LOAD_ADDR).
        planet_id = pine.read_int8(CURRENT_PLANET_ADDRESS)
        pine.write_int32(NEW_PLANET_START_LOAD_ADDR, planet_id)
        return

    duration = _trap_durations.get(trap_name)
    if duration is None:
        return

    loop = asyncio.get_event_loop()
    now = loop.time()
    new_deadline = max(_active_deadlines.get(trap_name, now), now) + duration
    _active_deadlines[trap_name] = new_deadline

    existing_handle = _revert_handles.pop(trap_name, None)
    if existing_handle is not None:
        existing_handle.cancel()

    if trap_name in _DIRECT_ADDRESSES:
        address = _DIRECT_ADDRESSES[trap_name]
        pine.write_int8(address, 1)

        def _revert() -> None:
            _active_deadlines.pop(trap_name, None)
            _revert_handles.pop(trap_name, None)
            pine.write_int8(address, 0)

        _revert_handles[trap_name] = loop.call_at(new_deadline, _revert)
        return

    bit = _CHEAT_BITS.get(trap_name)
    if bit is None:
        return
    current = pine.read_int8(CHEATS)
    pine.write_int8(CHEATS, current | bit)

    def _revert() -> None:
        _active_deadlines.pop(trap_name, None)
        _revert_handles.pop(trap_name, None)
        latest = pine.read_int8(CHEATS)
        pine.write_int8(CHEATS, latest & ~bit)

    _revert_handles[trap_name] = loop.call_at(new_deadline, _revert)


def reconcile_traps(pine: Pine) -> None:
    """Clear any trap effect active in game memory that this process has no
    bookkeeping for (i.e. not in _active_deadlines) — called whenever PINE
    (re)connects.

    _active_deadlines is in-memory only, so a client restart (or a PINE
    drop racing a revert write) can leave a bit stuck in-game with no timer
    left to ever clear it; this catches that case. Traps that still have a
    live deadline are left alone — their own revert timer will fire normally.
    """
    for trap_name, address in _DIRECT_ADDRESSES.items():
        if trap_name in _active_deadlines:
            continue
        if pine.read_int8(address):
            pine.write_int8(address, 0)

    clear_mask = 0
    for trap_name, bit in _CHEAT_BITS.items():
        if trap_name not in _active_deadlines:
            clear_mask |= bit
    if clear_mask:
        current = pine.read_int8(CHEATS)
        cleared = current & ~clear_mask
        if cleared != current:
            pine.write_int8(CHEATS, cleared)
