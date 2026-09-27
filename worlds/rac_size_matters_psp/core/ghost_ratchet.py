"""PSP native decoy with reciprocal object validation and transition guards."""
import math
import struct
from .scene_objects import START, END, discover, ready


class GhostRatchetInventory:
    def __init__(self, memory):
        self.memory = memory
        self.abandon()

    def abandon(self):
        self.planet = self.player = self.ghost = self.original = None

    def bind(self, planet):
        if not ready(self.memory, planet):
            self.abandon()
            return False
        if self.planet != planet:
            self.abandon()
            self.planet = planet
            raw = self.memory.read_bytes(START, END-START)
            players = discover(self.memory, 0x36919224, 4, raw)
            ghosts = discover(self.memory, 0x0805c334, 0x18c, raw)
            if len(players) == 1 and len(ghosts) == 1:
                self.player, self.ghost = players[0], ghosts[0]
        return bool(self.player and self.ghost and self.player.valid(self.memory)
                    and self.ghost.valid(self.memory))

    def read_own_position(self, planet):
        if not self.bind(planet):
            return None
        pos = struct.unpack('<3f', self.memory.read_bytes(self.player.matrix+0x30, 12))
        return pos if all(math.isfinite(x) and abs(x)<1e7 for x in pos) else None

    def follow(self, planet, x, y, z):
        if not all(math.isfinite(v) and abs(v)<1e7 for v in (x,y,z)) or not self.bind(planet):
            return False
        p, ghost = self.memory, self.ghost
        if self.original is None:
            if p.read_int32(ghost.matrix+0x64) != 0x8000:
                return False
            spans = ((ghost.obj+0x40,4), (ghost.matrix,0x40),
                     (ghost.matrix+0x64,4), (ghost.matrix+0x70,4))
            self.original = {a:p.read_bytes(a,n) for a,n in spans}
            p.write_bytes(ghost.payload, struct.pack('<I', self.player.matrix)+bytes(0x188))
        if p.read_int32(ghost.payload) != self.player.matrix:
            self.abandon()
            return False
        p.write_bytes(ghost.matrix, p.read_bytes(self.player.matrix,0x30))
        p.write_int32(ghost.obj+0x40,1)
        p.write_int32(ghost.matrix+0x64,1)
        p.write_bytes(ghost.matrix+0x70,struct.pack('<f',1000.0))
        p.write_bytes(ghost.matrix+0x30,struct.pack('<3f',x,y,z))
        return True

    def stop_following(self):
        if (self.original and self.planet is not None and ready(self.memory,self.planet)
                and self.ghost and self.ghost.valid(self.memory)):
            for address, data in self.original.items():
                self.memory.write_bytes(address,data)
        self.original = None
