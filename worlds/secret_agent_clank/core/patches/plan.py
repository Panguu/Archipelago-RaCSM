"""Return shape shared by patches/weapon_pickup.py and patches/vendor_only.py -- patches/hooks.py's LocationHooks.prepare() picks whichever builder applies, then copies this straight onto its own instance attributes."""
from dataclasses import dataclass, field

from .asm import Patch


@dataclass
class PatchPlan:
    patches: list[Patch]
    locations: dict[str, dict[int, str]]
    tables: dict[str, int]
    reported: set = field(default_factory=set)
    marker_address: int = 0
    module: int = 0
    entitlement_table: "int | None" = None
