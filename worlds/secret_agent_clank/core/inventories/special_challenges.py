
from ...constants import SPECIAL_CHALLENGE_FLAGS
from .case_events import EventFlagInventory
from ...pypine import Pine


class SpecialChallengeInventory(EventFlagInventory):

    def __init__(self, pine: Pine) -> None:
        super().__init__(pine, SPECIAL_CHALLENGE_FLAGS)

    def sync(self) -> None:
        """Saved completions remain pending until AP accepts their checks."""
        pass

    def check(self) -> list[str]:
        return [name for name in self.names if not self.completed[name] and self.get(name)]
