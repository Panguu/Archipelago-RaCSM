from __future__ import annotations

from typing import TYPE_CHECKING

from .address_maps import PLAYER_BOLT_COUNT

if TYPE_CHECKING:
    from ..pypine import Pine

# Bolt balance never exceeds this, regardless of source (organic gain,
# multiplier-boosted gain, or a one-shot AP grant) — imported directly by
# client/handlers.py and client/vendor.py, which write PLAYER_BOLT_COUNT
# outside this class for starting/filler bolt grants.
MAX_PLAYER_BOLTS = 9_999_000


class PlayerBoltInventory:
    """Pine-backed accessor + gain-multiplier tracking for the player's
    spendable bolt count (PLAYER_BOLT_COUNT) — global fixed address, no
    per-planet base, same as TitaniumBoltInventory.

    Distinct from TitaniumBoltInventory: that tracks the fixed set of
    Titanium Bolt collectible pickups (AP locations); this tracks the
    ordinary bolt currency balance, which only ever needs a gain multiplier,
    never location/completion tracking.
    """

    def __init__(self, pine: Pine) -> None:
        self.pine = pine
        # Bolt-multiplier option: 1 = no boost (default/off). Set directly
        # by the client from slot_data, same pattern as
        # WeaponInventory.experience_multiplier.
        self.multiplier: int = 1
        # Last-seen raw value, used only to diff this tick's gain from the
        # last one — see apply_boost().
        self._prev: int | None = None

    def get(self) -> int:
        return self.pine.read_int32(PLAYER_BOLT_COUNT)

    def set(self, value: int) -> None:
        self.pine.write_int32(PLAYER_BOLT_COUNT, min(value, MAX_PLAYER_BOLTS))

    def rebaseline(self, value: int | None = None) -> None:
        """Re-sync the baseline apply_boost() diffs against, without
        boosting anything. Callers that write PLAYER_BOLT_COUNT directly
        (starting bolts, filler bolt grants — both intentional one-shot AP
        grants, not organic in-game gain) must call this right after, or
        apply_boost()'s next tick would otherwise multiply that grant too.
        Pass the value just written if known, to avoid a redundant read."""
        self._prev = value if value is not None else self.get()

    def apply_boost(self) -> None:
        """Inflate ordinary bolt gain (crates, enemies, etc.) by
        multiplier, every tick — same diff-against-last-raw-reading
        approach as WeaponInventory.apply_experience_boost(). A same-or-
        lower reading (no gain yet, or a direct grant write already
        rebaselined) just re-syncs without writing anything."""
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
