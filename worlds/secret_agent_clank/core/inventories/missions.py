"""Read 32-bit mission states by native case label and mission title ID."""
import struct
from typing import TYPE_CHECKING, NamedTuple

from ...constants.missions import (
    ALL_CHAPTER_ENTRIES,
    CHAPTER_ENTRIES,
    COMPLETE_NAME_TO_CASE,
    DISPLAY_NAME_TO_CHAPTER_ENTRY,
    MISSION_COMPLETE_NAME,
    MISSION_NAME_TO_CHAPTER_ENTRY,
    MISSION_TO_CASE,
    MissionFlag,
)
from ...constants.planets import CASE_NAME_TO_CASE
from ..case_menu import CASE_LABELS
from ..symbols import RuntimeSymbols

if TYPE_CHECKING:
    from ...constants.planets import Case
    from ...pypine import Pine


# The USA module exports g_MISSION_LEVEL_LIST as a direct 33-slot array.
# Verified in live Museum RAM: base 0x5775A0, slot 1 -> 0x576200/count 3.
# The old resolver read the previous export, then compensated with +0x60.
_CHAPTER_TABLE_OFFSET = 0
_CHAPTER_TABLE_SLOTS = 33
_TASK_ENTRY_SIZE = 0x60        # bytes per task entry within a chapter's task array

# Internal bookkeeping below (self.completed/self._reported) stays keyed by
# the RAW native name throughout (matches core/core.py's own raw entry.name
# lookups) -- translated to/from the real AP location name (constants/
# missions.py's MISSION_COMPLETE_NAME / SACMissionEntry.display_name) only
# at the two boundaries that actually talk to AP: check()'s return value and
# confirm()/sync_from_ap()'s input.
_TASK_STATE_OFFSET = 0xC       # state field within a task entry (same field CHAPTER_ENTRIES
                                # addresses point at; 1 byte, MissionFlag-valued)

# A resolved (ptr, count) slot has to satisfy both of these to be trusted
# -- guards against a stale/mid-transition read being mistaken for a real
# slot. Deliberately generous (not tuned to one level) since the table's
# absolute address moves per level.
_PLAUSIBLE_PTR_RANGE: tuple[int, int] = (0x00100000, 0x02000000)  # PS2 EE main RAM, roughly
_PLAUSIBLE_MAX_COUNT = 10

# Byte-array scan windows. The symbol string and its reverse-reference
# were observed within roughly 0x6F000-0x70000 bytes of each other across
# two independent live captures (Klunk's Lair, Boltaire Museum) -- these
# defaults carry real margin above that and double automatically (up to
# _MAX_SEARCH_SIZE) rather than hard-failing if some other level's build
# differs more than observed so far.
_SYMBOL_SEARCH_START = 0x600000
_SYMBOL_SEARCH_SIZE = 0x200000       # 2 MiB
_REVERSE_REF_SEARCH_SIZE = 0x100000  # 1 MiB past the symbol string's own address
_MAX_SEARCH_SIZE = 0x800000          # hard cap (8 MiB) before giving up
_SCAN_CHUNK_SIZE = 0x40000           # 256 KiB per Pine.read_bytes() call -- stays well under Pine.MAX_IPC_RETURN_SIZE


def _scan_bytes(pine: "Pine", start: int, size: int) -> bytes:
    """Read `size` bytes starting at `start`, chunked to stay well under PINE's per-request return-size cap (Pine.MAX_IPC_RETURN_SIZE) -- Pine.read_bytes() itself doesn't chunk a single call that large."""
    out = bytearray()
    offset = 0
    while offset < size:
        chunk = min(_SCAN_CHUNK_SIZE, size - offset)
        out += pine.read_bytes(start + offset, chunk)
        offset += chunk
    return bytes(out)


def _find_bytes(pine: "Pine", needle: bytes, start: int, initial_size: int) -> "int | None":
    """Scan memory for `needle` starting at `start`, doubling the window up to _MAX_SEARCH_SIZE if it isn't found."""
    size = initial_size
    while size <= _MAX_SEARCH_SIZE:
        haystack = _scan_bytes(pine, start, size)
        pos = haystack.find(needle)
        if pos != -1:
            return start + pos
        size *= 2
    return None


def find_mission_level_list(pine: "Pine") -> "int | None":
    """Locate g_pMissionLevelList's real runtime address for whichever level/case is currently loaded -- no prior per-case confirmation needed (see module comment above)."""
    symbols = RuntimeSymbols(pine)
    symbols.refresh()
    return symbols.get("g_MISSION_LEVEL_LIST")


def resolve_chapter_table(pine: "Pine", base: int | None = None) -> "dict[int, tuple[int, int]]":
    """Batch-read all 51 chapter slots off a freshly-resolved g_pMissionLevelList, keeping only the ones that pass sanity checks (see _PLAUSIBLE_PTR_RANGE/_PLAUSIBLE_MAX_COUNT)."""
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


class ChapterTableRow(NamedTuple):
    """One row of MissionInventory.dump_chapter_table()'s output -- see that method's docstring."""
    slot: int
    task_count: int
    assumed_case: "str | None"
    expected_count: "int | None"
    matches: "bool | None"


def resolve_task_state_addresses(pine: "Pine", base: int | None = None) -> "dict[int, list[int]]":
    """resolve_chapter_table(), expanded out to each individual task entry's state-byte address (entry + _TASK_STATE_OFFSET, same field CHAPTER_ENTRIES' hardcoded addresses point at -- read/write it with read_int8/write_int8, same as MissionFlag elsewhere in this module)."""
    return {
        slot: [ptr + i * _TASK_ENTRY_SIZE + _TASK_STATE_OFFSET for i in range(count)]
        for slot, (ptr, count) in resolve_chapter_table(pine, base).items()
    }


class MissionInventory:

    def __init__(self, pine: "Pine") -> None:
        self.pine = pine
        self.table_base: int | None = None
        self.completed: dict[str, bool] = dict.fromkeys((entry.name for _, entry in ALL_CHAPTER_ENTRIES), False)
        # {slot: [state_address, ...]}, cached from resolve_task_state_
        # addresses() -- see invalidate_resolved_addresses()/
        # _resolve_case_addresses() below. None means "not resolved yet
        # this level", distinct from {} (resolved, but the scan itself
        # came back empty -- also worth retrying, so both are falsy and
        # treated the same by _resolve_case_addresses()).
        self._resolved_slots: dict[int, list[int]] | None = None
        self._resolved_cases = None
        self._story_addresses = {}
        self._reported = set()
        self._resolved_title_ids = {}

    def sync_from_ap(self, checked_location_names: set[str]) -> None:
        for case_name, complete_name in MISSION_COMPLETE_NAME.items():
            if complete_name in checked_location_names:
                self._reported.add(f"{case_name} Complete")
        for _, entry in ALL_CHAPTER_ENTRIES:
            if entry.display_name in checked_location_names:
                self._reported.add(entry.name)
                self.completed[entry.name] = True

    def invalidate_resolved_addresses(self) -> None:
        """Call once on every case transition (Core.tick()'s became_ready) -- forces the next _resolve_case_addresses() call to re-scan g_pMissionLevelList instead of reusing last level's now- stale addresses."""
        self._resolved_slots = None
        self._resolved_cases = None
        self._story_addresses = {}
        self._resolved_title_ids = {}

    def _resolve_labels(self):
        """Native labels identify cases even when they share one module slot."""
        if self._resolved_cases is not None:
            return
        groups, story = {}, {}
        for _, (pointer, count) in resolve_chapter_table(self.pine, self.table_base).items():
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
        for name in self._resolved_cases or {}:
            case = CASE_NAME_TO_CASE.get(name)
            if case is not None:
                found.extend(self.check(case, all_missions=all_missions))
        return found

    def _resolve_case_addresses(self, case: "Case") -> "list[int] | None":
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
        self._resolve_labels()
        if not all_missions:
            story = self._story_addresses.get(current_case.name, ())
            internal_key = f"{current_case.name} Complete"
            if story and internal_key not in self._reported and self.pine.read_int32(story[-1]) == 3:
                return [MISSION_COMPLETE_NAME[current_case.name]]
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
            if not flipped:
                continue
            newly.append(entry.display_name)
        return newly

    def confirm(self, name: str) -> None:
        """Mark a name check()/check_all() returned as successfully delivered to AP -- see core/case_events.py's CaseEventInventory.confirm() for why this must wait for Core.send_location(name) to return True rather than happening unconditionally inside check()."""
        case_name = COMPLETE_NAME_TO_CASE.get(name)
        if case_name is not None:
            self._reported.add(f"{case_name} Complete")
            return
        entry = DISPLAY_NAME_TO_CHAPTER_ENTRY.get(name)
        if entry is not None:
            self._reported.add(entry.name)

    def enforce_owned_first_missions(self, owned_cases: "set[str]") -> int:
        """Continuously self-heals every AP-owned case's first CHAPTER_ENTRIES mission back to UNLOCKED (2) if it's currently DISABLED, making each owned case reachable/playable without marking it complete (see module docstring for why nothing else unlocks a case's first mission)."""
        first_addresses: list[int] = []
        for case_name in owned_cases:
            entries = CHAPTER_ENTRIES.get(case_name)
            if not entries:
                continue
            case = CASE_NAME_TO_CASE.get(case_name)
            if case is None:
                continue
            addresses = self._resolve_case_addresses(case)
            if addresses is None:
                continue
            first_addresses.append(addresses[0])
        if not first_addresses:
            return 0
        current_values = self.pine.batch_read_int8(first_addresses)
        writes = [
            (address, MissionFlag.UNLOCKED)
            for address, value in zip(first_addresses, current_values)
            if value in (MissionFlag.DISABLED, MissionFlag.ENABLED)
        ]
        if writes:
            self.pine.batch_write_int8(writes)
        return len(writes)

    def force_flag(self, mission_name: str, value: int) -> bool:
        """Debug/testing helper -- force a single mission's flag byte to value (typically MissionFlag.DISABLED to lock, .UNLOCKED to make reachable without marking complete, or .UNLOCKED_COMPLETED for an actual completion), matched by exact mission name."""
        entry = MISSION_NAME_TO_CHAPTER_ENTRY.get(mission_name)
        case_name = MISSION_TO_CASE.get(mission_name)
        case = CASE_NAME_TO_CASE.get(case_name) if case_name else None
        if entry is None or case is None:
            return False
        addresses = self._resolve_case_addresses(case)
        if addresses is None:
            return False
        index = CHAPTER_ENTRIES[case_name].index(entry)
        self.pine.write_int8(addresses[index], value)
        return True

    def force_all(self, value: int) -> int:
        """Debug/testing helper -- force every known mission's flag byte to value in one batch write, each address resolved dynamically per case via _resolve_case_addresses() (see force_flag())."""
        writes: list[tuple[int, int]] = []
        for case_name in CHAPTER_ENTRIES:
            case = CASE_NAME_TO_CASE.get(case_name)
            if case is None:
                continue
            addresses = self._resolve_case_addresses(case)
            if addresses is None:
                continue
            writes.extend((address, value) for address in addresses)
        if writes:
            self.pine.batch_write_int8(writes)
        return len(writes)

    def dump_chapter_table(self) -> list["ChapterTableRow"]:
        """Debug helper for the client's /mission_table command -- resolves the WHOLE chapter table fresh (bypassing check()/ enforce_owned_first_missions()'s cache; this is a manual one-off diagnostic, not a hot path, so a full re-scan every call is fine) and cross-references every resolved slot against CASE_ID_TO_CASE's slot-index-equals-case_id assumption -- confirmed live only for slot 1 / Boltaire Museum's case_id 1 so far (see _resolve_case_addresses()'s docstring)."""
        slots = resolve_chapter_table(self.pine, self.table_base)
        rows = []
        for slot, (pointer, count) in sorted(slots.items()):
            labels = self.pine.batch_read_int32([pointer + i * 0x60 + 0x3C for i in range(count)])
            names = list(dict.fromkeys(CASE_LABELS[label] for label in labels if label in CASE_LABELS))
            expected = sum(len(CHAPTER_ENTRIES.get(name, ())) for name in names)
            rows.append(ChapterTableRow(slot, count, " / ".join(names) or None,
                                        expected if names else None, expected == count if names else None))
        return rows

    def __repr__(self) -> str:
        seen = sum(self.completed.values())
        return f"MissionInventory(completed={seen}/{len(self.completed)})"
