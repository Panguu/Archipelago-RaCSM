import unittest
from pathlib import Path
from types import SimpleNamespace

from BaseClasses import CollectionState
from test.general import setup_multiworld

from ..constants import CASE_NAME_TO_INFOBOT, CASES_BY_OPERATIVE, SACCases, SACOperatives
from ..constants.clank_gadgets import SACClankGadgets
from ..constants.nanotech import CLANK_XP_SAVE_OFFSET
from ..constants.weapon_progression import UNLOCK_TO_PROGRESSIVE
from ..core.patches.progression import Progression
from ..core.symbols import RuntimeSymbols
from ..rules.rule_helpers import CLANK_ENEMY_CASES
from ..world import SecretAgentClankWorld
from .test_runtime import Memory


class NanotechTests(unittest.TestCase):
    def test_clank_saved_xp_only_and_ng_caps(self):
        mem = Memory()
        p = Progression(mem)
        p.configure({"nanotech_checks": True})
        p.ng_address = 0x300ED4
        # Ratchet's XP must not send Clank checks.
        mem.batch_write_int32([(0x3198FC, 999999)])
        self.assertEqual(p.nanotech_checks(), ())
        for ng, count in ((0, 45), (1, 70), (2, 70)):
            p.configure({"nanotech_checks": True, "ng_plus": ng})
            mem.batch_write_int32([(0x300000 + CLANK_XP_SAVE_OFFSET, 469200)])
            self.assertEqual(len(p.nanotech_checks()), count)
        p.ng_address = None
        self.assertEqual(p.nanotech_checks(), ())

    def test_threshold_boundary_and_old_slots(self):
        mem = Memory()
        p = Progression(mem)
        p.ng_address = 0x300ED4
        for xp, count in ((699, 0), (700, 1), (2199, 1), (2200, 2)):
            p.configure({"nanotech_checks": True})
            mem.batch_write_int32([(0x300000 + CLANK_XP_SAVE_OFFSET, xp)])
            self.assertEqual(len(p.nanotech_checks()), count)
        p.configure({})
        self.assertEqual(p.nanotech_checks(), ())

    def test_generation_caps_and_disabled(self):
        for ng, count in ((0, 45), (1, 70), (2, 70)):
            mw = setup_multiworld(SecretAgentClankWorld, options={"ng_plus": ng, "nanotech_checks": True})
            locations = [l for l in mw.get_locations(1) if l.name.startswith("Clank Nanotech Level")]
            self.assertEqual(len(locations), count)
        # Clank Nanotech Locations are off by default.
        mw = setup_multiworld(SecretAgentClankWorld)
        self.assertFalse(any(l.name.startswith("Clank Nanotech Level") for l in mw.get_locations(1)))

    def test_clank_access_required_and_disabled_operative(self):
        mw = setup_multiworld(SecretAgentClankWorld, options={"infobots": "cases", "nanotech_checks": True})
        state = CollectionState(mw)
        for item in mw.precollected_items[1]:
            state.remove(item)
        location = mw.get_location("Clank Nanotech Level 16", 1)
        self.assertFalse(location.can_reach(state))
        mw = setup_multiworld(SecretAgentClankWorld, options={
            "goal": "qwark_opera", "operatives": {"Ratchet": 1, "Qwark": 1}, "nanotech_checks": True})
        self.assertFalse(any(l.name.startswith("Clank Nanotech Level") for l in mw.get_locations(1)))

    def test_case_count_tiers(self):
        # Each Clank case with enemy access puts 10 more levels in logic: 16-25, 26-35, ...
        mw = setup_multiworld(SecretAgentClankWorld, options={"infobots": "cases", "ng_plus": 1, "nanotech_checks": True})
        world = mw.worlds[1]
        infobots = [CASE_NAME_TO_INFOBOT[case.name] for case in CASES_BY_OPERATIVE[SACOperatives.CLANK]]
        state = CollectionState(mw)
        for item in mw.precollected_items[1]:
            if item.name in infobots:
                state.remove(item)
        for item in mw.itempool:
            if item.name not in infobots:
                state.collect(item, prevent_sweep=True)

        def reachable(level):
            return mw.get_location(f"Clank Nanotech Level {level}", 1).can_reach(state)

        self.assertFalse(reachable(16))
        # Klunk's Lair has no enemy access, so it never advances a tier.
        state.collect(world.create_item(CASE_NAME_TO_INFOBOT[SACCases.KLUNKS_LAIR]), prevent_sweep=True)
        self.assertFalse(reachable(16))
        for count, case in enumerate(list(CLANK_ENEMY_CASES)[:7], 1):
            state.collect(world.create_item(CASE_NAME_TO_INFOBOT[case]), prevent_sweep=True)
            self.assertTrue(reachable(15 + 10 * count))
            if count < 7:
                self.assertFalse(reachable(16 + 10 * count))
        self.assertTrue(reachable(85))

    def test_enemy_items_gate_tiers(self):
        mw = setup_multiworld(SecretAgentClankWorld, options={"infobots": "cases", "nanotech_checks": True})
        world = mw.worlds[1]
        infobots = {CASE_NAME_TO_INFOBOT[case.name] for case in CASES_BY_OPERATIVE[SACOperatives.CLANK]}
        state = CollectionState(mw)
        for item in mw.precollected_items[1]:
            state.remove(item)
        for item in mw.itempool:
            if item.name not in infobots and item.name != SACClankGadgets.JETBOOTS:
                state.collect(item, prevent_sweep=True)
        # Starting weapons are precollected rather than pooled, so add these explicitly.
        for name in CLANK_ENEMY_CASES[SACCases.GALACTIC_BOLT_RESERVE]:
            if name != SACClankGadgets.JETBOOTS:
                state.collect(world.create_item(UNLOCK_TO_PROGRESSIVE.get(name, name)
                                                if world.options.progressive_weapons else name), prevent_sweep=True)

        def reachable(level):
            return mw.get_location(f"Clank Nanotech Level {level}", 1).can_reach(state)

        # Galactic Bolt Reserve alone: its enemies need Jetboots.
        state.collect(world.create_item(CASE_NAME_TO_INFOBOT[SACCases.GALACTIC_BOLT_RESERVE]), prevent_sweep=True)
        self.assertFalse(reachable(16))
        state.collect(world.create_item(SACClankGadgets.JETBOOTS), prevent_sweep=True)
        self.assertTrue(reachable(25))
        self.assertFalse(reachable(26))

    def test_tiers_cap_at_available_cases(self):
        from ..rules.nanotech import nanotech_cases_required
        self.assertEqual([nanotech_cases_required(level) for level in (16, 25, 26, 60, 61, 85)], [1, 1, 2, 5, 5, 7])

    def test_ratchet_case_count_tiers(self):
        # Each reachable Ratchet case puts 15 more levels in logic: 21-35, 36-50, ...
        from ..rules.nanotech import ratchet_nanotech_cases_required
        self.assertEqual([ratchet_nanotech_cases_required(level) for level in (21, 35, 36, 60, 61, 90)],
                         [1, 1, 2, 3, 3, 5])
        mw = setup_multiworld(SecretAgentClankWorld, options={
            "infobots": "cases", "ng_plus": 1, "ratchet_nanotech_checks": True})
        world = mw.worlds[1]
        cases = [case.name for case in CASES_BY_OPERATIVE[SACOperatives.RATCHET]]
        infobots = {CASE_NAME_TO_INFOBOT[case] for case in cases}
        state = CollectionState(mw)
        for item in mw.precollected_items[1]:
            if item.name in infobots:
                state.remove(item)
        for item in mw.itempool:
            if item.name not in infobots:
                state.collect(item, prevent_sweep=True)

        def reachable(level):
            return mw.get_location(f"Ratchet Nanotech Level {level}", 1).can_reach(state)

        self.assertFalse(reachable(21))
        for count, case in enumerate(cases, 1):
            state.collect(world.create_item(CASE_NAME_TO_INFOBOT[case]), prevent_sweep=True)
            self.assertTrue(reachable(min(20 + 15 * count, 90)))
            if count < 5:
                self.assertFalse(reachable(21 + 15 * count))

    def test_native_capture_layout(self):

        path = Path(__file__).parents[1] / ".research/vendor_audit_live.ram"
        if not path.exists():
            self.skipTest("Local capture unavailable")
        mem = Memory()
        mem.data[:] = path.read_bytes()
        symbols = RuntimeSymbols.parse(mem.data, 0)
        p = Progression(mem)
        p.configure({"nanotech_checks": True})
        p.prepare(symbols, SimpleNamespace(patches=[]), 1, vendor_enabled=False)
