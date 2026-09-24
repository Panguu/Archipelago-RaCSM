"""Lifecycle for one prepared native patch."""
from abc import ABC, abstractmethod


class Patch(ABC):
    def __init__(self, pine):
        self.pine = pine
        self.address = None
        self.original = b""
        self.replacement = b""

    @abstractmethod
    def prepare(self, **kwargs):
        """Validate inputs and capture original bytes without changing RAM."""
        raise NotImplementedError

    def apply(self):
        """Write a prepared patch, verify it, and undo a failed write."""
        if self.address is None or not self.replacement:
            raise RuntimeError("Prepare the patch before applying it")
        if self.pine.read_bytes(self.address, len(self.original)) != self.original:
            raise RuntimeError("Code changed since patch preparation")
        try:
            self.pine.write_bytes(self.address, self.replacement)
            if self.pine.read_bytes(self.address, len(self.replacement)) != self.replacement:
                raise RuntimeError("Patch readback failed")
        except Exception:
            self.pine.write_bytes(self.address, self.original)
            if self.pine.read_bytes(self.address, len(self.original)) != self.original:
                raise RuntimeError("Patch rollback readback failed")
            raise

    @abstractmethod
    def read(self):
        """Read the runtime data associated with this patch without changing it."""
        raise NotImplementedError


class PatchSet(Patch):
    """A routine whose code and call sites require several coordinated writes."""

    def __init__(self, pine):
        super().__init__(pine)
        self.patches = []

    def apply(self):
        """Apply the complete prepared set while native execution is held."""
        if not self.patches:
            raise RuntimeError("Prepare a nonempty patch set before applying it")
        for patch in self.patches:
            if self.pine.read_bytes(patch.address, len(patch.original)) != patch.original:
                raise RuntimeError("Code changed since patch preparation")
        attempted = []
        try:
            for patch in self.patches:
                attempted.append(patch)
                self.pine.write_bytes(patch.address, patch.replacement)
            for patch in self.patches:
                if self.pine.read_bytes(patch.address, len(patch.replacement)) != patch.replacement:
                    raise RuntimeError("Patch readback failed")
        except Exception:
            for patch in reversed(attempted):
                self.pine.write_bytes(patch.address, patch.original)
                if self.pine.read_bytes(patch.address, len(patch.original)) != patch.original:
                    raise RuntimeError("Patch rollback readback failed")
            raise

    def read(self):
        """Read patched sites for diagnostics; code-only routines have no table."""
        return {patch.address: self.pine.read_bytes(patch.address, len(patch.replacement))
                for patch in self.patches}
