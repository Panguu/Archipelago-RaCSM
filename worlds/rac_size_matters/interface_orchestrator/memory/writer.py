from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable

from .base import MemoryInterface

logger = logging.getLogger("Client")


class MemoryWriter:

    def __init__(self, interface: MemoryInterface) -> None:
        self._interface = interface
        self._handlers: dict[int, list[Callable[[int, bytes], None]]] = defaultdict(list)

    def read(self, address: int, size: int) -> bytes:
        return self._interface.read(address, size)

    def write(self, address: int, data: bytes) -> None:
        self._interface.write(address, data)

    def on_change(self, address: int, handler: Callable[[int, bytes], None]) -> None:
        self._handlers[address].append(handler)

    def remove_handler(self, address: int, handler: Callable[[int, bytes], None]) -> None:
        handlers = self._handlers.get(address, [])
        if handler in handlers:
            handlers.remove(handler)

    def clear_handlers(self, address: int | None = None) -> None:
        if address is None:
            self._handlers.clear()
        else:
            self._handlers.pop(address, None)

    def notify_change(self, address: int, new_value: bytes) -> None:
        for handler in list(self._handlers.get(address, [])):
            try:
                handler(address, new_value)
            except Exception:
                # A single handler failing must not kill the poller thread —
                # that would silently stop ALL memory-change detection (planet
                # transitions, skill points, missions, etc.) for the rest of
                # the session.
                logger.exception(f"[RAC] Struct-change handler failed for address {address:#010x}")

    def swap_interface(self, interface: MemoryInterface) -> None:
        self._interface.disconnect()
        self._interface = interface
        self._interface.connect()
