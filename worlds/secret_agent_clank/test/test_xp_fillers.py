import random
import struct
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ..constants import (
    CASE_ID_TO_CASE,
    NativeFunctions,
    ProgressiveWeaponsOptions,
    SACFiller,
    SACOperatives,
    SACTraps,
)
from ..core import Core
from ..core.patches.asm import jump, packed
from ..core.player import ActivePlayer
from ..core.xp_fillers import GADGET_SIZE, boost_nanotech, boost_weapon, equipped_weapon
from ..world import SecretAgentClankWorld
from .test_runtime import Memory

GETTER, GET_DATA, GADGETS, PLAYER, DEFINITION = 0x200000, 0x200100, 0x300000, 0x400000, 0x310000
SYMBOLS = {NativeFunctions.WEAPON_GET_CURRENT_WEAPON: GETTER, NativeFunctions.GADGET_GET_DATA: GET_DATA,
           "GADGET_g_GadgetList": GADGETS}
BLASTER = 2  # its WEAPON_ORDER index


def holding(gadget=BLASTER, level=1, xp=100, xp_to_level=1000):
    """Memory where the player holds `gadget` at `level` (0-based), with `xp` of the `xp_to_level` it needs."""
    memory = Memory()
    memory.write_bytes(GETTER, packed([0x27BDFFF0, 0xFFBF0000, jump(GET_DATA, True), 0x8C840344]))
    struct.pack_into("<I", memory.data, PLAYER + 0x344, gadget)
    address = GADGETS + gadget * GADGET_SIZE
    for offset, value in ((0x5C, level), (0x64, xp), (0x10 + level * 4, DEFINITION)):
        struct.pack_into("<I", memory.data, address + offset, value)
    struct.pack_into("<I", memory.data, DEFINITION + 0x34, xp_to_level)
    return memory, address


class WeaponXPTests(unittest.TestCase):
    def test_adds_a_quarter_of_the_level(self):
        memory, address = holding()
        weapon = equipped_weapon(memory, SYMBOLS, PLAYER)
        self.assertEqual((weapon.internal, weapon.level, weapon.xp, weapon.xp_to_level), ("blaster", 1, 100, 1000))
        self.assertEqual(boost_weapon(memory, weapon), 250)
        self.assertEqual(memory.read_int32(address + 0x64), 350)

    def test_stops_one_short_of_levelling_up(self):
        memory, address = holding(xp=900)
        self.assertEqual(boost_weapon(memory, equipped_weapon(memory, SYMBOLS, PLAYER)), 99)
        self.assertEqual(memory.read_int32(address + 0x64), 999)
        self.assertEqual(boost_weapon(memory, equipped_weapon(memory, SYMBOLS, PLAYER)), 0)

    def test_max_level_and_non_weapons_get_nothing(self):
        memory, _ = holding(level=7)
        self.assertEqual(boost_weapon(memory, equipped_weapon(memory, SYMBOLS, PLAYER)), 0)
        self.assertEqual(memory.writes, [])
        for gadget in (0, 0x28):  # an empty slot, and out of range
            with self.subTest(gadget=gadget):
                memory, _ = holding()
                struct.pack_into("<I", memory.data, PLAYER + 0x344, gadget)
                self.assertIsNone(equipped_weapon(memory, SYMBOLS, PLAYER))

    def test_refuses_a_changed_getter(self):
        memory, _ = holding()
        struct.pack_into("<I", memory.data, GETTER + 12, 0x8C840348)
        with self.assertRaisesRegex(RuntimeError, "current-weapon getter"):
            equipped_weapon(memory, SYMBOLS, PLAYER)

    def test_progressive_weapons_decide_when_xp_counts(self):
        cases = (
            ({}, 350),  # off: XP counts
            ({"enabled": True}, 100),  # automatic: levels only come from AP
            ({"enabled": True, "manual": True, "levels": {"blaster": 2}}, 100),  # already at the received level
            ({"enabled": True, "manual": True, "levels": {"blaster": 3}}, 350),  # below it
        )
        for progression, xp in cases:
            with self.subTest(**progression):
                memory, address = holding()
                core = weapon_xp_core(memory, SACOperatives.CLANK, progression=progression)
                self.assertTrue(Core._weapon_xp(core))
                self.assertEqual(memory.read_int32(address + 0x64), xp)

    def test_qwark_and_gadgetbot_cases_boost_an_owned_weapon(self):
        for operative in (SACOperatives.QWARK, SACOperatives.GADGETBOTS):
            with self.subTest(operative=operative):
                memory, address = holding()
                core = weapon_xp_core(memory, operative, owned={"blaster": True, "throwTie": False})
                self.assertTrue(Core._weapon_xp(core))
                self.assertEqual(memory.read_int32(address + 0x64), 350)
                core.case.active_player.current_player.assert_not_called()

    def test_qwark_cases_give_nothing_without_a_weapon_that_can_gain_xp(self):
        for owned, level in (({}, 1), ({"blaster": True}, 7)):
            with self.subTest(owned=owned, level=level):
                memory, _ = holding(level=level)
                memory.writes.clear()
                self.assertTrue(Core._weapon_xp(weapon_xp_core(memory, SACOperatives.QWARK, owned=owned)))
                self.assertEqual(memory.writes, [])


def weapon_xp_core(memory, operative, *, owned=None, progression=None):
    case_id = next(case_id for case_id, case in CASE_ID_TO_CASE.items() if case.operative == operative)
    return SimpleNamespace(
        pine=memory, _log=Mock(), _debug=Mock(), _owned_equipment=Mock(return_value=owned or {}),
        case=SimpleNamespace(case_id=case_id, symbols=SYMBOLS,
                             active_player=Mock(current_player=Mock(return_value=PLAYER))),
        progression=SimpleNamespace(**{"enabled": False, "manual": False, "levels": {}, **(progression or {})}))


class NanotechXPTests(unittest.TestCase):
    def test_adds_a_quarter_of_the_level_below_the_cap(self):
        memory = Memory()
        data = {"saved_xp": 1200, "level_xp": 1000, "next_xp": 1400, "xp_address": 0x500000}
        with patch("worlds.secret_agent_clank.core.xp_fillers.read_nanotech", return_value=data):
            self.assertEqual(boost_nanotech(memory, {}, SACOperatives.CLANK), 100)
        self.assertEqual(memory.read_int32(0x500000), 1300)
        with patch("worlds.secret_agent_clank.core.xp_fillers.read_nanotech", return_value={**data, "next_xp": None}):
            self.assertEqual(boost_nanotech(memory, {}, SACOperatives.CLANK), 0)
        self.assertEqual(memory.read_int32(0x500000), 1300)

    def test_ratchet_cases_boost_ratchet_and_the_rest_boost_clank(self):
        for case_id, case in CASE_ID_TO_CASE.items():
            with self.subTest(case=case.name):
                core = SimpleNamespace(pine=Memory(), _log=Mock(), _debug=Mock(), case=SimpleNamespace(case_id=case_id, symbols={}))
                with patch("worlds.secret_agent_clank.core.core.boost_nanotech", return_value=5) as boost:
                    self.assertTrue(Core._nanotech_xp(core))
                expected = SACOperatives.RATCHET if case.operative == SACOperatives.RATCHET else SACOperatives.CLANK
                self.assertEqual(boost.call_args.args[2], expected)

    def test_loading_defers_it(self):
        core = SimpleNamespace(pine=Memory(), _log=Mock(), _debug=Mock(), case=SimpleNamespace(case_id=1, symbols={}))
        with patch("worlds.secret_agent_clank.core.core.boost_nanotech", side_effect=ValueError("loading")):
            self.assertFalse(Core._nanotech_xp(core))


class OneHPTrapTests(unittest.TestCase):
    def player(self, health):
        memory = Memory()
        player = ActivePlayer(memory)
        player.health_sample = Mock(return_value=None if health is None else (PLAYER, health))
        return memory, player

    def test_sets_health_to_one(self):
        memory, player = self.player(8.0)
        self.assertTrue(player.lower_health(1.0))
        self.assertEqual(struct.unpack_from("<f", memory.data, PLAYER + 0x274)[0], 1.0)

    def test_already_low_is_left_alone_and_no_player_defers(self):
        memory, player = self.player(0.5)
        self.assertTrue(player.lower_health(1.0))
        self.assertEqual(memory.writes, [])
        _, player = self.player(None)
        self.assertFalse(player.lower_health(1.0))

    def test_dispatch(self):
        player = Mock(lower_health=Mock(return_value=True))
        core = SimpleNamespace(case=SimpleNamespace(is_ready=True, active_player=player),
                               _inventory_initialized=True, _log=Mock())
        self.assertTrue(Core.activate_effect(core, SACTraps.ONE_HP))
        player.lower_health.assert_called_once_with(1.0)


class FillerChoiceTests(unittest.TestCase):
    def fillers(self, progressive_weapons):
        world = SimpleNamespace(random=random.Random(0), options=SimpleNamespace(
            trap_chance=SimpleNamespace(value=0), progressive_weapons=progressive_weapons))
        return {SecretAgentClankWorld.get_filler_item_name(world) for _ in range(200)}

    def test_every_filler_is_used(self):
        self.assertEqual(self.fillers(ProgressiveWeaponsOptions.OFF),
                         {SACFiller.BOLTS, SACFiller.NANOTECH_XP, SACFiller.WEAPON_XP})

    def test_no_weapon_xp_with_automatic_progressive_weapons(self):
        self.assertEqual(self.fillers(ProgressiveWeaponsOptions.AUTOMATIC), {SACFiller.BOLTS, SACFiller.NANOTECH_XP})
