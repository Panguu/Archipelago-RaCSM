"""Nanotech checks from the PSP player's maximum-health field."""
import math


class NanotechChecks:
    def __init__(self):
        self.checked = set()
        self.interval = 1
        self.maximum = 75

    def sync_from_ap(self, names):
        self.checked.update(names)

    def check(self, max_health):
        # Loading/stale structs can contain NaNs or fractional garbage. Never
        # turn those into a batch of irreversible location reports.
        if (not isinstance(max_health, (int, float)) or isinstance(max_health, bool)
                or not math.isfinite(max_health) or not 1 <= max_health <= 75
                or max_health != int(max_health)):
            return []
        names = [f"Nanotech Level: {level}"
                 for level in range(6, min(int(max_health), self.maximum) + 1)
                 if self.interval > 0 and level % self.interval == 0]
        fresh = [name for name in names if name not in self.checked]
        self.checked.update(fresh)
        return fresh
