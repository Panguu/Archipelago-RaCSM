import struct
import unittest
from pathlib import Path

from test.general import gen_steps, setup_multiworld
from worlds.AutoWorld import call_all

from ..constants import ALL_CASES, CASE_NAME_TO_INFOBOT
from ..constants.native_modules import CASE_MODULES
from ..core.patches import jump, packed
from ..core.patches.starting_case import StartingCase
from ..world import SecretAgentClankWorld
from .test_runtime import Memory


class FrontendMemory(Memory):
    def __init__(self):
        super().__init__()
        self.data[0x3652C0:0x3652D8] = StartingCase.FRONT_SIGNATURE
        for address, words in zip(StartingCase.STUBS, StartingCase.STUB_WORDS):
            self.data[address:address + len(words) * 4] = packed(words)
        for address in StartingCase.CALLS:
            self.data[address:address + 8] = packed([jump(StartingCase.INIT, True), 0x24050001])
        for address in StartingCase.TRAVEL_CALLS:
            self.data[address - 4:address + 8] = packed([
                0x24040001, jump(StartingCase.CHANGE_LEVEL, True), 0x24050001])
        self.batch_write_int32([(0x1AAE78, 0), (0x1AAE3C, 5),
                                (0x206324, 0xFFFFFFFF), (0x42DE34, 12)])
        self.writes.clear()

    def get_game_id(self):
        return "SCUS-97623"

    def write_bytes(self, address, data):
        self.writes.append((address, data))
        self.data[address:address + len(data)] = data


class StartingCaseTests(unittest.TestCase):
    def test_tracker_restores_saved_start_instead_of_rerolling(self):
        original = setup_multiworld(SecretAgentClankWorld, seed=812)
        saved = original.worlds[1].fill_slot_data()
        restored = setup_multiworld(SecretAgentClankWorld, seed=456, steps=())
        restored.re_gen_passthrough = {SecretAgentClankWorld.game: saved}
        for step in gen_steps:
            call_all(restored, step)
        self.assertEqual(restored.worlds[1].starting_case, saved["starting_case"])
        self.assertIn(CASE_NAME_TO_INFOBOT[saved["starting_case"]],
                      [item.name for item in restored.precollected_items[1]])

    def test_random_start_respects_characters_and_access_in_every_mode(self):
        observed = set()
        for mode in ("cases", "planets", "progressive_planet", "character_unlocks"):
            for seed in range(8):
                mw = setup_multiworld(SecretAgentClankWorld, seed=seed, options={
                    "operatives": {"Ratchet": 1, "Qwark": 1, "Gadgetbots": 1},
                    "goal": "qwark_opera", "infobots": mode, "all_missions": "all"})
                world = mw.worlds[1]
                name = world.starting_case
                observed.add(name)
                case = next(case for case in ALL_CASES if case.name == name)
                self.assertIn(case.operative, ("Ratchet", "Qwark", "Gadgetbots"))
                self.assertIn(CASE_NAME_TO_INFOBOT[name], [i.name for i in mw.precollected_items[1]])
                self.assertTrue(mw.state.can_reach(name, "Region", 1))
                self.assertEqual(world.fill_slot_data()["starting_case"], name)
        self.assertGreater(len(observed), 1)

    def test_install_idempotent_restore_and_disabled_validation(self):
        p = FrontendMemory()
        before = bytes(p.data)
        hook = StartingCase(p, lambda _: None)
        with self.assertRaises(ValueError):
            hook.configure({"starting_case": "Boltaire Museum", "operatives": {"Qwark": 1}})
        hook.configure({"starting_case": "Suck and Jive", "operatives": {"Qwark": 1}})
        self.assertTrue(hook.service())
        writes = list(p.writes)
        hook.service()
        self.assertEqual(p.writes, writes)
        hook.close()
        self.assertEqual(bytes(p.data), before)

    def test_unknown_layout_is_rejected_before_any_write(self):
        p = FrontendMemory()
        p.data[StartingCase.CALLS[1]] ^= 1
        hook = StartingCase(p, lambda _: None)
        hook.configure({"starting_case": "Max-Security Cells", "operatives": {"Ratchet": 1}})
        with self.assertRaises(RuntimeError):
            hook.service()
        self.assertEqual(p.writes, [])

    def test_no_patch_for_legacy_slots_or_gameplay(self):
        p = FrontendMemory()
        hook = StartingCase(p, lambda _: None)
        hook.configure({})
        hook.service()
        self.assertEqual(p.writes, [])
        hook.configure({"starting_case": "Max-Security Cells", "operatives": {"Ratchet": 1}})
        p.batch_write_int32([(0x1AAE78, 3)])
        p.writes.clear()
        self.assertFalse(hook.service())
        self.assertEqual(p.writes, [])

    def test_unloaded_frontend_is_never_restored_over_gameplay(self):
        p = FrontendMemory()
        hook = StartingCase(p, lambda _: None)
        hook.configure({"starting_case": "Max-Security Cells", "operatives": {"Ratchet": 1}})
        hook.service()
        p.batch_write_int32([(0x1AAE78, 3)])
        p.writes.clear()
        hook.close()
        self.assertEqual(p.writes, [])

    def test_load_game_call_is_preserved(self):
        p = FrontendMemory()
        load = 0x349FD8
        expected = packed([jump(StartingCase.CHANGE_LEVEL, True), 0x8C440ECC])
        p.data[load:load + 8] = expected
        hook = StartingCase(p, lambda _: None)
        hook.configure({"starting_case": "Max-Security Cells", "operatives": {"Ratchet": 1}})
        hook.service()
        self.assertEqual(p.read_bytes(load, 8), expected)

    def test_wrapper_executes_init_then_sets_destination_and_shared_flags(self):
        # Execute the emitted instructions with real branch delay semantics.
        # Model the native initializer as a call that clobbers caller registers.
        for name, flags in [("Max-Security Cells", (0, 0)),
                            ("Asyanica Rooftops", (1, 0)),
                            ("Rooftop Deathtrap", (0, 0)),
                            ("Suck and Jive", (0, 1)), ("Gondola Ascent", (0, 0))]:
            p = FrontendMemory()
            hook = StartingCase(p, lambda _: None)
            for edit in hook.prepare(name):
                p.write_bytes(edit.address, edit.replacement)
            for caller in hook.CALLS + hook.TRAVEL_CALLS:
                regs = [0] * 32
                regs[4], regs[29] = 0x200000, 0x700000
                struct.pack_into("<I", p.data, 0x418FD8, 0x200000)
                pc, pending, native_calls = caller, None, 0
                for _ in range(40):
                    if pc == caller + 8:
                        break
                    if pc == hook.INIT:
                        self.assertEqual((regs[4], regs[5]), (0x200000, 1))
                        native_calls += 1
                        regs[4] = regs[8] = 0xBAD
                        pc = regs[31]
                        continue
                    if pc == hook.CHANGE_LEVEL:
                        self.assertEqual((regs[4], regs[5]), (CASE_MODULES[name], 1))
                        native_calls += 1
                        pc = regs[31]
                        continue
                    word = p.read_int32(pc)
                    op, rs, rt = word >> 26, (word >> 21) & 31, (word >> 16) & 31
                    imm = word & 65535
                    imm -= 65536 if imm & 32768 else 0
                    destination, pending = pending, None
                    address = (regs[rs] + imm) & 0xFFFFFFFF
                    if op == 9:
                        regs[rt] = address
                    elif op == 15:
                        regs[rt] = (word & 65535) << 16
                    elif op == 35:
                        regs[rt] = p.read_int32(address)
                    elif op in (2, 3):
                        if op == 3:
                            regs[31] = pc + 8
                        pending = (word & 0x3FFFFFF) << 2
                    elif word & 63 == 8 and op == 0:
                        pending = regs[rs]
                    elif op == 63:
                        struct.pack_into("<Q", p.data, address, regs[rt])
                    elif op == 55:
                        regs[rt] = struct.unpack_from("<Q", p.data, address)[0]
                    elif op == 43:
                        struct.pack_into("<I", p.data, address, regs[rt])
                    elif op == 40:
                        p.data[address] = regs[rt] & 255
                    else:
                        self.assertEqual(word, 0)
                    pc = destination if destination is not None else pc + 4
                self.assertEqual(pc, caller + 8)
                self.assertEqual(native_calls, 1)
                self.assertEqual(regs[29], 0x700000)
                self.assertEqual(p.read_int32(0x200ECC), CASE_MODULES[name])
                self.assertEqual((p.read_int8(0x200589), p.read_int8(0x2005A8)), flags)
                self.assertEqual(p.read_int8(0x2005AA), 1)

    def test_plan_matches_real_frontend_capture(self):
        path = Path(__file__).parents[1] / ".research/main_menu_start.bin"
        if not path.exists():
            self.skipTest("Local frontend capture unavailable")
        p = FrontendMemory()
        p.data[:] = path.read_bytes()
        hook = StartingCase(p, lambda _: None)
        self.assertTrue(hook.is_frontend())
        self.assertEqual(len(hook.prepare("Max-Security Cells")), 9)
