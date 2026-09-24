"""Independent top-left AP text; the native interaction HUD is never modified."""
import struct
from dataclasses import dataclass

from ..vendor_profiles import PROFILES
from .counter import jump
from .code import CodePlan
from .plan import Patch


@dataclass(frozen=True)
class Font:
    draw: int
    width: int
    colour_slot: int
    scratch: int


def resolve_font(memory, profile, planet):
    ref = PROFILES[str(planet)]
    base = profile.frame - ref['renderer']['code']
    font = ref['overlay']
    def normalize(word):
        op = word >> 26
        if op in (2, 3):
            return word & 0xFC000000
        if op in (8, 9, 10, 11, 12, 13, 14, 15, 32, 33, 35, 36, 37, 40, 41, 43, 49, 57):
            return word & 0xFFFF0000
        return word
    memory.invalidate_code()
    blocks = {}
    for name, signature in font['signatures'].items():
        raw = memory.read_bytes(base+font[name], len(signature)*4)
        blocks[name] = struct.unpack('<'+'I'*len(signature), raw)
        if [normalize(w) for w in blocks[name]] != signature:
            raise RuntimeError('Notification font routine changed')
    for address, target in ((profile.frame+0xB8, font['colour']),
                            (profile.frame+0xE4, font['draw']),
                            (base+font['draw']+0x74, font['width'])):
        if memory.read_int32(address) != (0x0C000000 | (((base+target)>>2)&0x3FFFFFF)):
            raise RuntimeError('Notification font call changed')
    def pair(words, hi, lo):
        return ((words[hi]&65535)<<16) + ((words[lo]&65535)^32768)-32768
    if (pair(blocks['colour'], 0, 1) != base+font['colour_slot']
            or pair(blocks['draw'], 20, 28) != base+font['scratch']):
        raise RuntimeError('Notification font globals changed')
    return Font(**{key: base+font[key] for key in ('draw', 'width', 'colour_slot', 'scratch')})


def payload(address, state, text, entry, original, font):
    first, second = struct.unpack('<2I', original)
    if first != 0x27BDFFA0 or second >> 16 != 0x3C04:
        raise ValueError('Unsupported notification prologue')
    words = []
    def load(reg, value):
        words.extend((0x3C000000 | reg<<16 | value>>16,
                      0x34000000 | reg<<21 | reg<<16 | (value&65535)))
    def call(target):
        words.extend((jump(address+len(words)*4, target)|0x04000000, 0))
    # 16-byte outgoing argument area, saved callee-saved registers above it.
    words.extend((0x27BDFFC0, 0xAFB00020, 0xAFB10024, 0xAFB20028, 0xAFB3002C, 0xAFBF0030))
    load(16, state)
    words.append(0x8E080000)  # lw t0,0(s0)
    branch = len(words)
    words.extend((0, 0))     # blez t0,restore; nop
    words.extend((0x2508FFFF, 0xAE080000))
    load(8, font.colour_slot)
    words.extend((0x8D110000, 0x8E320000))  # colour pointer s1, old colour s2
    load(8, font.scratch)
    words.extend((0x8D130000, 0x2409FFFF, 0xAE290000, 0xAD090000))
    load(4, text)
    call(font.width)
    words.extend((0x00022043, 0x2484000C, 0x2405001C))  # x=12+width/2, y=28
    load(6, text)
    call(font.draw)
    words.append(0xAE320000)  # restore active font colour
    load(8, font.scratch)
    words.append(0xAD130000)  # restore font scratch colour
    restore = len(words)
    words[branch] = 0x19000000 | (restore-branch-1)
    words.extend((0x8FB00020, 0x8FB10024, 0x8FB20028, 0x8FB3002C, 0x8FBF0030, 0x27BD0040,
                  first, second))
    words.extend((jump(address+len(words)*4, entry+8), 0))
    return struct.pack('<'+'I'*len(words), *words)


class NotificationHook:
    def __init__(self, memory, storage, profile, planet):
        self.memory, self.storage, self.profile = memory, storage, profile
        self.planet = planet
        self.plan = None
        self.code = self.state = self.text = None

    def install(self):
        # Caller holds KernelBridge.frame at entry+12, beyond the hook return.
        font = resolve_font(self.memory, self.profile, self.planet)
        self.code = self.storage.reserve('notification-code', 256)
        self.state = self.storage.reserve('notification-timer', 4)
        self.text = self.storage.reserve('notification-text', 256)
        original = self.memory.read_bytes(self.profile.frame, 8)
        self.storage.write(self.code.name, payload(self.code.address, self.state.address,
            self.text.address, self.profile.frame, original, font))
        replacement = struct.pack('<2I', jump(self.profile.frame, self.code.address), 0)
        self.plan = CodePlan(self.memory, [Patch(self.profile.frame, original, replacement)],
                             name='Independent AP notification', planet_id=self.planet)
        self.storage.retain(self)
        self.plan.install()

    def show(self, text, frames=180):
        self.storage.write(self.text.name, text.encode('ascii')+b'\0')
        self.storage.write(self.state.name, struct.pack('<I', frames))

    def restore(self):
        if self.plan is not None:
            self.plan.restore()
            self.plan.validate(False)
            self.storage.release(self)
