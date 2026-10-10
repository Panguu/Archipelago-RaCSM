import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from BaseClasses import CollectionState
from test.general import setup_multiworld

from ..constants import CASE_NAME_TO_INFOBOT, SACCases
from ..constants.stealth import STEALTH_CASES, STEALTH_MAX_PER_CASE, stealth_location_name
from ..constants.weapon_progression import UNLOCK_TO_PROGRESSIVE
from ..locations import LOCATION_NAME_TO_ID
from ..constants.clank_gadgets import SACClankGadgets, SACClankWeapons
from ..core.patches import PICKUP_LOCATIONS, VENDOR_LOCATIONS, LocationHooks
from ..core.patches import mips as m
from ..core.patches.mission_travel import MissionTravel
from ..core.patches.progression import Progression
from ..core.patches.titan_vendor import TitanOffers, TitanVendor
from ..core.patches.vendor_catalog import VendorCatalog
from ..core.patches.vendor_presentation import VendorPresentation
from ..core.patches.weapon_mods import WeaponMods
from ..core.stealth import END, StealthState
from ..core.symbols import RuntimeSymbols
from ..world import SecretAgentClankWorld
from .mips_cpu import CPU
from .test_native_capture_plans import CaptureMemory


class StealthTests(unittest.TestCase):
    def test_generation_per_case_slider_and_stable_ids(self):
        ids = {}
        for setting in (0, 1, 4, STEALTH_MAX_PER_CASE):
            mw = setup_multiworld(SecretAgentClankWorld, options={"stealth_takedown_checks": setting})
            locations = {l.name: l.address for l in mw.get_locations(1)
                         if l.parent_region.name == "Clank Stealth Takedowns"}
            expected = {case: setting for case in STEALTH_CASES if setting}
            self.assertEqual(set(locations), {stealth_location_name(case, n)
                                              for case, count in expected.items() for n in range(1, count + 1)})
            for name, address in locations.items():
                self.assertEqual(ids.setdefault(name, address), address)
                self.assertEqual(address, LOCATION_NAME_TO_ID[name])
            slot = mw.worlds[1].fill_slot_data()
            self.assertEqual(slot["stealth_takedown_checks"], setting)
            self.assertEqual(slot["stealth_cases"], expected)
        # IDs exist for every stealth case and takedown up to the slider maximum.
        for case in STEALTH_CASES:
            for n in range(1, STEALTH_MAX_PER_CASE + 1):
                self.assertIn(stealth_location_name(case, n), LOCATION_NAME_TO_ID)
        # Without Clank the slider is ignored: no stealth locations, no options error.
        for operatives in ({"Qwark": 1, "Ratchet": 1}, {"Qwark": 1, "Clank": 0}):
            mw = setup_multiworld(SecretAgentClankWorld, options={"stealth_takedown_checks": 5,
                "goal": "qwark_opera", "operatives": operatives})
            self.assertFalse(any(l.parent_region.name == "Clank Stealth Takedowns" for l in mw.get_locations(1)))
            self.assertEqual(mw.worlds[1].fill_slot_data()["stealth_cases"], {})

    def test_access_requires_case_and_case_items(self):
        mw = setup_multiworld(SecretAgentClankWorld, options={"stealth_takedown_checks": 2, "infobots": "cases"})
        world = mw.worlds[1]
        state = CollectionState(mw)
        for item in mw.precollected_items[1]:
            state.remove(item)

        def reachable(case):
            return mw.get_location(stealth_location_name(case, 2), 1).can_reach(state)

        def collect_weapon(weapon):
            state.collect(world.create_item(UNLOCK_TO_PROGRESSIVE.get(weapon, weapon)
                                            if world.options.progressive_weapons else weapon))

        # Other stealth cases only need the case itself.
        museum = SACCases.BOLTAIRE_MUSEUM
        self.assertFalse(reachable(museum))
        state.collect(world.create_item(CASE_NAME_TO_INFOBOT[museum]))
        self.assertTrue(reachable(museum))
        # Asyanica Rooftops also needs its case-complete items: Throwtie, Jetboots and the Omnikey.
        rooftops = SACCases.ASYANICA_ROOFTOPS
        state.collect(world.create_item(CASE_NAME_TO_INFOBOT[rooftops]))
        self.assertFalse(reachable(rooftops))
        collect_weapon(SACClankWeapons.THROWTIE)
        self.assertFalse(reachable(rooftops))
        state.collect(world.create_item(SACClankGadgets.JETBOOTS))
        self.assertFalse(reachable(rooftops))
        # Galactic Bolt Reserve also needs Cufflink and the Omnikey.
        reserve = SACCases.GALACTIC_BOLT_RESERVE
        state.collect(world.create_item(CASE_NAME_TO_INFOBOT[reserve]))
        self.assertFalse(reachable(reserve))
        collect_weapon(SACClankWeapons.CUFFLINK)
        self.assertFalse(reachable(reserve))
        state.collect(world.create_item(SACClankGadgets.OMNIKEY))
        self.assertTrue(reachable(rooftops))
        self.assertTrue(reachable(reserve))

    def test_native_counter_caps_preserves_arguments_and_tail_calls(self):
        mem = CaptureMemory()
        mem.write_int32 = lambda a, n: mem.batch_write_int32([(a, n)])
        counter, entry, target = 0x110000, 0x120000, 0x130000
        mem.write_bytes(entry, StealthState.wrapper(counter, target))
        for count in (0, 4, STEALTH_MAX_PER_CASE - 1, STEALTH_MAX_PER_CASE):
            mem.write_int32(counter, count)
            cpu = CPU(mem)
            cpu.r[m.A0] = 0x123456
            cpu.run(entry, stop=target)
            self.assertEqual(mem.read_int32(counter), min(count + 1, STEALTH_MAX_PER_CASE))
            self.assertEqual(cpu.r[m.A0], 0x123456)
            self.assertEqual(cpu.r[m.RA], CPU.STOP)

    def test_poll_retry_reload_and_state_loading(self):
        museum, alley = SACCases.BOLTAIRE_MUSEUM, SACCases.AZCOTAL_ALLEY
        mem = CaptureMemory()
        s = StealthState(mem)
        s.configure({museum: 2, alley: 3}, reset=True)
        s.binding = (museum, 0x1000, 0x2000, b"site", 0x3000, b"code")
        mem.write_bytes(0x2000, b"site")
        mem.write_bytes(0x3000, b"code")
        mem.batch_write_int32([(0x1000, 4)])
        s.on_count = Mock()
        s.poll()
        self.assertEqual(s.checks(), ())
        s.load({alley: 1})
        s.poll()
        s.on_count.assert_called_once_with({museum: 4})
        # Each case is capped at its own check count; other cases keep their own progress.
        self.assertEqual(s.checks(), (stealth_location_name(museum, 1), stealth_location_name(museum, 2),
                                      stealth_location_name(alley, 1)))
        self.assertEqual(s.checks(), s.checks())  # checks retry until normal delivery accepts them
        mem.batch_write_int32([(0x1000, 0)])
        s.poll()
        self.assertEqual(mem.read_int32(0x1000), 4)
        s.configure({museum: 2, alley: 3})
        s.load({museum: 1})
        self.assertEqual(s.counts, {museum: 4, alley: 1})
        mem.write_bytes(0x2000, b"gone")
        s.poll()
        self.assertIsNone(s.binding)
        with self.assertRaises(ValueError):
            s.load(5)  # The old single global counter.
        s.configure({}, reset=True)
        self.assertEqual(s.checks(), ())

    def test_prepare_skips_cases_without_checks(self):
        s = StealthState(CaptureMemory())
        s.configure({SACCases.AZCOTAL_ALLEY: 1})
        self.assertEqual(s.prepare({}, Mock(), SACCases.BOLTAIRE_MUSEUM), [])
        self.assertIsNone(s.binding)

    def test_research_captures_validate_success_path_and_plan(self):
        paths = list((Path(__file__).parents[1] / ".research").glob("*.ram"))
        if not paths:
            self.skipTest("Local RAM captures unavailable")
        seen = 0
        for path in paths:
            mem = CaptureMemory()
            mem.data[:] = path.read_bytes()
            symbols = RuntimeSymbols.parse(mem.data, 0)
            if END not in symbols:
                continue
            seen += 1
            s = StealthState(mem)
            s.configure({SACCases.BOLTAIRE_MUSEUM: STEALTH_MAX_PER_CASE})
            s.load({SACCases.BOLTAIRE_MUSEUM: 7})
            progression = Progression(mem)
            progression.stealth = s
            edits = progression.prepare(symbols, SimpleNamespace(patches=[]), 1, vendor_enabled=False)
            self.assertIsNotNone(s.binding, path.name)
            spans = sorted((p.address, p.address + len(p.replacement)) for p in edits)
            self.assertTrue(all(b <= c for (a,b),(c,d) in zip(spans, spans[1:])))
            for edit in edits:
                self.assertEqual(mem.read_bytes(edit.address, len(edit.original)), edit.original)
                mem.write_bytes(edit.address, edit.replacement)
            s.poll()
            self.assertEqual(s.counts, {SACCases.BOLTAIRE_MUSEUM: 7})
            for edit in reversed(edits):
                mem.write_bytes(edit.address, edit.original)
            mem.batch_write_int32([(symbols[END] + 0x4C, 0)])
            with self.assertRaisesRegex(RuntimeError, "path changed"):
                s.prepare(symbols, Mock(), SACCases.BOLTAIRE_MUSEUM)
        self.assertGreater(seen, 0)

    def test_combined_pickup_vendor_progression_and_stealth_plans(self):
        paths = list((Path(__file__).parents[1] / ".research").glob("*.ram"))
        if not paths:
            self.skipTest("Local captures unavailable")
        verified = 0
        for path in paths:
            raw = path.read_bytes()
            symbols = RuntimeSymbols.parse(raw, 0)
            if END not in symbols:
                continue
            verified += 1
            for ng, mode in ((0, 0), (1, 1), (2, 2)):
                with self.subTest(capture=path.name, ng=ng, mode=mode):
                    mem = CaptureMemory()
                    mem.data[:] = raw
                    module = mem.read_int32(0x206328)
                    hooks = LocationHooks(mem)
                    hooks.prepare(symbols, pickup_locations=PICKUP_LOCATIONS,
                                  vendor_locations=VENDOR_LOCATIONS, entitlements={})
                    hooks.patches.extend(MissionTravel(mem).prepare(symbols))
                    mods = WeaponMods(mem)
                    mods.configure({"ng_plus": ng})
                    hooks.patches.extend(mods.prepare(symbols, hooks, module, (), True))
                    if ng:
                        hooks.patches.extend(TitanVendor(mem).prepare(symbols, hooks, ()))
                    else:
                        hooks.patches.extend(TitanOffers(mem).prepare(symbols))
                    prog = Progression(mem)
                    prog.configure({"ng_plus": ng, "progressive_weapons": mode,
                        "weapon_xp_multiplier": 4 if module == 1 else 1,
                        "health_xp_multiplier": 5 if module == 1 else 1,
                        "bolt_multiplier": 8 if module == 1 else 1})
                    prog.stealth = StealthState(mem)
                    prog.stealth.configure(dict.fromkeys(STEALTH_CASES, STEALTH_MAX_PER_CASE))
                    prog.stealth.load({})
                    hooks.patches.extend(VendorCatalog(mem).prepare(symbols, hooks))
                    hooks.patches.extend(prog.prepare(symbols, hooks, module))
                    hooks.patches.extend(VendorPresentation(mem).prepare(symbols, hooks))
                    # The pre-existing ConnectionWarning prologue signature
                    # does not match these captures (second word is LUI).
                    # Its unrelated installation is covered by its own tests.
                    spans = sorted((p.address, p.address + len(p.replacement)) for p in hooks.patches)
                    self.assertTrue(all(b <= c for (a,b),(c,d) in zip(spans, spans[1:])))
                    hooks._install_plan()
                    for change in reversed(hooks.patches):
                        mem.write_bytes(change.address, change.original)
                    self.assertEqual(mem.data, raw)

        self.assertGreater(verified, 0, "No combined capture plans were tested")
