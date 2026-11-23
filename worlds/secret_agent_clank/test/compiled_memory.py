from ..core.patches.module_arena import ModuleArena


def load_plan(hooks):
    memory = hooks.pine.data
    if not isinstance(memory, bytearray):
        raise TypeError("Compiler fixtures require a bytearray")
    for patch in hooks.patches:
        assert bytes(memory[patch.address:patch.address + len(patch.original)]) == patch.original
    for patch in hooks.patches:
        memory[patch.address:patch.address + len(patch.replacement)] = patch.replacement
    hooks.installed = True


def ram_arena(memory, size=0x10000):
    """A module arena over an unused, zeroed block of RAM, for tests on RAM captures."""
    start = memory.data.find(bytes(size + 16), 0x100000)
    if start < 0:
        raise ValueError("No free RAM for a test arena")
    start = (start + 15) & ~15
    return ModuleArena(start - 128, bytes(128 + size), 128)
