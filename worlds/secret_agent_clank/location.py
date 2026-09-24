"""A single, uniform location record -- planet + case + display name + category -- meant to
replace the growing pile of per-category dicts in locations/__init__.py (ALWAYS_ON_LOCATIONS,
STORY_MISSION_LOCATIONS, ALL_STORY_MISSION_LOCATIONS, CUTSCENE_LOCATIONS, SKILL_POINT_LOCATIONS,
KEYCARD_LOCATIONS, ALIEN_CODE_LOCATIONS, TITANIUM_BOLT_LOCATIONS, TITAN_VENDOR_LOCATIONS,
MOD_VENDOR_LOCATIONS, ...) with one dict of one class, categorized by a `type` field instead of
by which dict a name happens to live in. Mirrors worlds/rac3/constants/data/location.py's
dataclass-per-location shape, adapted to a single explicit category enum instead of a tag set.

This module only defines the record type -- migrating locations/*.py's construction to build
SACLocationType-tagged Location entries (and collapsing ALL_LOCATIONS accordingly) is a separate,
larger pass across every case file and is deliberately not done here.
"""
from enum import Enum, auto
from typing import NamedTuple

from .constants.planets import CASE_NAME_TO_PLANET


class SACLocationType(Enum):
    TITANIUM_BOLT = auto()
    SKILL_POINT = auto()
    MISSION = auto()
    CUTSCENE = auto()
    RATCHET_WEAPON = auto()
    CLANK_WEAPON = auto()
    RATCHET_GADGET = auto()
    CASE_FILE = auto()
    KEYCARD = auto()
    ALIEN_CODE = auto()
    GADGETBOT_CHALLENGE = auto()
    SPECIAL_CHALLENGE = auto()
    RATCHET_CHALLENGE = auto()
    TITAN_VENDOR = auto()
    MOD_VENDOR = auto()


class Location(NamedTuple):
    code: int
    planet: str  # SACPlanets constant -- derived from `case`, see from_case() below.
    case: str    # Case.name (constants/planets.py) -- single source of truth for `planet`.
    name: str    # Display name, e.g. the AP location name shown in the client/spoiler log.
    type: SACLocationType

    @classmethod
    def from_case(cls, code: int, case: str, name: str, type: SACLocationType) -> "Location":
        """Build a Location for `case`, resolving `planet` off constants/planets.py's
        CASE_NAME_TO_PLANET rather than passing it separately -- keeps a single source of
        truth for a case's planet the same way locations/_shared.py's SACLocationData did."""
        return cls(code, CASE_NAME_TO_PLANET[case], case, name, type)

    def __str__(self) -> str:
        return self.name
