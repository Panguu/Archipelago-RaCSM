"""Host the PSPPlayer test seed locally and launch the real PPSSPP client GUI."""
import asyncio
from functools import partial
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1]))
import Utils
state = ROOT / "build/live-state"
state.mkdir(parents=True, exist_ok=True)
Utils.user_path.cached_path = str(state)
Utils.persistent_load.storage = {}
Utils.init_logging("PSPPlaytest")
import websockets
from CommonClient import server_loop
from MultiServer import Context, server
from worlds.rac_size_matters_psp.client.context import RACContext


async def main():
    archive = next((ROOT / "build/playtest").glob("*.zip"))
    host = Context("127.0.0.1", 0, None, None, 1, 10, False)
    host.load(str(archive))
    host.init_save(True)
    async with websockets.serve(partial(server, ctx=host), "127.0.0.1", 0) as listener:
        port = listener.sockets[0].getsockname()[1]
        client = RACContext(f"127.0.0.1:{port}", None)
        client.auth = "PSPPlayer"
        client.server_task = asyncio.create_task(server_loop(client))
        client.run_gui()
        watcher = asyncio.create_task(client.game_watcher())
        previous = None
        try:
            while not client.exit_event.is_set():
                await asyncio.sleep(1)
                status = (client.psp_connected, client.current_planet,
                          client._wiring.planet.is_ready,
                          len(client.items_received), len(client.checked_locations))
                if status != previous:
                    print("LIVE", status, flush=True)
                    previous = status
        finally:
            watcher.cancel()
            await asyncio.gather(watcher, return_exceptions=True)
            await client.shutdown()
            host.save(now=True)


if __name__ == "__main__":
    asyncio.run(main())
