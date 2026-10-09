import struct
import unittest
from pathlib import Path

from ..core.patches import jump, packed
from ..core.patches.mission_travel import MissionTravel
from ..core.symbols import RuntimeSymbols
from .test_runtime import Memory


class MissionTravelTests(unittest.TestCase):
    def test_story_bypasses_in_captured_modules(self):
        captures = list((Path(__file__).parents[1] / '.research').glob('*.ram'))
        verified = 0
        for capture in captures:
            p = Memory()
            p.data[:] = capture.read_bytes()
            symbols = RuntimeSymbols.parse(p.data[:0x1000000], 0)
            helper = symbols.get('UPDATE_ChangeToLevelOrMapIfAlreadyCompleted__Fi')
            if helper is None:
                continue
            with self.subTest(capture=capture.name):
                change = symbols['UPDATE_ChangeToLevel__Fib']
                travel = MissionTravel(p)
                edits = travel._prepare_story_routes(symbols, helper, change)
                expected = {
                    symbols['SCRNGADGETBOTARENA_Update__Fv'] + 0x130,
                    symbols['SCRNVEHICLECHALLENGES_Update__Fv'] + 0x218,
                    symbols['SCRNVEHICLECHALLENGES_Exit__Fv'] + 0xA4,
                    symbols['SCRNGALACTICMAP_Level5MovieHackFinishedCallback__FPv'] + 12,
                }
                self.assertEqual({edit.address for edit in edits}, expected)
                for edit in edits:
                    self.assertEqual(p.read_bytes(edit.address, 4), edit.original)
                    self.assertEqual(edit.original, packed([jump(change, True)]))
                    self.assertEqual(edit.replacement, packed([jump(helper, True)]))
                # A changed native layout must not be accepted as this route.
                p.write_int32(edits[0].address, 0)
                with self.assertRaisesRegex(RuntimeError, 'Story Continue travel'):
                    travel._prepare_story_routes(symbols, helper, change)
                verified += 1
        if not verified:
            self.skipTest('Local gameplay captures unavailable')

    def test_completion_reloads_current_module_for_both_arena_exits(self):
        p = Memory()
        f, ender = 0x110000, 0x120000
        p.data[f:f+12] = packed([0x27BDFFF0, 0xFFB00000, 0xFFBF0008])
        p.data[f+0x14:f+0x24] = packed([0x0050102B, 0x14400010, 0x0200202D, jump(ender, True)])
        p.batch_write_int32([(f+0x34, 0x2404000E)])
        update, exit_screen, next_level, set_next, change = (
            0x130000, 0x140000, 0x150000, 0x160000, 0x170000)
        callback = exit_screen + 0x38
        p.data[update+0x188:update+0x198] = packed([
            jump(next_level, True), 0, 0x10000014, 0x0040202D])
        p.batch_write_int32([(update+0x228, 0x1240000B),
            (update+0x158, 0x3C060000 | ((callback+0x8000) >> 16)),
            (update+0x160, 0x24C60000 | (callback & 65535))])
        p.data[callback:callback+24] = packed([
            0x27BDFFF0, 0xFFBF0000, jump(next_level, True), 0,
            jump(set_next, True), 0x0040202D])
        p.batch_write_int32([(callback+0x20, jump(change, True))])
        p.data[callback+0x28:callback+0x34] = packed([
            0xDFBF0000, 0x03E00008, 0x27BD0010])
        symbols = {"UPDATE_ChangeToLevelOrMapIfAlreadyCompleted__Fi": f,
                   "SCRNGALACTICMAP_SetLevelEnder__Fv": ender,
                   "SCRNRATCHETARENA_Update__Fv": update,
                   "SCRNRATCHETARENA_Exit__Fv": exit_screen,
                   "Arena_GetLevelToLoad__Fv": next_level,
                   "SetNextLevel__Fi": set_next,
                   "UPDATE_ChangeToLevel__Fib": change}
        changes = MissionTravel(p).prepare(symbols)
        self.assertEqual(len(changes), 3)
        self.assertEqual(changes[0].address, f)
        self.assertEqual(changes[0].replacement, packed([
            0x3C040020, 0x8C846328, jump(change), 0x24050001]))
        # This loads a0 from CURRENT_CASE_ADDRESS, ignoring the caller's
        # next-story-module argument. a1 requests a native reload, and the
        # tail jump preserves the caller's return address and stack.
        for module in (1, 3, 4, 11, 16, 31):
            p.batch_write_int32([(0x206328, module), (0x206324, 29)])
            words = struct.unpack('<4I', changes[0].replacement)
            address = ((words[0] & 65535) << 16) + (words[1] & 65535)
            self.assertEqual(p.read_int32(address), module)
        # The direct Continue path calls the reload helper then skips the
        # challenge/quit handlers. The movie callback uses the same helper.
        direct = struct.unpack("<4I", changes[1].replacement)
        self.assertEqual(direct[:2], (jump(f, True), 0))
        self.assertEqual(update+0x194+(direct[2] & 65535)*4, update+0x228)
        self.assertEqual(changes[2].replacement, packed([jump(f, True)]))
        self.assertFalse(any(c.address == change for c in changes))
        p.batch_write_int32([(f+0x18, 0xFFFFFFFF)])
        with self.assertRaises(RuntimeError):
            MissionTravel(p).prepare(symbols)
