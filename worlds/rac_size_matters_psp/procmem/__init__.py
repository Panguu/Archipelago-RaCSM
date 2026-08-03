"""Direct-process-memory transport for PPSSPP on Windows.

Instead of routing every individual PSP-memory read/write through PPSSPP's
debugger WebSocket protocol (see ../pypsp/), this package attaches straight
to the running PPSSPP.exe process using the same technique tools like Cheat
Engine use: Windows' ReadProcessMemory/WriteProcessMemory APIs via ctypes,
reading/writing PPSSPP's own host-memory representation of the emulated PSP
RAM directly. See transport.py's module docstring for the full design and
winmem.py for the raw Win32 plumbing underneath it.

Windows-only. Nothing in here will work (or is expected to work) on other
platforms — the whole point of this variant is Win32-specific process
introspection.
"""
from __future__ import annotations

from .transport import ProcMemTransport
from .winmem import PPSSPP_PROCESS_NAMES, WinMemError

__all__ = ["PPSSPP_PROCESS_NAMES", "ProcMemTransport", "WinMemError"]
