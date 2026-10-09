"""Keycard locations and their bits in native flag 0xAA."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SACKeycardLocations:
    """Keycard location names."""

    RED_KEYCARD = "Asyanica (Clank) - Asyanica Rooftops: Red Keycard at the Second Set of Police Cars"
    BLUE_KEYCARD = "Fort Sprocket (Gadgetbots) - Inside the A-Eye: Blue Keycard during Vaultbreakers"
    YELLOW_KEYCARD = "Spaceship Graveyard (Qwark) - Saint Qwark: Yellow Keycard after Cannon Save"


KEYCARD_BITS: dict[str, int] = {
    SACKeycardLocations.RED_KEYCARD: 0,
    SACKeycardLocations.BLUE_KEYCARD: 1,
    SACKeycardLocations.YELLOW_KEYCARD: 2,
}


KEYCARD_ITEMS: dict[str, int] = {
    "Red Keycard": 0,
    "Blue Keycard": 1,
    "Yellow Keycard": 2,
}
