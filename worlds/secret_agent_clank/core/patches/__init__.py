"""Every module here reads original native instruction bytes, builds REPLACEMENT machine code, and writes it into the game's code region to change control flow -- as opposed to core/'s other files, which only read/write plain data fields (flags, counts, HUD text) and never construct new instructions."""
from .asm import MARKER, Patch, branch, jump, packed, words
from .entitlements import Entitlements
from .gameFlags import GameFlags
from .hooks import LocationHooks
from .locations import PICKUP_LOCATIONS, VENDOR_LOCATIONS
from .plan import PatchPlan

__all__ = [
    "MARKER",
    "PICKUP_LOCATIONS",
    "VENDOR_LOCATIONS",
    "Entitlements",
    "GameFlags",
    "LocationHooks",
    "Patch",
    "PatchPlan",
    "branch",
    "jump",
    "packed",
    "words",
]
