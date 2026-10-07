"""Full hook installation regressions against local read-only research captures."""
import unittest
from itertools import product
from pathlib import Path

from ..core.main_menu import is_main_menu
from ..core.patches import MARKER, PICKUP_LOCATIONS, VENDOR_LOCATIONS, LocationHooks
from ..core.native_runtime import NativeRuntime
from ..constants.native_functions import NativeFunctions
from ..core.patches.connection_warning import ConnectionWarning
from ..core.patches.gain_storage import GainStorage
from ..core.patches.mission_travel import MissionTravel
from ..core.patches.progression import Progression
from ..core.patches.titan_vendor import TitanOffers, TitanVendor
from ..core.patches.vendor_catalog import VendorCatalog
from ..core.patches.vendor_presentation import VendorPresentation
from ..core.patches.weapon_mods import WeaponMods
from ..core.patches.wrench import WrenchProgression
from ..core.stealth import StealthState
from ..core.symbols import RuntimeSymbols
from .test_runtime import Memory


class CaptureMemory(Memory):
    def write_bytes(self, address, data):
        self.data[address:address + len(data)] = data

    def write_int8(self, address, value):
        self.batch_write_int8([(address, value)])


class NativeCapturePlansTests(unittest.TestCase):
    def test_line_storage_rejects_changes_in_body_and_callee(self):
        capture = Path(__file__).parents[1] / ".research/SAC.p2s.ram"
        if not capture.exists():
            self.skipTest("Local clean capture not present")
        p = CaptureMemory()
        p.data[:] = capture.read_bytes()
        symbols = RuntimeSymbols.parse(p.data[:0x1000000], 0)
        before = bytes(p.data)
        guards, ranges = GainStorage(p).prepare_line(symbols)
        self.assertEqual(bytes(p.data), before)
        self.assertEqual(ranges, [(guards[0].address + 8, guards[0].address + 104)])
        for address in (guards[0].address, guards[0].address + 0x44,
                        guards[0].address + 0x54, symbols["SetARGB__7ApeRGBAUi"]):
            with self.subTest(address=hex(address)):
                p.data[address] ^= 1
                with self.assertRaisesRegex(RuntimeError, "line stub layout changed"):
                    GainStorage(p).prepare_line(symbols)
                p.data[address] ^= 1
                self.assertEqual(bytes(p.data), before)

    def test_gain_storage_rejects_a_changed_stub_body_without_writing(self):
        capture = Path(__file__).parents[1] / ".research/showers_forced_graveyard.bin"
        if not capture.exists():
            self.skipTest("Local Graveyard capture not present")
        p = CaptureMemory()
        p.data[:] = capture.read_bytes()
        symbols = RuntimeSymbols.parse(p.data[:0x1000000], 0)
        _guards, ranges = GainStorage(p).prepare(symbols)
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
        captures = [p for pattern in ("*.bin", "*.ram")
                    for p in (Path(__file__).parents[1] / ".research").glob(pattern)
                    if p.stat().st_size == 0x2000000]
        if not captures:
            self.skipTest("Local research RAM captures not present")
        for capture in captures:
            raw = capture.read_bytes()
            captured = CaptureMemory()
            captured.data[:] = raw
            if is_main_menu(captured):
                continue  # Title DLL has no gameplay hook plan.
            if MARKER in raw:
                with self.subTest(capture=capture.name):
                    self.skipTest("Capture already contains installed AP hooks")
                continue
            symbols = RuntimeSymbols.parse(raw[:0x1000000], 0)
            for ng, progressive, multiplier in product((0, 1, 2), (False, True, 1), (3, 4)):
                with self.subTest(capture=capture.name, ng=ng, progressive=progressive, multiplier=multiplier):
                    p = CaptureMemory()
                    p.data[:] = raw
                    module = p.read_int32(0x206328)
                    vendor = NativeRuntime(p, None, lambda _: None).vendor_enabled_for_module(module)
                    hooks = LocationHooks(p)
                    hooks.prepare(symbols, pickup_locations=PICKUP_LOCATIONS,
                                  vendor_locations=VENDOR_LOCATIONS if vendor else {},
                                  entitlements={}, vendor_enabled=vendor)
                    wrench = WrenchProgression(p)
                    wrench.enabled = True
                    hooks.patches.extend(wrench.prepare(symbols, module))
                    hooks.patches.extend(MissionTravel(p).prepare(symbols, module=module))
                    mods = WeaponMods(p)
                    mods.configure({"weapon_mods": True, "operatives": {"Ratchet": 1, "Clank": 1}, "ng_plus": ng})
                    hooks.patches.extend(mods.prepare(symbols, hooks, module, set(), vendor))
                    progression = Progression(p)
                    progression.configure({"ng_plus": ng, "progressive_weapons": progressive,
                        "weapon_xp_multiplier": multiplier, "health_xp_multiplier": multiplier, "bolt_multiplier": multiplier})
                    progression.stealth = StealthState(p)
                    progression.stealth.configure(3)
                    progression.stealth.load(0)
                    if ng and vendor:
                        hooks.patches.extend(TitanVendor(p).prepare(symbols, hooks, set()))
                    elif vendor:
                        hooks.patches.extend(TitanOffers(p).prepare(symbols))
                    if vendor:
                        hooks.patches.extend(VendorCatalog(p).prepare(symbols, hooks))
                    if vendor:
                        hooks.patches.extend(VendorPresentation(p).prepare(symbols, hooks))
                    hooks.patches.extend(ConnectionWarning(p).prepare(symbols, hooks))
                    hooks.patches.extend(progression.prepare(symbols, hooks, module,
                                                             vendor_enabled=vendor))
                    spans = sorted((x.address, x.address + len(x.replacement)) for x in hooks.patches)
                    self.assertTrue(all(b <= c for (a, b), (c, d) in zip(spans, spans[1:])))
                    self.assertEqual(p.data, raw, "Planning must not write RAM")
                    hooks._install_plan()
                    if not vendor:
                        for name, size in ((NativeFunctions.SCRNVENDOR_PROCESS_PURCHASE, 0x350),
                                           (NativeFunctions.GADGET_IS_SELLABLE, 0x30)):
                            address = symbols.get(name)
                            if address is not None:
                                self.assertEqual(p.read_bytes(address, size), raw[address:address + size])
                        self.assertNotIn("vendor", hooks.tables)
                    if progression.stealth.binding is not None:
                        counter, site, replacement, address, code = progression.stealth.binding
                        self.assertGreater(counter, 0)
                        self.assertEqual(p.read_bytes(site, len(replacement)), replacement)
                        self.assertEqual(p.read_bytes(address, len(code)), code)
                    if vendor:
                        flags = p.read_bytes(hooks.tables["vendor"], 40)
                        for slot in range(40):
                            self.assertEqual(flags[slot], 1 if slot in VENDOR_LOCATIONS else 4)
                    for change in reversed(hooks.patches):
                        p.write_bytes(change.address, change.original)
                    self.assertEqual(p.data, raw)
