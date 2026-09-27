import unittest
from unittest.mock import Mock

from ..core.address_maps import PLANET_ADDRESSES
from ..core.core import Core
from ..core.menu import MenuStateValue
from .test_client_gameplay import GameMemory


class TestMenuShortcuts(unittest.TestCase):
    def setUp(self):
        self.memory = GameMemory()
        self.core = Core(self.memory)
        self.core.clank_enabled = False
        self.core.tick()
        self.planet = self.core.planet

    def press(self, direction, shoulders=3):
        address = PLANET_ADDRESSES[self.planet.planet_id].controller_pause_select_v2
        self.memory.write_bytes(address, bytes((0xFF ^ direction, 0xFF ^ shoulders)))

    def test_pause_to_planets_and_back_without_repeated_requests(self):
        for source, direction, target in (
            (MenuStateValue.PAUSE_MENU, 0x80, MenuStateValue.PLANET_MENU),
            (MenuStateValue.PLANET_MENU, 0x20, MenuStateValue.PAUSE_MENU),
        ):
            with self.subTest(source=source):
                self.planet.menu.current = source
                self.planet.menu.update = 0
                self.press(direction)
                self.memory.write_int8 = Mock(wraps=self.memory.write_int8)
                self.planet.check_controller()
                self.assertEqual(self.planet.menu.update, target)
                self.assertEqual(self.planet.menu.current, source)
                self.memory.write_int8.reset_mock()
                self.planet.check_controller()
                self.memory.write_int8.assert_not_called()

    def test_ignores_gameplay_vendors_old_shortcuts_and_incomplete_combos(self):
        for menu, direction, shoulders in (
            (0, 0x80, 3), (9, 0x80, 3), (14, 0x20, 3),
            (3, 1, 3), (3, 8, 3), (3, 0x80, 1), (3, 0x80, 2),
            (3, 0x80, 0), (3, 0xA0, 3), (16, 0xA0, 3),
            (3, 0x20, 3), (16, 0x80, 3),
        ):
            with self.subTest(menu=menu, direction=direction, shoulders=shoulders):
                self.planet.menu.current = menu
                self.planet.menu.update = 0
                self.press(direction, shoulders)
                self.planet.check_controller()
                self.assertEqual(self.planet.menu.update, 0)

    def test_loading_never_requests_menu_switch(self):
        self.planet.menu.current = MenuStateValue.PAUSE_MENU
        self.planet.menu.update = 0
        self.press(0x80)
        self.planet.is_ready = False
        self.planet.check_controller()
        self.assertEqual(self.planet.menu.update, 0)
