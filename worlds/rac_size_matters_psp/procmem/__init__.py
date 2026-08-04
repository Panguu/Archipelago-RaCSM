"""Direct-process-memory transport for PPSSPP on Windows.

Instead of routing every PSP-memory read/write through PPSSPP's debugger
WebSocket protocol (see ../pypsp/), this package attaches straight to the
running PPSSPP.exe process via Windows' ReadProcessMemory/WriteProcessMemory
APIs. See transport.py and winmem.py for the implementation.

Windows-only.
"""
from __future__ import annotations

from .transport import ProcMemTransport
from .winmem import PPSSPP_PROCESS_NAMES, WinMemError

__all__ = ["PPSSPP_PROCESS_NAMES", "ProcMemTransport", "WinMemError"]
