from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

from .base import MemoryStruct


@dataclass
class AddressMap:

    interface_id: str = "default"
    _structs: list[type[MemoryStruct]] = field(default_factory=list, repr=False)

    def register(self, *struct_classes: type[MemoryStruct]) -> None:
        for cls in struct_classes:
            if cls not in self._structs:
                self._structs.append(cls)

    def structs(self) -> Iterator[type[MemoryStruct]]:
        yield from self._structs

    def get(self, name: str) -> type[MemoryStruct] | None:
        for cls in self._structs:
            if cls.__name__ == name:
                return cls
        return None
