def load_plan(hooks):
    memory = hooks.pine.data
    if not isinstance(memory, bytearray):
        raise TypeError("Compiler fixtures require a bytearray")
    for patch in hooks.patches:
        assert bytes(memory[patch.address:patch.address + len(patch.original)]) == patch.original
    for patch in hooks.patches:
        memory[patch.address:patch.address + len(patch.replacement)] = patch.replacement
    hooks.installed = True
