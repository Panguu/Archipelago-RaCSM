"""Transactional PSP data patches with verification and conservative restoration.

Executable hooks require PPSSPP JIT invalidation and PSP retail instruction
captures. They must not be installed through this data-only path.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Patch:
    address: int
    original: bytes
    replacement: bytes


class Plan:
    def __init__(self, memory, edits, *, name, planet_id=None):
        self.memory = memory
        self.name = name
        self.planet_id = planet_id
        self.edits = tuple(edits)
        self.installed = False
        spans = []
        for edit in self.edits:
            if not edit.original or len(edit.original) != len(edit.replacement):
                raise ValueError("Patch must preserve a nonempty byte range")
            end = edit.address + len(edit.original)
            if not 0x08000000 <= edit.address < end <= 0x0A000000:
                raise ValueError("Patch is outside PSP RAM")
            spans.append((edit.address, end))
        spans.sort()
        if any(a[1] > b[0] for a, b in zip(spans, spans[1:])):
            raise ValueError("Overlapping patches")

    def validate(self, installed=None):
        if self.memory.get_game_id() != "UCUS98633":
            raise RuntimeError("Patch requires UCUS98633")
        installed = self.installed if installed is None else installed
        for edit in self.edits:
            expected = edit.replacement if installed else edit.original
            if self.memory.read_bytes(edit.address, len(expected)) != expected:
                raise RuntimeError(f"{self.name}: unexpected bytes at {edit.address:#x}")

    def install(self):
        if self.installed:
            self.validate()
            return
        self.validate(False)
        attempted = []
        try:
            for edit in self.edits:
                attempted.append(edit)
                self.memory.write_bytes(edit.address, edit.replacement)
            self.validate(True)
        except Exception:
            for edit in reversed(attempted):
                self.memory.write_bytes(edit.address, edit.original)
            self.validate(False)
            raise
        self.installed = True

    def restore(self):
        if not self.installed:
            return
        # Preflight the entire plan before making any writes. Refuse to stomp
        # a newly loaded overlay or bytes modified by another patch.
        self.validate(True)
        for edit in reversed(self.edits):
            self.memory.write_bytes(edit.address, edit.original)
        self.validate(False)
        self.installed = False
