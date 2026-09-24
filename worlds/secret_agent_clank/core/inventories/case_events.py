"""Generic bit-flag-tracked-location inventory, shared by every Inventory class whose locations are constants/types.py's CaseStructure entries with a per-location completion bit (missions, cutscenes, gadgetbot/special/ratchet challenges, skill points) -- they used to each hand-roll the same get/sync/check logic against their own name->address(+offset) dicts (see git history), which is now just this one class parameterized by which CaseStructure tuple it tracks."""
from typing import TYPE_CHECKING

from ...constants.types import CaseStructure

if TYPE_CHECKING:
    from ...pypine import Pine


def read_flag(pine: "Pine", entry: CaseStructure) -> bool:
    """Read one CaseStructure's completion bit directly -- entry.event_address == 0 means "not confirmed live yet", so that always reads as incomplete rather than actually reading address 0."""
    if not entry.event_address:
        return False
    return entry.check_flag(pine.read_int8(entry.event_address))


class CaseEventInventory:

    def __init__(self, pine: "Pine", entries: tuple[CaseStructure, ...]) -> None:
        self.pine = pine
        self.entries = entries
        self.completed: dict[str, bool] = dict.fromkeys((str(entry) for entry in entries), False)

    def get(self, entry: CaseStructure) -> bool:
        return read_flag(self.pine, entry)

    def sync(self) -> None:
        """Baseline read without reporting anything as newly completed."""
        self.completed = {str(entry): self.get(entry) for entry in self.entries}

    def sync_from_ap(self, checked_location_names: set[str]) -> None:
        for entry in self.entries:
            name = str(entry)
            if name in checked_location_names:
                self.completed[name] = True

    def check(self) -> list[str]:
        """Returns full display names that flipped 0 -> 1 since the last call -- including ones already returned by an earlier check() but never confirm()ed, so a name AP's client rejected (see client/pine_mixin.py's _append_location_by_name) is retried instead of silently lost."""
        newly: list[str] = []
        for entry in self.entries:
            name = str(entry)
            now = self.get(entry)
            if now:
                if not self.completed.get(name, False):
                    newly.append(name)
            else:
                self.completed[name] = False
        return newly

    def confirm(self, name: str) -> None:
        """Mark a name check() returned as successfully delivered to AP -- only after this does check() stop re-including it."""
        self.completed[name] = True

    def __repr__(self) -> str:
        seen = sum(self.completed.values())
        return f"{type(self).__name__}(completed={seen}/{len(self.entries)})"
