
from ..constants import SKILL_POINT_FLAGS
from .inventories import EventFlagInventory
from ..pypine import Pine


class SkillPointState(EventFlagInventory):

    def __init__(self, pine: Pine) -> None:
        super().__init__(pine, SKILL_POINT_FLAGS)
        self.allowed_locations = None

    def check(self):
        found = super().check()
        return found if self.allowed_locations is None else [
            name for name in found if name in self.allowed_locations]
