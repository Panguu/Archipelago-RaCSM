from abc import ABC, abstractmethod

from ..batch_io import read_blocks


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

    @abstractmethod
    def read(self):
        """Read the runtime data associated with this patch without changing it."""
        raise NotImplementedError


class PatchSet(Patch):
    """A build-time collection of routine and call-site replacements."""

    def __init__(self, pine):
        super().__init__(pine)
        self.patches = []

    def read(self):
        """Read patched sites for diagnostics; code-only routines have no table."""
        current = read_blocks(self.pine, [(patch.address, len(patch.replacement)) for patch in self.patches])
        return {patch.address: data for patch, data in zip(self.patches, current)}
