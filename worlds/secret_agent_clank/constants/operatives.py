from dataclasses import dataclass


@dataclass(frozen=True)
class SACOperatives:
    RATCHET = "Ratchet"
    CLANK = "Clank"
    GADGETBOTS = "Gadgetbots"
    QWARK = "Qwark"
    SPECIAL_MISSIONS = "Special Missions"


ALL_OPERATIVES: tuple[str, ...] = (
    SACOperatives.RATCHET, SACOperatives.CLANK, SACOperatives.QWARK,
    SACOperatives.GADGETBOTS, SACOperatives.SPECIAL_MISSIONS,
)
OPTIONAL_OPERATIVES: tuple[str, ...] = tuple(op for op in ALL_OPERATIVES if op != SACOperatives.CLANK)
