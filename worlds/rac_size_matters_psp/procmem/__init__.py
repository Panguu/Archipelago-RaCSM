"""Local Windows PPSSPP memory access through pymem."""
from __future__ import annotations

from .transport import ProcMemTransport
from .winmem import PPSSPP_PROCESS_NAMES, WinMemError

__all__ = ["PPSSPP_PROCESS_NAMES", "ProcMemTransport", "WinMemError"]
