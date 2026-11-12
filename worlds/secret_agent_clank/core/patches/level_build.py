"""This module does not connect to PCSX2. The generated routines use writable
configuration tables for run-specific choices. Publishing a build additionally
requires frontend compilation and a matching runtime binding manifest.
"""
import struct

from ...constants import PICKUP_LOCATIONS, VENDOR_LOCATIONS, WEAPON_MODS, STEALTH_CASES, STEALTH_MAX_PER_CASE
from ..mission_failure import MissionFailure
from ..stealth import StealthState
from ..skins import Skins
from .hooks import LocationHooks
from .wrench import WrenchProgression
from .mission_travel import MissionTravel
from .weapon_mods import WeaponMods
from .progression import Progression
from .titan_vendor import TitanVendor
from .vendor_catalog import VendorCatalog
from .vendor_presentation import VendorPresentation
from .connection_warning import ConnectionWarning
from .keycard_hunt import KeycardHunt
from .vendor_icon import prepare_vendor_icon
from .credits import prepare_credits
from .module_arena import ModuleArena, reserve_arena
from .plan_compiler import compile_native_plan
from .bindings import BindingCompiler
from .snr2 import SNR2Module


class FileMemory:
    """Only the module and the known loader module-ID field are readable."""
    def __init__(self, base, loaded, module):
        self.base, self.loaded, self.module = base, loaded, module

    def read_bytes(self, address, size):
        if size == 0:
            return b""
        if address == 0x206328 and size == 4:
            return struct.pack("<I", self.module)
        offset = address - self.base
        if size < 0 or offset < 0 or offset + size > len(self.loaded):
            raise ValueError(f"Native planner read outside module: {address:#x}, size {size}")
        return self.loaded[offset:offset + size]

    def read_int32(self, address):
        return int.from_bytes(self.read_bytes(address, 4), "little")

    def read_int8(self, address):
        return self.read_bytes(address, 1)[0]

    def batch_read_int32(self, addresses):
        return [self.read_int32(address) for address in addresses]

    def batch_read(self, reads):
        return [int.from_bytes(self.read_bytes(address, size), "little") for size, address in reads]


def prepare_level(base, loaded, symbols, module, vendor, arena_start, *, identity=b""):
    memory = FileMemory(base, loaded, module)
    arena = ModuleArena(base, loaded, arena_start)
    if identity:
        arena.allocate(identity)
    hooks = LocationHooks(memory)
    hooks.prepare(symbols, pickup_locations=PICKUP_LOCATIONS,
                  vendor_locations=VENDOR_LOCATIONS if vendor else {}, entitlements={}, vendor_enabled=vendor)
    objects = {"hooks": hooks}
    wrench = objects["wrench"] = WrenchProgression(memory)
    hooks.patches.extend(wrench.prepare_permanent(symbols, module, arena))
    travel = objects["mission_travel"] = MissionTravel(memory)
    hooks.patches.extend(travel.prepare(symbols, module=module))
    skins = objects["skins"] = Skins(memory)
    skins.configure({})
    hooks.patches.extend(skins.prepare(symbols, arena=arena))
    mods = objects["weapon_mods"] = WeaponMods(memory)
    mods.configure({"operatives": {"Ratchet": 1, "Clank": 1}, "ng_plus": 2,
                    "weapon_mod_ids": [mod.mod_id for mod in WEAPON_MODS]})
    hooks.patches.extend(mods.prepare(symbols, hooks, module, set(), vendor))
    progression = objects["progression"] = Progression(memory)
    progression.mission_failure = objects["mission_failure"] = MissionFailure(memory)
    progression.configure({"ng_plus": 2, "progressive_weapons": 1})
    progression.stealth = objects["stealth"] = StealthState(memory)
    progression.stealth.configure(dict.fromkeys(STEALTH_CASES, STEALTH_MAX_PER_CASE))
    progression.stealth.load({})
    if vendor:
        hooks.patches.extend(prepare_vendor_icon(memory, symbols, arena))
        hooks.patches.extend(TitanVendor(memory).prepare(symbols, hooks, set()))
        catalog = objects["vendor_catalog"] = VendorCatalog(memory)
        hooks.patches.extend(catalog.prepare(symbols, hooks))
        presentation = objects["presentation"] = VendorPresentation(memory)
        hooks.patches.extend(presentation.prepare(symbols, hooks))
    warning = objects["connection_warning"] = ConnectionWarning(memory)
    hooks.patches.extend(warning.prepare(symbols, hooks))
    hunt = objects["keycard_hunt"] = KeycardHunt(memory)
    hooks.patches.extend(hunt.prepare_permanent(symbols, module, arena))
    hooks.patches.extend(progression.prepare(symbols, hooks, module, vendor_enabled=vendor, arena=arena))
    if module == 32:
        hooks.patches.extend(prepare_credits(base, loaded, symbols, arena))
    return [*hooks.patches, *arena.patches], objects


def compile_level(data, imports, module, vendor, *, identity=b"", with_bindings=False):
    expanded, start = reserve_arena(data)

    def builder(base, loaded, symbols):
        patches, _ = prepare_level(base, loaded, symbols, module, vendor, start, identity=identity)
        return patches

    compiled = compile_native_plan(expanded, imports, builder, arena_start=start)
    if not with_bindings:
        return compiled
    base = 0x400000
    loaded, symbols = SNR2Module(expanded).relocate(base, imports)
    _, objects = prepare_level(base, loaded, symbols, module, vendor, start, identity=identity)
    compiler = BindingCompiler(compiled, imports, base)
    bindings = compiler.objects(objects)
    return compiled, {"size": len(compiled), "identity_offset": start, "identity": identity.hex(),
                      "vendor": vendor, "objects": bindings}
