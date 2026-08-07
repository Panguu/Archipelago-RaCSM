from __future__ import annotations

from dataclasses import dataclass

from ...constants import Rac5Planets, Rac5SkillPoints


@dataclass(frozen=True)
class SkillPoint:
    planet_id: int  # used with mask for detection context
    bit:       int
    region:    str

    @property
    def mask(self) -> int:
        return 1 << self.bit


# Confirmed bit layout (groups of 2-3, 4-bit spacing between planets):
#
#  Planet        Count  Bits
#
#  Pokitaru        3     0,  1,  2
#  Ryllus          3     4,  5,  6
#  Kalidon         3     8,  9, 10
#  Metalis         3    12, 13, 14
#  Dreamtime       2    16, 17
#  Outpost Omega   1    20
#  Challax         3    24, 25, 26
#  Dayni Moon      3    28, 29, 30
#  Inside Clank    2    32, 33
#  Quodrona        2    36, 37

SKILL_POINTS: dict[str, SkillPoint] = {
    Rac5SkillPoints.POKITARU_TRAIN:          SkillPoint(0x01,  0, Rac5Planets.POKITARU),
    Rac5SkillPoints.POKITARU_BOAT:           SkillPoint(0x01,  1, Rac5Planets.POKITARU),
    Rac5SkillPoints.POKITARU_COWS:           SkillPoint(0x01,  2, Rac5Planets.POKITARU),
    Rac5SkillPoints.RYLLUS_BURY:             SkillPoint(0x02,  4, Rac5Planets.RYLLUS),
    Rac5SkillPoints.RYLLUS_CAMERA:           SkillPoint(0x02,  5, Rac5Planets.RYLLUS),
    Rac5SkillPoints.RYLLUS_SHIP_IT:          SkillPoint(0x02,  6, Rac5Planets.RYLLUS),
    Rac5SkillPoints.KALIDON_EXPLOSIVE:       SkillPoint(0x03,  8, Rac5Planets.KALIDON),
    Rac5SkillPoints.KALIDON_SUPER_LOMBAX:    SkillPoint(0x03,  9, Rac5Planets.KALIDON),
    Rac5SkillPoints.KALIDON_SKYBOARDER:      SkillPoint(0x03, 10, Rac5Planets.KALIDON),
    Rac5SkillPoints.METALIS_SHUTOUT:         SkillPoint(0x04, 12, Rac5Planets.METALIS),
    Rac5SkillPoints.METALIS_GLADIATOR:       SkillPoint(0x04, 14, Rac5Planets.METALIS),
    Rac5SkillPoints.DREAMTIME_FRIENDS:       SkillPoint(0x05, 16, Rac5Planets.DREAMTIME),
    Rac5SkillPoints.DREAMTIME_NIGHT_TERRORS: SkillPoint(0x05, 17, Rac5Planets.DREAMTIME),
    Rac5SkillPoints.OUTPOST_OMEGA_AWESOME:   SkillPoint(0x17, 20, Rac5Planets.OUTPOST_OMEGA),
    # Rac5SkillPoints.CHALLAX_SHOCK: SkillPoint(0x07, 24, Rac5Planets.CHALLAX)
    # Excluded: only one opportunity to complete this in the whole game (bit 24).
    Rac5SkillPoints.CHALLAX_MASTER:          SkillPoint(0x07, 25, Rac5Planets.CHALLAX),
    Rac5SkillPoints.DAYNI_MOON_GLADIATOR:    SkillPoint(0x08, 28, Rac5Planets.DAYNI_MOON),
    Rac5SkillPoints.DAYNI_MOON_WOOL_PROTEST: SkillPoint(0x08, 29, Rac5Planets.DAYNI_MOON),
    Rac5SkillPoints.DAYNI_MOON_BOUNCY:       SkillPoint(0x08, 30, Rac5Planets.DAYNI_MOON),
    Rac5SkillPoints.INSIDE_CLANK_SHOCK:      SkillPoint(0x09, 32, Rac5Planets.INSIDE_CLANK),
    Rac5SkillPoints.INSIDE_CLANK_RATCHET:    SkillPoint(0x09, 33, Rac5Planets.INSIDE_CLANK),
    Rac5SkillPoints.QUODRONA_ELITE:          SkillPoint(0x0A, 36, Rac5Planets.QUODRONA),
    Rac5SkillPoints.QUODRONA_STORM:          SkillPoint(0x0A, 37, Rac5Planets.QUODRONA),
    # Both appended last (rather than restored to their original spots
    # above) so every other skill point's positionally-derived id in
    # SKILL_POINT_LOCATIONS (locations.py) stays stable. Earned during their
    # respective Giant Clank sequences — see core/planets.py's
    # GIANT_CLANK_CONFIGS/Core.tick() for how those are now reachable.
    Rac5SkillPoints.METALIS_TERROR:          SkillPoint(0x04, 13, Rac5Planets.METALIS),
    Rac5SkillPoints.CHALLAX_VARMINTS:        SkillPoint(0x07, 26, Rac5Planets.CHALLAX),
}

# Curated "hard" tier for the Skill Points option. Everything else in SKILL_POINTS
# that isn't also a Clank/Skyboard challenge skill point counts as "easy".
HARD_SKILL_POINTS: frozenset[str] = frozenset({
    Rac5SkillPoints.RYLLUS_BURY,
    Rac5SkillPoints.KALIDON_SUPER_LOMBAX,
    Rac5SkillPoints.METALIS_TERROR,
    Rac5SkillPoints.DREAMTIME_FRIENDS,
    Rac5SkillPoints.DREAMTIME_NIGHT_TERRORS,
    Rac5SkillPoints.CHALLAX_MASTER,
    Rac5SkillPoints.DAYNI_MOON_WOOL_PROTEST,
    Rac5SkillPoints.INSIDE_CLANK_SHOCK,
    Rac5SkillPoints.INSIDE_CLANK_RATCHET,
    Rac5SkillPoints.QUODRONA_ELITE,
    Rac5SkillPoints.QUODRONA_STORM,
})

# Earned from Clank Challenge arenas — gated by enable_clank_challenge_skill_points,
# independent of the Skill Points easy/hard tier.
CLANK_CHALLENGE_SKILL_POINTS: frozenset[str] = frozenset({
    Rac5SkillPoints.METALIS_SHUTOUT,
    Rac5SkillPoints.METALIS_GLADIATOR,
    Rac5SkillPoints.DAYNI_MOON_GLADIATOR,
})

# Earned from Skyboard Challenges — gated by enable_skyboard_challenge_skill_points,
# independent of the Skill Points easy/hard tier.
SKYBOARD_CHALLENGE_SKILL_POINTS: frozenset[str] = frozenset({
    Rac5SkillPoints.KALIDON_SKYBOARDER,
    Rac5SkillPoints.OUTPOST_OMEGA_AWESOME,
})

# (planet_id, mask) → location name — mirrors BOLT_BY_PLANET_AND_DELTA
SKILL_POINT_BY_PLANET_AND_MASK: dict[tuple[int, int], str] = {
    (sp.planet_id, sp.mask): name
    for name, sp in SKILL_POINTS.items()
}

# Flat mask lookup used by the client (bits are globally unique so planet not needed for detection)
LOCATION_SKILL_POINTS: dict[str, int] = {
    name: sp.mask for name, sp in SKILL_POINTS.items()
}
