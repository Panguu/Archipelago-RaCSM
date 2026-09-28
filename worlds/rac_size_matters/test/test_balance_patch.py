"""Retail regional fixtures and execution tests for the balance callbacks."""

import json
import struct
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from ..core import address_maps
from ..core.native_runtime import NativeRuntime
from ..core.patches import PatchOptions, balance_patch, item_toast
from ..core.patches.asm import packed
from ..core.patches.loader_gate import LoaderGate
from ..options import BalancePatch
from .bases import RACSizeMatterTestBase
from .test_native_patches import CPU, Memory as NativeMemory, plans


FIXTURES = json.loads((Path(__file__).parent / "fixtures/balance_patch.json").read_text())
GAMES = {"us": "SCUS-97615", "eu": "SCES-55019", "jp": "SCPS-15120"}
BASE = 0xC00000


class Memory(NativeMemory):
    def __init__(self, fixture):
        self.data = bytearray(0x2000000)
        self.writes = []
        self.fail_once = None
        self.game_id = GAMES[fixture["region"]]
        for offset, raw in fixture["segments"]:
            raw = bytes.fromhex(raw)
            self.data[BASE + offset:BASE + offset + len(raw)] = raw

    def get_game_id(self):
        return self.game_id


def prepare(name):
    fixture = FIXTURES[name]
    memory = Memory(fixture)
    plan = balance_patch.prepare(memory, planet=fixture["planet"], code_start=BASE,
                                 code=memory.read_bytes(BASE, 0x280000))
    return memory, plan


class BalancePatchTests(unittest.TestCase):
    def test_default_off(self):
        self.assertEqual(BalancePatch.default, 0)
        self.assertFalse(PatchOptions().balance_patch)

    def test_all_retail_regions_install_restore_and_reject_changed_signatures(self):
        for name in FIXTURES:
            with self.subTest(name=name):
                memory, plan = prepare(name)
                before = bytes(memory.data)
                self.assertFalse(memory.writes)
                plan.install()
                self.assertNotEqual(memory.data, before)
                plan._validate(True)
                plan.restore()
                self.assertEqual(memory.data, before)
                memory.data[plan.edits[-1].address] ^= 1
                memory.writes.clear()
                with self.assertRaises(RuntimeError):
                    plan.install()
                with self.assertRaises(RuntimeError):
                    balance_patch.prepare(memory, planet=FIXTURES[name]["planet"], code_start=BASE,
                                          code=memory.read_bytes(BASE, 0x280000))
                self.assertFalse(memory.writes)

    def test_wrong_game_and_partial_write_roll_back(self):
        memory, plan = prepare("jp_1")
        memory.game_id = "SCUS-97615"
        with self.assertRaises(RuntimeError):
            plan.install()
        self.assertFalse(memory.writes)
        memory.game_id = "SCPS-15120"
        before = bytes(memory.data)
        memory.fail_once = plan.edits[2].address
        with self.assertRaises(OSError):
            plan.install()
        self.assertEqual(memory.data, before)

    def test_boss_thresholds_frame_timer_and_return_to_normal(self):
        for region in GAMES:
            memory, plan = prepare(region + "_10")
            toast = SimpleNamespace(timer=0xB00000, message=0xB00004)
            callback = balance_patch.prepare_callback(memory, balance=plan, arena=0xB01000,
                                                       max_health=0, toast=toast)
            plan.install()
            callback.install()
            state = LoaderGate(memory, game_id=memory.game_id).STATE
            memory.write_int32(state, 6)
            for upper, expected_boss in ((0x43F9, False), (0x43FA, True),
                                         (0x45BB, True), (0x45BC, False)):
                memory.write_int32(plan.health, upper << 16)
                CPU(memory).run(callback.entry)
                for address, normal, boss in plan.boss:
                    self.assertEqual(memory.read_int32(address), boss if expected_boss else normal)
            memory.write_int32(callback.counter, 0)
            memory.write_int32(plan.health, struct.unpack("<I", struct.pack("<f", 1000))[0])
            memory.write_int32(state, 5)
            CPU(memory).run(callback.entry)
            self.assertEqual(memory.read_int32(callback.counter), 0)
            memory.write_int32(state, 6)
            for _ in range(44):
                CPU(memory).run(callback.entry)
            self.assertEqual(memory.read_int32(toast.timer), 0)
            # An AP receipt takes priority; the reminder waits for an empty toast.
            memory.write_int32(toast.timer, 10)
            CPU(memory).run(callback.entry)
            self.assertEqual(memory.read_int32(callback.counter), 45)
            self.assertEqual(memory.read_int32(toast.timer), 10)
            memory.write_int32(toast.timer, 0)
            CPU(memory).run(callback.entry)
            self.assertEqual(memory.read_int32(callback.counter), 46)
            self.assertEqual(memory.read_int32(toast.timer), 180)
            self.assertIn(b"ammo has been refilled", memory.read_bytes(toast.message, 40))
            plan._validate(True)
            callback._validate(True)

    def test_ryllus_discovers_relocated_door_and_waits_sixty_frames(self):
        for region in GAMES:
            memory, plan = prepare(region + "_2")
            actor, record, health = 0x680000, 0x670000, 0xB00000
            memory.write_bytes(actor + 0x30, balance_patch.DOOR_POSITION)
            memory.write_bytes(record, packed(actor, 0, 3, 0, actor, 0, 3, 0))
            callback = balance_patch.prepare_callback(memory, balance=plan, arena=0xB01000,
                                                       max_health=health, toast=None)
            callback.install()
            memory.write_int32(LoaderGate(memory, game_id=memory.game_id).STATE, 6)
            balance_patch.bind_doors(callback)
            memory.write_int32(health, 0x41200000)
            CPU(memory).run(callback.entry)
            self.assertEqual(memory.read_int32(callback.counter), 0)
            memory.write_int32(health, 0x40800000)
            for _ in range(59):
                CPU(memory).run(callback.entry)
            self.assertEqual(memory.read_int32(record + 8), 3)
            CPU(memory).run(callback.entry)
            self.assertEqual(memory.read_int32(record + 8), 0)
            self.assertEqual(memory.read_int32(record + 24), 0)

    def test_three_toast_callbacks_preserve_empty_branch_and_receipts(self):
        memory = NativeMemory()
        vendor, original, *_ = plans(memory)
        hooks = (0xB00000, 0xB00010, 0xB00020)
        toast = item_toast.prepare(memory, code_start=0xD00000,
                                   code=memory.read_bytes(0xD00000, 0x400000),
                                   small_box=memory.fixture["small_box"], starter=vendor.starter,
                                   frame_hook=hooks[0], status_hook=hooks[1], balance_hook=hooks[2])
        toast.install()
        draw = (int.from_bytes(original.edits[0].replacement[8:12], "little") & 0x3FFFFFF) << 2
        stubs = [draw, toast.font, toast.colour, toast.text, *hooks]
        cpu = CPU(memory)
        cpu.run(toast.edits[0].address, stubs=stubs)
        self.assertNotIn(toast.text, cpu.calls)
        self.assertTrue(all(hook in cpu.calls for hook in hooks))
        item_toast.show(toast, "Test receipt")
        CPU(memory).run(toast.edits[0].address, stubs=stubs)
        self.assertEqual(memory.read_int32(toast.timer), 179)

    def test_changing_option_requests_a_fresh_level(self):
        for enabled in (False, True):
            memory = NativeMemory()
            planet = SimpleNamespace(is_ready=True, starting_planet_id=None)
            runtime = NativeRuntime(memory, SimpleNamespace(planet=planet, native_plan=None),
                                    lambda _: None, lambda _: None,
                                    patch_options=PatchOptions(vendor=False, balance_patch=enabled))
            runtime.enabled = True
            runtime.module = 1
            runtime.starting_planet.service = lambda _: None
            runtime.gate.arm = lambda: None
            runtime.gate.held_module = lambda: None
            memory.write_int32(runtime.gate.STATE, 6)
            memory.write_int32(address_maps.NEW_PLANET_START_LOAD_ADDR, 0xFFFFFFFF)
            runtime.patch_options = replace(runtime.patch_options, balance_patch=not enabled)
            self.assertTrue(runtime.tick())
            self.assertEqual(memory.read_int32(address_maps.NEW_PLANET_START_LOAD_ADDR), 1)

    def test_flying_clank_level_without_ratchet_address_map(self):
        for region in GAMES:
            memory = Memory(FIXTURES[region + "_15"])
            planet = SimpleNamespace(is_ready=False)
            runtime = NativeRuntime(memory, SimpleNamespace(planet=planet, native_plan=None),
                                    lambda _: None, lambda _: None,
                                    patch_options=PatchOptions(balance_patch=True))
            runtime._prepare(15, BASE)
            self.assertTrue(runtime.balance.installed)
            self.assertEqual(runtime.module, 15)
            self.assertEqual(len(runtime.plans), 1)
            runtime.patch_options = replace(runtime.patch_options, balance_patch=False)
            fresh = Memory(FIXTURES[region + "_15"])
            memory.data[:] = fresh.data
            memory.writes.clear()
            runtime._prepare(15, BASE)
            self.assertIsNone(runtime.balance)
            self.assertEqual(runtime.module, 15)
            self.assertFalse(memory.writes)


class TestBalanceOptionOff(RACSizeMatterTestBase):
    def test_slot_data_defaults_off(self):
        self.assertIs(self.world.fill_slot_data()["balance_patch"], False)


class TestBalanceOptionOn(RACSizeMatterTestBase):
    options = {"balance_patch": True}

    def test_slot_data_enabled(self):
        self.assertIs(self.world.fill_slot_data()["balance_patch"], True)
