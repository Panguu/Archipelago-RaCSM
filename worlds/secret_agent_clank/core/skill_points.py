"""Skill point tracking; flags (all 65 confirmed live) are in constants/skillpoints.py."""
from typing import TYPE_CHECKING

from ..constants.skillpoints import SKILL_POINT_FLAGS
from .inventories.case_events import EventFlagInventory

if TYPE_CHECKING:
    from ..pypine import Pine


class SkillPointState(EventFlagInventory):

    def __init__(self, pine: "Pine") -> None:
        super().__init__(pine, SKILL_POINT_FLAGS)
        self.allowed_locations = None

    def check(self):
        found = super().check()
        return found if self.allowed_locations is None else [
            name for name in found if name in self.allowed_locations]
