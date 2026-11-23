
from ...constants import GADGETBOT_CHALLENGE_FLAGS
from .case_events import EventFlagInventory
from ...pypine import Pine


class GadgetbotChallengeInventory(EventFlagInventory):

    def __init__(self, pine: Pine) -> None:
        super().__init__(pine, GADGETBOT_CHALLENGE_FLAGS)
