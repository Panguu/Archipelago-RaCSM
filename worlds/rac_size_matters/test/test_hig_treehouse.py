import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from ..constants import Rac5Locations, Rac5Planets, Rac5ShrinkRayGrindrail
from ..core.native_runtime import NativeRuntime
from ..core.patches import PatchOptions, ship_menu, treehouse_turret, treehouse_grindrail
from ..locations import ALL_LOCATIONS
from ..locations.hig_treehouse import CHALLENGE_NAMES
from ..locations.observation import LocationObservation
from ..options import RACSizeMatterOptions
from ..universal_tracker import setup_options_from_slot_data
from .bases import RACSizeMatterTestBase
from .test_native_patches import CPU, Memory


class TreehouseOptionsTests(unittest.TestCase):
    def test_new_ids_follow_existing_catalog(self):
        treehouse = {*CHALLENGE_NAMES, Rac5Locations.HIG_TREEHOUSE_TURRET, Rac5ShrinkRayGrindrail.HIG_TREEHOUSE_GRINDRAIL}
        self.assertEqual({ALL_LOCATIONS[name].code for name in treehouse}, set(range(77700375, 77700381)))
        self.assertTrue(all(location.code < 77700375 for name, location in ALL_LOCATIONS.items()
                            if name not in treehouse))

    def test_tracker_names_match_generated_locations(self):
        tracker = json.loads((Path(__file__).parent.parent / "tracker/locations.json").read_text())
        treehouse = next(child for child in tracker[0]["children"] if child["name"] == "11")
        self.assertEqual({section["name"] for section in treehouse["sections"]},
                         {*CHALLENGE_NAMES, Rac5Locations.HIG_TREEHOUSE_TURRET, Rac5ShrinkRayGrindrail.HIG_TREEHOUSE_GRINDRAIL})

    def test_option_combinations(self):
        for enabled in (0, 1):
            for clank in (0, 1, 2):
                for gadgetbot in (False, True):
                    with self.subTest(enabled=enabled, clank=clank, gadgetbot=gadgetbot):
                        values = dict(enable_hig_treehouse=enabled, clank_challenges=clank,
                                      clank_challenge_groups={"Gadgetbot"} if gadgetbot else set())
                        options = RACSizeMatterOptions(**{
                            name: cls.from_any(values.get(name, cls.default))
                            for name, cls in RACSizeMatterOptions.type_hints.items()
                        })
                        for name in CHALLENGE_NAMES:
                            self.assertEqual(ALL_LOCATIONS[name].available(options),
                                             bool(enabled and clank and gadgetbot))
                        self.assertEqual(ALL_LOCATIONS[Rac5Locations.HIG_TREEHOUSE_TURRET].available(options),
                                         bool(enabled))

    def test_counters_are_independent(self):
        for name in CHALLENGE_NAMES:
            definition = ALL_LOCATIONS[name]
            address = definition.completed.key
            observation = LocationObservation(challenges={address: 1}, previous={address: 0})
            self.assertEqual([n for n in CHALLENGE_NAMES if ALL_LOCATIONS[n].completed(observation)], [name])
            self.assertFalse(definition.completed(LocationObservation(challenges={address: 1}, previous={address: 1})))

    def test_grindrail_option_combinations(self):
        for enabled in (0, 1):
            for shrink in (0, 1, 2):
                values = dict(enable_hig_treehouse=enabled, shrink_ray_options=shrink,
                              clank_challenge_groups=set())
                options = RACSizeMatterOptions(**{
                    name: cls.from_any(values.get(name, cls.default))
                    for name, cls in RACSizeMatterOptions.type_hints.items()
                })
                self.assertEqual(ALL_LOCATIONS[Rac5ShrinkRayGrindrail.HIG_TREEHOUSE_GRINDRAIL].available(options),
                                 bool(enabled and shrink == 1))


class TestTreehouseEnabled(RACSizeMatterTestBase):
    options = {"enable_hig_treehouse": 1}

    def test_locations_and_slot_data(self):
        region = self.multiworld.get_region(Rac5Planets.HIG_TREEHOUSE, self.player)
        self.assertEqual({loc.name for loc in region.locations},
                         {*CHALLENGE_NAMES, Rac5Locations.HIG_TREEHOUSE_TURRET, Rac5ShrinkRayGrindrail.HIG_TREEHOUSE_GRINDRAIL})
        self.assertTrue(region.can_reach(self.multiworld.state))
        self.assertTrue(self.world.fill_slot_data()["enable_hig_treehouse"])

    def test_tracker_restores_treehouse_option(self):
        slot = self.world.fill_slot_data()
        self.world.options.enable_hig_treehouse.value = 0
        self.multiworld.re_gen_passthrough = {self.world.game: slot}
        setup_options_from_slot_data(self.world)
        self.assertTrue(self.world.options.enable_hig_treehouse)

    def test_grindrail_requires_shrink_ray(self):
        from ..constants import Rac5Gadgets
        location = self.multiworld.get_location(Rac5ShrinkRayGrindrail.HIG_TREEHOUSE_GRINDRAIL, self.player)
        self.assertFalse(location.can_reach(self.multiworld.state))
        self.collect_by_name(Rac5Gadgets.SHRINK_RAY)
        self.assertTrue(location.can_reach(self.multiworld.state))


class TestTreehouseWithoutGadgetbots(RACSizeMatterTestBase):
    options = {"enable_hig_treehouse": 1, "clank_challenge_groups": {"Demolition Derby"}}

    def test_turret_and_destination_remain(self):
        region = self.multiworld.get_region(Rac5Planets.HIG_TREEHOUSE, self.player)
        self.assertEqual({loc.name for loc in region.locations}, {Rac5Locations.HIG_TREEHOUSE_TURRET, Rac5ShrinkRayGrindrail.HIG_TREEHOUSE_GRINDRAIL})
        self.assertTrue(region.can_reach(self.multiworld.state))


class TestTreehouseDisabled(RACSizeMatterTestBase):
    options = {"enable_hig_treehouse": 0, "clank_challenges": 2}

    def test_destination_remains_without_checks(self):
        region = self.multiworld.get_region(Rac5Planets.HIG_TREEHOUSE, self.player)
        self.assertEqual(list(region.locations), [])
        self.assertTrue(region.can_reach(self.multiworld.state))


class TreehousePickupTests(unittest.TestCase):
    def prepare(self):
        memory = Memory()
        fixture = json.loads((Path(__file__).parent / "fixtures/treehouse_turret_us.json").read_text())
        for address, data in fixture["segments"]:
            memory.data[address:address + len(data) // 2] = bytes.fromhex(data)
        plan = treehouse_turret.prepare(memory, code_start=0xD00000,
                                       code=memory.read_bytes(0xD00000, 0x400000))
        return memory, plan

    def test_runtime_installs_only_checks_in_the_seed(self):
        for enabled in (False, True):
            with self.subTest(enabled=enabled):
                memory = Memory()
                memory.data[0xD00000:0x1100000] = bytes(0x400000)
                fixture = json.loads((Path(__file__).parent / "fixtures/treehouse_turret_us.json").read_text())
                grind = json.loads((Path(__file__).parent / "fixtures/treehouse_grindrail_us.json").read_text())
                preview = json.loads((Path(__file__).parent / "fixtures/ship_preview_us.json").read_text())["treehouse"]
                for address, data in [*fixture["segments"], *fixture["menu_segments"], *preview["segments"], *grind["segments"]]:
                    memory.data[address:address + len(data) // 2] = bytes.fromhex(data)
                runtime = NativeRuntime.__new__(NativeRuntime)
                runtime.pine = memory
                runtime.patch_options = PatchOptions()
                runtime.vendor = SimpleNamespace(planet=SimpleNamespace())
                runtime.checked = {Rac5Locations.HIG_TREEHOUSE_TURRET, Rac5ShrinkRayGrindrail.HIG_TREEHOUSE_GRINDRAIL}
                runtime.allowed_locations = runtime.checked if enabled else set()
                runtime._prepare(24, 0xD00000)
                self.assertEqual(runtime.module, 24)
                self.assertTrue(all(plan.installed for plan in runtime.plans))
                self.assertEqual(runtime.treehouse_pickup is not None, enabled)
                self.assertEqual(runtime.treehouse_grindrail is not None, enabled)
                if enabled:
                    self.assertEqual(memory.read_int8(runtime.treehouse_pickup.journals[0][0]), 2)
                    self.assertEqual(memory.read_int8(runtime.treehouse_grindrail.journals[0][0]), 2)

    def test_treehouse_menu_uses_native_treehouse_title(self):
        memory, _ = self.prepare()
        memory.data[0xD00000:0x1100000] = bytes(0x400000)
        fixture = json.loads((Path(__file__).parent / "fixtures/treehouse_turret_us.json").read_text())
        preview = json.loads((Path(__file__).parent / "fixtures/ship_preview_us.json").read_text())["treehouse"]
        for address, data in [*fixture["menu_segments"], *preview["segments"], fixture["title_segment"], fixture["title_table"]]:
            memory.data[address:address + len(data) // 2] = bytes.fromhex(data)
        plan = ship_menu.prepare(memory, code_start=0xD00000, code=memory.read_bytes(0xD00000, 0x400000))
        loop = plan.edits[0].address
        call = lambda address: (memory.read_int32(address) & 0x3FFFFFF) << 2
        unlock, group, name, add = [call(loop + offset) for offset in (4, 44, 56, 96)]
        localize = call(name + 0x64)
        plan.install()
        cpu = CPU(memory)
        cpu.r[17], cpu.r[18], cpu.r[19], cpu.r[20] = 1, 0xFFFFFFFF, 0x1800000, 1
        rows, title_ids = [], []

        def translate(c):
            title_ids.append(c.r[4])
            c.r[2] = 0x1900000

        cpu.run(loop, stop=loop + 120, stubs={
            unlock: lambda c: c.r.__setitem__(2, 0), group: lambda c: None,
            localize: translate, add: lambda c: rows.append(c.r[6]),
        })
        self.assertEqual(rows, [24])
        self.assertEqual(title_ids, [0xC5])

    def test_pickup_records_and_reports_once(self):
        memory, plan = self.prepare()
        plan.install()
        journal = plan.journals[0][0]
        self.assertEqual(memory.read_int8(journal), 1)
        entry = plan.edits[0].address
        CPU(memory).run(entry, stop=entry + 12)
        self.assertEqual(memory.read_int8(journal), 2)
        runtime = NativeRuntime.__new__(NativeRuntime)
        runtime.pine, runtime.treehouse_pickup = memory, plan
        runtime.balance_callback = runtime.connection_warning = runtime.presentation = None
        runtime.pickup = runtime.armour = runtime.toast = None
        runtime.vendor = SimpleNamespace(planet=SimpleNamespace(is_ready=False), native_plan=None)
        runtime.checked, runtime.allowed_locations = set(), {Rac5Locations.HIG_TREEHOUSE_TURRET}
        runtime.treehouse_grindrail = None
        runtime.send_location = Mock()
        runtime._poll()
        runtime._poll()
        runtime.send_location.assert_called_once_with(Rac5Locations.HIG_TREEHOUSE_TURRET)
        plan.restore()
        self.assertEqual(memory.read_int8(journal), 0)

    def test_changed_signature_rejected(self):
        memory, plan = self.prepare()
        memory.write_int32(plan.edits[0].address, 0)
        memory.writes.clear()
        with self.assertRaises(RuntimeError):
            treehouse_turret.prepare(memory, code_start=0xD00000,
                                     code=memory.read_bytes(0xD00000, 0x400000))
        self.assertEqual(memory.writes, [])


class TreehouseGrindrailTests(unittest.TestCase):
    def prepare(self, checked=False):
        memory = Memory()
        fixture = json.loads((Path(__file__).parent / "fixtures/treehouse_grindrail_us.json").read_text())
        for address, raw in fixture["segments"]:
            memory.data[address:address + len(raw) // 2] = bytes.fromhex(raw)
        plan = treehouse_grindrail.prepare(memory, code_start=0xD00000,
                                          code=memory.read_bytes(0xD00000, 0x400000), checked=checked)
        return memory, plan

    def test_completion_isolated_from_kalidon_and_reported_once(self):
        memory, plan = self.prepare()
        journal = plan.journals[0][0]
        memory.write_int32(0x1F4B40E, 0x12340001)  # Kalidon already complete.
        plan.install()
        cpu = CPU(memory)
        cpu.r[17] = 0x1800000
        cpu.run(plan.edits[0].address, stop=plan.edits[0].address + 16)
        self.assertEqual(cpu.r[2], 0)  # Treehouse remains locked.
        cpu.run(plan.edits[1].address, stop=plan.edits[1].address + 12)
        self.assertEqual(memory.read_int8(journal), 2)
        self.assertEqual(memory.read_int32(0x1F4B40E), 0x12340001)
        cpu.run(plan.edits[0].address, stop=plan.edits[0].address + 16)
        self.assertEqual(cpu.r[2], 1)
        runtime = NativeRuntime.__new__(NativeRuntime)
        runtime.pine, runtime.treehouse_grindrail = memory, plan
        runtime.treehouse_pickup = runtime.balance_callback = runtime.connection_warning = None
        runtime.presentation = runtime.pickup = runtime.armour = runtime.toast = None
        runtime.vendor = SimpleNamespace(planet=SimpleNamespace(is_ready=False), native_plan=None)
        name = Rac5ShrinkRayGrindrail.HIG_TREEHOUSE_GRINDRAIL
        runtime.checked, runtime.allowed_locations = set(), {name}
        runtime.send_location = Mock()
        runtime._poll()
        runtime._poll()
        runtime.send_location.assert_called_once_with(name)
        plan.restore()
        self.assertEqual(memory.read_int8(journal), 0)

    def test_checked_state_restored_and_signature_guarded(self):
        memory, plan = self.prepare(checked=True)
        plan.install()
        self.assertEqual(memory.read_int8(plan.journals[0][0]), 2)
        plan.restore()
        memory.write_int32(plan.edits[1].address, 0)
        memory.writes.clear()
        with self.assertRaises(RuntimeError):
            treehouse_grindrail.prepare(memory, code_start=0xD00000,
                                       code=memory.read_bytes(0xD00000, 0x400000))
        self.assertEqual(memory.writes, [])
