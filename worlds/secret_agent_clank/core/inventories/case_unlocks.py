"""Per-case unlock gate."""
from enum import IntEnum
from typing import TYPE_CHECKING

from ...constants import CHARACTER_ITEM_NAME, PROGRESSIVE_CHARACTER_ITEM_NAME, SACOperatives
from ...constants.planets import (
    ALL_CASES,
    CASE_ID_TO_CASE,
    CASE_NAME_TO_INFOBOT,
    CASES_BY_OPERATIVE,
    CASES_BY_PLANET,
    PLANET_ACCESS_ITEM_NAME,
    PLANET_NAMES,
)
from ...items import PROGRESSIVE_PLANET_ITEM_NAME
from ..address_maps import (
    CASE_NAME_TO_UNLOCK_SLOT,
    CASE_UNLOCK_BASE_ADDRESSES,
    CASE_UNLOCK_TABLE_OFFSETS,
)

if TYPE_CHECKING:
    from ...pypine import Pine


class CaseUnlockState(IntEnum):
    LOCKED = 0
    UNLOCKED = 2
    PERMANENTLY_UNLOCKED = 3


def resolve_owned_cases(received_names: list[str], *, character_unlocks: bool = False,
                        progressive_planets: list[str] | None = None) -> set[str]:
    """Every case name the player currently has logical access to, derived from received item names alone."""
    owned: set[str] = set()

    for case_name, infobot in CASE_NAME_TO_INFOBOT.items():
        if infobot in received_names:
            owned.add(case_name)

    for planet, item in PLANET_ACCESS_ITEM_NAME.items():
        if item in received_names:
            owned.update(case.name for case in CASES_BY_PLANET.get(planet, ()))

    progressive_count = received_names.count(PROGRESSIVE_PLANET_ITEM_NAME)
    if progressive_count:
        planets = PLANET_NAMES[1:] if progressive_planets is None else progressive_planets
        for planet in planets[:progressive_count]:
            owned.update(case.name for case in CASES_BY_PLANET.get(planet, ()))

    if character_unlocks:
        owned.update(case.name for case in CASES_BY_OPERATIVE[SACOperatives.SPECIAL_MISSIONS])
        for operative, item in CHARACTER_ITEM_NAME.items():
            if item in received_names:
                owned.update(case.name for case in CASES_BY_OPERATIVE[operative])
        for operative, item in PROGRESSIVE_CHARACTER_ITEM_NAME.items():
            owned.update(case.name for case in CASES_BY_OPERATIVE[operative][:received_names.count(item)])
    return owned


class CaseUnlockInventory:
    """Reads/writes every case's locked/unlocked gate in one batch call, resolved off whichever case is currently loaded (see module docstring)."""

    def __init__(self, pine: "Pine") -> None:
        self.pine = pine

    def _resolve_table(self, current_case_id: "int | None") -> dict[str, int]:
        """Every case's live address, re-derived fresh off whichever case is CURRENTLY loaded (see module docstring) -- never cached across calls, so a case transition since the last call is picked up automatically instead of reusing a now-stale table location."""
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

    def read_all(self, current_case_id: "int | None") -> dict[str, "CaseUnlockState | None"]:
        """Batch-read every case's current locked/unlocked byte."""
        table = self._resolve_table(current_case_id)
        if not table:
            return {}
        names = list(table)
        raw_values = self.pine.batch_read_int8([table[name] for name in names])
        result: dict[str, CaseUnlockState | None] = {}
        for name, value in zip(names, raw_values):
            try:
                result[name] = CaseUnlockState(value)
            except ValueError:
                result[name] = None
        return result

    def apply_all(self, owned_case_names: "set[str]", current_case_id: "int | None") -> None:
        """Rebuild every case's unlock gate from AP truth in a single batch write -- UNLOCKED for every case in owned_case_names, LOCKED otherwise."""
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

    def force_unlock(self, case_name: str, current_case_id: "int | None") -> bool:
        """Debug/testing helper -- force a single case's gate UNLOCKED (writes 3, PERMANENTLY_UNLOCKED -- the real unlocked value, see module docstring) without touching any other case's byte."""
        table = self._resolve_table(current_case_id)
        address = table.get(case_name)
        if address is None:
            return False
        self.pine.write_int8(address, CaseUnlockState.PERMANENTLY_UNLOCKED.value)
        return True

    def force_lock(self, case_name: str, current_case_id: "int | None") -> bool:
        """Debug/testing helper -- force a single case's gate LOCKED without touching any other case's byte."""
        table = self._resolve_table(current_case_id)
        address = table.get(case_name)
        if address is None:
            return False
        self.pine.write_int8(address, CaseUnlockState.LOCKED.value)
        return True
