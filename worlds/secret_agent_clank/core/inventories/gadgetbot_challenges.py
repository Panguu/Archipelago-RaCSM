"""Gadgetbot Challenge completion tracking -- see constants/gadgetbot_challenges.py's GADGETBOT_CHALLENGES for the per-challenge case/address data (CONFIRMED live for every entry so far)."""
from typing import TYPE_CHECKING

from ...constants.gadgetbot_challenges import GADGETBOT_CHALLENGES
from .case_events import CaseEventInventory

if TYPE_CHECKING:
    from ...pypine import Pine


class GadgetbotChallengeInventory(CaseEventInventory):

    def __init__(self, pine: "Pine") -> None:
        super().__init__(pine, GADGETBOT_CHALLENGES)
