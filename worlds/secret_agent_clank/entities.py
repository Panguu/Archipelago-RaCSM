"""Item and location classes, kept out of world.py so regions.py can import them without a cycle."""
from collections.abc import Sequence

from BaseClasses import Item, ItemClassification, Location


class SACItem(Item):
    game: str = "Secret Agent Clank"


class SACProgressiveItem(SACItem):
    """An item where each copy received unlocks the next entry in `stages`.

    For example, Progressive Hydrano's stages are Hydrano's cases in order: the
    first copy unlocks the first case, the second copy the second, and so on.
    """
    __slots__ = ("stages",)

    def __init__(self, name: str, classification: ItemClassification, code: int | None, player: int,
                 stages: Sequence[str]):
        super().__init__(name, classification, code, player)
        self.stages = tuple(stages)


class SACLocation(Location):
    game: str = "Secret Agent Clank"
