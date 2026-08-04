from __future__ import annotations

import struct
from typing import NoReturn

from ..pypsp.psp import Psp
from . import winmem
from .winmem import WinMemError

# Core/MemMap.h always applies this mask to guest PSP addresses before adding
# them to Memory::base. No-op for every address this codebase uses (all well
# under 0x40000000), but applied unconditionally anyway for correctness.
_PSP_ADDRESS_MASK = 0x3FFFFFFF


class ProcMemTransport:
    """Same public surface as pypsp.Psp, backed by direct ReadProcessMemory/
    WriteProcessMemory calls into PPSSPP's own process instead of its
    debugger WebSocket — except for connect()'s one-time bootstrap, which
    still briefly uses the WebSocket."""

    # Re-exported so existing ``except Psp.RequestError``/``except
    # Psp.ConnectionError`` call sites in core/*.py keep working unchanged
    # against a ProcMemTransport instance too, since this class raises the
    # same exception classes rather than reimplementing its own.
    ConnectionError = Psp.ConnectionError
    DuplicateConnectionError = Psp.DuplicateConnectionError
    RequestError = Psp.RequestError

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        timeout: float = 5.0,
        process_names: tuple[str, ...] = winmem.PPSSPP_PROCESS_NAMES,
    ) -> None:
        """host/port/timeout: passed through to the short-lived pypsp.Psp
        connection used for connect()'s bootstrap (None host/port means
        auto-discover). process_names: Windows executable names to try, in
        order, when locating the running PPSSPP process."""
        self._host = host
        self._port = port
        self._timeout = timeout
        self._process_names = process_names

        self._handle: int | None = None
        self._base: int | None = None
        self._cached_game_id: str = ""

    # ---- connection lifecycle ------------------------------------------------

    def _bootstrap(self) -> tuple[str, int]:
        """Open a short-lived pypsp.Psp WebSocket connection, fetch the
        currently-loaded game id and Memory::base, then close it. Lets
        Psp.ConnectionError propagate uncaught so callers see the same
        failure type pypsp.Psp itself raises."""
        ws = Psp(self._host, self._port, timeout=self._timeout)
        try:
            ws.connect()
            game_id = ws.get_game_id()
            base = ws.memory_base()
        finally:
            ws.disconnect()
        return game_id, base

    def connect(self) -> None:
        if self._handle is not None:
            return

        # Bootstrap first: if the debugger WebSocket isn't reachable, don't
        # bother scanning for the process — let that failure surface as-is.
        game_id, base = self._bootstrap()
        self._cached_game_id = game_id
        self._base = base

        # Doesn't compare game_id against an expected value — that's the
        # caller's job (client/psp_mixin.py's _attempt_psp_connect()), so this
        # transport doesn't need to know EXPECTED_GAME_ID.
        pid = winmem.find_pid_by_name(self._process_names)
        if pid is None:
            raise self.ConnectionError(
                "Could not find a running PPSSPP process (tried: "
                f"{', '.join(self._process_names)}). Is PPSSPP running?"
            )
        try:
            self._handle = winmem.open_process(pid)
        except WinMemError as exc:
            raise self.ConnectionError(f"Could not open PPSSPP process (pid={pid}): {exc}") from exc

    def disconnect(self) -> None:
        if self._handle is not None:
            winmem.close_handle(self._handle)
        self._handle = None
        self._base = None

    def is_socket_open(self) -> bool:
        return self._handle is not None

    def is_connected(self) -> bool:
        if self._handle is None:
            return False
        if not winmem.is_process_alive(self._handle):
            self.disconnect()
            return False
        return True

    # ---- raw memory access ---------------------------------------------------

    def _host_address(self, psp_address: int) -> int:
        if self._handle is None or self._base is None:
            raise self.ConnectionError("Not connected to PPSSPP. Call connect() first.")
        return self._base + (psp_address & _PSP_ADDRESS_MASK)

    def _fail(self, verb: str, psp_address: int, host_address: int, length: int,
               exc: WinMemError) -> NoReturn:
        """Turn a raw WinMemError into either a Psp.ConnectionError (PPSSPP
        itself is gone) or a Psp.RequestError (PPSSPP is running but this
        address/op failed, e.g. one of the still-unverified computed addresses
        in core/address_maps/psp.py). Distinguishing the two lets core.py's
        existing ``except Psp.RequestError`` guards keep working unchanged."""
        if not winmem.is_process_alive(self._handle):
            self.disconnect()
            raise self.ConnectionError(
                f"Lost connection to PPSSPP: process no longer running "
                f"({verb} of {length} byte(s) at PSP address {psp_address:#010x}): {exc}"
            ) from exc
        raise self.RequestError(
            f"{verb} of {length} byte(s) at PSP address {psp_address:#010x} "
            f"(host 0x{host_address:X}) failed: {exc}"
        ) from exc

    def _read_raw(self, address: int, length: int) -> bytes:
        host_address = self._host_address(address)
        try:
            return winmem.read_process_memory(self._handle, host_address, length)
        except WinMemError as exc:
            self._fail("read", address, host_address, length, exc)

    def _write_raw(self, address: int, data: bytes) -> None:
        host_address = self._host_address(address)
        try:
            winmem.write_process_memory(self._handle, host_address, data)
        except WinMemError as exc:
            self._fail("write", address, host_address, len(data), exc)

    # ---- reads -------------------------------------------------------------

    def read_int8(self, address: int) -> int:
        return self._read_raw(address, 1)[0]

    def read_int16(self, address: int) -> int:
        (value,) = struct.unpack("<H", self._read_raw(address, 2))
        return value

    def read_int32(self, address: int) -> int:
        (value,) = struct.unpack("<I", self._read_raw(address, 4))
        return value

    def read_int64(self, address: int) -> int:
        # Same compose-from-two-32-bit-reads approach as pypsp.Psp — PSP is
        # a 32-bit MIPS machine, PPSSPP's own debugger protocol has no
        # native 64-bit memory op either.
        low = self.read_int32(address)
        high = self.read_int32(address + 4)
        return (high << 32) | low

    def read_bytes(self, address: int, length: int) -> bytes:
        return self._read_raw(address, length)

    def read_string(self, address: int, max_length: int) -> str:
        # Unlike pypsp.Psp.read_string() (which asks PPSSPP's C++ side to find
        # the null terminator), there's no server here to do that — read
        # max_length raw bytes and find the terminator locally instead.
        raw = self._read_raw(address, max_length)
        nul = raw.find(b"\x00")
        if nul != -1:
            raw = raw[:nul]
        return raw.decode("utf-8", errors="replace")

    # ---- writes --------------------------------------------------------------

    def write_int8(self, address: int, value: int) -> None:
        self._write_raw(address, struct.pack("<B", value & 0xFF))

    def write_int16(self, address: int, value: int) -> None:
        self._write_raw(address, struct.pack("<H", value & 0xFFFF))

    def write_int32(self, address: int, value: int) -> None:
        self._write_raw(address, struct.pack("<I", value & 0xFFFFFFFF))

    def write_int64(self, address: int, value: int) -> None:
        self.write_int32(address, value & 0xFFFFFFFF)
        self.write_int32(address + 4, (value >> 32) & 0xFFFFFFFF)

    def write_float(self, address: int, value: float) -> None:
        self._write_raw(address, struct.pack("<f", value))

    def write_bytes(self, address: int, data: bytes) -> None:
        self._write_raw(address, bytes(data))

    def write_string(self, address: int, value: str) -> None:
        data = value.encode("ascii") + b"\x00"
        self.write_bytes(address, data)

    # ---- game / emu status --------------------------------------------------

    def get_game_id(self) -> str:
        """Returns the currently-loaded game's disc id, cached from connect()'s
        bootstrap check. Never re-opens the WebSocket itself, so a game
        swapped inside an already-running PPSSPP process won't be caught here."""
        return self._cached_game_id
