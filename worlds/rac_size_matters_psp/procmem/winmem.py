"""Raw Win32 process-memory access via ctypes — no third-party dependencies.

Deliberately does not use pywin32 or psutil: this module ships inside an
Archipelago .apworld that end users install into their own Archipelago
Python environment, and we can't assume either package is present (or ask
users to pip install anything extra just to run a client). Everything here
is plain ctypes against kernel32.dll, using the same well-documented Win32
APIs tools like Cheat Engine are built on: CreateToolhelp32Snapshot to find
the PPSSPP process by name, OpenProcess to get a handle to it, and
ReadProcessMemory/WriteProcessMemory to copy bytes directly into/out of its
address space.

Known caveat — bitness must match: ReadProcessMemory/WriteProcessMemory
require the calling process and the target process to be the same
bitness (both 32-bit or both 64-bit). A 32-bit Python cannot reliably read a
64-bit PPSSPP process's memory (and vice versa) — Windows will generally
fail the OpenProcess or ReadProcessMemory/WriteProcessMemory call outright
rather than silently returning corrupt data, so this surfaces as a
WinMemError with a real GetLastError code (commonly ERROR_ACCESS_DENIED)
rather than a crash or silent corruption. This module does not proactively
detect/compare bitness (reliably doing so from the outside — e.g. via
IsWow64Process — adds real complexity for a case that shouldn't come up on a
normal modern Windows install, where both a stock python.org/venv Python and
a stock PPSSPP release build are 64-bit); if it ever does happen, the error
message below is what will explain it.

This module is Windows-only and will fail to import cleanly (ctypes.WinDLL/
ctypes.wintypes don't exist) on any other platform — that's expected; the
whole point of this variant is Win32-specific process introspection.
"""
from __future__ import annotations

import ctypes
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
    """Mirrors Tlhelp32.h's PROCESSENTRY32W exactly (field order/types
    matter for ctypes to compute the right struct layout/offsets) — the wide
    (W) variant so szExeFile is UTF-16 and needs no extra decoding step."""
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
    """Raised for any Win32 process-memory API failure (process not found,
    OpenProcess denied, ReadProcessMemory/WriteProcessMemory failed, etc.).

    Always carries the real ctypes.GetLastError() code and
    ctypes.FormatError() text for that code, so a failure is diagnosable
    from the exception message alone rather than a bare "operation failed"
    or a cryptic ctypes crash.
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
    """Scan running processes via CreateToolhelp32Snapshot for the first one
    whose executable name case-insensitively matches any entry in `names`
    (checked in `names` order — first name in the list wins if more than
    one candidate process happens to be running).

    Returns the PID, or None if nothing matched. Raises WinMemError if the
    snapshot itself can't be taken (rare — a real OS-level failure, not
    "PPSSPP isn't running").
    """
    snapshot = _kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == _INVALID_HANDLE_VALUE or not snapshot:
        _raise("CreateToolhelp32Snapshot")

    wanted = {name.lower() for name in names}
    found_by_name: dict[str, int] = {}
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        if not _kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
            # An empty/failed-to-start snapshot enumeration — not an error
            # worth raising for, just means "found nothing".
            return None
        while True:
            exe_name = entry.szExeFile.lower()
            if exe_name in wanted and exe_name not in found_by_name:
                found_by_name[exe_name] = entry.th32ProcessID
            if not _kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                break
    finally:
        _kernel32.CloseHandle(snapshot)

    for name in names:
        pid = found_by_name.get(name.lower())
        if pid is not None:
            return pid
    return None


# ---- process handle lifecycle ----------------------------------------------

def open_process(pid: int) -> int:
    """OpenProcess with PROCESS_VM_READ | PROCESS_VM_WRITE |
    PROCESS_VM_OPERATION | PROCESS_QUERY_INFORMATION. Returns the raw HANDLE
    as a Python int. Raises WinMemError on failure (e.g. access denied,
    often the symptom of a 32/64-bit mismatch between this Python process
    and the target — see this module's docstring)."""
    handle = _kernel32.OpenProcess(PROCESS_ACCESS, False, pid)
    if not handle:
        _raise(f"OpenProcess(pid={pid})")
    return handle


def close_handle(handle: int) -> None:
    """CloseHandle wrapper. Safe to call with a handle that's already been
    closed or is otherwise invalid — failures here are logged-worthy at most,
    never worth crashing a disconnect over, so this never raises."""
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
    """ReadProcessMemory wrapper. `address` is a host-process pointer
    (Python int, treated as 64-bit-capable — NOT assumed to fit in 32 bits;
    PPSSPP's Windows build is normally 64-bit). Returns exactly `length`
    bytes, or raises WinMemError (including on a short/partial read — a
    partial copy generally means part of the requested range isn't valid
    memory in the target process, e.g. ERROR_PARTIAL_COPY)."""
    buffer = ctypes.create_string_buffer(length)
    bytes_read = ctypes.c_size_t(0)
    ok = _kernel32.ReadProcessMemory(
        handle, ctypes.c_void_p(address), buffer, ctypes.c_size_t(length), ctypes.byref(bytes_read)
    )
    if not ok or bytes_read.value != length:
        _raise(f"ReadProcessMemory(address=0x{address:X}, length={length})")
    return buffer.raw[:length]


def write_process_memory(handle: int, address: int, data: bytes) -> None:
    """WriteProcessMemory wrapper. `address` is a host-process pointer
    (Python int, 64-bit-capable)."""
    length = len(data)
    buffer = ctypes.create_string_buffer(data, length)
    bytes_written = ctypes.c_size_t(0)
    ok = _kernel32.WriteProcessMemory(
        handle, ctypes.c_void_p(address), buffer, ctypes.c_size_t(length), ctypes.byref(bytes_written)
    )
    if not ok or bytes_written.value != length:
        _raise(f"WriteProcessMemory(address=0x{address:X}, length={length})")


class ProcessHandle:
    """Thin context-manager/owning wrapper around a HANDLE from
    open_process(), so callers that want RAII-style cleanup don't have to
    remember to call close_handle() themselves. transport.py manages its
    own lifecycle explicitly instead (connect()/disconnect() bracket the
    whole client session, not a single `with` block), but this is here for
    any other caller — e.g. tests — that wants the safer pattern."""

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
