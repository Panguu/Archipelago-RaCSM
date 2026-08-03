"""
The pypsp API.

Client side implementation of PPSSPP's built-in debugger WebSocket protocol
(subprotocol "debugger.ppsspp.org", see Core/Debugger/WebSocket.cpp and
Core/Debugger/WebSocket/*.cpp in the PPSSPP source). Exposes PSP memory
within a running PPSSPP instance.

This intentionally mirrors pypine's `Pine` class method-for-method (same
names, same signatures, same synchronous/blocking calling convention) so
that code written against `Pine` — reads, writes, get_game_id(), etc. —
keeps working unmodified against a `Psp` instance instead. Only the
transport underneath changes: PINE's raw PCSX2 IPC socket becomes a JSON
WebSocket conversation with PPSSPP.

Requires PPSSPP's Settings -> Tools -> Developer tools -> "Allow remote
debugger" to be enabled. See pypsp/discover.py for how the (host, port) to
connect to gets picked automatically.
"""
from __future__ import annotations

import base64
import itertools
import json
import struct
from enum import IntEnum
from typing import Any

import websockets
from websockets.sync.client import ClientConnection, connect as ws_connect

from .discover import resolve_target

_SUBPROTOCOL = "debugger.ppsspp.org"
_CLIENT_NAME = "pypsp"
_CLIENT_VERSION = "0.1.0"


class Psp:
    """ Exposes PSP memory within a running instance of the PPSSPP emulator using its
    built-in debugger WebSocket protocol. """

    class ConnectionError(Exception):
        pass

    class DuplicateConnectionError(Exception):
        pass

    class RequestError(Exception):
        """Raised when PPSSPP responds to a request with an 'error' event
        (e.g. invalid address, CPU not started)."""
        pass

    class EmuStatus(IntEnum):
        RUNNING = 0
        PAUSED = 1
        SHUTDOWN = 2

    def __init__(self, host: str | None = None, port: int | None = None, timeout: float = 5.0):
        """host/port: connect to a specific PPSSPP instance directly. If
        either is omitted, connect() resolves a target automatically via
        pypsp.discover.resolve_target() (report.ppsspp.org, or
        PYPSP_HOST/PYPSP_PORT — see discover.py)."""
        self._host = host
        self._port = port
        self._timeout = timeout
        self._ws: ClientConnection | None = None
        self._ticket_counter = itertools.count(1)

    # ---- connection lifecycle ------------------------------------------------

    def connect(self) -> None:
        if self.is_socket_open():
            return
        host, port = self._host, self._port
        if host is None or port is None:
            try:
                host, port = resolve_target(timeout=self._timeout)
            except Exception as exc:
                raise self.ConnectionError(f"Could not find a PPSSPP instance: {exc}") from exc

        uri = f"ws://{host}:{port}/debugger"
        try:
            self._ws = ws_connect(uri, subprotocols=[_SUBPROTOCOL], open_timeout=self._timeout)
        except Exception as exc:
            self._ws = None
            raise self.ConnectionError(f"Could not connect to PPSSPP at {host}:{port}: {exc}") from exc

        # PPSSPP's docs ask clients to send a "version" event immediately
        # after connecting (Core/Debugger/WebSocket/GameSubscriber.cpp).
        try:
            self._request("version", name=_CLIENT_NAME, version=_CLIENT_VERSION)
        except Exception:
            self._close_socket()
            raise

    def disconnect(self) -> None:
        self._close_socket()

    def is_socket_open(self) -> bool:
        return self._ws is not None

    def is_connected(self) -> bool:
        try:
            _ = self.get_emu_status()
        except Exception:
            self._close_socket()
            return False
        return True

    def _close_socket(self) -> None:
        if self._ws is not None:
            try:
                self._ws.close()
            except Exception:
                pass
        self._ws = None

    # ---- raw request/response --------------------------------------------

    def _request(self, event: str, **params: Any) -> dict[str, Any]:
        if self._ws is None:
            raise self.ConnectionError("Not connected to PPSSPP. Call connect() first.")

        ticket = str(next(self._ticket_counter))
        message = {"event": event, "ticket": ticket, **params}
        try:
            self._ws.send(json.dumps(message))
        except Exception as exc:
            self._close_socket()
            raise self.ConnectionError(f"Lost connection to PPSSPP: {exc}") from exc

        # PPSSPP can send spontaneous broadcast events (game/log/stepping/input)
        # on this same socket at any time. Skip anything that isn't the reply
        # to *this* request (matched by ticket, falling back to event name).
        while True:
            try:
                raw = self._ws.recv(timeout=self._timeout)
            except TimeoutError as exc:
                raise TimeoutError(f"Response to '{event}' timed out.") from exc
            except Exception as exc:
                self._close_socket()
                raise self.ConnectionError(f"Lost connection to PPSSPP: {exc}") from exc

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if data.get("ticket") != ticket and data.get("event") != event:
                continue

            if data.get("event") == "error":
                raise self.RequestError(data.get("message", f"PPSSPP rejected '{event}'"))
            return data

    # ---- reads -------------------------------------------------------------

    def read_int8(self, address: int) -> int:
        return self._request("memory.read_u8", address=address)["value"]

    def read_int16(self, address: int) -> int:
        return self._request("memory.read_u16", address=address)["value"]

    def read_int32(self, address: int) -> int:
        return self._request("memory.read_u32", address=address)["value"]

    def read_int64(self, address: int) -> int:
        # PPSSPP's debugger protocol has no native 64-bit memory op (PSP is a
        # 32-bit MIPS machine) — compose from two little-endian 32-bit reads.
        low = self.read_int32(address)
        high = self.read_int32(address + 4)
        return (high << 32) | low

    def read_bytes(self, address: int, length: int) -> bytes:
        resp = self._request("memory.read", address=address, size=length)
        return base64.b64decode(resp["base64"])

    def read_string(self, address: int, max_length: int) -> str:
        resp = self._request("memory.readString", address=address, type="utf-8")
        return resp.get("value", "")[:max_length]

    # ---- writes --------------------------------------------------------------

    def write_int8(self, address: int, value: int) -> None:
        self._request("memory.write_u8", address=address, value=value)

    def write_int16(self, address: int, value: int) -> None:
        self._request("memory.write_u16", address=address, value=value)

    def write_int32(self, address: int, value: int) -> None:
        self._request("memory.write_u32", address=address, value=value)

    def write_int64(self, address: int, value: int) -> None:
        self.write_int32(address, value & 0xFFFFFFFF)
        self.write_int32(address + 4, (value >> 32) & 0xFFFFFFFF)

    def write_float(self, address: int, value: float) -> None:
        (bits,) = struct.unpack("<I", struct.pack("<f", value))
        self.write_int32(address, bits)

    def write_bytes(self, address: int, data: bytes) -> None:
        encoded = base64.b64encode(data).decode("ascii")
        self._request("memory.write", address=address, base64=encoded)

    def write_string(self, address: int, value: str) -> None:
        data = value.encode("ascii") + b"\x00"
        self.write_bytes(address, data)

    # ---- game / emu status --------------------------------------------------

    def get_game_id(self) -> str:
        resp = self._request("game.status")
        game = resp.get("game")
        return game["id"] if game else ""

    def memory_base(self) -> int:
        """Fetch PPSSPP's own host-memory pointer for the start of its
        emulated-RAM allocation (Memory::base, C++ side), via the
        "memory.base" debugger event (Core/Debugger/WebSocket/
        DisasmSubscriber.cpp's WebSocketDisasmState::Base()).

        Used only by procmem/transport.py's one-time (per-connect) bootstrap
        — not part of the regular read/write hot path, which for that
        variant bypasses this WebSocket entirely in favour of raw
        ReadProcessMemory/WriteProcessMemory into PPSSPP's process using the
        pointer this returns (host_address = memory_base() + (psp_address &
        0x3FFFFFFF), see Core/MemMap.h's GetPointerUnchecked).

        The response's "addressHex" field is a plain hex string with no "0x"
        prefix (PPSSPP's C++ side formats it with "%016llx") — matches how
        every other hex-ish field this module parses is handled: taken
        as-is and fed straight to int(..., 16). Still strips an optional
        "0x"/"0X" prefix defensively in case that format ever changes.
        """
        resp = self._request("memory.base")
        raw = resp.get("addressHex", "0")
        if raw.lower().startswith("0x"):
            raw = raw[2:]
        return int(raw, 16)

    def get_emu_status(self) -> EmuStatus:
        resp = self._request("game.status")
        if resp.get("game") is None:
            return self.EmuStatus.SHUTDOWN
        cpu = self._request("cpu.status")
        if cpu.get("paused"):
            return self.EmuStatus.PAUSED
        return self.EmuStatus.RUNNING


# Re-exported so `except websockets.exceptions.ConnectionClosed` works for
# callers that want to catch the underlying transport error specifically.
ConnectionClosed = websockets.exceptions.ConnectionClosed
