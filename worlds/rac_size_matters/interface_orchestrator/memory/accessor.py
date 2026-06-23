from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from .writer import MemoryWriter

if TYPE_CHECKING:
    from ..structs.base import MemoryStruct

class MemoryAccessor:

    def __init__(self, writer: MemoryWriter) -> None:
        self._writer = writer

    def read_struct(self, struct_cls: type[MemoryStruct]) -> MemoryStruct:
        return struct_cls.read_all(self._writer)

    def write_struct(self, instance: MemoryStruct) -> None:
        instance.write_all(self._writer)

    def read_field(self, struct_cls: type[MemoryStruct], field_name: str):
        return struct_cls.read_field(self._writer, field_name)

    def write_field(self, struct_cls: type[MemoryStruct], field_name: str, value) -> None:
        struct_cls.write_field(self._writer, field_name, value)

    def on_struct_change(
        self,
        struct_cls: type[MemoryStruct],
        handler: Callable[[int, bytes], None],
    ) -> None:
        self._writer.on_change(struct_cls.BASE_ADDRESS, handler)

    def on_field_change(
        self,
        struct_cls: type[MemoryStruct],
        field_name: str,
        handler: Callable[[int, bytes], None],
    ) -> None:
        self._writer.on_change(struct_cls.address_of(field_name), handler)

    def remove_struct_handler(
        self,
        struct_cls: type[MemoryStruct],
        handler: Callable[[int, bytes], None],
    ) -> None:
        self._writer.remove_handler(struct_cls.BASE_ADDRESS, handler)

    def remove_field_handler(
        self,
        struct_cls: type[MemoryStruct],
        field_name: str,
        handler: Callable[[int, bytes], None],
    ) -> None:
        self._writer.remove_handler(struct_cls.address_of(field_name), handler)

    def read_raw(self, address: int, size: int) -> bytes:
        return self._writer.read(address, size)

    def write_raw(self, address: int, data: bytes) -> None:
        self._writer.write(address, data)
