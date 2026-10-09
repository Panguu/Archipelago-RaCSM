import unittest
from types import SimpleNamespace

from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from Options import OptionError
from test.general import setup_multiworld

from ..constants.keycards import KEYCARD_BITS, KEYCARD_ITEMS
from ..constants.alien_codes import ALIEN_CODES_BY_MODULE
from ..constants.clank_gadgets import SACClankGadgets
from ..core.core import Core
from ..core.inventories.keycards import KeycardInventory
from ..core.inventories.alien_codes import AlienCodeInventory
from ..core.patches.asm import packed
from ..core.patches.keycard_hunt import KeycardHunt
from ..universal_tracker import setup_options_from_slot_data
from ..world import SecretAgentClankWorld
from .mips_cpu import CPU
from .test_runtime import Memory


class KeycardHuntTests(unittest.TestCase):
    def test_pool_checks_fill_and_tracker_round_trip(self):
        for hunt in (False, True):
            for checks in (False, True):
                with self.subTest(hunt=hunt, checks=checks):
                    mw = setup_multiworld(SecretAgentClankWorld, seed=12345, options={
                        "keycard_hunt": hunt, "keycards_and_alien_codes": checks,
                        "goal": "chalice_of_power"})
                    world = mw.worlds[1]
                    for name in KEYCARD_ITEMS:
                        self.assertEqual(sum(item.name == name for item in mw.itempool), int(hunt))
                    self.assertEqual(set(KEYCARD_BITS) & {loc.name for loc in mw.get_locations(1)},
                                     set(KEYCARD_BITS) if checks else set())
                    self.assertEqual(len(mw.itempool), len(mw.get_unfilled_locations(1)))
                    slot = world.fill_slot_data()
                    self.assertEqual(slot["keycard_hunt"], hunt)
                    mw.re_gen_passthrough = {world.game: slot}
                    world.options.keycard_hunt.value = not hunt
                    setup_options_from_slot_data(world)
                    self.assertEqual(bool(world.options.keycard_hunt), hunt)
                    distribute_items_restrictive(mw)
                    self.assertTrue(mw.fulfills_accessibility())
                    del slot["keycard_hunt"]
                    setup_options_from_slot_data(world)
                    self.assertFalse(world.options.keycard_hunt)

    def test_chalice_needs_received_cards_and_alien_code_access(self):
        mw = setup_multiworld(SecretAgentClankWorld, options={
            "keycard_hunt": True, "goal": "chalice_of_power"})
        world = mw.worlds[1]
        victory = next(loc for loc in mw.get_locations(1) if loc.name.startswith("Victory:"))
        state = CollectionState(mw)
        for name in KEYCARD_ITEMS:
            state.collect(world.create_item(name))
        self.assertFalse(victory.can_reach(state))
        state = mw.get_all_state(False)
        self.assertTrue(victory.can_reach(state))
        for name in (*KEYCARD_ITEMS, SACClankGadgets.THERM_OPTIC_SHADES):
            with self.subTest(missing=name):
                state.remove(world.create_item(name))
                self.assertFalse(victory.can_reach(state))
                state.collect(world.create_item(name))

    def test_hunt_lets_clank_alone_goal_on_the_chalice(self):
        # Shuffled cards replace the Gadgetbots and Qwark keycard pickups;
        # the Alien Codes and the Treehouse they open are all Clank's.
        options = {"goal": "chalice_of_power", "operatives": {"Clank": 1}}
        mw = setup_multiworld(SecretAgentClankWorld, seed=1, options={**options, "keycard_hunt": True})
        self.assertEqual([loc.name for loc in mw.get_locations(1) if loc.name.startswith("Victory:")],
                         ["Victory: Collect the Chalice of Power"])
        self.assertTrue(mw.get_all_state(False).can_reach(
            next(loc for loc in mw.get_locations(1) if loc.name.startswith("Victory:"))))
        with self.assertRaisesRegex(OptionError, "Inside the A-Eye"):
            setup_multiworld(SecretAgentClankWorld, seed=1, options={**options, "keycard_hunt": False})

    def test_receipts_never_complete_physical_checks(self):
        core = Core(Memory())
        cards = core.keycards
        cards.hunt.enabled = True
        values = {0xAA: b"\0", 0xCB: b"\0"}
        cards.flags.read = lambda index: values[index]
        core.apply_inventory(ratchet={}, clank={}, received_names=list(KEYCARD_ITEMS))
        self.assertTrue(cards.has_all)
        self.assertEqual(cards.check(), [])
        self.assertFalse(cards.chalice_collected)
        self.assertEqual(core.pine.writes, [])
        values[0xAA] = b"\7"
        self.assertEqual(set(cards.check()), set(KEYCARD_BITS))
        cards.sync_from_ap(set(KEYCARD_BITS))
        self.assertEqual(cards.check(), [])
        cards.hunt.receive([])
        self.assertFalse(cards.has_all, "Physical pickups must not bypass shuffled ownership")

    def test_native_reader_uses_ap_cards_without_touching_save_flags(self):
        p = Memory()
        getter, pointer, save, entry = 0x110000, 0x120000, 0x130000, 0x140000
        original = packed([0x3C020012, 0x30A500FF, 0x8C430000,
                           0x00641821, 0x906204E0, 0x03E00008, 0x00451024])
        p.data[getter:getter + len(original)] = original
        p.write_int32(pointer, save)
        p.data[save + 0x4E0 + 0xAA] = 2
        p.data[save + 0x4E0 + 0xCB] = 1
        p.write_int32(0x206328, 31)
        p.write_int32(0x206324, 0xFFFFFFFF)
        hunt = KeycardHunt(p)
        hunt.enabled = True
        hunt.receive(["Red Keycard", "Yellow Keycard", "Red Keycard"])
        hooks = SimpleNamespace(extra_ranges=[(entry, entry + 256)], patches=[], gain_storage_prepared=False)
        symbols = {"GLOBAL_GetFlag__FUiUc": getter}
        edits = hunt.prepare(symbols, hooks, 31)
        for edit in edits:
            p.data[edit.address:edit.address + len(edit.replacement)] = edit.replacement
        cards = KeycardInventory(p)
        cards.hunt = hunt
        cards.bind(symbols)
        self.assertEqual(set(cards.check()), {name for name, bit in KEYCARD_BITS.items() if bit == 1})
        # Alien-code access must remain readable after the getter is hooked.
        count_getter, counts = 0x150000, 0x160000
        code = packed([0x2484FFFF, 0x3C020016, 0x24420000,
                       0x00042080, 0x00822021, 0x03E00008, 0x8C820000])
        p.data[count_getter:count_getter + len(code)] = code
        for module, names in ALIEN_CODES_BY_MODULE.items():
            p.write_int32(counts + (module - 1) * 4, len(names))
        symbols["GLOBALVARS_GetTotalAlienCodeCount__FUi"] = count_getter
        aliens = AlienCodeInventory(p)
        self.assertTrue(aliens.bind(symbols, flag_pointer_address=hunt.pointer_address))
        p.data[save + 0x4E0 + 0x38:save + 0x4E0 + 0x38 + 15] = bytes([255] * 15)
        aliens.check()
        self.assertTrue(aliens.all_found)
        for flag, mask, expected in ((0xAA, 255, 5), (0xAA, 2, 0), (0xCB, 255, 1)):
            cpu = CPU(p)
            cpu.r[4], cpu.r[5] = flag, mask
            cpu.run(getter)
            self.assertEqual(cpu.r[2], expected)
        hunt.receive(list(KEYCARD_ITEMS))
        hunt.sync()
        cpu = CPU(p)
        cpu.r[4], cpu.r[5] = 0xAA, 7
        cpu.run(getter)
        self.assertEqual(cpu.r[2], 7)
        self.assertEqual(p.read_int8(save + 0x4E0 + 0xAA), 2)
        self.assertEqual(hunt.prepare({}, hooks, 4), [])
        self.assertIsNone(hunt.table)

    def test_unrecognized_getter_and_stale_patch_fail_without_writes(self):
        p = Memory()
        hunt = KeycardHunt(p)
        hunt.enabled = True
        hooks = SimpleNamespace(extra_ranges=[], patches=[], gain_storage_prepared=False)
        with self.assertRaisesRegex(RuntimeError, "getter layout changed"):
            hunt.prepare({"GLOBAL_GetFlag__FUiUc": 0x110000}, hooks, 31)
        self.assertEqual(p.writes, [])
        hunt.entry, hunt.table, hunt.code = 0x110000, 0x120000, b"changed"
        p.write_int32(0x206328, 31)
        p.write_int32(0x206324, 0xFFFFFFFF)
        p.writes.clear()
        with self.assertRaisesRegex(RuntimeError, "code changed"):
            hunt.sync()
        self.assertEqual(p.writes, [])
