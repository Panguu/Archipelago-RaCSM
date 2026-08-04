from __future__ import annotations

from typing import TYPE_CHECKING

from .address_maps import PLAYER_BOLT_COUNT

if TYPE_CHECKING:
    from pypine import Pine

# Bolt balance never exceeds this regardless of source — also imported
# directly by client/handlers.py and client/vendor.py for starting/filler
# bolt grants written outside this class.
MAX_PLAYER_BOLTS = 9_999_000


class PlayerBoltInventory:
    """Pine-backed accessor + gain-multiplier tracking for the player's
    spendable bolt count (global fixed address, no per-planet base)."""

    def __init__(self, pine: Pine) -> None:
        self.pine = pine
        # 1 = no boost (default/off); set directly by the client from slot_data.
        self.multiplier: int = 1
        # Last-seen raw value, used to diff this tick's gain — see apply_boost().
        self._prev: int | None = None

    def get(self) -> int:
        return self.pine.read_int32(PLAYER_BOLT_COUNT)

    def set(self, value: int) -> None:
        self.pine.write_int32(PLAYER_BOLT_COUNT, min(value, MAX_PLAYER_BOLTS))

    def rebaseline(self, value: int | None = None) -> None:
        """Re-sync the baseline apply_boost() diffs against, without
        boosting anything. Callers that write PLAYER_BOLT_COUNT directly
        (starting/filler bolt grants) must call this right after, or
        apply_boost()'s next tick would multiply that grant too."""
        self._prev = value if value is not None else self.get()

    def apply_boost(self) -> None:
        """Inflate ordinary bolt gain (crates, enemies, etc.) by multiplier,
        every tick, by diffing against the last raw reading."""
        current = self.get()
        if self._prev is None:
            self._prev = current
            return
        diff = current - self._prev
        if diff <= 0:
            self._prev = current
            return
        if self.multiplier > 1:
            boosted = min(self._prev + diff * self.multiplier, MAX_PLAYER_BOLTS)
            self.set(boosted)
            self._prev = boosted
        else:
            self._prev = current

    def __repr__(self) -> str:
        return f"PlayerBoltInventory(prev={self._prev}, multiplier={self.multiplier})"
