from .compiled_memory import load_plan, ram_arena
"""Full hook installation regressions against local read-only research captures."""
import unittest
from itertools import product
from pathlib import Path

from ..core import (
    ItemNotifications,
    MissionFailure,
    NativeRuntime,
    RuntimeSymbols,
    StealthState,
    is_main_menu,
)
from ..constants import (
    PICKUP_LOCATIONS,
    STEALTH_CASES,
    STEALTH_MAX_PER_CASE,
    VENDOR_LOCATIONS,
    WEAPON_MODS,
    NativeFunctions,
)
from ..core.patches import (
    MARKER,
    ConnectionWarning,
    GainStorage,
    LocationHooks,
    MissionTravel,
    Progression,
    TitanOffers,
    TitanVendor,
    VendorCatalog,
    VendorPresentation,
    WeaponMods,
    WrenchProgression,
)
from .test_runtime import Memory


class CaptureMemory(Memory):
    def write_bytes(self, address, data):
        self.data[address:address + len(data)] = data

    def write_int8(self, address, value):
        self.batch_write_int8([(address, value)])


class NativeCapturePlansTests(unittest.TestCase):
    def test_repeat_xp_patches_match_captured_ratchet_and_clank_code(self):
        captures = [Path(__file__).parents[1] / ".research" / name for name in
                    ("SAC.p2s.ram", "prison_skin_live.bin", "sac_finished.p2s.ram")]
        if not any(capture.exists() for capture in captures):
            self.skipTest("Local research RAM captures not present")
        for capture in captures:
            if not capture.exists():
                continue
            with self.subTest(capture=capture.name):
                p = CaptureMemory()
                p.data[:] = capture.read_bytes()
                before = bytes(p.data)
                symbols = RuntimeSymbols.parse(p.data[:0x1000000], 0)
                edits = Progression(p).replay_xp_patches(symbols)
                self.assertEqual(len(edits), 2)
                self.assertEqual(bytes(p.data), before)
                for edit in edits:
                    self.assertEqual(p.read_bytes(edit.address, 4), edit.original)
                    p.write_bytes(edit.address, edit.replacement)
                    self.assertEqual(p.read_int32(edit.address), 0x3C013F80)
                for edit in reversed(edits):
                    p.write_bytes(edit.address, edit.original)
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
                continue
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
                    arena = ram_arena(p)
                    hooks = LocationHooks(p)
                    hooks.prepare(symbols, pickup_locations=PICKUP_LOCATIONS,
                                  vendor_locations=VENDOR_LOCATIONS if vendor else {},
                                  entitlements={}, vendor_enabled=vendor)
                    hooks.patches.extend(WrenchProgression(p).prepare(symbols, module, arena))
                    hooks.patches.extend(MissionTravel(p).prepare(symbols, module=module))
                    mods = WeaponMods(p)
                    mods.configure({"operatives": {"Ratchet": 1, "Clank": 1}, "ng_plus": ng, "weapon_mod_ids": [mod.mod_id for mod in WEAPON_MODS]})
                    hooks.patches.extend(mods.prepare(symbols, hooks, module, set(), vendor))
                    progression = Progression(p)
                    progression.mission_failure = MissionFailure(p)
                    progression.configure({"ng_plus": ng, "progressive_weapons": progressive,
                        "weapon_xp_multiplier": multiplier, "health_xp_multiplier": multiplier, "bolt_multiplier": multiplier})
                    progression.stealth = StealthState(p)
                    progression.stealth.configure(dict.fromkeys(STEALTH_CASES, STEALTH_MAX_PER_CASE))
                    progression.stealth.load({})
                    if ng and vendor:
                        hooks.patches.extend(TitanVendor(p).prepare(symbols, hooks, set()))
                    elif vendor:
                        hooks.patches.extend(TitanOffers(p).prepare(symbols))
                    if vendor:
                        hooks.patches.extend(VendorCatalog(p).prepare(symbols, hooks))
                    if vendor:
                        hooks.patches.extend(VendorPresentation(p).prepare(symbols, hooks))
                    hooks.patches.extend(ConnectionWarning(p).prepare(symbols, hooks))
                    hooks.patches.extend(progression.prepare(symbols, module, arena, vendor_enabled=vendor))
                    hooks.patches.extend(arena.patches)
                    if module != 31:
                        patched = {patch.address for patch in progression.patches}
                        for name in (NativeFunctions.GLOBALVARS_ADD_EXPERIENCE,
                                     NativeFunctions.GLOBALVARS_ADD_CLANK_EXPERIENCE):
                            if symbols.get(name) is not None:
                                self.assertIn(symbols[name], patched)
                        xp = symbols[NativeFunctions.GADGET_GETS_XP]
                        self.assertIn(xp, patched)
                        self.assertIn(xp + 0x104, patched)
                    spans = sorted((x.address, x.address + len(x.replacement)) for x in hooks.patches)
                    self.assertTrue(all(b <= c for (a, b), (c, d) in zip(spans, spans[1:])))
                    self.assertEqual(p.data, raw, "Planning must not write RAM")
                    load_plan(hooks)
                    self.assertTrue(ItemNotifications(p).bind(symbols), "Receipt HUD must bind after install")
                    if not vendor:
                        for name, size in ((NativeFunctions.SCRNVENDOR_PROCESS_PURCHASE, 0x350),
                                           (NativeFunctions.GADGET_IS_SELLABLE, 0x30)):
                            address = symbols.get(name)
                            if address is not None:
                                self.assertEqual(p.read_bytes(address, size), raw[address:address + size])
                        self.assertNotIn("vendor", hooks.tables)
                    if progression.stealth.binding is not None:
                        _, counter, site, replacement, address, code = progression.stealth.binding
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
