"""Executable edits with PPSSPP CPU and JIT coordination.

Payload storage must be separately owned. Retail instruction captures belong
to each PSP hook; callers must never register PS2 instructions or code caves.
"""
from .plan import Plan


class CodePlan(Plan):
    def __init__(self, memory, edits, **kwargs):
        super().__init__(memory, edits, **kwargs)
        if any(edit.address % 4 or len(edit.original) % 4 for edit in self.edits):
            raise ValueError("Executable patches must cover whole PSP instructions")

    def install(self):
        with self.memory.paused():
            self.memory.invalidate_code()
            # This preflight also rejects pending JIT emuhack opcodes when a
            # deferred invalidation has not completed yet. No write on failure.
            super().install()

    def restore(self):
        if not self.installed:
            return
        with self.memory.paused():
            self.memory.invalidate_code()
            super().restore()
