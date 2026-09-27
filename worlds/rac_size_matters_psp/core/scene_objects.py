"""Validated native scene object links, shared by PSP optional features."""
from dataclasses import dataclass
import struct
from .address_maps import CURRENT_PLANET_ADDRESS
from .structs.game import TransitionGateStruct, TRANSITION_GATE_IDLE

START, END = 0x08800000, 0x0A000000


def pointer(value, size=4):
    return value % 4 == 0 and START <= value <= END - size


def ready(memory, planet):
    return (memory.get_game_id() == 'UCUS98633'
            and memory.read_int32(TransitionGateStruct.BASE_ADDRESS) == TRANSITION_GATE_IDLE
            and memory.read_int8(CURRENT_PLANET_ADDRESS) == planet)


@dataclass(frozen=True)
class SceneObject:
    obj: int
    matrix: int
    definition: int
    payload: int
    signature: int
    size: int

    def valid(self, memory):
        m = memory.read_int32
        return (m(self.obj + 0x24) == self.signature
                and m(self.obj + 0x0c) == self.matrix
                and m(self.obj + 0x10) == self.definition
                and m(self.matrix + 0x40) == self.obj
                and m(self.matrix + 0x58) == self.payload
                and m(self.definition + 0x1c) == self.size)


def discover(memory, signature, size, raw=None):
    raw = memory.read_bytes(START, END-START) if raw is None else raw
    def word(address):
        return struct.unpack_from('<I', raw, address-START)[0]
    found, offset = [], 0
    needle = struct.pack('<I', signature)
    while True:
        offset = raw.find(needle, offset)
        if offset < 0:
            break
        obj = START + offset - 0x24
        offset += 4
        if not pointer(obj, 0x50):
            continue
        matrix, definition = word(obj+12), word(obj+16)
        if not pointer(matrix, 0x80) or not pointer(definition, 0x20):
            continue
        payload = word(matrix+0x58)
        if (word(matrix+0x40) == obj and pointer(payload, size)
                and word(definition+0x1c) == size):
            found.append(SceneObject(obj, matrix, definition, payload, signature, size))
    return found
