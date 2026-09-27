"""Resident PSP Nanotech XP (save + 0x1c34), using pymem."""
PLAYER_HEALTH_EXP = 0x088C2734
MAX_XP = 0x7fffffff


class PlayerHealthExpInventory:
    def __init__(self, memory):
        self.memory = memory
        self.multiplier = 1
        self._prev = None

    def rebaseline(self):
        self._prev = self.memory.read_int32(PLAYER_HEALTH_EXP)

    def abandon(self):
        self._prev = None

    def apply_boost(self):
        current = self.memory.read_int32(PLAYER_HEALTH_EXP)
        previous, self._prev = self._prev, current
        if not 0 <= current <= MAX_XP:
            self._prev = None
            return
        if previous is None or current <= previous or self.multiplier <= 1:
            return
        boosted = min(MAX_XP, previous + (current - previous) * self.multiplier)
        self.memory.write_int32(PLAYER_HEALTH_EXP, boosted)
        self._prev = boosted
