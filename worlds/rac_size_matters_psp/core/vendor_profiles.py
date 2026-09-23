"""Resolve retail PSP vendor data from code references, never guessed offsets."""
import json
import struct
from dataclasses import dataclass
from importlib.resources import files

from .address_maps import CURRENT_PLANET_ADDRESS, MENU_ADDR_BY_PLANET_ID
from .structs.game import TransitionGateStruct, TRANSITION_GATE_IDLE


@dataclass(frozen=True)
class VendorProfile:
    rows: int
    icons: int
    textures: int
    menu: int
    text: int
    frame: int = 0
    timer: int = 0
    panel_calls: tuple = ()


PROFILES = json.loads(files(__package__.rsplit('.', 1)[0]).joinpath('data', 'psp_vendor_profiles.json').read_text())
# Renderer stores: f20, f22, s0, s1, ra, followed by bnez/nop.
# No relocations or JIT entry opcode are included in this anchor.
ANCHOR = struct.pack('<7I', 0xE7B40040, 0xE7B60044, 0xAFB00048,
                     0xAFB1004C, 0xAFBF0050, 0x14800003, 0)


def resolve(memory, planet_id):
    profile = PROFILES.get(str(planet_id))
    menu = MENU_ADDR_BY_PLANET_ID.get(planet_id)
    if profile is None or menu is None:
        return None
    # Freeze only for a coherent identification snapshot. All reads use pymem.
    with memory.paused():
        if (memory.read_int8(CURRENT_PLANET_ADDRESS) != planet_id
                or memory.read_int32(TransitionGateStruct.BASE_ADDRESS) != TRANSITION_GATE_IDLE):
            return None
        # Compiled block markers can replace words inside these routines.
        # Request retail bytes back; never accept a marker as a signature.
        memory.invalidate_code()
        start = 0x08800000
        raw = memory.read_bytes(start, 0x1800000)
        hit = raw.find(ANCHOR)
        if hit < 0 or raw.find(ANCHOR, hit+1) >= 0:
            return None
        base = start + hit - 12 - profile['renderer']['code']
        addresses = {}
        for name in ('rows', 'icons', 'textures', 'text'):
            ref = profile[name]
            offset = base + ref['code'] - start
            if not 0 <= offset <= len(raw)-64:
                return None
            words = struct.unpack_from('<16I', raw, offset)
            if any(word & mask != expected for word, mask, expected in zip(words, ref['masks'], ref['words'])):
                return None
            high, low = words[ref['hi']], words[ref['lo']]
            if [high & 0xFFFF0000, low & 0xFFFF0000] != ref['address_ops']:
                return None
            address = ((high & 65535) << 16) + ((low & 65535) ^ 32768) - 32768 + ref['delta']
            if address != base + ref['relative'] or not 0x08800000 <= address < 0x0A000000:
                return None
            addresses[name] = address
        timer = base + profile['renderer']['relative']
        frame = base + profile['renderer']['code']
        expected = struct.pack('<3I', 0x27BDFFA0, 0x3C040000 | ((timer+0x8000)>>16),
                               0x8C840000 | (timer&65535))
        if memory.read_bytes(frame, 12) != expected:
            return None
        panel_calls = []
        for call in profile['panel_calls']:
            address = frame+call['offset']
            expected = struct.pack('<2I', 0x0C000000 | (((base+call['target'])>>2)&0x3FFFFFF), call['delay'])
            if memory.read_bytes(address, 8) != expected:
                return None
            panel_calls.append((address, expected))
        return VendorProfile(menu=menu, frame=frame, timer=timer, panel_calls=tuple(panel_calls), **addresses)
