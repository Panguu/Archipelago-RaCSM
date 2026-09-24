import unittest
from collections import Counter

from test.general import setup_multiworld

from ..constants import CASE_NAME_TO_INFOBOT
from ..constants.weapon_progression import PROGRESSIVE_TO_INTERNAL, max_level
from ..world import SecretAgentClankWorld


class StartingEquipmentTests(unittest.TestCase):
    def test_counts_pool_balance_and_progressive_copy_conservation(self):
        case_file_names = set(CASE_NAME_TO_INFOBOT.values())
        for progressive in (False, True):
            for weapons, gadgets in ((0, 0), (1, 1), (4, 3)):
                m = setup_multiworld(SecretAgentClankWorld, seed=12345, options={
                    "starting_weapons": weapons, "starting_gadgets": gadgets,
                    "progressive_weapons": progressive})
                starting = [i.name for i in m.precollected_items[1]]
                # Infobots=cases (the default) precollects a second Case
                # File too when more than one is available -- see world.py's
                # create_items()'s second_starting_case.
                starting_case_files = sum(1 for name in starting if name in case_file_names)
                self.assertEqual(len(starting), starting_case_files + weapons + gadgets)
                self.assertEqual(len(set(starting)), len(starting))
                self.assertEqual(len(m.itempool), len(m.get_unfilled_locations(1)))
                total = Counter(starting + [i.name for i in m.itempool])
                for name in starting:
                    if name in PROGRESSIVE_TO_INTERNAL:
                        self.assertEqual(total[name], max_level(PROGRESSIVE_TO_INTERNAL[name], 0))
                    else:
                        self.assertEqual(total[name], 1)

    def test_starting_choices_are_seed_deterministic(self):
        options = {"starting_weapons": 4, "starting_gadgets": 3}
        a = setup_multiworld(SecretAgentClankWorld, seed=777, options=options)
        b = setup_multiworld(SecretAgentClankWorld, seed=777, options=options)
        self.assertEqual([i.name for i in a.precollected_items[1]],
                         [i.name for i in b.precollected_items[1]])
