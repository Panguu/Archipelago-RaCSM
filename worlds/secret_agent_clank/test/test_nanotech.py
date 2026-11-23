import unittest
from pathlib import Path
from types import SimpleNamespace

from BaseClasses import CollectionState
from test.general import setup_multiworld

from ..constants import (
    CASES_BY_OPERATIVE,
    CASE_NAME_TO_INFOBOT,
    UNLOCK_TO_PROGRESSIVE,
    SACCases,
    SACClankGadgets,
    SACOperatives as Ops,
    SACOperatives,
)
from ..core import RuntimeSymbols, read_nanotech
from ..core.patches import Progression
from ..rules import CLANK_ENEMY_CASES
from ..world import SecretAgentClankWorld
from .test_runtime import Memory
from ..rules.nanotech import nanotech_cases_required
from ..rules.nanotech import ratchet_nanotech_cases_required


class ClankNativeNanotechTests(unittest.TestCase):
    CLANK_XP = 0x19930

    def setUp(self):
        path = Path(__file__).parents[1] / ".research/prison_skin_live.bin"
        if not path.exists():
            self.skipTest("Local capture unavailable")
        self.mem = Memory()
        self.mem.data[:] = path.read_bytes()
        self.symbols = RuntimeSymbols.parse(self.mem.data[:0x1000000], 0)
        self.save = self.mem.read_int32(self.symbols["pGV"])

    def test_native_table_and_caps(self):
        data = read_nanotech(self.mem, self.symbols, Ops.CLANK)
        self.assertEqual((data["ng_cap"], data["ng_plus_cap"]), (60, 85))
        for ng, xp, expected in ((0, 699, 15), (0, 700, 16), (0, 2200, 17), (0, 469200, 60), (1, 469200, 85)):
            with self.subTest(ng=ng, xp=xp):
                self.mem.write_int32(self.save + 0xED4, ng)
                self.mem.write_int32(self.save + self.CLANK_XP, xp)
                self.mem.write_int32(self.save + 0x198FC, 0)
                self.assertEqual(read_nanotech(self.mem, self.symbols, Ops.CLANK)["xp_nanotech"], expected)

    def test_clank_saved_xp_only_and_ng_caps(self):
        p = Progression(self.mem)
        p.ng_address = self.save + 0xED4
        p.configure({"nanotech_checks": True})
        self.mem.write_int32(self.save + self.CLANK_XP, 0)
        self.mem.write_int32(self.save + 0x198FC, 333600)
        self.assertEqual(p.nanotech_checks(self.symbols), ())
        for ng, count in ((0, 45), (1, 70), (2, 70)):
            p.configure({"nanotech_checks": True, "ng_plus": ng})
            self.mem.write_int32(self.save + 0xED4, ng)
            self.mem.write_int32(self.save + self.CLANK_XP, 469200)
            self.assertEqual(len(p.nanotech_checks(self.symbols)), count)
        p.ng_address = None
        self.assertEqual(p.nanotech_checks(self.symbols), ())

    def test_threshold_boundary_and_old_slots(self):
        p = Progression(self.mem)
        p.ng_address = self.save + 0xED4
        self.mem.write_int32(self.save + 0xED4, 0)
        for xp, count in ((699, 0), (700, 1), (2199, 1), (2200, 2)):
            p.configure({"nanotech_checks": True})
            self.mem.write_int32(self.save + self.CLANK_XP, xp)
            self.assertEqual(len(p.nanotech_checks(self.symbols)), count)
        p.configure({})
        self.assertEqual(p.nanotech_checks(self.symbols), ())

    def test_changed_table_rejected(self):
        self.mem.write_int32(self.symbols["g_LevelProgressionExperienceData_Clank"] + 8, 99)
        with self.assertRaisesRegex(ValueError, "table changed"):
            read_nanotech(self.mem, self.symbols, Ops.CLANK)


class NanotechTests(unittest.TestCase):

    def test_generation_caps_and_disabled(self):
        for ng, count in ((0, 45), (1, 70), (2, 70)):
            mw = setup_multiworld(SecretAgentClankWorld, options={"ng_plus": ng, "nanotech_checks": True})
            locations = [l for l in mw.get_locations(1) if l.name.startswith("Clank Nanotech Level")]
            self.assertEqual(len(locations), count)
        mw = setup_multiworld(SecretAgentClankWorld)
        self.assertFalse(any(l.name.startswith("Clank Nanotech Level") for l in mw.get_locations(1)))

    def test_clank_access_required_and_clank_always_enabled(self):
        mw = setup_multiworld(SecretAgentClankWorld, options={"infobots": "cases", "nanotech_checks": True})
        state = CollectionState(mw)
        for item in mw.precollected_items[1]:
            state.remove(item)
        location = mw.get_location("Clank Nanotech Level 16", 1)
        self.assertFalse(location.can_reach(state))
        mw = setup_multiworld(SecretAgentClankWorld, options={
            "goal": "qwark_opera", "operatives": {"Ratchet": 1, "Qwark": 1}, "nanotech_checks": True})
        self.assertTrue(any(l.name.startswith("Clank Nanotech Level") for l in mw.get_locations(1)))

    def test_case_count_tiers(self):
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
        for name in CLANK_ENEMY_CASES[SACCases.GALACTIC_BOLT_RESERVE]:
            if name != SACClankGadgets.JETBOOTS:
                state.collect(world.create_item(UNLOCK_TO_PROGRESSIVE.get(name, name)
                                                if world.options.progressive_weapons else name), prevent_sweep=True)

        def reachable(level):
            return mw.get_location(f"Clank Nanotech Level {level}", 1).can_reach(state)

        state.collect(world.create_item(CASE_NAME_TO_INFOBOT[SACCases.GALACTIC_BOLT_RESERVE]), prevent_sweep=True)
        self.assertFalse(reachable(16))
        state.collect(world.create_item(SACClankGadgets.JETBOOTS), prevent_sweep=True)
        self.assertTrue(reachable(25))
        self.assertFalse(reachable(26))

    def test_tiers_cap_at_available_cases(self):
        self.assertEqual([nanotech_cases_required(level) for level in (16, 25, 26, 60, 61, 85)], [1, 1, 2, 5, 5, 7])

    def test_ratchet_case_count_tiers(self):
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
