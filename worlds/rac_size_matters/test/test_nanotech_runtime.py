import json
import struct
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from ..core import address_maps
from ..core.location_checks import LocationChecks
from ..core.player import PlayerInventory
from ..core.player_health_exp import NANOTECH_XP_THRESHOLDS, PlayerHealthExpInventory


class TestNanotechRuntime(unittest.TestCase):
    def make_core(self, planet_id):
        self.memory = {}
        pine = SimpleNamespace(
            read_int32=lambda address: self.memory.get(address, 0),
            read_int8=lambda address: self.memory.get(address, 0),
            read_bytes=lambda address, size: struct.pack("<f", self.memory.get(address, 0)),
        )
        player = PlayerInventory(pine)
        player.set_base(planet_id)
        self.base = player.movement_addr - 0x100
        self.memory[address_maps.CURRENT_PLANET_ADDRESS] = planet_id
        self.memory[self.base + 0x5B0] = 0x200000
        self.memory[self.base + 0x59C] = 0x200000
        self.memory[player.max_health_addr] = 5.0
        return SimpleNamespace(
            pine=pine,
            planet=SimpleNamespace(planet_id=planet_id, is_ready=True, player=player),
            player_health_exp=PlayerHealthExpInventory(pine),
            send_location=Mock(),
        )

    def test_challenge_hp_is_ignored_and_ratchet_levels_resume(self):
        original = address_maps.GAME_ID
        try:
            for game_id in address_maps.SUPPORTED_GAMES:
                address_maps.select_game(game_id)
                for planet_id in (4, 8, 24):
                    with self.subTest(game=game_id, planet=planet_id):
                        core = self.make_core(planet_id)
                        checks = LocationChecks(core)
                        checks.nanotech()
                        self.memory[core.planet.player.max_health_addr] = 20.0
                        # Reproduce the missed case: HP changes while BOTH
                        # player pointers still identify Ratchet.
                        checks.nanotech()
                        self.memory[self.base + 0x59C] = 0x210000
                        checks.nanotech()
                        core.send_location.assert_not_called()
                        self.assertEqual(core.player_health_exp._last_level, 5)
                        self.memory[self.base + 0x59C] = 0x200000
                        checks.nanotech()  # Return pointer can precede HP restoration too.
                        core.send_location.assert_not_called()
                        self.memory[core.planet.player.max_health_addr] = 6.0
                        self.memory[address_maps.PLAYER_HEALTH_EXP] = 1800
                        checks.nanotech()
                        core.send_location.assert_called_once_with("Nanotech Level: 6")
        finally:
            address_maps.select_game(original)

    def test_transition_or_missing_player_cannot_report_hp(self):
        for state in ("loading", "changed_level", "missing_player"):
            with self.subTest(state=state):
                core = self.make_core(4)
                self.memory[address_maps.PLAYER_HEALTH_EXP] = 1800
                self.memory[core.planet.player.max_health_addr] = 20.0
                if state == "loading":
                    core.planet.is_ready = False
                elif state == "changed_level":
                    self.memory[address_maps.CURRENT_PLANET_ADDRESS] = 8
                else:
                    self.memory[self.base + 0x5B0] = 0
                    self.memory[self.base + 0x59C] = 0
                LocationChecks(core).nanotech()
                core.send_location.assert_not_called()
                self.assertEqual(core.player_health_exp._last_level, 5)

    def test_xp_thresholds_match_retail_table_and_all_boundaries(self):
        rows = json.loads((Path(__file__).parent / 'fixtures/nanotech_table.json').read_text())['rows']
        self.assertEqual(list(NANOTECH_XP_THRESHOLDS), [row[1] for row in rows])
        core = self.make_core(4)
        self.memory[address_maps.CHALLENGE_MODE_BASE] = 1
        for _, xp, level in rows[1:]:
            self.memory[address_maps.PLAYER_HEALTH_EXP] = xp - 1
            self.assertEqual(core.player_health_exp.check_level(), [])
            self.memory[address_maps.PLAYER_HEALTH_EXP] = xp
            self.assertEqual(core.player_health_exp.check_level(), [f'Nanotech Level: {level}'])
            self.assertEqual(core.player_health_exp.check_level(), [])

    def test_normal_game_cap_and_real_multi_level_gain(self):
        core = self.make_core(4)
        self.memory[address_maps.PLAYER_HEALTH_EXP] = 5850
        self.assertEqual(core.player_health_exp.check_level(),
                         [f'Nanotech Level: {level}' for level in range(6, 9)])
        self.memory[address_maps.PLAYER_HEALTH_EXP] = 488250
        self.assertEqual(core.player_health_exp.check_level(),
                         [f'Nanotech Level: {level}' for level in range(9, 51)])
        self.memory[address_maps.CHALLENGE_MODE_BASE] = 1
        self.assertEqual(core.player_health_exp.check_level(),
                         [f'Nanotech Level: {level}' for level in range(51, 76)])
