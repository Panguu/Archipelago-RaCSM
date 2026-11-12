import unittest

from ..constants import (
    CASES_BY_PLANET,
    CASE_NAME_TO_INFOBOT,
    PLANET_NAMES,
    PROGRESSIVE_PLANET_ITEM_NAME,
    SACCases,
)
from ..core.inventories import resolve_owned_cases


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
