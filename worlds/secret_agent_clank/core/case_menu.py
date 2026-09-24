"""Native Operatives -> Cases menu, separate from mission completion flags."""
import struct
from dataclasses import dataclass

from ..constants.planets import SACCases

# Text IDs stored in mission+0x3C, grouped by operative in the USA table.
# Catalog IDs are NOT loaded module IDs: Asyanica shares module 4 and Qwark's
# Suck and Jive shares module 11; Countess's Villa uses module 7.
CASE_LABELS = {
    5636: SACCases.HIGH_TREEHOUSE,
    **dict(zip(range(5606, 5611), (SACCases.MAX_SECURITY_CELLS, SACCases.THE_MESS_HALL,
        SACCases.THE_EXERCISE_YARD, SACCases.THE_SHOWERS, SACCases.PRISON_BREAKOUT))),
    **dict(zip(range(5611, 5621), (SACCases.BOLTAIRE_MUSEUM, SACCases.ASYANICA_ROOFTOPS,
        SACCases.AZCOTAL_ALLEY, SACCases.GONDOLA_ASCENT, SACCases.HIGH_ROLLERS_CASINO,
        SACCases.VENANTONIO_LABS, SACCases.GALACTIC_BOLT_RESERVE,
        SACCases.SPACESHIP_GRAVEYARD, SACCases.UNDERWATER_BUNKER, SACCases.KLUNKS_LAIR))),
    **dict(zip(range(5621, 5626), (SACCases.LARGER_THAN_LIFE, SACCases.SUCK_AND_JIVE,
        SACCases.MADAM_BUTTERQWARK, SACCases.SAINT_QWARK, SACCases.A_FICTION_FULL_OF_DOLLARS))),
    **dict(zip(range(5626, 5629), (SACCases.ROOFTOP_DEATHTRAP, SACCases.INSIDE_THE_A_EYE,
        SACCases.BULKHEAD_LOCK))),
    **dict(zip(range(5629, 5636), (SACCases.BOLTAIRE_GEM_WING, SACCases.COUNTESS_VILLA,
        SACCases.GLACIARA_SKI_SLOPES, SACCases.HIGH_STAKES_ROOM, SACCases.VENANTONIO_CANALS,
        SACCases.THE_QUASAR_FIELDS, SACCases.DAMS_EDGE_HYDRANO))),
}


def ee_pointer(address: int, size: int = 4) -> bool:
    return address % 4 == 0 and 0x100000 <= address <= 0x2000000 - size


@dataclass(frozen=True)
class CaseMenuEntry:
    index: int
    node: int
    mission: int
    selectable: int
    visible: int
    module_id: int
    operative_mask: int
    operative_label: int
    case_label: int


class CaseMenu:
    def __init__(self, pine):
        self.pine = pine
        self.screen_address = None
        self.parent_header = None
        self.child_header = None
        self.mission_table = None

    def bind_runtime(self, symbols) -> bool:
        self.screen_address = self.parent_header = self.child_header = None
        self.mission_table = None
        pause = symbols.get("g_PauseModeData")
        update = symbols.get("SCRNGALACTICMAP_Update__Fv")
        render = symbols.get("SCRNGALACTICMAP_Render__Fv")
        getter = symbols.get("PAUSEMENU_GetCurrentItemNode__FP10tPAUSEMENU")
        if None in (pause, update, render, getter) or not 0 < render - update <= 0x1000:
            return False
        code = self.pine.read_bytes(update, render - update)
        words = struct.unpack("<" + "I" * (len(code) // 4), code)
        targets = []
        for i in range(1, len(words) - 1):
            if words[i] != 0x0C000000 | (getter >> 2):
                continue
            delay = words[i + 1]
            if delay & 0xFFFF0000 != 0x24840000:  # addiu a0,a0,lo
                continue
            high = next((words[j] for j in range(i - 1, max(-1, i - 3), -1)
                         if words[j] & 0xFFFF0000 == 0x3C040000), None)
            if high is None:
                continue
            low = delay & 0xFFFF
            address = ((high & 0xFFFF) << 16) + (low - 0x10000 if low & 0x8000 else low)
            if ee_pointer(address, 12) and address not in targets:
                targets.append(address)
        if len(targets) != 2:
            return False
        self.child_header, self.parent_header = targets
        self.screen_address = pause + 12
        self.mission_table = symbols.get("g_MISSION_LEVEL_LIST")
        return True

    def unlock_owned_missions(self, owned_cases: set[str]) -> set[str]:
        """Expose the first story mission for each received case by menu label."""
        if self.mission_table is None or not owned_cases:
            return set()
        table = self.pine.read_bytes(self.mission_table, 33 * 8)
        first = {}
        for slot in range(33):
            pointer, count = struct.unpack_from("<2I", table, slot * 8)
            if not 0 < count <= 16 or not ee_pointer(pointer, count * 0x60):
                continue
            tasks = self.pine.read_bytes(pointer, count * 0x60)
            for index in range(count):
                task = index * 0x60
                kind = struct.unpack_from("<I", tasks, task)[0]
                label = struct.unpack_from("<I", tasks, task + 0x3C)[0]
                name = CASE_LABELS.get(label)
                if kind == 1 and name in owned_cases and name not in first:
                    first[name] = (pointer + task + 12,
                                   struct.unpack_from("<I", tasks, task + 12)[0])
        # A completion or module reload can happen while PINE reads the table.
        # Never downgrade a mission that completed after the initial snapshot.
        if self.pine.read_bytes(self.mission_table, 33 * 8) != table:
            return set()
        changed = {name: address for name, (address, state) in first.items()
                   if state in (0, 1) and self.pine.read_int32(address) in (0, 1)}
        writes = [(address, 2) for address in changed.values()]
        if writes:
            self.pine.batch_write_int32(writes)
        return set(changed)

    def _header(self, address):
        if address is None:
            return None
        pointer, count, selected = struct.unpack("<3I", self.pine.read_bytes(address, 12))
        if not 0 < count <= 64 or selected >= count or not ee_pointer(pointer, count * 4):
            return None
        return pointer, count, selected

    def read_entries(self) -> list[CaseMenuEntry]:
        if self.screen_address is None or self.pine.read_int32(self.screen_address) != 14:
            return []
        parent = self._header(self.parent_header)
        child = self._header(self.child_header)
        if parent is None or child is None:
            return []
        parent_node = self.pine.read_int32(parent[0] + parent[2] * 4)
        if not ee_pointer(parent_node, 0xD4):
            return []
        operative = self.pine.read_int32(parent_node + 0xD0)
        if operative not in range(5601, 5606):
            return []
        entries = []
        nodes = self.pine.batch_read_int32([child[0] + i * 4 for i in range(child[1])])
        for index, node in enumerate(nodes):
            if not ee_pointer(node, 0xD4):
                return []
            flags = self.pine.read_bytes(node + 0xCC, 8)
            selectable, visible = flags[:2]
            mission = struct.unpack_from("<I", flags, 4)[0]
            if selectable not in (0, 1) or visible not in (0, 1) or not ee_pointer(mission, 0x60):
                return []
            module, mask, parent_label, label = struct.unpack("<4I", self.pine.read_bytes(mission + 0x30, 16))
            if not 1 <= module <= 31 or mask not in (1, 2, 4, 8, 16) or parent_label != operative:
                return []
            entries.append(CaseMenuEntry(index, node, mission, selectable, visible, module, mask, parent_label, label))
        if self._header(self.parent_header) != parent or self._header(self.child_header) != child:
            return []
        return entries

    def apply_access(self, owned_cases: set[str]) -> None:
        """Reconcile visible case rows; never write mission state or visibility."""
        for entry in self.read_entries():
            name = CASE_LABELS.get(entry.case_label)
            if name is None:
                continue
            desired = int(name in owned_cases)
            if entry.selectable == desired:
                continue
            # Check the row's identity again immediately before the write.
            # Header addresses are rebound by CaseInventory after transitions.
            if (self.pine.read_int32(self.screen_address) != 14
                    or self.pine.read_int32(entry.node + 0xD0) != entry.mission
                    or self.pine.read_int32(entry.mission + 0x3C) != entry.case_label):
                return
            self.pine.write_int8(entry.node + 0xCC, desired)
