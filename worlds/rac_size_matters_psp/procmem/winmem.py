"""Windows process discovery and pymem-backed memory access.

pymem is imported lazily so world generation does not require a Windows client.
"""
from __future__ import annotations

import ctypes
import subprocess
from ctypes import wintypes

# ---- constants -------------------------------------------------------------

# Ordered list of known PPSSPP Windows executable names, tried in order when
# scanning running processes. Matched case-insensitively. Extend this tuple
# to support another build/distribution's exe name — nothing else needs to
# change.
PPSSPP_PROCESS_NAMES: tuple[str, ...] = (
    "PPSSPPWindows64.exe",
    "PPSSPPWindows.exe",
    "PPSSPPQt.exe",
)

TH32CS_SNAPPROCESS = 0x00000002

PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_ACCESS = (
    PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_QUERY_INFORMATION
)

STILL_ACTIVE = 259

_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

# ---- ctypes struct/function bindings ---------------------------------------

_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)


class PROCESSENTRY32W(ctypes.Structure):
    """Mirrors Tlhelp32.h's PROCESSENTRY32W exactly (field order/types matter
    for ctypes layout). Wide (W) variant so szExeFile is UTF-16 already."""
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t),  # ULONG_PTR
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),  # MAX_PATH
    ]


_kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
_kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE

_kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
_kernel32.Process32FirstW.restype = wintypes.BOOL

_kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
_kernel32.Process32NextW.restype = wintypes.BOOL

_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
_kernel32.CloseHandle.restype = wintypes.BOOL

_kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_kernel32.OpenProcess.restype = wintypes.HANDLE

_kernel32.ReadProcessMemory.argtypes = [
    wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
_kernel32.ReadProcessMemory.restype = wintypes.BOOL

_kernel32.WriteProcessMemory.argtypes = [
    wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
_kernel32.WriteProcessMemory.restype = wintypes.BOOL

_kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
_kernel32.GetExitCodeProcess.restype = wintypes.BOOL


class WinMemError(Exception):
    """Raised for any Win32 process-memory API failure. Always carries the
    real ctypes.GetLastError() code and its FormatError() text, so a failure
    is diagnosable from the exception message alone.
    """

    def __init__(self, action: str, *, winerror: int | None = None):
        self.winerror = winerror if winerror is not None else ctypes.get_last_error()
        try:
            description = ctypes.FormatError(self.winerror)
        except OSError:
            description = "(no description available)"
        super().__init__(f"{action} failed: [WinError {self.winerror}] {description}")


def _raise(action: str) -> None:
    raise WinMemError(action)


# ---- process discovery -------------------------------------------------

def find_pid_by_name(names: tuple[str, ...] = PPSSPP_PROCESS_NAMES) -> int | None:
    """Scan running processes for the first whose executable name
    case-insensitively matches any entry in `names` (checked in order).

    Returns the PID, or None if nothing matched. Raises WinMemError if the
    snapshot itself can't be taken.
    """
    snapshot = _kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == _INVALID_HANDLE_VALUE or not snapshot:
        _raise("CreateToolhelp32Snapshot")

    wanted = {name.lower() for name in names}
    found_by_name: dict[str, int] = {}
    found_pids: set[int] = set()
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        if not _kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
            return None  # empty/failed-to-start enumeration, not an error
        while True:
            exe_name = entry.szExeFile.lower()
            if exe_name in wanted:
                found_pids.add(entry.th32ProcessID)
            if exe_name in wanted and exe_name not in found_by_name:
                found_by_name[exe_name] = entry.th32ProcessID
            if not _kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                break
    finally:
        _kernel32.CloseHandle(snapshot)

    if len(found_pids) > 1:
        raise WinMemError("Multiple PPSSPP processes found; close the extra instances")
    for name in names:
        pid = found_by_name.get(name.lower())
        if pid is not None:
            return pid
    return None


# ---- process handle lifecycle ----------------------------------------------

def open_process(pid: int) -> int:
    """Open a process using pymem; callers own the returned handle."""
    try:
        import pymem.process
        handle = pymem.process.open(pid, debug=False, process_access=PROCESS_ACCESS)
    except ImportError as exc:
        raise WinMemError("pymem is required: install requirements.txt in the client Python environment") from exc
    if not handle:
        import pymem.ressources.kernel32
        raise WinMemError(f"pymem.open(pid={pid})", winerror=pymem.ressources.kernel32.GetLastError())
    return handle


def close_handle(handle: int) -> None:
    """CloseHandle wrapper. Safe to call with an already-closed or invalid
    handle — never raises, so it's safe to call unconditionally on disconnect."""
    if not handle:
        return
    _kernel32.CloseHandle(handle)


def is_process_alive(handle: int) -> bool:
    """True if the process behind `handle` is still running. Used to tell
    apart "this one address is bad" from "PPSSPP itself is gone" when a
    Read/WriteProcessMemory call fails (see transport.py)."""
    exit_code = wintypes.DWORD()
    if not _kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
        return False
    return exit_code.value == STILL_ACTIVE


# ---- memory read/write -------------------------------------------------

def read_process_memory(handle: int, address: int, length: int) -> bytes:
    import pymem.memory
    try:
        return pymem.memory.read_bytes(handle, address, length)
    except Exception as exc:
        raise WinMemError(f"pymem read at {address:#x} ({length} bytes)") from exc


def write_process_memory(handle: int, address: int, data: bytes) -> None:
    import pymem.memory
    try:
        pymem.memory.write_bytes(handle, address, data, len(data))
    except Exception as exc:
        raise WinMemError(f"pymem write at {address:#x} ({len(data)} bytes)") from exc


class ProcessHandle:
    """Thin context-manager/owning wrapper around a HANDLE from open_process(),
    for callers (e.g. tests) that want RAII-style cleanup. transport.py
    manages its own lifecycle explicitly instead."""

    def __init__(self, pid: int):
        self.pid = pid
        self.handle = open_process(pid)

    def close(self) -> None:
        if self.handle:
            close_handle(self.handle)
            self.handle = 0

    def __enter__(self) -> "ProcessHandle":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


def debugger_ports(pid: int) -> tuple[int, ...]:
    """Find only listening sockets owned by the selected local emulator."""
    result = subprocess.run(
        ["netstat", "-ano", "-p", "tcp"], capture_output=True, text=True,
        timeout=5, check=True, creationflags=subprocess.CREATE_NO_WINDOW,
    )
    ports = set()
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) == 5 and fields[0] == "TCP" and fields[-1] == str(pid) and fields[2].endswith(":0"):
            ports.add(int(fields[1].rsplit(":", 1)[1]))
    return tuple(sorted(ports))
