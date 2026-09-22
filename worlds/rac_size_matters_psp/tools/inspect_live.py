"""Read current gameplay diagnostics through pymem without changing the save."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from worlds.rac_size_matters_psp.procmem import ProcMemTransport
from worlds.rac_size_matters_psp.core.address_maps import (
    CURRENT_PLANET_ADDRESS, PLANET_ADDRESSES, PLAYER_BOLT_COUNT,
    WEAPON_VENDOR_SLOTS, WEAPON_VENDOR_ITEMS,
)
from worlds.rac_size_matters_psp.core.structs.game import TransitionGateStruct


memory = ProcMemTransport()
try:
    memory.connect()
    memory.validate_session()
    planet_id = memory.read_int32(CURRENT_PLANET_ADDRESS)
    print("planet", planet_id, "gate", hex(memory.read_int32(TransitionGateStruct.BASE_ADDRESS)),
          "bolts", memory.read_int32(PLAYER_BOLT_COUNT))
    planet = PLANET_ADDRESSES.get(planet_id)
    if planet:
        print("menu", memory.read_bytes(planet.menu, 8).hex(),
              "health", memory.read_float(planet.player_health),
              "max_health", memory.read_float(planet.player_health + 4))
        print("vendor_slots", memory.read_bytes(WEAPON_VENDOR_SLOTS, 16).hex(),
              "vendor_items", memory.read_bytes(WEAPON_VENDOR_ITEMS, 32).hex())
finally:
    memory.disconnect()
