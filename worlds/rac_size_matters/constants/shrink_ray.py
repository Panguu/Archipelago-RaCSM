"""This module contains string constants for Shrink Ray puzzle-gate locations"""

from dataclasses import dataclass
from enum import IntFlag


@dataclass(frozen=True)
class Rac5ShrinkRayGrindrail:
    """String constants for Shrink Ray puzzle-gate locations"""

    KALIDON_ENTER_FACTORY = "Kalidon: Shrink Ray Enter the Factory"
    KALIDON_INSIDE_FACTORY = "Kalidon: Shrink Ray Inside the Factory"
    CHALLAX_GRINDRAIL = "Challax: Shrink Ray Grindrail"
    DAYNI_MOON_TITANIUM_BOLT_ENTRANCE = "Dayni Moon: Shrink Ray Titanium bolt entrance"
    INSIDE_CLANK_GRINDRAIL = "Inside Clank: Shrink Ray Grindrail"
    QUODRONA_ENTRANCE = "Quodrona: Shrink Ray Entrance"
    QUODRONA_CLONE_TRAINING_ROOM = "Quodrona: Shrink Ray Clone Training Room"


# 16-bit bitmask — every member here is a single bit within
# SHRINK_RAY_GATE_ADDRESS's 2-byte field (read/written via
# read_int16/write_int16, see core/shrink_ray.py). Same across every
# regional build, unlike the addresses in core/address_maps/ — the game's
# own bit layout for this field doesn't change per release.
class ShrinkRayPuzzleBit(IntFlag):
    KALIDON_ENTER_FACTORY = 0x0100
    KALIDON_INSIDE_FACTORY = 0x0200
    CHALLAX_GRINDRAIL = 0x1000
    DAYNI_MOON_TITANIUM_BOLT_ENTRANCE = 0x4000
    INSIDE_CLANK_GRINDRAIL = 0x8000
    QUODRONA_ENTRANCE = 0x0002
    QUODRONA_CLONE_TRAINING_ROOM = 0x0004
    # Outpost Omega's grindrail bit isn't a puzzle a player solves or skips —
    # it's forced solved unconditionally, every tick the client is connected,
    # regardless of the Shrink Ray Skips/Locations options (see
    # core/shrink_ray.py's ShrinkRaySkipInventory.force_outpost_omega_open()).
    # Not in SHRINK_RAY_PUZZLE_BITS: it isn't a meaningful AP location and
    # isn't part of skip_all()'s option-gated bulk write.
    OUTPOST_OMEGA_GRINDRAIL = 0x0400


OUTPOST_OMEGA_GRINDRAIL_BIT: ShrinkRayPuzzleBit = ShrinkRayPuzzleBit.OUTPOST_OMEGA_GRINDRAIL

# Location name -> the bit that signals its completion. Fixed by the game's
# own bit layout, same across every regional build.
SHRINK_RAY_PUZZLE_BITS: dict[str, ShrinkRayPuzzleBit] = {
    Rac5ShrinkRayGrindrail.KALIDON_ENTER_FACTORY: ShrinkRayPuzzleBit.KALIDON_ENTER_FACTORY,
    Rac5ShrinkRayGrindrail.KALIDON_INSIDE_FACTORY: ShrinkRayPuzzleBit.KALIDON_INSIDE_FACTORY,
    Rac5ShrinkRayGrindrail.CHALLAX_GRINDRAIL: ShrinkRayPuzzleBit.CHALLAX_GRINDRAIL,
    Rac5ShrinkRayGrindrail.DAYNI_MOON_TITANIUM_BOLT_ENTRANCE: ShrinkRayPuzzleBit.DAYNI_MOON_TITANIUM_BOLT_ENTRANCE,
    Rac5ShrinkRayGrindrail.INSIDE_CLANK_GRINDRAIL: ShrinkRayPuzzleBit.INSIDE_CLANK_GRINDRAIL,
    Rac5ShrinkRayGrindrail.QUODRONA_ENTRANCE: ShrinkRayPuzzleBit.QUODRONA_ENTRANCE,
    Rac5ShrinkRayGrindrail.QUODRONA_CLONE_TRAINING_ROOM: ShrinkRayPuzzleBit.QUODRONA_CLONE_TRAINING_ROOM,
}
