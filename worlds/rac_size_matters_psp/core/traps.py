"""PSP trap effects serviced by the locked gameplay poll, never timer callbacks."""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from weakref import WeakKeyDictionary

from ..constants import Rac5Traps
from ..data.traps import TRAP_DURATIONS as _DEFAULT_DURATIONS
from .address_maps import CHEATS
from .structs.game import TransitionGateStruct, TRANSITION_GATE_IDLE

MIRROR_LEVEL_CHEAT_BIT = 0x10
REVERSE_CONTROLS_CHEAT_BIT = 0x40
WEAPON_SWITCHING_CHEAT_BIT = 0x80
_CHEAT_BITS = {
    Rac5Traps.TRAP_MIRROR_LEVEL: MIRROR_LEVEL_CHEAT_BIT,
    Rac5Traps.TRAP_REVERSE_CONTROLS: REVERSE_CONTROLS_CHEAT_BIT,
    Rac5Traps.TRAP_WEAPON_SWITCHING: WEAPON_SWITCHING_CHEAT_BIT,
}
# The remaining PS2 effects need independently verified PSP addresses/hooks.
TRAP_DURATIONS = {name: _DEFAULT_DURATIONS[name] for name in _CHEAT_BITS}
ALL_TRAPS = frozenset(TRAP_DURATIONS)
_MASK = sum(_CHEAT_BITS.values())


@dataclass
class _TrapState:
    durations: dict[str, float] = field(default_factory=lambda: dict(TRAP_DURATIONS))
    deadlines: dict[str, float] = field(default_factory=dict)


_states = WeakKeyDictionary()
_default_durations = dict(TRAP_DURATIONS)


def _state(memory):
    if memory not in _states:
        _states[memory] = _TrapState(dict(_default_durations))
    return _states[memory]


def set_trap_durations(overrides, memory=None):
    """Use the PS2 option defaults; reset omitted values for every new seed."""
    durations = dict(TRAP_DURATIONS)
    for name, value in overrides.items():
        if name not in durations:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f'Invalid duration for {name}')
        durations[name] = float(value)
    if memory is None:
        _default_durations.clear()
        _default_durations.update(durations)
    else:
        state = _state(memory)
        state.durations = durations
        state.deadlines.clear()


def activate_trap(memory, trap_name):
    """Apply before acknowledging receipt; a failed write leaves the item retryable."""
    if trap_name not in ALL_TRAPS:
        return
    state = _state(memory)
    duration = state.durations[trap_name]
    if duration == 0:
        return
    memory.validate_session()
    if memory.read_int32(TransitionGateStruct.BASE_ADDRESS) != TRANSITION_GATE_IDLE:
        raise RuntimeError('Trap delivery deferred until the planet finishes loading')
    now = time.monotonic()
    deadline = max(state.deadlines.get(trap_name, now), now) + duration
    current = memory.read_int8(CHEATS)
    memory.write_int8(CHEATS, current | _CHEAT_BITS[trap_name])
    state.deadlines[trap_name] = deadline


def reconcile_traps(memory):
    """Call only with the PSP lock held and a loaded gameplay session.

    Timers continue across loading/disconnection, but no memory writes occur
    until polling resumes. Reapply live effects after a level/save reload and
    clear expired effects without touching unrelated cheat flags.
    """
    state = _state(memory)
    if memory.read_int32(TransitionGateStruct.BASE_ADDRESS) != TRANSITION_GATE_IDLE:
        return
    now = time.monotonic()
    active = {name: deadline for name, deadline in state.deadlines.items() if deadline > now}
    flags = sum(_CHEAT_BITS[name] for name in active)
    current = memory.read_int8(CHEATS)
    desired = (current & ~_MASK) | flags
    if current != desired:
        memory.write_int8(CHEATS, desired)
    state.deadlines = active


def suspend_traps(memory):
    """Clear effects on a clean disconnect, retaining deadlines for reconnect."""
    current = memory.read_int8(CHEATS)
    if current & _MASK:
        memory.write_int8(CHEATS, current & ~_MASK)
