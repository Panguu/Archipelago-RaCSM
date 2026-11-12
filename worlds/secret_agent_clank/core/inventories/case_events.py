from collections.abc import Iterable

from ...constants import EventFlag
from ...pypine import Pine


class CaseEventInventory:
    """Reports each location name once get() reads it complete and AP has not confirmed it."""

    def __init__(self, pine: Pine, names: Iterable[str]) -> None:
        self.pine = pine
        self.names: tuple[str, ...] = tuple(names)
        self.completed: dict[str, bool] = dict.fromkeys(self.names, False)

    def get(self, name: str) -> bool:
        raise NotImplementedError

    def sync(self) -> None:
        """Baseline read without reporting anything as newly completed."""
        self.completed = {name: self.get(name) for name in self.names}

    def sync_from_ap(self, checked_location_names: set[str]) -> None:
        for name in self.names:
            if name in checked_location_names:
                self.completed[name] = True

    def check(self) -> list[str]:
        """Location names that are complete but not yet confirmed, so rejected sends are retried."""
        newly: list[str] = []
        for name in self.names:
            if self.get(name):
                if not self.completed.get(name, False):
                    newly.append(name)
            else:
                self.completed[name] = False
        return newly

    def confirm(self, name: str) -> None:
        """Stop reporting `name`; call only once AP has accepted the check."""
        self.completed[name] = True

    def __repr__(self) -> str:
        seen = sum(self.completed.values())
        return f"{type(self).__name__}(completed={seen}/{len(self.names)})"


class EventFlagInventory(CaseEventInventory):
    """Locations whose completion is a bitmask in one byte of EE memory."""

    def __init__(self, pine: Pine, event_flags: dict[str, EventFlag]) -> None:
        super().__init__(pine, event_flags)
        self.event_flags = event_flags

    def get(self, name: str) -> bool:
        flag = self.event_flags[name]
        return flag.is_set(self.pine.read_int8(flag.address))
