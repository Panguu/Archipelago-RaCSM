"""Read-only PSP RAM capture for native patch research; run from the AP root."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1]))
from worlds.rac_size_matters_psp.procmem import ProcMemTransport

memory = ProcMemTransport()
try:
    memory.connect()
    memory.validate_session()
    destination = ROOT / '.research'
    destination.mkdir(exist_ok=True)
    status = memory._control._request('game.status')
    cpu = memory._control._request('cpu.status')
    with memory.paused():
        memory.invalidate_code()
        data = b''.join(memory.read_bytes(address, 0x10000) for address in range(0x08000000, 0x0A000000, 0x10000))
    (destination / 'ram.bin').write_bytes(data)
    (destination / 'session.json').write_text(json.dumps({'game': status, 'cpu': cpu}, indent=2))
    print('Captured', len(data), 'bytes; game', memory.get_game_id(), 'planet', memory.read_int32(0x088C272C))
finally:
    memory.disconnect()
