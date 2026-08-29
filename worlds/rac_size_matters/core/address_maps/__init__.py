"""Platform address map. Import from here — not from us_addresses.py directly.
Set RACSM_PLATFORM=psp in the environment to select PSP addresses instead of US PS2."""
import os as _os

_platform = _os.environ.get("RACSM_PLATFORM", "us").lower()

if _platform == "psp":
    from .psp import *  # type: ignore[assignment]  # noqa: F403  # Not yet implemented
else:
    from .us_addresses import *  # noqa: F403

# Legacy dict views derived from PLANET_ADDRESSES — computed once here instead
# of being redefined in every platform's address file.
PLAYER_ADDRS: dict[int, tuple[int, int]] = {
    pid: (p.player_state, p.player_health) for pid, p in PLANET_ADDRESSES.items()
}

MENU_ADDR_BY_PLANET_ID: dict[int, int] = {
    pid: p.menu for pid, p in PLANET_ADDRESSES.items() if p.menu is not None
}

MAX_HEALTH_ADDR_BY_PLANET_ID: dict[int, int] = {
    pid: p.max_health for pid, p in PLANET_ADDRESSES.items() if p.max_health is not None
}

WEAPON_ARRAY_BASE_BY_PLANET: dict[int, int] = {
    pid: p.weapon_array for pid, p in PLANET_ADDRESSES.items() if p.weapon_array is not None
}

PLANET_MISSION_ADDRESSES: dict[str, int] = {
    p.name: p.mission for p in PLANET_ADDRESSES.values() if p.mission is not None
}

SMALL_TEXT_BOX_BY_PLANET: dict[int, int] = {
    pid: p.small_text_box for pid, p in PLANET_ADDRESSES.items() if p.small_text_box is not None
}

MULTI_LINE_TEXT_BOX_BY_PLANET: dict[int, int] = {
    pid: p.multi_line_text_box for pid, p in PLANET_ADDRESSES.items() if p.multi_line_text_box is not None
}

# (apply, cycle_state, current_weapon, stored_weapon) — only present for a
# planet once all four addresses are known (Pokitaru only, for now).
WEAPON_CYCLER_ADDRS_BY_PLANET: dict[int, tuple[int, int, int, int]] = {
    pid: (p.weapon_cycler_apply, p.weapon_cycler_state, p.weapon_cycler_current, p.weapon_cycler_stored)
    for pid, p in PLANET_ADDRESSES.items()
    if p.weapon_cycler_apply is not None and p.weapon_cycler_state is not None
    and p.weapon_cycler_current is not None and p.weapon_cycler_stored is not None
}
