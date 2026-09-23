from types import SimpleNamespace
import unittest

from ..client.vendor import InventoryMixin
from ..core.core import Core
from ..core.planets import PLANET_UNLOCKS, PlanetUnlockState
from ..data.planets import INFOBOT_ITEM_TO_PLANET
from .test_client_gameplay import GameMemory


class TestPlanetReceipts(unittest.TestCase):
    def setUp(self):
        self.memory = GameMemory()
        self.state = PlanetUnlockState(self.memory)
        self.state.split_infobots = True
        self.state.set_unlocked_planets(set())

    def parse(self, names):
        context = SimpleNamespace(
            game="PSP", item_names={"PSP": dict(enumerate(names))},
            items_received=[SimpleNamespace(item=i) for i in range(len(names))],
            _wiring=SimpleNamespace(planet=SimpleNamespace(planet_id=1)),
        )
        return InventoryMixin._parse_inventory(context)["infobot_planets"]

    def assert_bytes(self, name, unlocked):
        record = PLANET_UNLOCKS[name]
        value = 3 if unlocked else 0
        self.assertEqual(self.memory.read_int8(record.unlock_addr), value)
        self.assertEqual(self.memory.read_int8(record.state_addr), max(value, record.default_state))

    def test_each_receipt_unlocks_only_its_planet(self):
        for item, destinations in INFOBOT_ITEM_TO_PLANET.items():
            with self.subTest(item=item):
                self.state.set_unlocked_planets(self.parse([item]))
                self.state.check()
                for name in PLANET_UNLOCKS:
                    if name != "INSIDE_CLANK":
                        self.assert_bytes(name, name == "DREAMTIME" or name.lower() in destinations)

    def test_stale_save_and_reconnect_do_not_grant_starting_planets(self):
        for name in ("POKITARU", "RYLLUS", "KALIDON"):
            record = PLANET_UNLOCKS[name]
            self.memory.write_int8(record.unlock_addr, 3)
            self.memory.write_int8(record.state_addr, 3)
        self.state.reset_session()
        self.state.sync()
        Core(self.memory).restore_world_states(set())
        for name in ("POKITARU", "RYLLUS", "KALIDON"):
            self.assert_bytes(name, False)

    def test_natural_entrance_untouched(self):
        record = PLANET_UNLOCKS["INSIDE_CLANK"]
        self.memory.write_int8(record.unlock_addr, 2)
        self.memory.write_int8(record.state_addr, 1)
        self.state.check()
        self.assertEqual(self.memory.read_int8(record.unlock_addr), 2)
        self.assertEqual(self.memory.read_int8(record.state_addr), 1)

    def test_legacy_combined_receipt(self):
        self.assertEqual(self.parse(["Infobot: Pokitaru and Ryllus"]), {"POKITARU", "RYLLUS"})

    def test_legacy_ryllus_exception_is_disabled_for_random_start(self):
        self.state.split_infobots = False
        self.state.reset_session()
        self.assertTrue(self.state.is_unlocked("RYLLUS"))
        self.state.on_ryllus_cutscene_ended()
        self.assertFalse(self.state.is_unlocked("RYLLUS"))
        self.state.set_random_start(True)
        self.state.reset_session()
        self.assertFalse(self.state.is_unlocked("RYLLUS"))

    def test_received_unlock_survives_reset_and_cutscene(self):
        self.state.set_unlocked_planets(self.parse(["Infobot: Ryllus"]))
        self.state.reset_session()
        self.state.on_ryllus_cutscene_ended()
        self.state.check()
        self.assert_bytes("RYLLUS", True)
        self.assert_bytes("POKITARU", False)
