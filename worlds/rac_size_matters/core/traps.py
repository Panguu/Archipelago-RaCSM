from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from ..constants import Rac5Traps
from .address_maps import BRIGHTNESS_ADDRESS, CHEATS, DREAMTIME_EFFECT

if TYPE_CHECKING:
    from ..pypine import Pine

# TRAP_RESET_LEVEL is intentionally absent below — not functional yet.

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

# Default seconds each trap stays active before automatically reverting —
# also the TrapDuration option's own default (options.py). Never mutated;
# _trap_durations (below) is the live, possibly-slot_data-overridden copy
# activate_trap() actually reads from.
TRAP_DURATIONS: dict[str, float] = {
    Rac5Traps.TRAP_FEVERDREAMTIME:   70,
    Rac5Traps.TRAP_BRIGHTNESS:       70,
    Rac5Traps.TRAP_MIRROR_LEVEL:     70,
    Rac5Traps.TRAP_REVERSE_CONTROLS: 70,
    Rac5Traps.TRAP_WEAPON_SWITCHING: 70,
}

ALL_TRAPS: frozenset[str] = frozenset(TRAP_DURATIONS)

# Live durations activate_trap() actually uses — starts as a copy of the
# defaults above, overwritten once by the client from slot_data's
# TrapDuration option on connect (see set_trap_durations()).
_trap_durations: dict[str, float] = dict(TRAP_DURATIONS)


def set_trap_durations(overrides: dict[str, float]) -> None:
    """Apply the TrapDuration option's per-trap seconds, called once by the
    client right after connecting. Only overwrites known trap names —
    anything absent/unrecognized keeps its existing (default) duration."""
    for trap_name, seconds in overrides.items():
        if trap_name in _trap_durations:
            _trap_durations[trap_name] = seconds

# Per-trap-name bookkeeping so repeated activations of the same trap stack
# (extend the revert deadline) instead of racing independent timers, where
# the first trap's revert would fire early and cancel the effect while a
# later-activated copy is still supposed to be running.
_active_deadlines: dict[str, float] = {}
_revert_handles: dict[str, asyncio.TimerHandle] = {}


def activate_trap(pine: Pine, trap_name: str) -> None:
    """Activate a trap by name and schedule it to automatically revert.

    A trap activated again while still active extends its revert deadline by
    another full duration (e.g. two Feverdream traps in a row keep the effect
    active for 140s total) rather than reverting at the first trap's deadline.

    Unknown/unimplemented traps (e.g. Reset Level) are silently ignored.
    """
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
    """Clear any trap effect currently active in game memory that this
    client process has no record of (i.e. not in _active_deadlines) —
    called once whenever PINE (re)connects.

    _active_deadlines/_revert_handles are this process's only source of
    truth for "what's actually supposed to be active right now"; they're
    plain in-memory dicts, not persisted, so a client restart always starts
    with both empty. Game memory itself can still show a trap as active
    across that restart (or across a PINE drop/reconnect racing a revert
    timer's own write — see activate_trap()'s _revert(), which pops the
    bookkeeping before writing, so a write that fails mid-drop leaves the
    bit stuck with no bookkeeping left to retry it) — that combination is
    exactly a trap PINE has no way to ever revert on its own again, so it
    must be cleared here instead of waiting on a timer that no longer exists.

    Deliberately does not touch any trap that _does_ still have a live
    deadline (a PINE reconnect mid-trap keeps running as normal — its
    existing revert timer will still fire and clean up on schedule).
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
