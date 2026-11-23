from . import mips as m
from .asm import Patch, jump, packed
from .module_arena import ModuleArena, reserve_arena
from .plan_compiler import compile_native_plan
from .snr2 import SNR2Module
from .starting_case import StartingCase


RETAIL_BASE = 0x328B00
# The frontend imports these level-only globals. The loader resolves names it
# can't find to 0, so they're allowed here; any other missing import is an error.
FRONTEND_NULL_IMPORTS = frozenset(("G_levelId", "g_pActivePlayer"))


def frontend_imports(data, imports):
    result = dict(imports)
    missing = {symbol.name for symbol in SNR2Module(data).symbols
               if symbol.kind == 1 and symbol.name not in result}
    if missing != FRONTEND_NULL_IMPORTS:
        raise ValueError(f"Unexpected frontend import layout: {sorted(missing)}")
    result.update(dict.fromkeys(missing, 0))
    return result


def prepare_frontend(base, loaded, start, *, identity=b""):
    arena = ModuleArena(base, loaded, start)
    if identity:
        arena.allocate(identity)
    rebase = lambda address: base + address - RETAIL_BASE
    init, change = rebase(StartingCase.INIT), rebase(StartingCase.CHANGE_LEVEL)
    config = arena.allocate(packed([1, 0, 0]))

    def set_case():
        return [*m.li32(m.T2, config), m.lw(m.T1, 0, m.T2), m.sw(m.T1, 0xECC, m.T0),
                m.lw(m.T1, 4, m.T2), m.sb(m.T1, 0x589, m.T0),
                m.lw(m.T1, 8, m.T2), m.sb(m.T1, 0x5A8, m.T0),
                m.addiu(m.T1, m.ZERO, 1), m.sb(m.T1, 0x5AA, m.T0)]

    entry = arena.allocate(packed([0x27BDFFF0, 0xFFBF0000, 0xFFA40008,
                                  jump(init, True), 0, 0xDFA80008,
                                  *set_case(), 0xDFBF0000, m.jr(m.RA), 0x27BD0010]))
    pointer = rebase(0x418FD8)
    travel = arena.allocate(packed([*m.li32(m.T0, pointer), m.lw(m.T0, 0, m.T0),
                                   *set_case(), m.lw(m.A0, 0, m.T2), jump(change), 0]))
    patches = []
    for site in StartingCase.CALLS:
        patches.append(Patch(rebase(site), packed([jump(init, True), 0x24050001]),
                             packed([jump(entry, True), 0x24050001])))
    for site in StartingCase.TRAVEL_CALLS:
        patches.append(Patch(rebase(site) - 4, packed([0x24040001, jump(change, True), 0x24050001]),
                             packed([0x24040001, jump(travel, True), 0x24050001])))
    for patch in patches:
        offset = patch.address - base
        if loaded[offset:offset + len(patch.original)] != patch.original:
            raise ValueError(f"Frontend call differs at {offset:#x}")
    return [*patches, *arena.patches], config


def compile_frontend(data, imports, *, identity=b"", with_bindings=False):
    imports = frontend_imports(data, imports)
    expanded, start = reserve_arena(data, 4096)
    compiled = compile_native_plan(expanded, imports,
        lambda base, loaded, symbols: prepare_frontend(base, loaded, start, identity=identity)[0], arena_start=start)
    if not with_bindings:
        return compiled
    base = 0x400000
    loaded, _ = SNR2Module(expanded).relocate(base, imports)
    _, config = prepare_frontend(base, loaded, start, identity=identity)
    return compiled, {"size": len(compiled), "identity_offset": start, "identity": identity.hex(),
                      "config_offset": config - base}
