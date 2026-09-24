"""Shared, dependency-free building blocks for the per-case location files in this package -- kept in their own leaf module (no imports from `.` or from any case file) so every locations/<case>.py file can import them at module load time with no circular-import ordering concerns."""
from collections.abc import Callable
from typing import NamedTuple

from ..constants.missions import CHAPTER_ENTRIES

BASE_ID = 77_800_000

# Generous per-case id block -- no case comes close to needing 1000 distinct
# location ids, this just gives every case file a fixed, non-overlapping id
# range it can compute on its own (BASE_ID + (case_id - 1) * this), instead
# of sharing one mutable counter across all 30 files (which would force a
# strict import order between them).
CASE_ID_BLOCK_SIZE = 1000


class SACLocationData(NamedTuple):
    code: int
    case: str  # Case.name (constants/planets.py) -- single source of truth
    # for this location's planet/operative; regions.py/rules.py both derive
    # those via CASE_NAME_TO_CASE[case] rather than storing them separately.


class CaseLocations(NamedTuple):
    """One case file's full location set, grouped by which options.py toggle (if
    any) gates that group -- replaces 5 separate module-level dict exports per
    case file (and __init__.py's matching positional 5-tuple) with a single
    named export, built in the same _take_id() call order as before so every
    location keeps the exact same id."""
    always_on: dict[str, SACLocationData]
    mission: dict[str, SACLocationData]
    all_missions: dict[str, SACLocationData]
    cutscene: dict[str, SACLocationData]
    other: dict[str, SACLocationData]


def all_mission_locations(
    case_name: str, take_id: Callable[[], int],
) -> dict[str, "SACLocationData"]:
    """Missions=all granularity's location set for one case: one location per individual CHAPTER_ENTRIES mission belonging to case_name, each getting its own id from take_id (a case file's own _take_id()) -- the finer-grained alternative to that same case file's *_MISSION_ LOCATIONS single "{case_name} Complete" entry (Missions= level_completion)."""
    return {
        entry.display_name: SACLocationData(take_id(), case_name)
        for entry in CHAPTER_ENTRIES.get(case_name, ())
    }
