from enum import IntEnum

from ...constants import (
    ALL_CASES,
    CASE_ID_TO_CASE,
    CASE_NAME_TO_INFOBOT,
    PROGRESSIVE_PLANET_ITEM_NAME,
)
from ..address_maps import (
    CASE_NAME_TO_UNLOCK_SLOT,
    CASE_UNLOCK_BASE_ADDRESSES,
    CASE_UNLOCK_TABLE_OFFSETS,
)
from ...pypine import Pine


class CaseUnlockState(IntEnum):
    LOCKED = 0
    UNLOCKED = 2
    PERMANENTLY_UNLOCKED = 3


def resolve_owned_cases(received_names: list[str], *, planet_cases: dict[str, list[str]] | None = None) -> set[str]:
    """Every case name the player currently has logical access to, derived from received item names alone."""
    owned: set[str] = set()

    for case_name, infobot in CASE_NAME_TO_INFOBOT.items():
        if infobot in received_names:
            owned.add(case_name)

    for planet, cases in (planet_cases or {}).items():
        owned.update(cases[:received_names.count(PROGRESSIVE_PLANET_ITEM_NAME[planet])])
    return owned


class CaseUnlockInventory:
    """Reads and writes every case's locked/unlocked gate, located from the currently loaded case."""

    def __init__(self, pine: Pine) -> None:
        self.pine = pine

    def _resolve_table(self, current_case_id: int | None) -> dict[str, int]:
        """Every case's gate address, recomputed each call from the currently loaded case."""
        current_case = CASE_ID_TO_CASE.get(current_case_id) if current_case_id is not None else None
        if current_case is None:
            return {}
        anchor = CASE_UNLOCK_BASE_ADDRESSES.get(current_case.name, 0)
        if not anchor:
            return {}
        current_slot = CASE_NAME_TO_UNLOCK_SLOT.get(current_case.name)
        if current_slot is None:
            return {}
        current_offset = CASE_UNLOCK_TABLE_OFFSETS[current_slot - 1]
        result = {}
        for case in ALL_CASES:
            slot = CASE_NAME_TO_UNLOCK_SLOT.get(case.name)
            if slot is None:
                continue
            result[case.name] = anchor + (CASE_UNLOCK_TABLE_OFFSETS[slot - 1] - current_offset)
        return result

    def apply_all(self, owned_case_names: set[str], current_case_id: int | None) -> None:
        """Unlock every owned case and lock the rest, in one batch write."""
        table = self._resolve_table(current_case_id)
        if not table:
            return
        names = list(table)
        addresses = [table[name] for name in names]
        current_values = self.pine.batch_read_int8(addresses)
        recognized = {state.value for state in CaseUnlockState}
        writes = [
            (
                address,
                (CaseUnlockState.PERMANENTLY_UNLOCKED if name in owned_case_names else CaseUnlockState.LOCKED).value,
            )
            for name, address, current in zip(names, addresses, current_values)
            if current in recognized and current != (
                CaseUnlockState.PERMANENTLY_UNLOCKED.value if name in owned_case_names
                else CaseUnlockState.LOCKED.value
            )
        ]
        if writes:
            self.pine.batch_write_int8(writes)
