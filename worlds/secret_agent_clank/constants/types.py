from dataclasses import dataclass
from typing import NamedTuple


@dataclass(frozen=True)
class Case:
    name: str
    case_id: int
    planet: str
    operative: str
    menu_id: int | None = None


class EventFlag(NamedTuple):
    """A completion flag: set when the byte at `address` has any of `mask`'s bits."""
    address: int
    mask: int

    def is_set(self, value: int) -> bool:
        return bool(value & self.mask)
