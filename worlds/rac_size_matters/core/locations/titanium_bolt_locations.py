from __future__ import annotations

from dataclasses import dataclass

from ...constants import Rac5Planets, Rac5TBolts


@dataclass(frozen=True)
class TitaniumBolt:
    # Usually a single planet ID; some locations (e.g. Outpost Omega Dream,
    # reachable from both the first and second Outpost Omega visit) can be
    # picked up while registered under more than one planet ID for the same
    # physical location — pass a tuple in that case.
    planet_id: int | tuple[int, ...]
    bit:       int  # bit position in the pickup int64
    region:    str  # AP region name

    @property
    def delta(self) -> int:
        return 1 << self.bit

    @property
    def planet_ids(self) -> tuple[int, ...]:
        return self.planet_id if isinstance(self.planet_id, tuple) else (self.planet_id,)


TITANIUM_BOLTS: dict[str, TitaniumBolt] = {
    Rac5TBolts.POKITARU_ZIPLINE:   TitaniumBolt(0x01,  0, Rac5Planets.POKITARU),
    Rac5TBolts.POKITARU_HUT:       TitaniumBolt(0x01,  1, Rac5Planets.POKITARU),
    Rac5TBolts.RYLLUS_CLIFF:       TitaniumBolt(0x02,  4, Rac5Planets.RYLLUS),
    Rac5TBolts.RYLLUS_WALL:        TitaniumBolt(0x02,  5, Rac5Planets.RYLLUS),
    Rac5TBolts.KALIDON_SHIP:       TitaniumBolt(0x03,  8, Rac5Planets.KALIDON),
    Rac5TBolts.KALIDON_FACTORY:    TitaniumBolt(0x03, 10, Rac5Planets.KALIDON),
    Rac5TBolts.KALIDON_RAMP:       TitaniumBolt(0x03,  9, Rac5Planets.KALIDON),
    Rac5TBolts.METALIS_DOOR:       TitaniumBolt(0x04, 12, Rac5Planets.METALIS),
    Rac5TBolts.DREAMTIME_HAT:      TitaniumBolt(0x05, 16, Rac5Planets.DREAMTIME),
    Rac5TBolts.DREAMTIME_GARAGE:   TitaniumBolt(0x05, 17, Rac5Planets.DREAMTIME),
    Rac5TBolts.DREAMTIME_CRAB:     TitaniumBolt(0x05, 18, Rac5Planets.DREAMTIME),
    Rac5TBolts.OUTPOST_OMEGA_DREAM:TitaniumBolt((0x06, 0x17), 20, Rac5Planets.OUTPOST_OMEGA),
    Rac5TBolts.CHALLAX_MECH_PAD:   TitaniumBolt(0x07, 24, Rac5Planets.CHALLAX),
    Rac5TBolts.CHALLAX_ROOM:       TitaniumBolt(0x07, 25, Rac5Planets.CHALLAX),
    Rac5TBolts.CHALLAX_PLANT:      TitaniumBolt(0x07, 26, Rac5Planets.CHALLAX),
    Rac5TBolts.DAYNI_MOON_BARN:    TitaniumBolt(0x08, 28, Rac5Planets.DAYNI_MOON),
    Rac5TBolts.DAYNI_MOON_MIMIC:   TitaniumBolt(0x08, 29, Rac5Planets.DAYNI_MOON),
    Rac5TBolts.INSIDE_CLANK_LADDER:TitaniumBolt(0x09, 32, Rac5Planets.INSIDE_CLANK),
    Rac5TBolts.INSIDE_CLANK_WALL:  TitaniumBolt(0x09, 33, Rac5Planets.INSIDE_CLANK),
    Rac5TBolts.QUODRONA_DUMMIES:   TitaniumBolt(0x0A, 36, Rac5Planets.QUODRONA),
}

# (planet_id, delta) → location name — used by the client for unambiguous detection
BOLT_BY_PLANET_AND_DELTA: dict[tuple[int, int], str] = {
    (planet_id, bolt.delta): name
    for name, bolt in TITANIUM_BOLTS.items()
    for planet_id in bolt.planet_ids
}
