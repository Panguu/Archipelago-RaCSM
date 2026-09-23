import asyncio
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from ..constants import Rac5Traps
from ..core import address_maps, traps
from ..core.no_clank import BACKPACK_SLOTS, HIDDEN, NoClank
from ..core.patches.loader_gate import LoaderGate
from ..items import ALL_ITEMS, TRAP_ITEM_TABLE
from ..options import TrapDuration, TrapWeight


class Memory:
    def __init__(self):
        self.data = {}
        self.writes = []

    def get_game_id(self):
        return address_maps.GAME_ID

    def read_int32(self, address):
        return self.data.get(address, 0)

    read_int16 = read_int32

    def write_int32(self, address, value):
        self.data[address] = value
        self.writes.append((address, value))


class TestNoClank(unittest.TestCase):
    def setUp(self):
        self.region = address_maps.GAME_ID
        address_maps.select_game("SCUS-97615")
        self.pine = Memory()
        self.effect = NoClank(self.pine)
        self.load(1)

    def tearDown(self):
        address_maps.select_game(self.region)

    def load(self, planet, object_shift=0):
        p = self.pine
        config = address_maps.PLANET_ADDRESSES[planet]
        self.base = config.player_state - 0x100
        p.data[LoaderGate(p, game_id=address_maps.GAME_ID).STATE] = 6
        p.data[address_maps.CURRENT_PLANET_ADDRESS] = planet
        p.data[address_maps.NEW_PLANET_START_LOAD_ADDR] = 0xFFFFFFFF
        p.data[self.base + 0x59C] = p.data[self.base + 0x5B0] = 0x200000 + object_shift
        self.objects = (0x210000 + object_shift, 0x220000 + object_shift)
        for offset, obj in zip(BACKPACK_SLOTS, self.objects):
            p.data[self.base + offset] = obj
            p.data[obj + 0x40] = 0x230000 + object_shift
            p.data[obj + 0x64] = 0x101

    def test_detaches_and_restores_without_losing_other_flags(self):
        self.effect.update(True)
        for offset, obj in zip(BACKPACK_SLOTS, self.objects):
            self.assertEqual(self.pine.read_int32(self.base + offset), 0)
            self.assertEqual(self.pine.read_int32(obj + 0x64), 0x101 | HIDDEN)
            self.pine.data[obj + 0x64] |= 0x400
        self.effect.update(False)
        for offset, obj in zip(BACKPACK_SLOTS, self.objects):
            self.assertEqual(self.pine.read_int32(self.base + offset), obj)
            self.assertEqual(self.pine.read_int32(obj + 0x64), 0x501)

    def test_waits_for_ground_and_closed_menu(self):
        self.pine.data[self.base + 0x100] = 3
        self.effect.update(True)
        self.assertEqual(self.pine.writes, [])
        self.pine.data[self.base + 0x100] = 0
        menu = address_maps.PLANET_ADDRESSES[1].menu
        self.pine.data[menu] = 3
        self.effect.update(True)
        self.assertEqual(self.pine.writes, [])
        self.pine.data[menu] = 0
        self.effect.update(True)
        self.assertTrue(self.effect.backpacks)

    def test_travel_discards_old_objects_and_applies_on_new_planet(self):
        self.effect.update(True)
        old_addresses = {address for address, _ in self.pine.writes}
        self.pine.writes.clear()
        self.pine.data[LoaderGate.STATE] = 5
        self.effect.update(True)
        self.assertEqual(self.pine.writes, [])
        self.load(7, 0x100000)
        self.effect.update(True)
        self.effect.update(False)
        self.assertTrue(old_addresses.isdisjoint(address for address, _ in self.pine.writes))
        self.assertEqual(self.pine.read_int32(self.base + 0x5AC), self.objects[1])

    def test_expiry_during_loading_does_not_write_stale_memory(self):
        self.effect.update(True)
        self.pine.writes.clear()
        self.pine.data[LoaderGate.STATE] = 4
        self.effect.update(False)
        self.assertEqual(self.pine.writes, [])
        self.assertEqual(self.effect.backpacks, [])

    def test_does_not_affect_playable_clank_or_special_levels(self):
        self.pine.data[self.base + 0x59C] = 0x240000
        self.effect.update(True)
        self.assertEqual(self.pine.writes, [])
        self.pine.data[address_maps.CURRENT_PLANET_ADDRESS] = 15
        self.effect.update(True)
        self.assertEqual(self.pine.writes, [])

    def test_outpost_return_visit_can_remove_and_unlock_pack(self):
        self.load(0x17)
        traps.set_clank_pack_ownership(self.pine, enabled=True, owned=False)
        self.assertEqual(self.pine.read_int32(self.base + 0x5AC), 0)
        traps.set_clank_pack_ownership(self.pine, enabled=True, owned=True)
        self.assertEqual(self.pine.read_int32(self.base + 0x5AC), self.objects[1])

    def test_naturally_absent_or_hidden_pack_remains_so(self):
        self.pine.data[self.base + 0x5AC] = 0
        self.pine.data[self.objects[0] + 0x64] |= HIDDEN
        self.effect.update(True)
        self.effect.update(False)
        self.assertEqual(self.pine.read_int32(self.base + 0x5AC), 0)
        self.assertTrue(self.pine.read_int32(self.objects[0] + 0x64) & HIDDEN)

    def test_respawn_never_restores_replaced_objects(self):
        self.effect.update(True)
        old_objects = self.objects
        self.load(1, 0x100000)
        self.pine.writes.clear()
        self.effect.update(False)
        self.assertEqual(self.pine.writes, [])
        self.assertNotEqual(self.pine.read_int32(self.base + 0x5AC), old_objects[1])

    def test_all_maps_use_current_region_and_player_addresses(self):
        for game in address_maps.SUPPORTED_GAMES:
            with self.subTest(game=game):
                address_maps.select_game(game)
                self.pine = Memory()
                self.effect = NoClank(self.pine)
                self.load(1)
                self.effect.update(True)
                self.effect.update(False)
                self.assertEqual(self.pine.read_int32(self.base + 0x5AC), self.objects[1])

    def test_new_item_appends_without_renumbering_existing_items(self):
        baseline = json.loads((Path(__file__).parent / "fixtures/refactor_ids.json").read_text())
        for name, (code, classification) in baseline["items"].items():
            self.assertEqual([ALL_ITEMS[name].code, int(ALL_ITEMS[name].classification)], [code, classification])
        name = Rac5Traps.TRAP_NO_CLANK
        self.assertIn(name, TRAP_ITEM_TABLE)
        self.assertEqual(TrapDuration.default[name], 20)
        self.assertEqual(TrapWeight.default[name], 1)

    def test_stacking_expiry_and_disconnect_restore(self):
        loop = asyncio.new_event_loop()
        name = Rac5Traps.TRAP_NO_CLANK
        try:
            with patch.object(asyncio, "get_event_loop", return_value=loop):
                traps.activate_trap(self.pine, name)
                deadline = traps._active_deadlines[name]
                first = traps._revert_handles[name]
                traps.activate_trap(self.pine, name)
                self.assertTrue(first.cancelled())
                self.assertEqual(traps._active_deadlines[name], deadline + 20)
                # Invoke expiry without waiting for wall-clock time.
                timer = traps._revert_handles[name]
                callback = timer._callback
                timer.cancel()
                callback()
                self.assertNotIn(name, traps._active_deadlines)
                self.assertEqual(self.pine.read_int32(self.base + 0x5AC), self.objects[1])
                traps.activate_trap(self.pine, name)
                traps.close_no_clank_trap(self.pine)
                self.assertEqual(self.pine.read_int32(self.base + 0x5AC), self.objects[1])
        finally:
            traps.close_no_clank_trap(self.pine)
            loop.close()

    def test_pack_unlock_during_trap_waits_for_expiry(self):
        loop = asyncio.new_event_loop()
        try:
            traps.set_clank_pack_ownership(self.pine, enabled=True, owned=False)
            self.assertEqual(self.pine.read_int32(self.base + 0x5AC), 0)
            with patch.object(asyncio, "get_event_loop", return_value=loop):
                traps.activate_trap(self.pine, Rac5Traps.TRAP_NO_CLANK)
            traps.set_clank_pack_ownership(self.pine, enabled=True, owned=True)
            self.assertEqual(self.pine.read_int32(self.base + 0x5AC), 0)
            timer = traps._revert_handles[Rac5Traps.TRAP_NO_CLANK]
            callback = timer._callback
            timer.cancel()
            callback()
            self.assertEqual(self.pine.read_int32(self.base + 0x5AC), self.objects[1])
        finally:
            traps.close_no_clank_trap(self.pine)
            loop.close()

    def test_trap_expiry_does_not_grant_unowned_pack(self):
        loop = asyncio.new_event_loop()
        try:
            traps.set_clank_pack_ownership(self.pine, enabled=True, owned=False)
            with patch.object(asyncio, "get_event_loop", return_value=loop):
                traps.activate_trap(self.pine, Rac5Traps.TRAP_NO_CLANK)
            timer = traps._revert_handles[Rac5Traps.TRAP_NO_CLANK]
            callback = timer._callback
            timer.cancel()
            callback()
            self.assertEqual(self.pine.read_int32(self.base + 0x5AC), 0)
            # Disabling the option also returns the normal pack.
            traps.set_clank_pack_ownership(self.pine, enabled=False, owned=False)
            self.assertEqual(self.pine.read_int32(self.base + 0x5AC), self.objects[1])
        finally:
            traps.close_no_clank_trap(self.pine)
            loop.close()
