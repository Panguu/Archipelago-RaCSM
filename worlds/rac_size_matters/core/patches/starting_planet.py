"""US frontend New Game destinations, verified against main_menu.p2s.

Offsets are relative to the relocated frontend SNR2 module. Existing saves
skip the initialization block and retain their saved destination.
"""
from .asm import Patch, jump, packed
from .loader_gate import LoaderGate
from .plan import Plan

ELIGIBLE = frozenset((1, 2, 3, 4, 7, 8, 23))
INIT = 0x2F80
INIT_SIGNATURE = packed(0x27BDFED0, 0xFFB10108, 0xFFB30118)
SAVE = 0x3024
TRAVEL = (0x1819C, 0x18BC4)
CHANGE_LEVEL = 0x1B40


def prepare(pine, base, planet):
    if planet not in ELIGIBLE:
        raise ValueError(f"Invalid starting planet: {planet!r}")
    # Keep s0 == 1: the initializer also uses it for unrelated save defaults.
    # v0 already holds the save pointer, so the redundant reload into v1 can
    # become a temporary destination without allocating a code cave.
    pointer_offset = (base + 0x27E9C) & 0xFFFF
    edits = [Patch(base + SAVE,
                   packed(0x8E220000 | pointer_offset, 0xAC401C74,
                          0x8E230000 | pointer_offset, 0xAC701C6C),
                   packed(0x8E220000 | pointer_offset, 0xAC401C74,
                          0x24080000 | planet, 0xAC481C6C))]
    for offset in TRAVEL:
        edits.append(Patch(base + offset,
                           packed(0x24040001, jump(base + CHANGE_LEVEL), 0x24050001),
                           packed(0x24040000 | planet, jump(base + CHANGE_LEVEL), 0x24050001)))
    plan = Plan(pine, edits)
    plan._validate()
    return plan


class StartingPlanet:
    def __init__(self, pine, log):
        self.pine, self.log = pine, log
        self.plan = None
        self.base = None
        self.planet = None

    def frontend(self):
        p = self.pine
        if (p.get_game_id() != "SCUS-97615"
                or p.read_int32(LoaderGate.STATE) != 6
                or p.read_int32(LoaderGate.TARGET) != 0
                or p.read_int32(0x1F4C76C) != 0):
            return None
        handle = p.read_int32(LoaderGate.HANDLE)
        if not 0 <= handle < 8:
            return None
        entry = LoaderGate.MODULES + handle * 0x418
        base = p.read_int32(entry + 4)
        if not p.read_int32(entry + 8) & 1 or not 0x100000 <= base < 0x1C00000:
            return None
        # The fourth instruction contains a relocated address, unlike the
        # first three prologue instructions.
        if p.read_bytes(base + INIT, 12) != INIT_SIGNATURE[:12]:
            return None
        return base

    def service(self, planet):
        if planet is not None and planet not in ELIGIBLE:
            raise ValueError(f"Invalid starting planet: {planet!r}")
        base = self.frontend()
        if base is None or base != self.base:
            # A different DLL owns this storage now. Never restore stale code.
            self.plan = None
            self.planet = None
            self.base = base
        if base is None:
            return
        if self.plan is not None:
            # A reset/savestate can put the original frontend back in place.
            if all(self.pine.read_bytes(e.address, len(e.original)) == e.original
                   for e in self.plan.edits):
                self.plan = None
                self.planet = None
            else:
                self.plan._validate(replacement=True)
        if self.planet == planet:
            return
        self.close()
        if planet not in (None, 1):
            self.base = base
            plan = prepare(self.pine, base, planet)
            plan.install()
            self.plan = plan
        self.planet = planet
        if planet is not None:
            self.log(f"[RAC] New saves will start on planet {planet}. Ready to start a new game.")

    def close(self):
        if self.plan is not None and self.frontend() == self.base:
            if not all(self.pine.read_bytes(e.address, len(e.original)) == e.original
                       for e in self.plan.edits):
                self.plan.restore()
        self.plan = None
        self.planet = None
