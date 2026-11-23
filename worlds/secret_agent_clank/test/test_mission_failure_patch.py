import os
import json
import struct
import unittest
from pathlib import Path
from unittest.mock import Mock

from ..core import Core
from ..core.mission_failure import MissionFailure
from ..core.patches.level_build import FileMemory
from ..core.patches.module_arena import ModuleArena, reserve_arena
from ..core.patches.plan_compiler import compile_native_plan
from ..core.patches.snr2 import SNR2Module, resident_exports
from ..patcher.filenames import EXECUTABLE, LEVEL_FILES
from ..patcher.iso import ISOImage
from .mips_cpu import CPU
from .test_runtime import Memory


@unittest.skipUnless(os.environ.get("SAC_TEST_ISO"), "Set SAC_TEST_ISO to verify native failure paths")
class NativeMissionFailureTests(unittest.TestCase):
    def setUp(self):
        self.source = open(os.environ["SAC_TEST_ISO"], "rb")
        self.addCleanup(self.source.close)
        self.iso = ISOImage(self.source)
        self.imports = resident_exports(self.iso.read_file(EXECUTABLE))

    def prepare(self, module, base=0x400000):
        data, start = reserve_arena(self.iso.read_file(LEVEL_FILES[module]))
        loaded, symbols = SNR2Module(data).relocate(base, self.imports)
        memory = Memory()
        memory.data = bytearray(0x2000000)
        memory.write_int8 = lambda address, value: memory.batch_write_int8([(address, value)])
        memory.write_bytes(base, loaded)
        arena = ModuleArena(base, loaded, start)
        failure = MissionFailure(memory)
        patches = failure.prepare(symbols, arena.allocate)
        for patch in patches + arena.patches:
            memory.write_bytes(patch.address, patch.replacement)
        return memory, symbols, failure, patches

    def test_all_modules_accept_hooks_and_preserve_native_entries(self):
        for module in LEVEL_FILES:
            with self.subTest(module=module):
                memory, symbols, failure, patches = self.prepare(module)
                self.assertIsNotNone(failure.binding)
                flag = failure.binding[-1]
                for patch in patches:
                    if len(patch.original) != 8:
                        continue  # Call hooks are exercised separately.
                    memory.write_int32(flag, 0)
                    cpu = CPU(memory)
                    cpu.r[4], cpu.r[16], cpu.r[29] = 0x120000, 123, 0x700000
                    arena = patch.address == symbols.get("Arena_FailChallenge__FP4Moby")
                    cpu.run(patch.address, stop=CPU.STOP if arena else patch.address + 8)
                    self.assertEqual(failure.active(), patch.address != symbols.get(
                        "VehicleChallengeController_StartChallenge__FUiUi"))
                    self.assertEqual(cpu.r[31], CPU.STOP)
                    self.assertEqual(cpu.r[4], 0x120000)
                    if arena:
                        self.assertEqual(memory.read_int8(0x120045), 8)
                    else:
                        self.assertEqual(cpu.r[29], 0x700000 + int.from_bytes(
                            patch.original[:2], "little", signed=True))

    def test_gadgetbots_only_send_after_entire_squad_dies(self):
        for module in (4, 20, 28):
            for base in (0x400000, 0x508010):
                memory, symbols, failure, _ = self.prepare(module, base)
                update = symbols["GadgetBot_UpdateType__FP8MobyType"]
                memory.write_int32(0x11003C, 3)
                memory.write_int32(0x11000C, 0x120000)
                for bot in range(3):
                    memory.batch_write_int8([(0x120064 + bot * 0x80, 1)])
                for deaths, animation_done in ((0, True), (1, True), (2, True), (3, False), (3, True)):
                    with self.subTest(module=module, base=base, deaths=deaths, animation_done=animation_done):
                        memory.write_int32(failure.binding[-1], 0)
                        cpu = CPU(memory)
                        cpu.r[19], cpu.r[20] = 0x110000, 0x200000
                        def dead(c):
                            c.r[2] = int((c.r[4] - 0x120000) // 0x80 < deaths)
                        def anim(c):
                            c.r[2] = int(animation_done)
                        def fading(c):
                            c.r[2] = 0
                        stubs = {
                            symbols["GadgetBot_IsDead__FP4Moby"]: dead,
                            symbols["MOBY_CheckMobyAnimDone__FPC4Mobyb"]: anim,
                            symbols["FADEOVERLAY_Refresh__FUiUcUcUcb"]: lambda c: self.assertEqual(c.r[8], 0),
                            symbols["FADEOVERLAY_IsAtFinalUpAlpha__Fv"]: fading,
                        }
                        cpu.run(update + 0x104, stop=update + 0x1A4, stubs=stubs)
                        self.assertEqual(failure.active(), deaths == 3 and animation_done)

    def test_failure_hooks_compile_with_native_relocations(self):
        for module in (4, 5, 17, 18, 20, 28):
            with self.subTest(module=module):
                data, start = reserve_arena(self.iso.read_file(LEVEL_FILES[module]))
                def builder(base, loaded, symbols):
                    arena = ModuleArena(base, loaded, start)
                    failure = MissionFailure(FileMemory(base, loaded, module))
                    return failure.prepare(symbols, arena.allocate) + arena.patches
                compile_native_plan(data, self.imports, builder, arena_start=start)

    def test_vehicle_failure_branches_and_retry(self):
        memory, symbols, failure, _ = self.prepare(17)
        reset = symbols["VehicleSectionStarter_Reset__Fv"]
        start = symbols["VehicleChallengeController_StartChallenge__FUiUi"]
        for name, offset in (("VehicleChallengeController_ChallengeFinished__FUiUi", 0x44),
                             ("VehicleChallengeController_Update__FP4Mobyf", 0x138)):
            cpu = CPU(memory)
            cpu.r[29] = 0x200000
            cpu.run(start, stop=start + 8)
            self.assertFalse(failure.active())
            site = symbols[name] + offset
            cpu = CPU(memory)
            cpu.r[2], cpu.r[3], cpu.r[16] = 0x210000, 0x220000, 1
            cpu.run(site, stop=reset)
            self.assertTrue(failure.active())
            self.assertEqual(cpu.r[31], site + 8)

    def test_vehicle_success_does_not_latch_failure(self):
        memory, symbols, failure, _ = self.prepare(17)
        finish = symbols["VehicleChallengeController_ChallengeFinished__FUiUi"]
        # Run the retail decision with sufficient rings, and the other two
        # challenge types, up to its success path. None may set the latch.
        for high, low in ((0x24, 0x2C), (0x28, 0x30)):
            address = (memory.read_int32(finish + high) & 0xFFFF) << 16
            offset = memory.read_int32(finish + low) & 0xFFFF
            address += offset - 0x10000 if offset & 0x8000 else offset
            memory.write_int32(address, 10)
        for challenge in (0, 1, 2):
            cpu = CPU(memory)
            cpu.r[4], cpu.r[29] = challenge, 0x200000
            cpu.run(finish, stop=finish + 0x74)
            self.assertFalse(failure.active())

    @unittest.skipUnless(os.environ.get("SAC_TEST_BUILD"), "Set SAC_TEST_BUILD to audit compiled bindings")
    def test_compiled_failure_reaches_deathlink_once(self):
        root = Path(os.environ["SAC_TEST_BUILD"])
        build = json.loads((root / "data" / "sac-runtime.json").read_text())
        for module in LEVEL_FILES:
            with self.subTest(module=module):
                base = 0x328B00
                loaded, symbols = SNR2Module((root / f"module-{module}.rel").read_bytes()).relocate(
                    base, self.imports)
                memory = Memory()
                memory.data = bytearray(0x2000000)
                memory.write_bytes(base, loaded)
                core = Core(memory, permanent_build=build)
                core._strip_all_inventories = Mock()
                send = Mock()
                core.wire(send_location=Mock(), death_link_enabled=lambda: True, send_deathlink=send)
                core.native_runtime._bind(module, base)
                self.assertFalse(core.case.mission_failure.active())
                site = symbols["PLAYER_PlayerIsDeadRequestLevelRestart__FP6PLAYER"]
                CPU(memory).run(site, stop=site + 8)
                core.case.check_mission_failure()
                core.case.check_mission_failure()
                send.assert_called_once_with('failed a mission')

    @unittest.skipUnless(os.environ.get("SAC_TEST_BUILD"), "Set SAC_TEST_BUILD to audit compiled bindings")
    def test_compiled_ratchet_failure_at_full_health_sends_once(self):
        root = Path(os.environ["SAC_TEST_BUILD"])
        build = json.loads((root / "data" / "sac-runtime.json").read_text())
        for module in (3, 9, 14, 21, 25):
            with self.subTest(module=module):
                base = 0x328B00
                loaded, symbols = SNR2Module((root / f"module-{module}.rel").read_bytes()).relocate(
                    base, self.imports)
                memory = Memory()
                memory.data = bytearray(0x2000000)
                memory.write_int8 = lambda address, value: memory.batch_write_int8([(address, value)])
                memory.write_bytes(base, loaded)
                core = Core(memory, permanent_build=build)
                core._strip_all_inventories = Mock()
                send = Mock()
                core.wire(send_location=Mock(), death_link_enabled=lambda: True, send_deathlink=send)
                core.native_runtime._bind(module, base)
                core.case.is_ready = True
                player = core.case.active_player
                player.pointer_address, player.state_kind, player.state_offset = 0x110000, "Ratchet", 0xAB4
                memory.write_int32(0x110000, 0x120000)
                memory.write_bytes(0x120274, struct.pack('<2f', 10, 10))
                core.case.check_death()
                send.assert_not_called()
                cpu = CPU(memory)
                cpu.r[4] = 0x130000  # Arena controller, not the player.
                cpu.run(symbols["Arena_FailChallenge__FP4Moby"])
                self.assertEqual(memory.read_int8(0x130045), 8)
                self.assertEqual(player.health_sample(), (0x120000, 10))
                for _ in range(3):
                    core.case.check_death()
                send.assert_called_once_with('failed a mission')
                # A subsequent player-death callback is still the same failure.
                site = symbols["PLAYER_PlayerIsDeadRequestLevelRestart__FP6PLAYER"]
                CPU(memory).run(site, stop=site + 8)
                core.case.check_death()
                send.assert_called_once()
