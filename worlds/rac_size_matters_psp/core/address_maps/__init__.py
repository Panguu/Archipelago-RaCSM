"""Platform address map. Import from here — not from psp.py directly.

This world only ever talks to PPSSPP (see client/psp_mixin.py), so there's
no platform to switch between anymore — always PSP addresses.
"""
from .psp import *  # noqa: F403
