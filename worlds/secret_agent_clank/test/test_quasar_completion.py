import unittest
from pathlib import Path
from unittest.mock import Mock

from ..constants.cutscenes import CUTSCENE_FLAGS, SACCutsceneLocations
from ..constants.missions import CHAPTER_ENTRIES, MISSION_COMPLETE_NAME
from ..constants.planets import SACCases, CASE_NAME_TO_CASE
from ..core.core import Core
from ..core.patches.mission_travel import MissionTravel
from ..core.symbols import RuntimeSymbols
from .test_runtime import Memory


class QuasarCompletionTests(unittest.TestCase):
    CASE_NAME = SACCases.THE_QUASAR_FIELDS
    MODULE = 24
    NEXT_INTRO = SACCutsceneLocations.PRISON_BREAKOUT_ENTER_CUTSCENE

    def test_next_intro_does_not_report_previous_case_completion(self):
        for all_missions in (False, True):
            with self.subTest(all_missions=all_missions):
                p = Memory()
                core = Core(p)
                case = CASE_NAME_TO_CASE[self.CASE_NAME]
                entry = CHAPTER_ENTRIES[case.name][0]
                inv = core.missions
                inv._resolved_cases = {case.name: [0x12000C]}
                inv._resolved_title_ids = {case.name: [entry.title_id]}
                inv._story_addresses = {case.name: [0x12000C]}
                intro = self.NEXT_INTRO
                flag = CUTSCENE_FLAGS[intro]
                p.data[flag.address] = flag.mask
                # Retail derives this task state from the next case's intro.
                p.write_int32(0x12000C, 3)
                p.writes.clear()
                self.assertIn(intro, core.cutscenes.check())
                self.assertEqual(inv.check_all(all_missions=all_missions), [])
                self.assertFalse(inv.completed[entry.name])
                self.assertEqual(p.writes, [])

    def test_finish_is_captured_before_reload_and_restored_afterward(self):
        for all_missions in (False, True):
            with self.subTest(all_missions=all_missions):
                p = Memory()
                core = Core(p)
                core.missions_all = lambda: all_missions
                sent = []
                core.send_location = lambda name: sent.append(name) or True
                runtime = core.native_runtime
                runtime.starting_case = Mock()
                runtime.starting_case.service.return_value = False
                runtime.gate = Mock(armed=True, STATE=0x100)
                runtime.gate.held_module.return_value = None
                runtime.hooks = Mock(installed=True, module=self.MODULE, entitlement_table=None)
                runtime.hooks.is_current.return_value = True
                runtime.mission_travel = Mock(completion_mailbox=0x110000)
                runtime.connection_warning = Mock()
                p.batch_write_int32([(0x206328, self.MODULE), (0x206324, 0xFFFFFFFF),
                                     (0x206338, 3), (0x100, 5), (0x110000, 1)])
                case = CASE_NAME_TO_CASE[self.CASE_NAME]
                entry = CHAPTER_ENTRIES[case.name][0]
                expected = entry.name if all_missions else MISSION_COMPLETE_NAME[case.name]
                original_write = p.write_int32
                def write(address, value):
                    if address == 0x206324:
                        self.assertEqual(sent, [expected])
                    original_write(address, value)
                p.write_int32 = write
                self.assertFalse(runtime.service(set(), {}))
                self.assertEqual(p.read_int32(0x206324), self.MODULE)
                inv = core.missions
                inv._resolved_cases = {case.name: [0x12000C]}
                inv._resolved_title_ids = {case.name: [entry.title_id]}
                p.data[0x12000C] = 2
                self.assertEqual(inv.check(case, all_missions=all_missions), [])
                self.assertEqual(p.read_int32(0x12000C), 3)
                self.assertEqual(p.read_int8(CUTSCENE_FLAGS[self.NEXT_INTRO].address), 0)

    def test_server_check_restores_completion_on_reconnect(self):
        p = Memory()
        inv = Core(p).missions
        case = CASE_NAME_TO_CASE[self.CASE_NAME]
        entry = CHAPTER_ENTRIES[case.name][0]
        inv._resolved_cases = {case.name: [0x12000C]}
        inv._resolved_title_ids = {case.name: [entry.title_id]}
        inv.sync_from_ap({MISSION_COMPLETE_NAME[case.name]})
        inv.check(case, all_missions=False)
        self.assertEqual(p.read_int32(0x12000C), 3)
        self.assertEqual(p.read_int8(CUTSCENE_FLAGS[self.NEXT_INTRO].address), 0)

    def test_hook_records_finish_without_requesting_travel(self):
        capture = Path(__file__).parents[1] / '.research/SAC.p2s.ram'
        if not capture.exists():
            self.skipTest('Local clean capture unavailable')
        p = Memory()
        p.data[:] = capture.read_bytes()
        symbols = RuntimeSymbols.parse(p.data[:0x1000000], 0)
        travel = MissionTravel(p)
        changes = travel.prepare(symbols, module=self.MODULE)
        for change in changes:
            p.data[change.address:change.address + len(change.replacement)] = change.replacement
        # Execute the short MIPS receipt routine, including its return delay slot.
        registers = [0] * 32
        registers[31] = 0x123456
        pc = changes[0].address
        target = None
        for _ in range(6):
            word = p.read_int32(pc)
            op, rs, rt, imm = word >> 26, word >> 21 & 31, word >> 16 & 31, word & 65535
            if op == 15:
                registers[rt] = imm << 16
            elif op == 13:
                registers[rt] = registers[rs] | imm
            elif op == 9:
                registers[rt] = registers[rs] + (imm if imm < 32768 else imm - 65536)
            elif op == 43:
                p.write_int32(registers[rs] + imm, registers[rt])
            elif op == 0 and word & 63 == 8:
                target = registers[rs]
            else:
                self.fail(f'Unexpected instruction {word:#x}')
            pc += 4
        self.assertEqual(target, 0x123456)
        self.assertEqual(registers[2], 1)
        self.assertEqual(p.read_int32(travel.completion_mailbox), 1)
        self.assertEqual(p.writes, [(travel.completion_mailbox, 1)])

    def test_rejected_check_is_retained_for_retry(self):
        core = Core(Memory())
        core.send_location = Mock(return_value=False)
        core.missions_all = lambda: True
        core._record_mission_completion(self.CASE_NAME)
        case = CASE_NAME_TO_CASE[self.CASE_NAME]
        core.missions._resolved_cases = {}
        self.assertEqual(core.missions.check_all(all_missions=True), [CHAPTER_ENTRIES[case.name][0].name])


class UnderwaterCompletionTests(QuasarCompletionTests):
    CASE_NAME = SACCases.UNDERWATER_BUNKER
    MODULE = 29
    NEXT_INTRO = SACCutsceneLocations.KLUNKS_LAIR_ENTERE_CUTSCENE
