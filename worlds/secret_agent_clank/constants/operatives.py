from dataclasses import dataclass


@dataclass(frozen=True)
class SACOperatives:
    """String constants for each Operatives group."""

    RATCHET = "Ratchet"
    CLANK = "Clank"
    GADGETBOTS = "Gadgetbots"
    QWARK = "Qwark"
    SPECIAL_MISSIONS = "Special Missions"


ALL_OPERATIVES: tuple[str, ...] = (
    SACOperatives.RATCHET, SACOperatives.CLANK, SACOperatives.QWARK,
    SACOperatives.GADGETBOTS, SACOperatives.SPECIAL_MISSIONS,
)

# Character Items option (see options.py): Ratchet/Clank unlock with one
# flat item each; Qwark/Gadgetbots are progressive instead (user: "progressive
# characters specifically for qwark and gadgetbots") -- each copy unlocks
# that character's next case in CASES_BY_OPERATIVE order (see
# constants/planets.py), rather than all-or-nothing. Special Missions has no
# entry in either table -- see module docstring.
CHARACTER_ITEM_NAME: dict[str, str] = {
    SACOperatives.RATCHET: "Play as Ratchet",
    SACOperatives.CLANK:   "Play as Clank",
}
PROGRESSIVE_CHARACTER_ITEM_NAME: dict[str, str] = {
    SACOperatives.QWARK:      "Progressive Qwark",
    SACOperatives.GADGETBOTS: "Progressive Gadgetbots",
}
