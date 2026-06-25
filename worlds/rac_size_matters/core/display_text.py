from __future__ import annotations

import asyncio
import struct
from dataclasses import dataclass

# Colour encoding
# 0x09 = colour-change marker; the following byte selects the colour.

class TextColour:
    YELLOW  = bytes([0x90, 0x10])
    PURPLE = bytes([0x90, 0x04])
    RED = bytes([0x90, 0x03])
    ORANGE = bytes([0x90, 0x02])
    WHITE  = bytes([0x90, 0x01])


def colored_text(*parts: bytes | str) -> bytes:
    """Build a null-terminated byte string from text and TextColour constants.

    Example:
        colored_text("Received ", TextColour.PURPLE, "X", TextColour.WHITE, " from Y")
    """
    buf = bytearray()
    for part in parts:
        buf.extend(part if isinstance(part, (bytes, bytearray)) else part.encode("ascii"))
    buf.append(0x00)
    return bytes(buf)


from ..interface_orchestrator.memory.accessor import MemoryAccessor
from ..interface_orchestrator.state.base_state import BaseState
from ..interface_orchestrator.storage.local import LocalStorage
from ..interface_orchestrator.structs.address_map import AddressMap
from .address_maps import (
    MULTI_LINE_TEXT_BOX_BY_PLANET,
    PLANET_ADDRESSES,
    SMALL_TEXT_BOX_BY_PLANET,
    STATIC_TEXT_BUFFER as _STATIC_TEXT_BUFFER,
)
from .structs.game import CountdownTimerStruct, VendorVisibilityStruct

# Data
# Both box types share the same in-memory layout relative to their base address:
#   base + 0x00  countdown_timer      (float, seconds remaining)
#   base + 0x20  is_visible           (u16, message-ID when visible)
#   base + 0x28  message_str_pointer  (u16, current message ID)

@dataclass(frozen=True)
class SmallTextBox:
    planet_id: int
    base_addr: int

    @property
    def countdown_timer(self) -> int:     return self.base_addr
    @property
    def is_visible(self) -> int:          return self.base_addr + 0x20
    @property
    def message_str_pointer(self) -> int: return self.base_addr + 0x28

    def write_message(self, ipc, msg_id: int) -> None:
        ipc.write_int16(self.message_str_pointer, msg_id)

    def write_text(self, ipc, text: bytes) -> None:
        ipc.write_bytes(_STATIC_TEXT_BUFFER, text)
        ipc.write_int32(self.message_str_pointer, _STATIC_TEXT_BUFFER)
        ipc.write_int8(self.countdown_timer, 0xAA)
        trigger_addr = self.base_addr + 0x39
        ipc.write_int8(trigger_addr, 0x02)
        asyncio.get_event_loop().call_later(7.0, lambda: ipc.write_int8(trigger_addr, 0x01))


@dataclass(frozen=True)
class MultiLineTextBox:
    planet_id: int
    base_addr: int

    @property
    def countdown_timer(self) -> int:     return self.base_addr
    @property
    def is_visible(self) -> int:          return self.base_addr + 0x20
    @property
    def message_str_pointer(self) -> int: return self.base_addr + 0x28

    def write_message(self, ipc, msg_id: int) -> None:
        ipc.write_int16(self.message_str_pointer, msg_id)

    def write_text(self, ipc, text: bytes) -> None:
        ipc.write_bytes(_STATIC_TEXT_BUFFER, text)
        ipc.write_int32(self.message_str_pointer, _STATIC_TEXT_BUFFER)
        ipc.write_int8(self.countdown_timer, 0xFF)
        trigger_addr = self.base_addr + 0x39
        ipc.write_int8(trigger_addr, 0x02)
        asyncio.get_event_loop().call_later(5.0, lambda: ipc.write_int8(trigger_addr, 0x01))


TextBoxConfig = SmallTextBox | MultiLineTextBox


SmallTextBoxAddrs: list[SmallTextBox] = [
    SmallTextBox(planet_id=pid, base_addr=addr)
    for pid, addr in SMALL_TEXT_BOX_BY_PLANET.items()
]

MultiLineTextBoxAddrs: list[MultiLineTextBox] = [
    MultiLineTextBox(planet_id=pid, base_addr=addr)
    for pid, addr in MULTI_LINE_TEXT_BOX_BY_PLANET.items()
]


# State (runtime)

class DisplayedTextBoxState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self.is_displayed: bool = False
        self._active_config: TextBoxConfig | None = None

    def activate(self, config: TextBoxConfig) -> None:
        self._active_config = config

    def deactivate(self) -> None:
        self._active_config = None
        self.is_displayed = False

    def on_exit(self) -> None:
        self.is_displayed = False

    def _register_handlers(self) -> None:
        cls = self._countdown_struct()
        if cls is not None:
            self.accessor.on_struct_change(cls, self._on_countdown_change)

    def _unregister_handlers(self) -> None:
        cls = self._countdown_struct()
        if cls is not None:
            self.accessor.remove_struct_handler(cls, self._on_countdown_change)

    def _countdown_struct(self) -> type[CountdownTimerStruct] | None:
        for cls in self.addresses.structs():
            if issubclass(cls, CountdownTimerStruct) and cls is not CountdownTimerStruct:
                return cls
        return None

    def _on_countdown_change(self, address: int, new_bytes: bytes) -> None:
        del address
        if len(new_bytes) < 4:
            return
        timer = struct.unpack_from("<f", new_bytes)[0]
        was_displayed = self.is_displayed
        self.is_displayed = timer > 0
        if self.is_displayed and not was_displayed:
            self.on_text_box_shown()
        elif not self.is_displayed and was_displayed:
            self.on_text_box_hidden()

    def sync(self) -> None:
        cls = self._countdown_struct()
        if cls is None:
            return
        raw = self.accessor.read_raw(cls.BASE_ADDRESS, 4)
        if len(raw) < 4:
            return
        timer = struct.unpack_from("<f", raw)[0]
        self.is_displayed = timer > 0

    def on_text_box_shown(self) -> None:
        pass

    def on_text_box_hidden(self) -> None:
        pass

    def __repr__(self) -> str:
        return f"DisplayedTextBoxState(is_displayed={self.is_displayed})"

class DisplayTextBoxState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self.is_vendor_prompt: bool    = False
        self._vendor_value: int        = 0
        self._active_config: TextBoxConfig | None = None
        self.on_vendor_prompt_shown:  callable = lambda: None
        self.on_vendor_prompt_hidden: callable = lambda: None

    def activate(self, config: TextBoxConfig) -> None:
        self._active_config = config
        pa = PLANET_ADDRESSES.get(config.planet_id)
        self._vendor_value  = pa.vendor_prompt_id if pa is not None and pa.vendor_prompt_id is not None else 0

    def deactivate(self) -> None:
        self._active_config = None
        self.is_vendor_prompt = False

    def on_exit(self) -> None:
        self.is_vendor_prompt = False

    def _register_handlers(self) -> None:
        cls = self._visibility_struct()
        if cls is not None:
            self.accessor.on_struct_change(cls, self._on_visibility_change)

    def _unregister_handlers(self) -> None:
        cls = self._visibility_struct()
        if cls is not None:
            self.accessor.remove_struct_handler(cls, self._on_visibility_change)

    def _visibility_struct(self) -> type[VendorVisibilityStruct] | None:
        for cls in self.addresses.structs():
            if issubclass(cls, VendorVisibilityStruct) and cls is not VendorVisibilityStruct:
                return cls
        return None

    def _on_visibility_change(self, address: int, new_bytes: bytes) -> None:
        del address
        if len(new_bytes) < 2:
            return
        raw = struct.unpack_from("<H", new_bytes)[0]
        msg_val = ((raw & 0xFF) << 8) | (raw >> 8)
        was_prompt = self.is_vendor_prompt
        self.is_vendor_prompt = (msg_val == self._vendor_value)
        if self.is_vendor_prompt and not was_prompt:
            self.on_vendor_prompt_shown()
        elif not self.is_vendor_prompt and was_prompt:
            self.on_vendor_prompt_hidden()

    def sync(self) -> None:
        cls = self._visibility_struct()
        if cls is None:
            return
        raw_bytes = self.accessor.read_raw(cls.BASE_ADDRESS, 2)
        if len(raw_bytes) < 2:
            return
        raw = struct.unpack_from("<H", raw_bytes)[0]
        msg_val = ((raw & 0xFF) << 8) | (raw >> 8)
        self.is_vendor_prompt = (msg_val == self._vendor_value)

    def __repr__(self) -> str:
        return f"DisplayTextBoxState(vendor_prompt={self.is_vendor_prompt})"
