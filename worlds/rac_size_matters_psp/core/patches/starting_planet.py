"""UCUS98633 New Game destination patch, mapped from retail FRONTEND.PRX.

No guest allocation or runtime teleport. Existing-save load paths are unchanged.
Live frontend validation remains pending; exact retail preflight is mandatory.
"""
import logging
import struct
from ..address_maps import CURRENT_PLANET_ADDRESS
from ..structs.game import TransitionGateStruct, TRANSITION_GATE_IDLE
from .code import CodePlan
from .plan import Patch

ELIGIBLE = frozenset((1, 2, 3, 4, 7, 8, 23))
INIT = 0x19F4
ANCHOR_OFFSET = 0x1A0C

def packed(*words):
    return struct.pack('<'+'I'*len(words), *words)

ANCHOR = packed(0x2410FFFF, 0x30B200FF, 0xAFB3011C, 0xAFBF0120)

def initializer(base):
    pointer = base+0x112690
    return packed(0x27BDFED0, 0xAFB10114,
                  0x3C110000 | ((pointer+0x8000)>>16),
                  0xAFB00110, 0xAFB20118, 0xAE240000 | (pointer&65535))

def prepare(memory, base, planet):
    if type(planet) is not int or planet not in ELIGIBLE:
        raise ValueError('Invalid PSP starting planet')
    if memory.read_bytes(base+INIT, 24) != initializer(base):
        raise RuntimeError('PSP save initializer signature changed')
    pointer = base+0x112690
    # a0 already holds the save pointer. Replace its redundant reload with
    # a temporary destination in a2, then restore the original lui a2,5.
    # a1 must stay 1: later stores use it for unrelated new-save defaults.
    edits = [Patch(base+0x1AAC,
                   packed(0x8E240000 | (pointer&65535), 0x3C060005, 0xAC851C2C),
                   packed(0x34060000 | planet, 0xAC861C2C, 0x3C060005))]
    call = 0x0C000000 | (((base+0xF38)>>2)&0x3FFFFFF)
    for offset in (0x198B4, 0x19E34):
        edits.append(Patch(base+offset, packed(0x34040014, call, 0x34050001),
                           packed(0x34040000 | planet, call, 0x34050001)))
    plan = CodePlan(memory, edits, name='PSP New Game starting planet', planet_id=0)
    plan.validate(False)
    return plan


class StartingPlanet:
    def __init__(self, memory):
        self.memory = memory
        self.target = None
        self.base = self.plan = self.applied = None

    def configure(self, planet):
        if planet is not None and (type(planet) is not int or planet not in ELIGIBLE):
            raise ValueError('Invalid PSP starting planet')
        self.target = planet

    def _frontend(self):
        m = self.memory
        if (m.get_game_id() != 'UCUS98633' or m.read_int8(CURRENT_PLANET_ADDRESS) != 0
                or m.read_int32(TransitionGateStruct.BASE_ADDRESS) != TRANSITION_GATE_IDLE):
            return None
        if self.base is not None and m.read_bytes(self.base+INIT, 24) == initializer(self.base):
            return self.base
        raw = m.read_bytes(0x08800000, 0x1800000)
        hit = raw.find(ANCHOR)
        if hit < 0 or raw.find(ANCHOR, hit+1) >= 0:
            return None
        base = 0x08800000+hit-ANCHOR_OFFSET
        if not 0x08800000 <= base <= 0x0A000000-0x240000:
            return None
        if m.read_bytes(base+INIT, 24) != initializer(base):
            return None
        return base

    def service(self):
        if self.target in (None, 1) and self.plan is None:
            return
        if (self.memory.read_int8(CURRENT_PLANET_ADDRESS) != 0
                or self.memory.read_int32(TransitionGateStruct.BASE_ADDRESS) != TRANSITION_GATE_IDLE):
            self.base = self.plan = self.applied = None
            return
        with self.memory.paused():
            self.memory.invalidate_code()
            base = self._frontend()
            if base is None or base != self.base:
                # Another module owns the old addresses. Never restore it.
                self.plan = self.applied = None
                self.base = base
            if base is None:
                return
            if self.plan is not None:
                if all(self.memory.read_bytes(e.address, len(e.original)) == e.original for e in self.plan.edits):
                    self.plan = self.applied = None  # reset/savestate restored retail
                else:
                    self.plan.validate(True)
            if self.applied == self.target:
                return
            if self.plan is not None:
                self.plan.restore()
                self.plan = None
            if self.target not in (None, 1):
                self.plan = prepare(self.memory, base, self.target)
                self.plan.install()
            self.applied = self.target
            if self.target is not None:
                logging.getLogger('CommonClient').info(
                    '[RAC] New saves will start on planet %s. Ready to start a new game.', self.target)

    def close(self):
        if self.plan is not None:
            with self.memory.paused():
                self.memory.invalidate_code()
                if self._frontend() == self.base:
                    if not all(self.memory.read_bytes(e.address, len(e.original)) == e.original for e in self.plan.edits):
                        self.plan.restore()
        self.base = self.plan = self.applied = None
