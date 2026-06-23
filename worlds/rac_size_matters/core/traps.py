from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from ..constants import RACSMLOCATION
from .address_maps import BRIGHTNESS_ADDRESS, CHEATS, DREAMTIME_EFFECT

if TYPE_CHECKING:
    from ..pypine.pypine.pine import Pine

# ── Data ────────────────────────────────────────────────────────────────────────
# TRAP_RESET_LEVEL is intentionally absent below — not functional yet.

# Direct memory-flag traps: write 1 to activate, write 0 to revert.
_DIRECT_ADDRESSES: dict[str, int] = {
    RACSMLOCATION.TRAP_FEVERDREAMTIME: DREAMTIME_EFFECT,
    RACSMLOCATION.TRAP_BRIGHTNESS:     BRIGHTNESS_ADDRESS,
}

# Cheat-flag traps: bits OR'd into CHEATS (0x21F4C440) so multiple cheat traps
# can be active at once; reverted by clearing only this trap's bit.
MIRROR_LEVEL_CHEAT_BIT:     int = 0x10
REVERSE_CONTROLS_CHEAT_BIT: int = 0x40
WEAPON_SWITCHING_CHEAT_BIT: int = 0x80

_CHEAT_BITS: dict[str, int] = {
    RACSMLOCATION.TRAP_MIRROR_LEVEL:     MIRROR_LEVEL_CHEAT_BIT,
    RACSMLOCATION.TRAP_REVERSE_CONTROLS: REVERSE_CONTROLS_CHEAT_BIT,
    RACSMLOCATION.TRAP_WEAPON_SWITCHING: WEAPON_SWITCHING_CHEAT_BIT,
}

# Seconds each trap stays active before automatically reverting.
TRAP_DURATIONS: dict[str, float] = {
    RACSMLOCATION.TRAP_FEVERDREAMTIME:   70,
    RACSMLOCATION.TRAP_BRIGHTNESS:       70,
    RACSMLOCATION.TRAP_MIRROR_LEVEL:     70,
    RACSMLOCATION.TRAP_REVERSE_CONTROLS: 70,
    RACSMLOCATION.TRAP_WEAPON_SWITCHING: 70,
}

ALL_TRAPS: frozenset[str] = frozenset(TRAP_DURATIONS)


# ── Activation ───────────────────────────────────────────────────────────────────

def activate_trap(pine: Pine, trap_name: str) -> None:
    """Activate a trap by name and schedule it to automatically revert.

    Unknown/unimplemented traps (e.g. Reset Level) are silently ignored.
    """
    duration = TRAP_DURATIONS.get(trap_name)
    if duration is None:
        return

    if trap_name in _DIRECT_ADDRESSES:
        address = _DIRECT_ADDRESSES[trap_name]
        pine.write_int8(address, 1)
        asyncio.get_event_loop().call_later(duration, lambda: pine.write_int8(address, 0))
        return

    bit = _CHEAT_BITS.get(trap_name)
    if bit is None:
        return
    current = pine.read_int8(CHEATS)
    pine.write_int8(CHEATS, current | bit)

    def _revert() -> None:
        latest = pine.read_int8(CHEATS)
        pine.write_int8(CHEATS, latest & ~bit)

    asyncio.get_event_loop().call_later(duration, _revert)
