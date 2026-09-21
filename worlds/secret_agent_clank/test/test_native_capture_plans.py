"""Full hook installation regressions against local read-only research captures."""
import unittest
from pathlib import Path

from ..core.patches import PICKUP_LOCATIONS, VENDOR_LOCATIONS, LocationHooks
from ..core.patches.gain_storage import GainStorage
from ..core.patches.mission_travel import MissionTravel
from ..core.patches.progression import Progression
from ..core.patches.vendor_presentation import VendorPresentation
from ..core.patches.connection_warning import ConnectionWarning
from ..core.patches.titan_vendor import TitanOffers, TitanVendor
from ..core.patches.weapon_mods import WeaponMods
from ..core.patches.wrench import WrenchProgression
from ..core.symbols import RuntimeSymbols
from .test_runtime import Memory


class CaptureMemory(Memory):
    def write_bytes(self, address, data):
        self.data[address:address + len(data)] = data


class NativeCapturePlansTests(unittest.TestCase):
    def test_gain_storage_rejects_a_changed_stub_body_without_writing(self):
        capture = Path(__file__).parents[1] / ".research/showers_forced_graveyard.bin"
        if not capture.exists():
            self.skipTest("Local Graveyard capture not present")
        p = CaptureMemory()
        p.data[:] = capture.read_bytes()
        symbols = RuntimeSymbols.parse(p.data[:0x1000000], 0)
        guards, ranges = GainStorage(p).prepare(symbols)
        self.assertEqual(len(ranges), 4)
        self.assertTrue(all(end - start >= 32 for start, end in ranges))
        # A changed body, even with the original entry still intact, must
        # never become storage: it could now contain actual game behavior.
        p.data[ranges[-1][0]] ^= 1
        before = bytes(p.data)
        with self.assertRaisesRegex(RuntimeError, "Gain storage stub layout changed"):
            GainStorage(p).prepare(symbols)
        self.assertEqual(p.data, before)

    def test_complete_plans_fit_and_restore_every_captured_module(self):
        captures = [p for p in (Path(__file__).parents[1] / ".research").glob("*.bin")
                    if p.stat().st_size == 0x2000000]
        if not captures:
            self.skipTest("Local research RAM captures not present")
        for capture in captures:
            raw = capture.read_bytes()
            from ..core.main_menu import is_main_menu
            captured = CaptureMemory()
            captured.data[:] = raw
            if is_main_menu(captured):
                continue  # Title DLL has no gameplay hook plan.
            symbols = RuntimeSymbols.parse(raw[:0x1000000], 0)
            for ng in (0, 1, 2):
                for progressive in (False, True):
                    with self.subTest(capture=capture.name, ng=ng, progressive=progressive):
                        p = CaptureMemory()
                        p.data[:] = raw
                        module = p.read_int32(0x206328)
                        vendor = module not in (2, 3, 21, 31)
                        hooks = LocationHooks(p)
                        hooks.prepare(symbols, pickup_locations=PICKUP_LOCATIONS,
                                      vendor_locations=VENDOR_LOCATIONS if vendor else {},
                                      entitlements={})
                        wrench = WrenchProgression(p)
                        wrench.enabled = True
                        hooks.patches.extend(wrench.prepare(symbols, module))
                        hooks.patches.extend(MissionTravel(p).prepare(symbols))
                        mods = WeaponMods(p)
                        mods.configure({"weapon_mods": True, "operatives": {"Ratchet": 1, "Clank": 1}, "ng_plus": ng})
                        hooks.patches.extend(mods.prepare(symbols, hooks, module, set(), vendor))
                        progression = Progression(p)
                        progression.configure({"ng_plus": ng, "progressive_weapons": progressive,
                            "weapon_xp_multiplier": 4, "health_xp_multiplier": 5, "bolt_multiplier": 8})
                        if ng and vendor:
                            hooks.patches.extend(TitanVendor(p).prepare(symbols, hooks, set()))
                        elif vendor:
                            hooks.patches.extend(TitanOffers(p).prepare(symbols))
                        hooks.patches.extend(progression.prepare(symbols, hooks, module,
                                                                 vendor_enabled=vendor))
                        if vendor:
                            hooks.patches.extend(VendorPresentation(p).prepare(symbols, hooks))
                        hooks.patches.extend(ConnectionWarning(p).prepare(symbols, hooks))
                        spans = sorted((x.address, x.address + len(x.replacement)) for x in hooks.patches)
                        self.assertTrue(all(b <= c for (a, b), (c, d) in zip(spans, spans[1:])))
                        hooks._install_plan()
                        if vendor:
                            flags = p.read_bytes(hooks.tables["vendor"], 40)
                            for slot in range(40):
                                self.assertEqual(flags[slot], 1 if slot in VENDOR_LOCATIONS else 4)
                        for change in reversed(hooks.patches):
                            p.write_bytes(change.address, change.original)
                        self.assertEqual(p.data, raw)
