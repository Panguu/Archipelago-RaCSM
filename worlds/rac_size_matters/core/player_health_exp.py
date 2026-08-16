from __future__ import annotations

from typing import TYPE_CHECKING

from .address_maps import PLAYER_HEALTH_EXP

if TYPE_CHECKING:
    from ..pypine import Pine

# Nanotech level runs 1-75; max_health itself is the level number (e.g. a
# reading of 6.0 means Nanotech Level 6) — no separate threshold table.
_MIN_NANOTECH_LEVEL = 1
_MAX_NANOTECH_LEVEL = 75


def _level_from_max_health(max_health: float) -> int | None:
    """max_health read as the Nanotech level directly, or None if the
    rounded reading falls outside the valid 1-75 range (unbound/garbage
    read, e.g. during a load)."""
    level = round(max_health)
    if _MIN_NANOTECH_LEVEL <= level <= _MAX_NANOTECH_LEVEL:
        return level
    return None


class PlayerHealthExpInventory:
    """Pine-backed accessor + gain-multiplier tracking for the player's
    Nanotech (health) EXP counter (global fixed address, no per-planet
    base). Mirrors PlayerBoltInventory.

    Also tracks Nanotech Level location checks, but those are driven by
    PlayerInventory.max_health (see check_level()) rather than by this
    class's own EXP counter — the EXP counter is only what the multiplier
    boosts to speed up the game's own leveling."""

    def __init__(self, pine: Pine) -> None:
        self.pine = pine
        # 1 = no boost (default/off); set directly by the client from slot_data.
        self.multiplier: int = 1
        # Last-seen raw value, used to diff this tick's gain — see apply_boost().
        self._prev: int | None = None
        # Last-seen Nanotech level derived from max_health, used to detect
        # newly-reached levels — see check_level(). Starts at 5 (the
        # player's default starting level, never itself a location) so the
        # very first call after connecting reports every level already
        # reached (6 up to current) same as WeaponInventory.check()'s
        # "levels" list does for weapons on first observation — safe because
        # send_location() no-ops for anything already in checked_locations.
        self._last_level: int = 5

    def get(self) -> int:
        return self.pine.read_int32(PLAYER_HEALTH_EXP)

    def set(self, value: int) -> None:
        self.pine.write_int32(PLAYER_HEALTH_EXP, value)

    def rebaseline(self, value: int | None = None) -> None:
        """Re-sync the baseline apply_boost() diffs against, without
        boosting anything. Callers that write PLAYER_HEALTH_EXP directly
        must call this right after, or apply_boost()'s next tick would
        multiply that grant too."""
        self._prev = value if value is not None else self.get()

    def apply_boost(self) -> None:
        """Inflate ordinary Nanotech EXP gain by multiplier, every tick, by
        diffing against the last raw reading."""
        current = self.get()
        if self._prev is None:
            self._prev = current
            return
        diff = current - self._prev
        if diff <= 0:
            self._prev = current
            return
        if self.multiplier > 1:
            boosted = self._prev + diff * self.multiplier
            self.set(boosted)
            self._prev = boosted
        else:
            self._prev = current

    def check_level(self, max_health: float | None) -> list[str]:
        """Given the current planet's PlayerInventory.max_health, return the
        Nanotech Level location names newly reached since the last call (in
        ascending order, so a multi-level jump — including the very first
        call after connecting, if the player is already above level 5 —
        doesn't skip any of their locations; same convention as
        WeaponInventory.check()'s "levels" list).

        No-op (returns []) while max_health is None (unbound, e.g. no planet
        loaded) or its rounded value falls outside the valid 1-75 range."""
        if max_health is None:
            return []
        current_level = _level_from_max_health(max_health)
        if current_level is None:
            return []
        if current_level <= self._last_level:
            return []
        newly = [
            f"Nanotech Level: {lvl}"
            for lvl in range(self._last_level + 1, current_level + 1)
            if lvl >= 6
        ]
        self._last_level = current_level
        return newly

    def __repr__(self) -> str:
        return f"PlayerHealthExpInventory(prev={self._prev}, multiplier={self.multiplier})"
