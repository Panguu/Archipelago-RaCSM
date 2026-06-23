from __future__ import annotations

import ctypes
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..memory.writer import MemoryWriter

class MemoryStruct(ctypes.LittleEndianStructure):

    BASE_ADDRESS: int = 0x0000

    @classmethod
    def address_of(cls, field_name: str) -> int:
        return cls.BASE_ADDRESS + getattr(cls, field_name).offset

    @classmethod
    def size(cls) -> int:
        return ctypes.sizeof(cls)

    @classmethod
    def field_size(cls, field_name: str) -> int:
        return getattr(cls, field_name).size

    @classmethod
    def field_offset(cls, field_name: str) -> int:
        return getattr(cls, field_name).offset

    @classmethod
    def field_names(cls) -> list[str]:
        return [name for name, *_ in cls._fields_]

    @classmethod
    def from_bytes(cls, raw: bytes) -> MemoryStruct:
        instance = cls()
        ctypes.memmove(ctypes.addressof(instance), raw, ctypes.sizeof(cls))
        return instance

    def to_bytes(self) -> bytes:
        return bytes(self)

    def to_dict(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in self.field_names()}

    def update_from_dict(self, data: dict[str, Any]) -> None:
        for name, value in data.items():
            if hasattr(self, name):
                setattr(self, name, value)

    @classmethod
    def read_all(cls, writer: MemoryWriter) -> MemoryStruct:
        raw = writer.read(cls.BASE_ADDRESS, cls.size())
        return cls.from_bytes(raw)

    def write_all(self, writer: MemoryWriter) -> None:
        writer.write(self.BASE_ADDRESS, self.to_bytes())

    @classmethod
    def read_field(cls, writer: MemoryWriter, field_name: str) -> Any:
        descriptor = getattr(cls, field_name)
        raw = writer.read(cls.address_of(field_name), descriptor.size)
        instance = cls()
        ctypes.memmove(
            ctypes.addressof(instance) + descriptor.offset,
            raw,
            descriptor.size,
        )
        return getattr(instance, field_name)

    @classmethod
    def write_field(cls, writer: MemoryWriter, field_name: str, value: Any) -> None:
        descriptor = getattr(cls, field_name)
        instance = cls()
        setattr(instance, field_name, value)
        raw = bytes(instance)[descriptor.offset: descriptor.offset + descriptor.size]
        writer.write(cls.address_of(field_name), raw)

    def __repr__(self) -> str:
        fields = ", ".join(f"{k}={v!r}" for k, v in self.to_dict().items())
        return f"{self.__class__.__name__}({fields})"
