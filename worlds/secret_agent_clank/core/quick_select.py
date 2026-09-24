"""Weapon quick-select wheel tracking."""
from typing import TYPE_CHECKING

from .address_maps import QUICK_SELECT_ADDRESS, QUICK_SELECT_SLOT_COUNT

if TYPE_CHECKING:
    from ..pypine import Pine


class QuickSelectState:

    def __init__(self, pine: "Pine") -> None:
        self.pine = pine

    @property
    def slots(self) -> list[int]:
        """The weapon id currently bound to each of the 8 wheel slots, in slot order."""
        return [
            self.pine.read_int32(QUICK_SELECT_ADDRESS + slot * 4)
            for slot in range(QUICK_SELECT_SLOT_COUNT)
        ]

    def __repr__(self) -> str:
        return f"QuickSelectState(slots={self.slots!r})"
