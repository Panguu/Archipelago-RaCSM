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
        raise NotImplementedError

    @abstractmethod
    def read(self):
        raise NotImplementedError


class PatchSet(Patch):
    def __init__(self, pine):
        super().__init__(pine)
        self.patches = []

    def read(self):
        current = read_blocks(self.pine, [(patch.address, len(patch.replacement)) for patch in self.patches])
        return {patch.address: data for patch, data in zip(self.patches, current)}
