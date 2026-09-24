"""Native keycard flag 0xAA: red bit 0, blue bit 1, yellow bit 2."""
from dataclasses import dataclass

from .planets import SACCases
from .types import CaseStructure, SACTags, group_by_case


@dataclass(frozen=True)
class SACKeycards:
    RED_KEYCARD = "Red Keycard"
    BLUE_KEYCARD = "Blue Keycard"
    YELLOW_KEYCARD = "Yellow Keycard"


KEYCARDS: tuple[CaseStructure, ...] = (
    CaseStructure(SACCases.ASYANICA_ROOFTOPS, SACKeycards.RED_KEYCARD, SACTags.KEYCARD),
    CaseStructure(SACCases.INSIDE_THE_A_EYE, SACKeycards.BLUE_KEYCARD, SACTags.KEYCARD),
    CaseStructure(SACCases.SAINT_QWARK, SACKeycards.YELLOW_KEYCARD, SACTags.KEYCARD),
)

KEYCARDS_BY_CASE: dict[str, tuple[str, ...]] = group_by_case(
    tuple(entry for entry in KEYCARDS if entry.case_name != "TODO")
)


@dataclass(frozen=True)
class SACKeycardLocations:
    """Full display-name constants for keycard locations, for use in rules files
    (mirrors SACSkillPointLocations/SACAlienCodeLocations -- get_location() needs
    the full "{operative}: {case}: Keycard: {name}" string, not the bare event name)."""

    RED_KEYCARD = str(KEYCARDS[0])
    BLUE_KEYCARD = str(KEYCARDS[1])
    YELLOW_KEYCARD = str(KEYCARDS[2])
