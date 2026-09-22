"""Temporarily replace Pokitaru vendor-row icons; restore on menu close."""
import struct
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1]))
from worlds.rac_size_matters_psp.procmem import ProcMemTransport
from worlds.rac_size_matters_psp.core.patches import Patch, Plan

memory = ProcMemTransport()
plan = None
try:
    memory.connect()
    if memory.read_int32(0x088c272c) != 1 or memory.read_int32(0x09597b24) != 9:
        raise RuntimeError("Open the Pokitaru weapon vendor before this probe")
    pixels = (ROOT / "images/icons/archipelago-psp.t4").read_bytes()
    palette = (ROOT / "images/icons/archipelago-psp.rgba").read_bytes()
    count = memory.read_int32(0x088c0bc4)
    if not 1 <= count <= 21:
        raise RuntimeError("Unexpected vendor count")
    ids = struct.unpack(f"<{count}I", memory.read_bytes(0x088c0b60, count * 4))
    edits, seen = [], set()
    for index, identity in enumerate(ids):
        row = struct.unpack("<7I", memory.read_bytes(0x093fee8c + index * 28, 28))
        if row[0] != identity or not 0 < row[3] <= 108:
            raise RuntimeError("Vendor row identity changed")
        resource = memory.read_int32(0x093f7cac + row[3] * 4)
        if not 0 < resource < 1024:
            raise RuntimeError("Invalid icon resource")
        image, clut = struct.unpack("<II", memory.read_bytes(0x094420c0 + resource * 44 + 12, 8))
        ih, ph = memory.read_bytes(image, 64), memory.read_bytes(clut, 64)
        if struct.unpack_from("<4H", ih, 4) != (4, 1, 32, 32) or struct.unpack_from("<3H", ph, 4) != (3, 0, 16):
            raise RuntimeError("Unsupported PSP icon texture format")
        for header, payload in ((ih, pixels), (ph, palette)):
            address = struct.unpack_from("<I", header, 48)[0]
            if address not in seen:
                seen.add(address)
                edits.append(Patch(address, memory.read_bytes(address, len(payload)), payload))
    plan = Plan(memory, edits, name="PSP vendor icon probe", planet_id=1)
    with memory.paused():
        plan.install()
    print("AP texture applied to vendor icons; close vendor to restore", flush=True)
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        if memory.read_int32(0x088c272c) != 1 or memory.read_int32(0x09597b24) != 9:
            break
        time.sleep(.2)
finally:
    if plan is not None and plan.installed:
        with memory.paused():
            plan.restore()
        print("Original icon textures restored", flush=True)
    memory.disconnect()
