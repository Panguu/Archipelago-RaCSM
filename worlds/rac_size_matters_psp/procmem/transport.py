from __future__ import annotations

import struct
import time
from contextlib import contextmanager
from typing import NoReturn

from ..pypsp.psp import Psp
from . import winmem
from .winmem import WinMemError

# Core/MemMap.h always applies this mask to guest PSP addresses before adding
# them to Memory::base. No-op for every address this codebase uses (all well
# under 0x40000000), but applied unconditionally anyway for correctness.
_PSP_ADDRESS_MASK = 0x3FFFFFFF


class ProcMemTransport:
    """pymem-backed PSP RAM access with local debugger metadata validation.

    No gameplay memory reads or writes are sent to the debugger API.
    """

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
        """Optional local debugger endpoint; otherwise discover by process ID."""
        self._host = host
        self._port = port
        self._timeout = timeout
        self._process_names = process_names

        self._control: Psp | None = None
        self._handle: int | None = None
        self._base: int | None = None
        self._cached_game_id: str = ""

    # ---- connection lifecycle ------------------------------------------------

    def _bootstrap(self, pid: int) -> tuple[str, int]:
        # Debugger is a metadata/control channel only. Never call memory.read*.
        if self._host not in (None, "localhost", "127.0.0.1", "::1"):
            raise self.ConnectionError("pymem requires a local PPSSPP process")
        ports = winmem.debugger_ports(pid)
        if self._port is not None:
            if self._port not in ports:
                raise self.ConnectionError("Debugger port does not belong to the selected PPSSPP process")
            ports = (self._port,)
        for port in ports:
            ws = Psp("127.0.0.1", port, timeout=self._timeout)
            try:
                ws.connect()
                game_id, base = ws.get_game_id(), ws.memory_base()
                self._control = ws
                return game_id, base
            except Exception:
                ws.disconnect()
        raise self.ConnectionError("No local PPSSPP debugger found. Enable Allow remote debugger and load UCUS98633.")

    def connect(self) -> None:
        if self.is_connected():
            return
        try:
            pid = winmem.find_pid_by_name(self._process_names)
            if pid is None:
                raise self.ConnectionError("No running PPSSPP process found")
            game_id, base = self._bootstrap(pid)
            if game_id != "UCUS98633":
                raise self.ConnectionError(f"Unsupported PSP game {game_id!r}; expected UCUS98633")
            if not isinstance(base, int) or base <= 0:
                raise self.ConnectionError("PPSSPP returned an invalid Memory::base")
            self._handle = winmem.open_process(pid)
            self._base = base
            self._cached_game_id = game_id
            self.read_bytes(0x08800000, 4)
        except Exception as exc:
            self.disconnect()
            if isinstance(exc, self.ConnectionError):
                raise
            raise self.ConnectionError(f"Could not attach to PPSSPP: {exc}") from exc

    def disconnect(self) -> None:
        if self._control is not None:
            self._control.disconnect()
        self._control = None
        if self._handle is not None:
            winmem.close_handle(self._handle)
        self._handle = None
        self._base = None
        self._cached_game_id = ""

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

    def _host_address(self, psp_address: int, length: int = 1) -> int:
        if self._handle is None or self._base is None:
            raise self.ConnectionError("Not connected to PPSSPP. Call connect() first.")
        if not isinstance(psp_address, int) or not 0 <= psp_address <= 0xFFFFFFFF:
            raise self.RequestError("Invalid PSP address")
        guest = psp_address & _PSP_ADDRESS_MASK
        if length < 0 or not 0x08000000 <= guest < 0x0A000000 or guest + length > 0x0A000000:
            raise self.RequestError(f"Access outside PSP RAM: {guest:#x}, length={length}")
        return self._base + guest

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
        host_address = self._host_address(address, length)
        if not length:
            return b""
        try:
            return winmem.read_process_memory(self._handle, host_address, length)
        except WinMemError as exc:
            self._fail("read", address, host_address, length, exc)

    def _write_raw(self, address: int, data: bytes) -> None:
        host_address = self._host_address(address, len(data))
        if not data:
            return
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
        return struct.unpack("<Q", self._read_raw(address, 8))[0]

    def read_bytes(self, address: int, length: int) -> bytes:
        return self._read_raw(address, length)

    def read_float(self, address: int) -> float:
        return struct.unpack("<f", self._read_raw(address, 4))[0]

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
        self._write_raw(address, struct.pack("<Q", value & 0xFFFFFFFFFFFFFFFF))

    def write_float(self, address: int, value: float) -> None:
        self._write_raw(address, struct.pack("<f", value))

    def write_bytes(self, address: int, data: bytes) -> None:
        self._write_raw(address, bytes(data))

    def write_string(self, address: int, value: str) -> None:
        data = value.encode("ascii") + b"\x00"
        self.write_bytes(address, data)

    # ---- game / emu status --------------------------------------------------

    def get_game_id(self) -> str:
        return self._cached_game_id

    def validate_session(self) -> None:
        """Check metadata before a gameplay cycle, including game swaps and RAM remaps."""
        if not self.is_connected() or self._control is None:
            raise self.ConnectionError("PPSSPP disconnected")
        try:
            if self._control.get_game_id() != self._cached_game_id or self._control.memory_base() != self._base:
                raise self.ConnectionError("PPSSPP game or memory mapping changed; reconnect required")
        except Exception:
            self.disconnect()
            raise

    def batch_read(self, requests):
        return [int.from_bytes(self.read_bytes(address, size), "little") for size, address in requests]


    @contextmanager
    def paused(self, *, resume_on_error=True):
        """Stop the guest CPU while updating native code; retain an existing pause."""
        self.validate_session()
        status = self._control._request("cpu.status")
        resume = not status.get("stepping", False)
        succeeded = False
        try:
            if resume:
                self._control._request("cpu.stepping")
            if not self._control._request("cpu.status").get("stepping", False):
                raise self.RequestError("PPSSPP did not stop the CPU")
            yield
            succeeded = True
        finally:
            if resume and self._control is not None and (succeeded or resume_on_error):
                self._control._request("cpu.resume")

    def invalidate_code(self):
        """Clear PPSSPP's JIT through a temporary, disabled memory breakpoint.

        PPSSPP's breakpoint manager invalidates compiled code on memcheck
        add/remove. This is control only: no debugger memory read/write event.
        Call with the CPU stepping. Never replace an existing user breakpoint.
        """
        if not self._control._request("cpu.status").get("stepping", False):
            raise self.RequestError("Code invalidation requires a stopped CPU")
        existing = self._control._request("memory.breakpoint.list").get("breakpoints", [])
        used = {entry["address"] for entry in existing}
        address = next((a for a in range(0x08000000, 0x08000100, 4) if a not in used), None)
        if address is None:
            raise self.RequestError("No free temporary breakpoint address")
        try:
            self._control._request("memory.breakpoint.add", address=address, size=1,
                                   enabled=False, log=False, read=False, write=False)
        finally:
            self._control._request("memory.breakpoint.remove", address=address, size=1)
        # PPSSPP 1.20 applies this in its frame loop, not in the request handler.
        # Patch plans still verify original instruction bytes after this wait.
        time.sleep(0.25)
