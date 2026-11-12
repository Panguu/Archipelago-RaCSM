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
    entitlement_table: int | None = None
    gadget_base: int | None = None
