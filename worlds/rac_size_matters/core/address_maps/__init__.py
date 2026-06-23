"""Platform address map. Import from here — not from ps2.py directly.

When PSP support is added, set RACSM_PLATFORM=psp in the environment before
launching to select PSP addresses instead of PS2.
"""
import os as _os

_platform = _os.environ.get("RACSM_PLATFORM", "ps2").lower()

if _platform == "psp":
    from .psp import *  # type: ignore[assignment]  # noqa: F403  # Not yet implemented
else:
    from .ps2 import *  # noqa: F403
