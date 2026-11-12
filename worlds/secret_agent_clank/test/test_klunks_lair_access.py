import unittest

from BaseClasses import CollectionState
from test.general import setup_multiworld

from ..constants import SACCases, SACClankGadgets, SACProgressiveClankWeapons
from ..rules import KLUNKS_LAIR_WEAPONS
from ..world import SecretAgentClankWorld

KLUNK = SACCases.KLUNKS_LAIR


def _state(mw, names):
    state = CollectionState(mw)
    state.prog_items[1].clear()
    state.stale[1] = True
    for name in names:
        state.collect(mw.worlds[1].create_item(name), prevent_sweep=True)
    return state


class KlunksLairAccessTests(unittest.TestCase):
    def test_case_file_alone_is_not_enough(self):
        mw = setup_multiworld(SecretAgentClankWorld, options={"infobots": "cases"})
        entrance = mw.get_entrance(f"To {KLUNK}", 1)
        self.assertFalse(entrance.access_rule(_state(mw, [KLUNK])))
        self.assertFalse(entrance.access_rule(_state(mw, [KLUNK, *KLUNKS_LAIR_WEAPONS[:2]])))
        self.assertTrue(entrance.access_rule(_state(mw, [KLUNK, *KLUNKS_LAIR_WEAPONS[:3]])))

    def test_progressive_weapons_need_three_different_weapons(self):
        mw = setup_multiworld(SecretAgentClankWorld, options={"infobots": "cases", "progressive_weapons": "manual"})
        entrance = mw.get_entrance(f"To {KLUNK}", 1)
        tie = SACProgressiveClankWeapons.THROWTIE
        self.assertFalse(entrance.access_rule(_state(mw, [KLUNK, tie, tie, tie])))
        self.assertTrue(entrance.access_rule(_state(
            mw, [KLUNK, tie, SACProgressiveClankWeapons.CUFFLINK, SACProgressiveClankWeapons.TANGLEVINE])))

    def test_challenge_mode_also_needs_pda_and_nanotech(self):
        for options in ({"ng_plus": 1}, {"ng_plus": 2, "progressive_challenge_mode": True}):
            with self.subTest(**options):
                mw = setup_multiworld(SecretAgentClankWorld, options={"infobots": "cases", **options})
                entrance = mw.get_entrance(f"To {KLUNK}", 1)
                everything = [item.name for item in mw.itempool if item.player == 1 and item.advancement]
                everything += [item.name for item in mw.precollected_items[1]]
                self.assertFalse(entrance.access_rule(_state(mw, [KLUNK, *KLUNKS_LAIR_WEAPONS[:3]])))
                self.assertFalse(entrance.access_rule(_state(
                    mw, [name for name in everything if name != SACClankGadgets.CLANKPDA])))
                self.assertTrue(entrance.access_rule(_state(mw, everything)))

    def test_klunks_lair_is_never_a_starting_case(self):
        for mode in ("cases", "progressive_planet"):
            for seed in range(10):
                with self.subTest(mode=mode, seed=seed):
                    world = setup_multiworld(SecretAgentClankWorld, seed=seed, options={"infobots": mode}).worlds[1]
                    self.assertNotIn(KLUNK, (world.starting_case, world.second_starting_case))
