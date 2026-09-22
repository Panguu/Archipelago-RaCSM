"""Connect the real PSP client to a generated local server using synthetic RAM.

No emulator is touched. Verifies AP authentication, starting items/checkpoints,
game polling, a mission check, and delivery of its randomized reward.
"""
import asyncio
from functools import partial
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1]))
import websockets
import Utils
Utils.gui_enabled = False
state = ROOT / "build/smoke-state"
state.mkdir(parents=True, exist_ok=True)
Utils.user_path.cached_path = str(state)
Utils.persistent_load.storage = {}
from CommonClient import server_loop
from MultiServer import Context, server
from worlds.rac_size_matters_psp.client.context import RACContext
from worlds.rac_size_matters_psp.core.core import Core
from worlds.rac_size_matters_psp.core.native_runtime import NativeRuntime
from worlds.rac_size_matters_psp.core.address_maps import PLANET_MISSION_ADDRESSES, PLAYER_BOLT_COUNT
from worlds.rac_size_matters_psp.test.test_client_gameplay import GameMemory


class Memory(GameMemory):
    attached = False
    def connect(self):
        self.attached = True
    def disconnect(self):
        self.attached = False
    def is_connected(self):
        return self.attached
    def get_game_id(self):
        return "UCUS98633"


async def main():
    archive = next((ROOT / "build/playtest").glob("*.zip"))
    host = Context("127.0.0.1", 0, None, None, 1, 10, False)
    host.load(str(archive))
    async with websockets.serve(partial(server, ctx=host), "127.0.0.1", 0) as listener:
        port = listener.sockets[0].getsockname()[1]
        client = RACContext(f"127.0.0.1:{port}", None)
        client.auth = "PSPPlayer"
        memory = Memory()
        client.pine = client.memory = memory
        client.native = NativeRuntime(memory)
        client._wiring = Core(memory)
        client.server_task = asyncio.create_task(server_loop(client))
        try:
            async with asyncio.timeout(20):
                while not (client.psp_connected and client._filler_checkpoint_synced
                           and client._starting_checkpoint_synced and client.items_received):
                    await asyncio.sleep(.05)
                await client._poll_game()
                await client._grant_starting_items()
                assert memory.read_int32(PLAYER_BOLT_COUNT) == 45000
                assert any(client._wiring.planet.weapons.weapons.values())
                before = len(client.items_received)
                address = PLANET_MISSION_ADDRESSES["Pokitaru"]
                memory.write_int16(address, memory.read_int16(address) | 4)
                await client._poll_game()
                location = client._location_name_to_id["Pokitaru: Rescue the girl"]
                while location not in host.location_checks[0, 1] or len(client.items_received) <= before:
                    await asyncio.sleep(.05)
                await client._poll_game()
                print("PASS: real server authentication, starting weapons/bolts, mission check, reward delivery")
        finally:
            await client.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
