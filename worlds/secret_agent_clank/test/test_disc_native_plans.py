"""Opt-in verification against a user's clean ISO; no game data is bundled.

Set SAC_TEST_ISO to run. Plans are prepared in local memory only, never sent
to PCSX2 and never written to the ISO. This does not test native execution.
"""
import os
from pathlib import Path
import struct
import unittest

from ..core.native_runtime import CLANK_MODULES
from ..core.patches import Progression
from ..patcher.iso import ISOImage
from ..core.patches.snr2 import SNR2Module, resident_exports
from ..core.patches.module_compiler import ModuleEdit, compile_module
from ..core.patches.plan_compiler import compile_native_plan
from ..patcher.filenames import EXECUTABLE, LEVEL_FILES, FRONTEND
from .test_runtime import Memory
from ..core.patches.frontend_build import compile_frontend
from ..core.patches.level_build import compile_level, prepare_level
from ..core.patches.module_arena import reserve_arena
from ..core.patches.iso_startup_barrier import patch_resident_loader


@unittest.skipUnless(os.environ.get("SAC_TEST_ISO"), "Set SAC_TEST_ISO to audit the clean disc")
class TestDiscNativePlans(unittest.TestCase):
    def test_compile_permanent_frontend(self):
        with Path(os.environ["SAC_TEST_ISO"]).open("rb") as source:
            iso = ISOImage(source)
            data = iso.read_file(FRONTEND)
            result = compile_frontend(data, resident_exports(iso.read_file(EXECUTABLE)))
            self.assertGreater(len(result), len(data))

    @unittest.skipUnless(os.environ.get("SAC_TEST_COMPILE"), "Set SAC_TEST_COMPILE for permanent level compilation")
    def test_compile_permanent_level_plans(self):
        with Path(os.environ["SAC_TEST_ISO"]).open("rb") as source:
            iso = ISOImage(source)
            executable = iso.read_file(EXECUTABLE)
            self.assertNotEqual(patch_resident_loader(executable), executable)
            imports = resident_exports(executable)
            for module, path in LEVEL_FILES.items():
                vendor = module in CLANK_MODULES or module in (3, 9, 14, 21, 25)
                with self.subTest(module=module):
                    data = iso.read_file(path)
                    compiled = compile_level(data, imports, module, vendor)
                    self.assertGreater(len(compiled), len(data))
                    print(f"Compiled permanent module {module}: {len(data)} -> {len(compiled)}", flush=True)

    @unittest.skipUnless(os.environ.get("SAC_TEST_COMPILE"), "Set SAC_TEST_COMPILE for the full native compiler audit")
    def test_compile_complete_native_plans(self):
        with Path(os.environ["SAC_TEST_ISO"]).open("rb") as source:
            iso = ISOImage(source)
            imports = resident_exports(iso.read_file(EXECUTABLE))
            for module, path in LEVEL_FILES.items():
                data = iso.read_file(path)
                vendors = (False, True) if module in (4, 11) else (
                    module in CLANK_MODULES or module in (3, 9, 14, 21, 25),)
                for vendor in vendors:
                    with self.subTest(module=module, vendor=vendor):
                        def build(base, loaded, symbols):
                            memory = Memory()
                            memory.data = bytearray(0x2000000)
                            memory.data[base:base + len(loaded)] = loaded
                            struct.pack_into("<I", memory.data, 0x206328, module)
                            return self._prepare(memory, symbols, module, vendor, 2, 1, 3)
                        compiled = compile_native_plan(data, imports, build)
                        self.assertGreater(len(compiled), len(data))
                        print(f"Compiled module {module}, vendor={vendor}: {len(data)} -> {len(compiled)} bytes", flush=True)

    def test_compiled_level_edits_relocate_like_runtime_edits(self):
        with Path(os.environ["SAC_TEST_ISO"]).open("rb") as source:
            iso = ISOImage(source)
            imports = resident_exports(iso.read_file(EXECUTABLE))
            for module, path in LEVEL_FILES.items():
                with self.subTest(module=module):
                    data = iso.read_file(path)
                    rel = SNR2Module(data)
                    base = 0x328B00
                    loaded, symbols = rel.relocate(base, imports)
                    memory = Memory()
                    memory.data = bytearray(0x2000000)
                    memory.data[base:base + len(loaded)] = loaded
                    plan = Progression(memory).replay_xp_patches(symbols)
                    if not plan:
                        continue
                    edits = tuple(ModuleEdit(p.address - base,
                                             data[p.address - base:p.address - base + len(p.original)],
                                             p.replacement) for p in plan)
                    compiled = SNR2Module(compile_module(data, edits))
                    for check_base in (0x328B00, 0x908000):
                        original, _ = rel.relocate(check_base, imports)
                        patched, _ = compiled.relocate(check_base, imports)
                        expected = bytearray(original)
                        for edit in edits:
                            expected[edit.offset:edit.offset + len(edit.replacement)] = edit.replacement
                        # Headers and relocation tables intentionally differ.
                        code_end = min(struct.unpack_from("<I", data, offset)[0] for offset in (4, 12, 52))
                        self.assertEqual(patched[128:code_end], expected[128:code_end])

    def test_relocations_match_unmodified_ram_captures(self):
        root = Path(__file__).parents[1] / ".research"
        captures = [root / name for name in (
            "gadgetbot_forAmondo.p2s.ram",
            "gadgetbot_SCUS-97623 (293ABC84).10.p2s.ram",
            "SAC.p2s.ram", "sac_finished.p2s.ram") if (root / name).exists()]
        if not captures:
            self.skipTest("Local unmodified RAM captures not present")
        with Path(os.environ["SAC_TEST_ISO"]).open("rb") as source:
            iso = ISOImage(source)
            imports = resident_exports(iso.read_file(EXECUTABLE))
            for capture in captures:
                with self.subTest(capture=capture.name):
                    ram = capture.read_bytes()
                    module = struct.unpack_from("<I", ram, 0x206328)[0]
                    base = ram.find(b"SNR2", 0x200000, 0x1000000)
                    self.assertGreater(base, 0)
                    rel = SNR2Module(iso.read_file(LEVEL_FILES[module]))
                    loaded, _ = rel.relocate(base, imports)
                    for relocation in rel.local_relocations + rel.import_relocations:
                        offset = relocation.offset
                        self.assertEqual(loaded[offset:offset + 4], ram[base + offset:base + offset + 4],
                                         f"Relocation mismatch at {offset:#x}")

    def test_all_level_plans(self):
        with Path(os.environ["SAC_TEST_ISO"]).open("rb") as source:
            iso = ISOImage(source)
            imports = resident_exports(iso.read_file(EXECUTABLE))
            for module, path in LEVEL_FILES.items():
                data, start = reserve_arena(iso.read_file(path))
                rel = SNR2Module(data)
                vendors = (False, True) if module in (4, 11) else (
                    module in CLANK_MODULES or module in (3, 9, 14, 21, 25),)
                for base in (0x800000, 0x908000):
                    loaded, symbols = rel.relocate(base, imports)
                    for vendor in vendors:
                        with self.subTest(module=module, base=hex(base), vendor=vendor):
                            patches, _ = prepare_level(base, loaded, symbols, module, vendor, start)
                            spans = sorted((p.address, p.address + len(p.replacement)) for p in patches)
                            self.assertTrue(all(b <= c for (_, b), (c, _) in zip(spans, spans[1:])),
                                            "Patch allocations overlap")
                            for patch in patches:
                                offset = patch.address - base
                                self.assertEqual(loaded[offset:offset + len(patch.original)], patch.original)
                                self.assertEqual(len(patch.original), len(patch.replacement))
