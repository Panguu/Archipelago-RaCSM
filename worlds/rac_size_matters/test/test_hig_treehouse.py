import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ..constants import Rac5Infobots, Rac5Locations, Rac5Planets, Rac5ShrinkRayGrindrail
from ..core.location_checks import LocationChecks
from ..core.native_runtime import NativeRuntime
from ..core.patches import PatchOptions, ship_menu, treehouse_grindrail
from ..locations import ALL_LOCATIONS
from ..locations.hig_treehouse import CHALLENGE_NAMES
from ..locations.observation import LocationObservation
from ..locations.shared import required_skill_points
from ..options import RACSizeMatterOptions
from ..universal_tracker import setup_options_from_slot_data
from .bases import RACSizeMatterTestBase
from .test_native_patches import CPU, Memory


class TreehouseOptionsTests(unittest.TestCase):
    def test_new_ids_follow_existing_catalog(self):
        treehouse = {*CHALLENGE_NAMES, Rac5ShrinkRayGrindrail.HIG_TREEHOUSE_GRINDRAIL,
                     Rac5Locations.HIG_TREEHOUSE_ALL_SKILL_POINTS}
        self.assertEqual({ALL_LOCATIONS[name].code for name in treehouse}, set(range(77700375, 77700382)) - {77700379})
        self.assertTrue(all(location.code < 77700375 for name, location in ALL_LOCATIONS.items()
                            if name not in treehouse))

    def test_tracker_names_match_generated_locations(self):
        tracker = json.loads((Path(__file__).parent.parent / "tracker/locations.json").read_text())
        treehouse = next(child for child in tracker[0]["children"] if child["name"] == "11")
        self.assertEqual({section["name"] for section in treehouse["sections"]},
                         {*CHALLENGE_NAMES, Rac5ShrinkRayGrindrail.HIG_TREEHOUSE_GRINDRAIL,
                          Rac5Locations.HIG_TREEHOUSE_ALL_SKILL_POINTS})

    def test_all_skill_points_option_combinations(self):
        for enabled in (0, 1):
            for skill_points in (0, 1, 2):
                with self.subTest(enabled=enabled, skill_points=skill_points):
                    values = dict(enable_hig_treehouse=enabled, skill_points=skill_points)
                    options = RACSizeMatterOptions(**{
                        name: cls.from_any(values.get(name, cls.default))
                        for name, cls in RACSizeMatterOptions.type_hints.items()
                    })
                    self.assertEqual(ALL_LOCATIONS[Rac5Locations.HIG_TREEHOUSE_ALL_SKILL_POINTS].available(options),
                                     bool(enabled and skill_points))

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
                         {*CHALLENGE_NAMES, Rac5ShrinkRayGrindrail.HIG_TREEHOUSE_GRINDRAIL})
        self.assertFalse(region.can_reach(self.multiworld.state))
        self.collect_by_name(Rac5Infobots.HIG_TREEHOUSE)
        self.assertTrue(region.can_reach(self.multiworld.state))
        self.assertTrue(self.world.fill_slot_data()["enable_hig_treehouse"])

    def test_infobot_in_pool_once(self):
        self.assertEqual([item.name for item in self.multiworld.itempool
                          if item.name == Rac5Infobots.HIG_TREEHOUSE], [Rac5Infobots.HIG_TREEHOUSE])

    def test_tracker_restores_treehouse_option(self):
        slot = self.world.fill_slot_data()
        self.world.options.enable_hig_treehouse.value = 0
        self.multiworld.re_gen_passthrough = {self.world.game: slot}
        setup_options_from_slot_data(self.world)
        self.assertTrue(self.world.options.enable_hig_treehouse)

    def test_grindrail_requires_shrink_ray(self):
        from ..constants import Rac5Gadgets
        location = self.multiworld.get_location(Rac5ShrinkRayGrindrail.HIG_TREEHOUSE_GRINDRAIL, self.player)
        self.collect_by_name(Rac5Infobots.HIG_TREEHOUSE)
        self.assertFalse(location.can_reach(self.multiworld.state))
        self.collect_by_name(Rac5Gadgets.SHRINK_RAY)
        self.assertTrue(location.can_reach(self.multiworld.state))


class TestTreehouseAllSkillPointsEasy(RACSizeMatterTestBase):
    options = {"enable_hig_treehouse": 1, "skill_points": 1, "enable_clank_challenge_skill_points": 1,
               "enable_skyboard_challenge_skill_points": 1}

    def test_requires_only_easy_skill_points(self):
        required = required_skill_points(self.world.options)
        self.assertTrue(required)
        self.assertTrue(all("easy_skill_point" in ALL_LOCATIONS[name].categories for name in required))
        self.assertEqual(set(required), {location.name for location in self.multiworld.get_locations(self.player)
                                         if location.name in ALL_LOCATIONS
                                         and "easy_skill_point" in ALL_LOCATIONS[location.name].categories})

    def test_reachable_only_once_every_skill_point_is(self):
        location = self.multiworld.get_location(Rac5Locations.HIG_TREEHOUSE_ALL_SKILL_POINTS, self.player)
        state = self.multiworld.get_all_state()
        self.assertTrue(location.can_reach(state))
        self.assertEqual(location.can_reach(self.multiworld.state), all(
            self.multiworld.get_location(name, self.player).can_reach(self.multiworld.state)
            for name in required_skill_points(self.world.options)
        ))


class TestTreehouseAllSkillPointsHard(RACSizeMatterTestBase):
    options = {"enable_hig_treehouse": 1, "skill_points": 2}

    def test_requires_easy_and_hard_skill_points(self):
        required = set(required_skill_points(self.world.options))
        categories = set().union(*(ALL_LOCATIONS[name].categories for name in required))
        self.assertIn("easy_skill_point", categories)
        self.assertIn("hard_skill_point", categories)
        self.assertEqual(required, {location.name for location in self.multiworld.get_locations(self.player)
                                    if location.name in ALL_LOCATIONS and ALL_LOCATIONS[location.name].categories
                                    & {"easy_skill_point", "hard_skill_point"}})


class AllSkillPointsClientTests(unittest.TestCase):
    def check(self, allowed, completed):
        sent = []
        core = SimpleNamespace(native=SimpleNamespace(allowed_locations=allowed),
                               skill_points=SimpleNamespace(completed=completed), send_location=sent.append)
        LocationChecks(core).all_skill_points()
        return sent

    def test_waits_for_every_skill_point_in_the_seed(self):
        easy = {name for name, location in ALL_LOCATIONS.items() if "easy_skill_point" in location.categories}
        hard = {name for name, location in ALL_LOCATIONS.items() if "hard_skill_point" in location.categories}
        name = Rac5Locations.HIG_TREEHOUSE_ALL_SKILL_POINTS
        self.assertEqual(self.check({name, *easy}, set(easy)), [name])
        self.assertEqual(self.check({name, *easy}, set(easy) - {next(iter(easy))}), [])
        self.assertEqual(self.check({name, *easy, *hard}, set(easy)), [])
        self.assertEqual(self.check({name, *easy, *hard}, easy | hard), [name])
        self.assertEqual(self.check(set(easy), set(easy)), [])
        self.assertEqual(self.check(None, set(easy)), [])


class TestTreehouseWithoutGadgetbots(RACSizeMatterTestBase):
    options = {"enable_hig_treehouse": 1, "clank_challenge_groups": {"Demolition Derby"}}

    def test_grindrail_and_destination_remain(self):
        region = self.multiworld.get_region(Rac5Planets.HIG_TREEHOUSE, self.player)
        self.assertEqual({loc.name for loc in region.locations}, {Rac5ShrinkRayGrindrail.HIG_TREEHOUSE_GRINDRAIL})
        self.collect_by_name(Rac5Infobots.HIG_TREEHOUSE)
        self.assertTrue(region.can_reach(self.multiworld.state))


class TestTreehouseDisabled(RACSizeMatterTestBase):
    options = {"enable_hig_treehouse": 0, "clank_challenges": 2}

    def test_destination_remains_without_checks(self):
        region = self.multiworld.get_region(Rac5Planets.HIG_TREEHOUSE, self.player)
        self.assertEqual(list(region.locations), [])
        self.assertTrue(region.can_reach(self.multiworld.state))
        self.assertNotIn(Rac5Infobots.HIG_TREEHOUSE, {item.name for item in self.multiworld.itempool})


class TreehouseStartingPlanetTests(unittest.TestCase):
    def generate(self, enabled, seed):
        from test.general import setup_multiworld

        from ..world import RACSizeMatterWorld
        return setup_multiworld(RACSizeMatterWorld, seed=seed, options={
            "enable_hig_treehouse": enabled, "random_starting_planet": "unweighted"})

    def test_treehouse_can_start_only_when_enabled(self):
        starts = {enabled: set() for enabled in (0, 1)}
        for enabled in (0, 1):
            for seed in range(40):
                world = self.generate(enabled, seed).worlds[1]
                starts[enabled].add(world.starting_planet_id)
                if world.starting_planet_id == 24:
                    self.assertIn(Rac5Infobots.HIG_TREEHOUSE, world.preplaced_items)
        self.assertNotIn(24, starts[0])
        self.assertIn(24, starts[1])


class TreehouseClientUnlockTests(unittest.TestCase):
    def sync(self, enabled, planets, runtime):
        from ..core.inventory_sync import InventorySync
        from ..core.options import ClientOptions
        core = SimpleNamespace(
            _refresh_main_menu_state=lambda: False, _ap_inventory_ready=False, pine=None,
            options=ClientOptions(hig_treehouse_enabled=enabled), native=runtime,
            planet_unlock=SimpleNamespace(set_unlocked_planets=Mock()),
            progressive_challenge_mode_enabled=False, armour=SimpleNamespace(set_ap_armour=Mock()),
            vendor_active=False,
            planet=SimpleNamespace(is_ready=False, weapons_available=False, weapons=SimpleNamespace()),
        )
        with patch("worlds.rac_size_matters.core.inventory_sync.set_clank_pack_ownership"):
            InventorySync(core).apply_inventory(weapons={}, gadgets={}, weapon_levels={}, weapon_mods={},
                                                armour_unlocked={}, infobot_planets=planets)

    def test_flag_follows_infobot_and_writes_live(self):
        memory = SimpleNamespace(write_int32=Mock())
        runtime = NativeRuntime.__new__(NativeRuntime)
        runtime.pine, runtime._treehouse_unlocked = memory, True
        runtime.ship_menu = SimpleNamespace(installed=True, treehouse_flag=0x1234)
        self.sync(True, set(), runtime)
        self.assertFalse(runtime.treehouse_unlocked)
        memory.write_int32.assert_called_once_with(0x1234, 0)
        self.sync(True, {"HIG_TREEHOUSE"}, runtime)
        self.assertTrue(runtime.treehouse_unlocked)
        memory.write_int32.assert_called_with(0x1234, 1)
        self.sync(False, set(), runtime)
        self.assertTrue(runtime.treehouse_unlocked)


class TreehouseRuntimeTests(unittest.TestCase):
    def test_runtime_installs_only_checks_in_the_seed(self):
        from .test_treehouse_addresses import FIXTURES, relocated_references

        for enabled in (False, True):
            with self.subTest(enabled=enabled):
                memory = Memory()
                memory.data[0xD00000:0x1100000] = bytes(0x400000)
                fixture = json.loads((Path(__file__).parent / "fixtures/treehouse_turret_us.json").read_text())
                grind = json.loads((Path(__file__).parent / "fixtures/treehouse_grindrail_us.json").read_text())
                preview = json.loads((Path(__file__).parent / "fixtures/ship_preview_us.json").read_text())["treehouse"]
                for address, data in [*fixture["segments"], *fixture["menu_segments"], *preview["segments"], *grind["segments"]]:
                    memory.data[address:address + len(data) // 2] = bytes.fromhex(data)
                for address, raw in relocated_references(FIXTURES['us'], FIXTURES['us']['relocation_delta']):
                    memory.data[address:address + len(raw)] = raw
                runtime = NativeRuntime.__new__(NativeRuntime)
                runtime.pine = memory
                runtime.patch_options = PatchOptions()
                runtime.vendor = SimpleNamespace(planet=SimpleNamespace())
                old_shrink = Mock()
                old_shrink._validate.side_effect = RuntimeError("Previous overlay was unloaded")
                runtime.shrink_ray = SimpleNamespace(plan=old_shrink, planet=8)
                runtime._treehouse_unlocked = True
                runtime.checked = {Rac5ShrinkRayGrindrail.HIG_TREEHOUSE_GRINDRAIL}
                runtime.allowed_locations = runtime.checked if enabled else set()
                runtime._prepare(24, 0xD00000)
                self.assertIsNone(runtime.shrink_ray.plan)
                self.assertIsNone(runtime.shrink_ray.planet)
                old_shrink.restore.assert_not_called()
                self.assertEqual(runtime.module, 24)
                self.assertTrue(all(plan.installed for plan in runtime.plans))
                self.assertEqual(runtime.treehouse_grindrail is not None, enabled)
                if enabled:
                    self.assertEqual(memory.read_int8(runtime.treehouse_grindrail.journals[0][0]), 2)
                # Gameplay must stay ready rather than request another load
                # because the previous planet's Shrink Ray signature changed.
                from ..core import address_maps
                runtime.enabled = True
                runtime.starting_planet = Mock()
                runtime.vendor.planet.starting_planet_id = None
                runtime.gate = Mock(STATE=0x1000)
                runtime.gate.armed = False
                runtime.gate.held_module.return_value = None
                runtime._released = False
                runtime._poll = Mock()
                memory.write_int32(runtime.gate.STATE, 6)
                memory.write_int32(address_maps.CURRENT_PLANET_ADDRESS, 24)
                memory.write_int32(address_maps.NEW_PLANET_START_LOAD_ADDR, 0xFFFFFFFF)
                for _ in range(3):
                    self.assertFalse(runtime.tick())
                    self.assertEqual(runtime.module, 24)
                    self.assertEqual(memory.read_int32(address_maps.NEW_PLANET_START_LOAD_ADDR), 0xFFFFFFFF)
                old_shrink._validate.assert_not_called()

    def test_treehouse_menu_uses_native_treehouse_title(self):
        memory = Memory()
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
        runtime.balance_callback = runtime.connection_warning = None
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
