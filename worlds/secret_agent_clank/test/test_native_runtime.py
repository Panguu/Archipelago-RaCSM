import struct
import unittest
from unittest.mock import Mock, patch

from ..constants.alien_codes import ALIEN_CODE_MODULES
from ..constants.clank_gadgets import SACClankGadgets
from ..constants.missions import MISSION_COMPLETE_NAME
from ..core.case_menu import CASE_LABELS
from ..core.core import Core
from ..core.inventories.alien_codes import AlienCodeInventory
from ..core.inventories.missions import MissionInventory
from ..core.native_runtime import NativeRuntime
from .test_runtime import Memory


class NativeRuntimeTests(unittest.TestCase):
    def test_title_module_releases_loader_without_gameplay_hooks(self):
        self.runtime.gate.held_module.return_value = 0
        self.assertFalse(self.runtime.service(set(), {}))
        self.runtime.gate.release.assert_called_once()
        self.hooks.prepare.assert_not_called()
        self.runtime.log.assert_not_called()

    def test_settled_title_does_not_request_a_level_reset(self):
        self.p.batch_write_int32([(0x1AAE78, 0), (0x1AAE3C, 5), (0x19EF04, 1),
                                 (0x206324, 0xFFFFFFFF), (0x206338, 3)])
        self.assertFalse(self.runtime.service(set(), {}))
        self.runtime.log.assert_not_called()
        self.runtime.gate.arm.assert_called_once()

    def test_vendor_selection_uses_native_modules_and_shared_cases(self):
        from ..constants.planets import SACCases
        runtime = NativeRuntime(Memory(), Mock(), Mock())
        runtime.configure_vendors([SACCases.ASYANICA_ROOFTOPS, SACCases.GONDOLA_ASCENT])
        self.assertEqual(runtime.vendor_modules, {4, 11})
        self.assertNotIn(21, runtime.vendor_modules)

    def test_no_vendor_module_keeps_progression_without_titan_hooks(self):
        self.runtime.configure_vendors([])
        self.runtime.gate.held_module.return_value = 21
        self.runtime.progression = Mock(ng_plus=1)
        self.runtime.progression.prepare.return_value = []
        self.hooks.patches = []
        with patch("worlds.secret_agent_clank.core.native_runtime.RuntimeSymbols"):
            self.assertFalse(self.runtime.service(set(), {}))
        self.assertEqual(self.hooks.prepare.call_args.kwargs["vendor_locations"], {})
        self.assertFalse(self.runtime.progression.prepare.call_args.kwargs["vendor_enabled"])
        self.hooks.install_at_loader_gate.assert_called_once()

    def setUp(self):
        travel = patch("worlds.secret_agent_clank.core.patches.mission_travel.MissionTravel.prepare", return_value=[])
        travel.start()
        self.addCleanup(travel.stop)
        self.p = Memory()
        self.hooks = Mock(installed=False, entitlement_table=None, module=16)
        self.runtime = NativeRuntime(self.p, self.hooks, Mock())
        self.runtime.gate = Mock(armed=False, STATE=0x100)
        self.runtime.gate.held_module.return_value = None
        self.p.batch_write_int32([(0x206324, 0xFFFFFFFF), (0x206328, 16),
                                 (0x206338, 3), (0x100, 5)])

    def test_incoming_hooks_survive_outgoing_module_during_startup(self):
        from ..core.patches import MARKER, LocationHooks
        hooks = LocationHooks(self.p)
        hooks.installed = True
        hooks.module = 16
        hooks.marker_address = 0x120000
        self.p.data[0x120000:0x120000 + len(MARKER)] = MARKER
        core = Core(self.p)
        core.location_hooks = hooks
        core.native_runtime = self.runtime
        self.runtime.hooks = hooks
        self.runtime.awaiting_start = True
        core.apply_inventory(ratchet={}, clank={})
        core.case.check_transition = Mock(return_value=False)
        self.p.batch_write_int32([(0x206328, 1)])
        core.tick()
        self.assertTrue(hooks.installed)
        self.assertTrue(self.runtime.awaiting_start)
        self.runtime.log.assert_not_called()
        self.p.batch_write_int32([(0x206328, 16)])
        self.assertTrue(self.runtime.service(set(), {}))
        self.assertTrue(hooks.installed)
        self.runtime.log.assert_not_called()

    def test_waits_for_preinit_before_resuming_polling(self):
        self.runtime.awaiting_start = True
        self.hooks.entitlement_table = 0x120000
        self.assertFalse(self.runtime.service(set(), {}))
        self.assertTrue(self.runtime.awaiting_start)
        self.hooks.is_current.assert_not_called()
        self.runtime.log.assert_not_called()

    def test_inventory_waits_for_native_startup_to_finish(self):
        self.hooks.installed = True
        self.hooks.is_current.return_value = True
        self.p.batch_write_int32([(0x206338, 1)])
        self.assertFalse(self.runtime.service(set(), {11: True}))
        self.hooks.sync_entitlements.assert_not_called()

    def test_initial_connection_requires_reset_without_inventory_writes(self):
        self.assertFalse(self.runtime.service(set(), {11: True}))
        self.runtime.gate.arm.assert_called_once()
        self.hooks.prepare.assert_not_called()

    def test_held_module_installs_before_release_then_rearms_after_start(self):
        gate = self.runtime.gate
        gate.armed = True
        gate.held_module.return_value = 1
        calls = []
        self.hooks.install_at_loader_gate.side_effect = lambda g: calls.append("install")
        gate.release.side_effect = lambda: calls.append("release")
        with patch("worlds.secret_agent_clank.core.native_runtime.RuntimeSymbols"):
            self.assertFalse(self.runtime.service({"throwTie"}, {11: True}))
        self.assertEqual(calls, ["install", "release"])
        self.assertTrue(self.runtime.awaiting_start)
        self.p.batch_write_int32([(0x100, 4)])
        gate.reset_mock()
        self.assertFalse(self.runtime.service(set(), {}))
        gate.arm.assert_not_called()
        self.p.batch_write_int32([(0x100, 5)])
        gate.armed = False
        gate.held_module.return_value = None
        self.hooks.installed = True
        self.hooks.is_current.return_value = True
        self.assertTrue(self.runtime.service(set(), {11: False}))
        gate.arm.assert_called_once()
        self.hooks.sync_entitlements.assert_called_once_with({11: False})

    def test_failed_install_releases_loader(self):
        self.runtime.gate.held_module.return_value = 1
        self.hooks.prepare.side_effect = ValueError("signature")
        with patch("worlds.secret_agent_clank.core.native_runtime.RuntimeSymbols"), self.assertRaises(ValueError):
            self.runtime.service(set(), {})
        self.runtime.gate.release.assert_called_once()

    def test_ap_session_cannot_disable_native_hooks(self):
        core = Core(self.p)
        with self.assertRaises(RuntimeError):
            core.set_native_locations(False)
        core.apply_inventory(ratchet={"throwTie": False}, clank={SACClankGadgets.BLACK_OUT_PEN: True})
        self.assertEqual(core._entitlements(), {11: False, 17: True, 25: False})


class MissionLabelTests(unittest.TestCase):
    def test_shared_module_reports_each_case_independently_and_deduplicates(self):
        p = Memory()
        inv = MissionInventory(p)
        inv.table_base = 0x110000
        struct.pack_into("<2I", p.data, inv.table_base + 11 * 8, 0x120000, 2)
        for i, label in enumerate((5614, 5622)):
            struct.pack_into("<I", p.data, 0x120000 + i * 96, 1)
            struct.pack_into("<I", p.data, 0x120000 + i * 96 + 12, 3)
            struct.pack_into("<I", p.data, 0x120000 + i * 96 + 60, label)
        found = inv.check_all()
        self.assertEqual(set(found), {MISSION_COMPLETE_NAME[CASE_LABELS[x]] for x in (5614, 5622)})
        for name in found:
            inv.confirm(name)
        self.assertEqual(inv.check_all(), [])
        inv.invalidate_resolved_addresses()
        self.assertEqual(inv.check_all(), [])

    def test_completion_uses_last_story_task_without_requiring_bonus_challenge(self):
        p = Memory()
        inv = MissionInventory(p)
        inv.table_base = 0x110000
        struct.pack_into("<2I", p.data, inv.table_base + 4 * 8, 0x120000, 3)
        for i, kind in enumerate((1, 1, 4)):
            struct.pack_into("<I", p.data, 0x120000 + i * 96, kind)
            struct.pack_into("<I", p.data, 0x120000 + i * 96 + 12, 3 if i == 1 else 0)
            struct.pack_into("<I", p.data, 0x120000 + i * 96 + 60, 5626)
        self.assertEqual(inv.check_all(), [MISSION_COMPLETE_NAME[CASE_LABELS[5626]]])


class AlienFlagTests(unittest.TestCase):
    def test_goal_catalog_has_every_code_and_card(self):
        from ..locations import ALIEN_CODE_LOCATIONS, KEYCARD_LOCATIONS
        self.assertEqual(len(ALIEN_CODE_LOCATIONS), 27)
        self.assertEqual(len(KEYCARD_LOCATIONS), 3)
        self.assertEqual(len({entry.code for entry in ALIEN_CODE_LOCATIONS.values()}), 27)

    def test_chalice_collection_not_cards_or_door_completes_goal(self):
        from ..core.inventories.keycards import KeycardInventory
        p = Memory()
        cards = KeycardInventory(p)
        values = {0xAA: bytes([7]), 0xCB: bytes([0])}
        cards.flags.read = lambda index: values[index]
        cards._door_is_open = Mock(return_value=True)
        self.assertEqual(len(cards.check()), 3)
        self.assertTrue(cards.door_opened)
        self.assertFalse(cards.chalice_collected)
        core = Core(p)
        core.keycards = cards
        core.goal = 3
        core.on_goal = Mock()
        core._check_goal()
        core.on_goal.assert_not_called()
        values[0xCB] = bytes([1])
        cards.check()
        core._check_goal()
        core._check_goal()
        core.on_goal.assert_called_once()

    def test_all_27_bits_and_nibble_boundaries(self):
        inv = AlienCodeInventory(Memory())
        inv.valid = True
        data = bytearray(15)
        for module in ALIEN_CODE_MODULES.values():
            data[(module - 1) // 2] |= 7 << (((module - 1) & 1) * 4)
        inv.flags.read = Mock(return_value=bytes(data))
        found = inv.check()
        self.assertEqual(len(found), 27)
        self.assertTrue(inv.all_found)
        for name in found:
            inv.confirm(name)
        self.assertEqual(inv.check(), [])
        data[0] &= ~1
        inv.flags.read.return_value = bytes(data)
        inv.check()
        self.assertFalse(inv.all_found)

    def test_invalid_binding_cannot_complete_goal(self):
        inv = AlienCodeInventory(Memory())
        inv.found = set(range(27))
        self.assertFalse(inv.all_found)
