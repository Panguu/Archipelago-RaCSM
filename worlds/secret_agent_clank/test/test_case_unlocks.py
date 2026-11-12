import unittest

from ..constants import (
    CASES_BY_PLANET,
    CASE_ID_TO_CASE,
    CASE_NAME_TO_INFOBOT,
    PLANET_NAMES,
    PROGRESSIVE_PLANET_ITEM_NAME,
    SACCases,
)
from ..core.address_maps import CASE_UNLOCK_BASE_ADDRESSES, CASE_UNLOCK_TABLE_OFFSETS, CASE_UNLOCK_TABLE_SLOT_TO_CASE
from ..core.inventories import CaseUnlockInventory, CaseUnlockState, resolve_owned_cases


class TestCaseUnlockState(unittest.TestCase):

    def test_values(self):
        self.assertEqual(0, int(CaseUnlockState.LOCKED))
        self.assertEqual(2, int(CaseUnlockState.UNLOCKED))
        self.assertEqual(3, int(CaseUnlockState.PERMANENTLY_UNLOCKED))


class TestCaseUnlockResolveTable(unittest.TestCase):
    def test_every_confirmed_case_resolves_to_its_own_anchor(self):
        inventory = CaseUnlockInventory(pine=None)
        for case_id, case in CASE_ID_TO_CASE.items():
            anchor = CASE_UNLOCK_BASE_ADDRESSES.get(case.name)
            if not anchor:
                continue
            table = inventory._resolve_table(case_id)
            self.assertEqual(anchor, table.get(case.name), f"case_id {case_id} ({case.name})")

    def test_resolves_every_other_case_relative_to_the_current_anchor(self):
        inventory = CaseUnlockInventory(pine=None)
        table = inventory._resolve_table(1)
        anchor = CASE_UNLOCK_BASE_ADDRESSES[SACCases.BOLTAIRE_MUSEUM]
        self.assertEqual(anchor + 0x060, table[SACCases.BOLTAIRE_GEM_WING])

    def test_table_offsets_has_31_slots(self):
        self.assertEqual(31, len(CASE_UNLOCK_TABLE_OFFSETS))

    def test_slot_is_case_id_plus_one_for_every_case(self):
        for case_id, case in CASE_ID_TO_CASE.items():
            self.assertEqual(case.name, CASE_UNLOCK_TABLE_SLOT_TO_CASE[case_id + 1])

    def test_resolving_a_case_not_the_current_anchor_does_not_reuse_its_own_stale_address(self):
        inventory = CaseUnlockInventory(pine=None)
        larger_than_life_own_anchor = CASE_UNLOCK_BASE_ADDRESSES[SACCases.LARGER_THAN_LIFE]
        resolved_from_boltaire = inventory._resolve_table(1)[SACCases.LARGER_THAN_LIFE]
        self.assertNotEqual(larger_than_life_own_anchor, resolved_from_boltaire)
        boltaire_offset = CASE_UNLOCK_TABLE_OFFSETS[1]
        larger_than_life_offset = CASE_UNLOCK_TABLE_OFFSETS[5]
        boltaire_anchor = CASE_UNLOCK_BASE_ADDRESSES[SACCases.BOLTAIRE_MUSEUM]
        expected = boltaire_anchor + (larger_than_life_offset - boltaire_offset)
        self.assertEqual(expected, resolved_from_boltaire)


class _FakePine:
    def __init__(self, values_by_address: dict[int, int]) -> None:
        self._values = dict(values_by_address)
        self.writes: dict[int, int] = {}

    def batch_read_int8(self, addresses: list[int]) -> list[int]:
        return [self._values[address] for address in addresses]

    def batch_write_int8(self, writes: list[tuple[int, int]]) -> None:
        for address, value in writes:
            self.writes[address] = value


class TestCaseUnlockApplyAllSkipsGarbageReadback(unittest.TestCase):
    """During a transition the old table can read garbage (192 seen live); apply_all() must not write over it."""

    def _table_addresses(self, anchor_case_id: int) -> dict[str, int]:
        inventory = CaseUnlockInventory(pine=None)
        return inventory._resolve_table(anchor_case_id)

    def test_garbage_readback_is_left_untouched(self):
        table = self._table_addresses(1)
        boltaire_museum_addr = table[SACCases.BOLTAIRE_MUSEUM]
        boltaire_gem_wing_addr = table[SACCases.BOLTAIRE_GEM_WING]
        values = dict.fromkeys(table.values(), 0)
        values[boltaire_gem_wing_addr] = 192
        pine = _FakePine(values)
        inventory = CaseUnlockInventory(pine=pine)

        inventory.apply_all({SACCases.BOLTAIRE_MUSEUM, SACCases.BOLTAIRE_GEM_WING}, 1)

        self.assertEqual(CaseUnlockState.PERMANENTLY_UNLOCKED.value, pine.writes.get(boltaire_museum_addr))
        self.assertNotIn(boltaire_gem_wing_addr, pine.writes, "garbage readback must not be written over")

    def test_valid_readback_still_locks_and_unlocks_normally(self):
        table = self._table_addresses(1)
        owned_addr = table[SACCases.BOLTAIRE_MUSEUM]
        unowned_addr = table[SACCases.BOLTAIRE_GEM_WING]
        values = dict.fromkeys(table.values(), 0)
        pine = _FakePine(values)
        inventory = CaseUnlockInventory(pine=pine)

        inventory.apply_all({SACCases.BOLTAIRE_MUSEUM}, 1)

        self.assertEqual(CaseUnlockState.PERMANENTLY_UNLOCKED.value, pine.writes[owned_addr])
        self.assertNotIn(unowned_addr, pine.writes, "already locked needs no write")

    def test_already_permanently_unlocked_is_skipped_same_as_before(self):
        table = self._table_addresses(1)
        owned_addr = table[SACCases.BOLTAIRE_MUSEUM]
        values = dict.fromkeys(table.values(), 0)
        values[owned_addr] = CaseUnlockState.PERMANENTLY_UNLOCKED.value
        pine = _FakePine(values)
        inventory = CaseUnlockInventory(pine=pine)

        inventory.apply_all({SACCases.BOLTAIRE_MUSEUM}, 1)

        self.assertNotIn(owned_addr, pine.writes, "already-3 case is a no-op skip, not a re-write")

    def test_unowned_native_unlock_is_revoked(self):
        table = self._table_addresses(1)
        address = table[SACCases.BOLTAIRE_GEM_WING]
        values = dict.fromkeys(table.values(), 0)
        values[address] = 3
        pine = _FakePine(values)
        CaseUnlockInventory(pine).apply_all(set(), 1)
        self.assertEqual(pine.writes[address], 0)


class TestResolveOwnedCases(unittest.TestCase):

    def test_no_received_items_owns_nothing(self):
        owned = resolve_owned_cases([])
        self.assertEqual(set(), owned)

    def test_starting_case_infobot_grants_boltaire_museum(self):
        infobot = CASE_NAME_TO_INFOBOT[SACCases.BOLTAIRE_MUSEUM]
        owned = resolve_owned_cases([infobot])
        self.assertIn(SACCases.BOLTAIRE_MUSEUM, owned)
        self.assertEqual(1, len(owned))

    def test_case_infobot_grants_its_case(self):
        infobot = CASE_NAME_TO_INFOBOT[SACCases.LARGER_THAN_LIFE]
        owned = resolve_owned_cases([infobot])
        self.assertIn(SACCases.LARGER_THAN_LIFE, owned)

    def test_progressive_planet_unlocks_that_planets_cases_in_order(self):
        planet = PLANET_NAMES[0]
        order = [case.name for case in CASES_BY_PLANET[planet]]
        item = PROGRESSIVE_PLANET_ITEM_NAME[planet]
        self.assertEqual(resolve_owned_cases([item], planet_cases={planet: order}), {order[0]})
        self.assertEqual(resolve_owned_cases([item, item], planet_cases={planet: order}), set(order))
