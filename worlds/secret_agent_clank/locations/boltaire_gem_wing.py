"""All locations tied to Boltaire Gem Wing, grouped into a CaseLocations bundle by which options.py toggle (if any) gates each part -- see locations/__init__.py for how these get merged/re-derived for regions.py."""
from ..constants import (
    ALIEN_CODES_BY_CASE,
    CASE_NAME_TO_CASE,
    CUTSCENE_TO_CASE,
    GADGETBOT_CHALLENGES_BY_CASE,
    KEYCARDS_BY_CASE,
    MISSION_COMPLETE_NAME,
    RATCHET_CHALLENGES_BY_CASE,
    SKILL_POINTS_BY_CASE,
    SPECIAL_CHALLENGES_BY_CASE,
    WEAPONS_BY_CASE,
    SACCases,
)
from ._shared import BASE_ID, CASE_ID_BLOCK_SIZE, CaseLocations, SACLocationData, all_mission_locations

_CASE_NAME = SACCases.BOLTAIRE_GEM_WING
_CASE_ID = CASE_NAME_TO_CASE[_CASE_NAME].case_id
_next_id = BASE_ID + (_CASE_ID - 1) * CASE_ID_BLOCK_SIZE


def _take_id() -> int:
    global _next_id
    taken, _next_id = _next_id, _next_id + 1
    return taken


_always_on: dict[str, SACLocationData] = {}
for _name in WEAPONS_BY_CASE.get(_CASE_NAME, ()):
    _always_on[_name] = SACLocationData(_take_id(), _CASE_NAME)
for _name in (
    *GADGETBOT_CHALLENGES_BY_CASE.get(_CASE_NAME, ()),
    *SPECIAL_CHALLENGES_BY_CASE.get(_CASE_NAME, ()),
    *RATCHET_CHALLENGES_BY_CASE.get(_CASE_NAME, ()),
):
    _always_on[_name] = SACLocationData(_take_id(), _CASE_NAME)

_mission: dict[str, SACLocationData] = {
    MISSION_COMPLETE_NAME[_CASE_NAME]: SACLocationData(_take_id(), _CASE_NAME),
}

_all_missions: dict[str, SACLocationData] = all_mission_locations(_CASE_NAME, _take_id)

_cutscene: dict[str, SACLocationData] = {
    _cutscene_name: SACLocationData(_take_id(), _CASE_NAME)
    for _cutscene_name, _case_name in CUTSCENE_TO_CASE.items() if _case_name == _CASE_NAME
}

_other: dict[str, SACLocationData] = {}
for _name in (
    *SKILL_POINTS_BY_CASE.get(_CASE_NAME, ()),
    *KEYCARDS_BY_CASE.get(_CASE_NAME, ()),
    *ALIEN_CODES_BY_CASE.get(_CASE_NAME, ()),
):
    _other[_name] = SACLocationData(_take_id(), _CASE_NAME)

BOLTAIRE_GEM_WING_LOCATIONS = CaseLocations(_always_on, _mission, _all_missions, _cutscene, _other)
