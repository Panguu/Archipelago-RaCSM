import struct

from ...constants import (
    CASE_NAME_TO_CASE,
    CHAPTER_ENTRIES,
    CUTSCENE_FLAGS,
    MISSION_COMPLETE_NAME,
    MISSION_NAMES,
    NATIVE_FINISH_CASES,
    MissionFlag,
    SACCases,
    SACCutsceneLocations,
)
from ..case_menu import CASE_LABELS
from ..symbols import RuntimeSymbols
from ...constants.planets import Case
from ...pypine import Pine


_CHAPTER_TABLE_OFFSET = 0
_CHAPTER_TABLE_SLOTS = 33
_TASK_ENTRY_SIZE = 0x60
_TASK_STATE_OFFSET = 0xC

_REPORTABLE_NAMES = frozenset((*MISSION_NAMES, *MISSION_COMPLETE_NAME.values()))

_PLAUSIBLE_PTR_RANGE: tuple[int, int] = (0x00100000, 0x02000000)
_PLAUSIBLE_MAX_COUNT = 10


def find_mission_level_list(pine: Pine) -> int | None:
    symbols = RuntimeSymbols(pine)
    symbols.refresh()
    return symbols.get("g_MISSION_LEVEL_LIST")


def resolve_chapter_table(pine: Pine, base: int | None = None) -> dict[int, tuple[int, int]]:
    """Read the chapter table's slots as {slot: (pointer, count)}, keeping only plausible ones."""
    if base is None:
        base = find_mission_level_list(pine)
    if base is None:
        return {}
    table_base = base + _CHAPTER_TABLE_OFFSET
    raw = pine.read_bytes(table_base, _CHAPTER_TABLE_SLOTS * 8)
    slots: dict[int, tuple[int, int]] = {}
    lo, hi = _PLAUSIBLE_PTR_RANGE
    for i in range(_CHAPTER_TABLE_SLOTS):
        ptr, count = struct.unpack_from("<II", raw, i * 8)
        if ptr == 0 and count == 0:
            continue
        if lo <= ptr < hi and 0 < count <= _PLAUSIBLE_MAX_COUNT and ptr + count * _TASK_ENTRY_SIZE <= hi:
            slots[i] = (ptr, count)
    return slots


class MissionInventory:

    def __init__(self, pine: Pine) -> None:
        self.pine = pine
        self.table_base: int | None = None
        self.completed: dict[str, bool] = dict.fromkeys(MISSION_NAMES, False)
        self._resolved_cases = None
        self._story_addresses = {}
        self._reported: set[str] = set()
        self._resolved_title_ids = {}

    def sync_from_ap(self, checked_location_names: set[str]) -> None:
        for name in _REPORTABLE_NAMES & checked_location_names:
            self._reported.add(name)
            if name in self.completed:
                self.completed[name] = True

    def invalidate_resolved_addresses(self) -> None:
        """Forget resolved addresses; call on every case transition."""
        self._resolved_cases = None
        self._story_addresses = {}
        self._resolved_title_ids = {}

    def _resolve_labels(self):
        """Native labels identify cases even when they share one module slot."""
        if self._resolved_cases is not None:
            return
        groups, story = {}, {}
        for pointer, count in resolve_chapter_table(self.pine, self.table_base).values():
            data = self.pine.read_bytes(pointer, count * _TASK_ENTRY_SIZE)
            for index in range(count):
                offset = index * _TASK_ENTRY_SIZE
                kind = struct.unpack_from("<I", data, offset)[0]
                label = struct.unpack_from("<I", data, offset + 0x3C)[0]
                name = CASE_LABELS.get(label)
                if name is None or kind not in (1, 4):
                    continue
                address = pointer + offset + _TASK_STATE_OFFSET
                groups.setdefault(name, []).append(address)
                title = struct.unpack_from("<I", data, offset + 4)[0]
                self._resolved_title_ids.setdefault(name, []).append(title)
                if kind == 1:
                    story.setdefault(name, []).append(address)
        if groups:
            self._resolved_cases, self._story_addresses = groups, story

    def check_all(self, *, all_missions=False):
        """Progress can persist into the next module before the next host poll."""
        self._resolve_labels()
        found = []
        names = dict.fromkeys(self._resolved_cases or {})
        names[SACCases.KLUNKS_LAIR] = None
        names.update(dict.fromkeys(NATIVE_FINISH_CASES.values()))
        for name in names:
            case = CASE_NAME_TO_CASE.get(name)
            if case is not None:
                found.extend(self.check(case, all_missions=all_missions))
        return found

    def _resolve_case_addresses(self, case: Case) -> list[int] | None:
        """Resolve this case by label and verify its native title IDs."""
        self._resolve_labels()
        addresses = (self._resolved_cases or {}).get(case.name)
        titles = self._resolved_title_ids.get(case.name)
        entries = CHAPTER_ENTRIES.get(case.name, ())
        if titles is not None and titles != [entry.title_id for entry in entries]:
            return None
        return addresses

    def check(self, current_case: "Case | None", *, all_missions: bool = True) -> list[str]:
        """Report individual tasks, or the final story task for case completion."""
        newly: list[str] = []
        if current_case is None:
            return newly
        if current_case.name in NATIVE_FINISH_CASES.values():
            mission = CHAPTER_ENTRIES[current_case.name][0].name
            complete_name = MISSION_COMPLETE_NAME[current_case.name]
            if self.completed[mission] or complete_name in self._reported:
                addresses = self._resolve_case_addresses(current_case)
                if addresses and len(addresses) == 1:
                    if self.pine.read_int32(addresses[0]) != MissionFlag.UNLOCKED_COMPLETED:
                        self.pine.write_int32(addresses[0], MissionFlag.UNLOCKED_COMPLETED)
                name = mission if all_missions else complete_name
                return [] if name in self._reported else [name]
            return []
        if current_case.name == SACCases.KLUNKS_LAIR:
            ending = CUTSCENE_FLAGS[SACCutsceneLocations.KLUNKS_LAIR_COMPLETE_CUTSCENE]
            if ending.is_set(self.pine.read_int8(ending.address)):
                mission = CHAPTER_ENTRIES[SACCases.KLUNKS_LAIR][0].name
                self.completed[mission] = True
                name = mission if all_missions else MISSION_COMPLETE_NAME[SACCases.KLUNKS_LAIR]
                return [] if name in self._reported else [name]
        self._resolve_labels()
        if not all_missions:
            story = self._story_addresses.get(current_case.name, ())
            complete_name = MISSION_COMPLETE_NAME[current_case.name]
            if story and complete_name not in self._reported and self.pine.read_int32(story[-1]) == 3:
                return [complete_name]
            return []
        entries = CHAPTER_ENTRIES.get(current_case.name)
        if not entries:
            return newly
        addresses = self._resolve_case_addresses(current_case)
        if addresses is None or len(addresses) != len(entries):
            return newly
        values = self.pine.batch_read_int32(addresses)
        for entry, value in zip(entries, values):
            now = value == MissionFlag.UNLOCKED_COMPLETED
            flipped = now and entry.name not in self._reported
            self.completed[entry.name] = now or self.completed.get(entry.name, False)
            if flipped:
                newly.append(entry.name)
        return newly

    def confirm(self, name: str) -> None:
        """Stop reporting `name`; call only once AP has accepted the check."""
        if name in _REPORTABLE_NAMES:
            self._reported.add(name)

    def __repr__(self) -> str:
        seen = sum(self.completed.values())
        return f"MissionInventory(completed={seen}/{len(self.completed)})"
