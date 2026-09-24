"""Exercise region selection in fresh processes, including import-time caches."""

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


class RegionSelectionTests(unittest.TestCase):
    def test_client_core_and_loader_select_the_same_region(self):
        script = """
import json
from worlds.rac_size_matters.core import address_maps
from worlds.rac_size_matters.core.core import Core
from worlds.rac_size_matters.core.structs.game import TransitionGateStruct
from worlds.rac_size_matters.pypine import Pine
p = Pine()
core = Core(p)
core.planet.set_planet(1)
print(json.dumps({
    'game': address_maps.GAME_ID,
    'gate_game': core.native.gate.game_id,
    'frontend_game': core.native.starting_planet.game_id,
    'health': core.planet.player.health_addr,
    'transition': TransitionGateStruct.BASE_ADDRESS,
    'loader_state': core.native.gate.STATE,
    'text_box': core.planet.small_text._config.base_addr,
}))
"""
        for region, game, health, transition, loader, text in (
            ("us", "SCUS-97615", 0xF80E2C, 0x1EDDAD4, 0x1EDDAB8, 0xF479E8),
            ("eu", "SCES-55019", 0xF80EAC, 0x1EDD8D4, 0x1EDD8B8, 0xF47A68),
            ("jp", "SCPS-15120", 0xF8092C, 0x1EDF7F4, 0x1EDF7D8, 0xF47468),
        ):
            with self.subTest(region=region):
                result = subprocess.run(
                    [sys.executable, "-c", script],
                    cwd=Path(__file__).resolve().parents[3],
                    env={**os.environ, "RACSM_PLATFORM": region},
                    capture_output=True, text=True, timeout=60,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                actual = json.loads(result.stdout.strip().splitlines()[-1])
                self.assertEqual(actual, {
                    "game": game, "gate_game": game, "frontend_game": game,
                    "health": health, "transition": transition,
                    "loader_state": loader, "text_box": text,
                })


class AutomaticRegionTests(unittest.IsolatedAsyncioTestCase):
    async def test_connect_and_live_swaps_keep_ap_state_and_reject_other_games(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch
        from ..client.pine_mixin import PineMixin
        from ..core import address_maps
        from ..core.core import Core
        from ..core.native_runtime import NativeRuntime
        from ..core.structs.game import TransitionGateStruct
        from ..pypine import Pine

        class SerialOnlyPine(Pine):
            game_id = "SCES-55019"
            def connect(self):
                pass
            def disconnect(self):
                pass
            def get_game_id(self):
                return self.game_id
            def read_bytes(self, *args):
                raise AssertionError("Region selection must not read game memory")
            def write_bytes(self, *args):
                raise AssertionError("Region selection must not write game memory")

        previous = address_maps.GAME_ID
        address_maps.select_game("SCUS-97615")
        try:
            ctx = PineMixin()
            ctx.pine = SerialOnlyPine()
            ctx._pine_lock = asyncio.Lock()
            ctx._wiring = Core(ctx.pine)
            ctx.pine_connected = False
            ctx.slot = ctx.server = None
            ctx.items_received = []
            ctx.current_planet = "Galaxy"
            ctx._items_received_ready = ctx._save_data_received = False
            ctx._connection_sync_pending = False
            ctx._checked_location_names = lambda: set()
            ctx._read_initial_state_sync = Mock()
            ctx._write_notification_text = Mock()
            ctx.handle_connection_loss = Mock()
            for name in ("force_sync", "_send_map_page", "_apply_received_items"):
                setattr(ctx, name, AsyncMock())
            for name in ("_maybe_persist_weapon_state", "_maybe_sync_ammo_link",
                         "_maybe_sync_bolt_link", "_maybe_sync_ghost_link"):
                setattr(ctx, name, Mock())
            core = ctx._wiring
            core.native.enabled = True
            core.native.checked = {"already checked"}
            core.planet.weapons.ap_weapons = {"lacerator": True}
            core.planet.weapons.experience_multiplier = 3
            core.planet.starting_planet_id = 2
            core.native.presentation = Mock()
            old_presentation = core.native.presentation
            old_gate = core.native.gate
            old_gate.armed = True
            with patch("worlds.rac_size_matters.client.pine_mixin.PINE_CONNECT_SETTLE_DELAY_S", 0), \
                    patch.object(NativeRuntime, "tick", return_value=False):
                await ctx._attempt_pine_connect()
                self.assertTrue(ctx.pine_connected)
                self.assertEqual(core.native.gate.game_id, "SCES-55019")
                old_presentation.close.assert_not_called()
                for serial, health, transition, text in (
                    ("SCUS-97615", 0xF80E2C, 0x1EDDAD4, 0xF479E8),
                    ("SCES-55019", 0xF80EAC, 0x1EDD8D4, 0xF47A68),
                    ("SCPS-15120", 0xF8092C, 0x1EDF7F4, 0xF47468),
                    ("SCUS-97615", 0xF80E2C, 0x1EDDAD4, 0xF479E8),
                ):
                    ctx.pine.game_id = serial
                    await ctx._poll_game()
                    self.assertTrue(ctx.pine_connected)
                    self.assertFalse(core.planet.is_ready)
                    self.assertEqual(core.native.gate.game_id, serial)
                    self.assertEqual(core.native.starting_planet.game_id, serial)
                    self.assertEqual(TransitionGateStruct.BASE_ADDRESS, transition)
                    core.planet.set_planet(1)
                    self.assertEqual(core.planet.player.health_addr, health)
                    self.assertEqual(core.planet.small_text._config.base_addr, text)
                    self.assertEqual(core.planet.weapons.ap_weapons, {"lacerator": True})
                    self.assertEqual(core.planet.weapons.experience_multiplier, 3)
                    self.assertEqual(core.planet.starting_planet_id, 2)
                    self.assertIn("already checked", core.native.checked)
                    self.assertTrue(core.native.enabled)
                    self.assertIs(core.vendor.weapons, core.planet.weapons)
                ctx.pine.game_id = "OTHER-GAME"
                await ctx._poll_game()
                self.assertFalse(ctx.pine_connected)
                self.assertEqual(address_maps.GAME_ID, "SCUS-97615")
                with self.assertRaises(ValueError):
                    core.select_game("OTHER-GAME")
                self.assertEqual(address_maps.GAME_ID, "SCUS-97615")
        finally:
            address_maps.select_game(previous)


class RegionalSaveAddressTests(unittest.TestCase):
    def test_save_fields_and_completion_reads_follow_region_after_import(self):
        from ..core import address_maps
        from ..core.armour import ArmourStruct
        from ..core.skill_points import SkillPointInventory
        from ..core.titanium_bolts import TitaniumBoltInventory
        from ..core.skins import SkinInventory, Skin
        from ..core.missions import MissionInventory, _NAME_TO_ADDR_MASK
        from ..locations.observation import LocationObservation, source_addresses
        from .test_runtime_refactor import Memory

        class SaveMemory(Memory):
            def read_int8(self, a):
                return int.from_bytes(self.read_bytes(a, 1), "little")
            def write_int8(self, a, v):
                self.write_bytes(a, bytes([v]))
            def read_int16(self, a):
                return int.from_bytes(self.read_bytes(a, 2), "little")
            def write_int16(self, a, v):
                self.write_bytes(a, v.to_bytes(2, "little"))

        previous = address_maps.GAME_ID
        memory = SaveMemory()
        skills, bolts, skin = SkillPointInventory(memory), TitaniumBoltInventory(memory), SkinInventory(memory)
        missions = MissionInventory(memory)
        try:
            for serial, delta in (("SCPS-15120", -0x1C0), ("SCUS-97615", 0), ("SCES-55019", 0)):
                address_maps.select_game(serial)
                memory.data.clear()
                skills.bits = 0x123456789A
                bolts.pickup = 0x1234567890
                bolts.total = 17
                skin.set(Skin.DAN)
                self.assertEqual(ArmourStruct.BASE_ADDRESS, 0x1F4B354 + delta)
                self.assertEqual(memory.read_bytes(0x1F4B437 + delta, 5), bytes.fromhex("9a78563412"))
                self.assertEqual(memory.read_bytes(0x1F4B444 + delta, 6), bytes.fromhex("907856341211"))
                self.assertEqual(memory.read_bytes(0x1F4B45A + delta, 2), bytes((0x7F, 15)))
                name, (address, mask) = next(iter(_NAME_TO_ADDR_MASK.items()))
                missions.set(name, True)
                self.assertTrue(memory.read_int16(address + delta) & mask)
                self.assertTrue(missions.get(name))
                observation = LocationObservation.read_bytes(memory, 1, True, True, True)
                self.assertEqual(observation.skill_bits, 0x123456789A)
                self.assertEqual(observation.bolt_bits, 0x1234567890)
                self.assertEqual(observation.missions[address] & mask, mask)
                requests = memory.reads[-1]
                expected = {a + delta for source in ("missions", "challenges", "skyboard") for a in source_addresses(source)}
                self.assertTrue(expected.issubset({a for size, a in requests}))
        finally:
            address_maps.select_game(previous)
