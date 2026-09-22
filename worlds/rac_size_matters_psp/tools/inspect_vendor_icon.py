"""Read-only diagnostic for the verified vendor texture layout."""
from pathlib import Path
import sys
import struct
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from worlds.rac_size_matters_psp.procmem import ProcMemTransport
from worlds.rac_size_matters_psp.core.vendor_presentation import VendorPresentation

m = ProcMemTransport()
try:
    m.connect()
    view = VendorPresentation(m)
    for i in range(4):
        print('row', i, struct.unpack('<7I', m.read_bytes(0x093fee8c+i*28, 28)))
    edits = view._edits(1)
    print('edits', None if edits is None else [(hex(a), len(e.original), e.original == e.replacement) for a,e in edits.items()])
    state = m.read_bytes(0x094a0ec0, 24)
    pointer, count = struct.unpack_from('<I', state)[0], struct.unpack_from('<I', state, 16)[0]
    if 0 < count < 20000:
        table = m.read_bytes(pointer, count * 12)
        for offset in range(0, len(table), 12):
            identity, address = struct.unpack_from('<II', table, offset+4)
            if identity in (30, 367, 38, 371):
                print('string', identity, hex(address), repr(m.read_bytes(address, 100).split(b'\0')[0]))
finally:
    m.disconnect()
