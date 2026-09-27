"""PSP Shrink Ray checks and reversible native door interlocks."""
from ..constants.shrink_ray import SHRINK_RAY_PUZZLE_BITS, SHRINK_RAY_LOCATION_PLANETS
from .scene_objects import discover, pointer, ready

SHRINK_RAY_GATE_ADDRESS = 0x088C13CE


class ShrinkRaySkipInventory:
    def __init__(self, memory):
        self.memory = memory
        self.completed = set()
        self.planet = None
        self.locks = None
        self.changed = {}

    def sync_from_ap(self, names):
        self.completed.update(set(names) & SHRINK_RAY_PUZZLE_BITS.keys())

    def check(self, planet):
        raw = self.memory.read_int16(SHRINK_RAY_GATE_ADDRESS)
        fresh = [name for name, bit in SHRINK_RAY_PUZZLE_BITS.items()
                 if SHRINK_RAY_LOCATION_PLANETS[name] == planet
                 and raw & bit and name not in self.completed]
        self.completed.update(fresh)
        return fresh

    def abandon(self):
        self.planet, self.locks = None, None
        self.changed.clear()

    def _puzzle(self, lock):
        if not lock.valid(self.memory):
            return None
        pv = self.memory.read_int32(lock.matrix + 0x54)
        if not pointer(pv, 20) or self.memory.read_int32(lock.payload+4) != lock.matrix:
            return None
        puzzle = self.memory.read_int32(pv+12)
        return puzzle if 0 <= puzzle <= 10 else None

    def set_skip(self, planet, enabled):
        if not enabled and self.planet is None:
            return
        if not ready(self.memory, planet):
            self.abandon()
            return
        if self.planet != planet:
            self.abandon()
            self.planet = planet
        if not enabled:
            self.restore()
            return
        if self.locks is None:
            self.locks = discover(self.memory, 0x61b79aac, 0x58)
        for lock in self.locks:
            puzzle = self._puzzle(lock)
            if puzzle is None or self.memory.read_int32(lock.payload+0x4c) != 0:
                continue
            if self.memory.read_int8(lock.payload+0x50) == 1:
                self.changed[lock] = puzzle
                self.memory.write_int8(lock.payload+0x50, 0)

    def restore(self):
        if self.planet is None or not ready(self.memory, self.planet):
            self.abandon()
            return
        flags = self.memory.read_int16(SHRINK_RAY_GATE_ADDRESS)
        for lock, puzzle in list(self.changed.items()):
            if self._puzzle(lock) == puzzle and self.memory.read_int32(lock.payload+0x4c) == 0:
                self.memory.write_int8(lock.payload+0x50, int(not flags & (1 << puzzle)))
                del self.changed[lock]
