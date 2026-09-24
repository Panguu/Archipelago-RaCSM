import unittest

from ..core.patches import (
    MARKER,
    PICKUP_LOCATIONS,
    VENDOR_LOCATIONS,
    Entitlements,
    GameFlags,
    LocationHooks,
    jump,
    words,
)
from .test_runtime import Memory


def run_routine(code, gadget, flag):
    """Execute the emitted MIPS subset, including validation of delay slots."""
    program = words(code)
    registers = [0] * 32
    registers[4:7] = [gadget, 1, 1]
    registers[31] = 0x700000
    memory = {0x180000 + gadget: flag}
    pc = 0
    for _ in range(40):
        instruction = program[pc]
        op, rs, rt = instruction >> 26, (instruction >> 21) & 31, (instruction >> 16) & 31
        imm = instruction & 0xFFFF
        signed = imm - 0x10000 if imm & 0x8000 else imm
        next_pc = pc + 1
        if op == 11:
            registers[rt] = int(registers[rs] < imm)
        elif op == 4:
            self_delay = program[pc + 1]
            assert self_delay == 0
            next_pc = pc + 1 + signed if registers[rs] == registers[rt] else pc + 2
        elif op == 15:
            registers[rt] = imm << 16
        elif op == 13:
            registers[rt] = registers[rs] | imm
        elif op == 9:
            registers[rt] = (registers[rs] + signed) & 0xFFFFFFFF
        elif op == 36:
            registers[rt] = memory[registers[rs] + signed]
        elif op == 40:
            memory[registers[rs] + signed] = registers[rt] & 255
        elif op == 0 and instruction & 63 == 33:
            registers[(instruction >> 11) & 31] = registers[rs] + registers[rt]
        elif op == 2 or (op == 0 and instruction & 63 == 8):
            assert program[pc + 1] == 0
            target = (instruction & 0x03FFFFFF) << 2 if op == 2 else registers[rs]
            return target, registers, memory
        else:
            raise AssertionError(f"Unexpected instruction {instruction:08x}")
        registers[0] = 0
        pc = next_pc
    raise AssertionError("Routine did not return")


class LocationHookTests(unittest.TestCase):
    def test_partial_installation_rolls_back_before_returning_failure(self):
        from ..core.patches import Patch
        mem = Memory()
        calls = []

        def write(address, data):
            calls.append(address)
            mem.data[address:address + len(data)] = data
            if len(calls) == 2:
                raise OSError("Simulated transport failure after write")

        mem.write_bytes = write
        hooks = LocationHooks(mem)
        hooks.patches = [Patch(0x100, b"AAAA", b"aaaa"), Patch(0x104, b"BBBB", b"bbbb")]
        mem.data[0x100:0x108] = b"AAAABBBB"
        with self.assertRaises(OSError):
            hooks._install_plan()
        self.assertEqual(mem.read_bytes(0x100, 8), b"AAAABBBB")
        self.assertFalse(hooks.installed)

    def test_preinit_entitlements_preserve_unmanaged_slots_and_return_address(self):
        program = words(Entitlements._build_routine(0x180000, 0x200000, 0x350000))
        regs = [0] * 32
        regs[31] = 0x123456
        mem = Memory()
        for slot in range(40):
            mem.data[0x180000 + slot] = {0: 1, 11: 2, 39: 2}.get(slot, 0)
            mem.batch_write_int32([(0x200070 + slot * 0x74, 7)])

        def simple(inst):
            op, rs, rt = inst >> 26, (inst >> 21) & 31, (inst >> 16) & 31
            imm = inst & 0xFFFF
            signed = imm - 0x10000 if imm & 0x8000 else imm
            if inst == 0:
                return
            if op == 15:
                regs[rt] = imm << 16
            elif op == 13:
                regs[rt] = regs[rs] | imm
            elif op == 9:
                regs[rt] = (regs[rs] + signed) & 0xFFFFFFFF
            elif op == 36:
                regs[rt] = mem.read_int8(regs[rs] + signed)
            elif op == 40:
                mem.data[regs[rs] + signed] = regs[rt] & 255
            elif op == 43:
                mem.batch_write_int32([(regs[rs] + signed, regs[rt])])
            else:
                self.fail(f"Unexpected MIPS instruction {inst:08x}")

        pc = 0
        for _ in range(400):
            inst = program[pc]
            op = inst >> 26
            if op in (4, 5):
                rs, rt = (inst >> 21) & 31, (inst >> 16) & 31
                taken = (regs[rs] == regs[rt]) == (op == 4)
                imm = inst & 0xFFFF
                signed = imm - 0x10000 if imm & 0x8000 else imm
                simple(program[pc + 1])
                pc = pc + 1 + signed if taken else pc + 2
            elif op == 2:
                simple(program[pc + 1])
                self.assertEqual((inst & 0x03FFFFFF) << 2, 0x350000)
                break
            else:
                simple(inst)
                pc += 1
        else:
            self.fail("Pre-init routine did not terminate")
        self.assertEqual(regs[31], 0x123456)
        self.assertEqual(mem.read_int8(0x180028), 1)
        for slot in range(40):
            self.assertEqual(mem.read_int32(0x200070 + slot * 0x74),
                             {0: 0, 11: 1, 39: 1}.get(slot, 7))

    def test_hook_locations_exist_and_sources_do_not_overlap(self):
        from ..constants.weapons import EQUIPMENT_INTERNAL_TO_DISPLAY
        from ..locations import ALL_LOCATIONS
        # PICKUP_LOCATIONS/VENDOR_LOCATIONS are raw WEAPON_ORDER internal
        # names (e.g. "throwTie"), not AP display names -- translate the
        # same way core.py's _read_native_locations()/poll_purchases()
        # loops do before comparing against real location names. Names
        # already in display form (e.g. "Black Out Pen (Pickup)") aren't in
        # the dict and pass through unchanged.
        self.assertFalse(set(PICKUP_LOCATIONS) & set(VENDOR_LOCATIONS))
        pickup_names = {EQUIPMENT_INTERNAL_TO_DISPLAY.get(n, n) for n in PICKUP_LOCATIONS.values()}
        vendor_names = {EQUIPMENT_INTERNAL_TO_DISPLAY.get(n, n) for n in VENDOR_LOCATIONS.values()}
        self.assertTrue(pickup_names <= set(ALL_LOCATIONS))
        self.assertTrue(vendor_names <= set(ALL_LOCATIONS))

    def test_code_and_marker_are_word_aligned(self):
        self.assertEqual(len(MARKER), 16)
        for record in (False, True):
            self.assertEqual(len(GameFlags._build_routine(0x180000, 0x350000, record=record)) % 4, 0)
        with self.assertRaises(ValueError):
            jump(0x350001)

    def test_managed_getter_uses_location_flag(self):
        for flag, expected in ((1, 0), (2, 1)):
            target, regs, memory = run_routine(GameFlags._build_routine(0x180000, 0x350000, record=False), 17, flag)
            self.assertEqual((target, regs[2]), (0x700000, expected))
            self.assertEqual(memory, {0x180011: flag})

    def test_native_grant_latches_location_and_preserves_arguments(self):
        target, regs, memory = run_routine(GameFlags._build_routine(0x180000, 0x350000, record=True), 26, 1)
        self.assertEqual(target, 0x700000)
        self.assertEqual(regs[4:7], [26, 1, 1])
        self.assertEqual(memory, {0x18001A: 2})

    def test_unmanaged_and_out_of_range_ids_use_original_function(self):
        for record in (False, True):
            for gadget, flag in ((17, 0), (40, 1), (0xFFFFFFFF, 1)):
                target, regs, _ = run_routine(GameFlags._build_routine(0x180000, 0x350000, record=record), gadget, flag)
                self.assertEqual(target, 0x350000)
                self.assertEqual(regs[4:7], [gadget, 1, 1])

    def test_poll_separates_vendor_and_pickup_and_deduplicates(self):
        memory = Memory()
        hooks = LocationHooks(memory)
        hooks.installed = True
        hooks.module = 0
        hooks.marker_address = 0x110000
        memory.data[0x110000:0x110010] = MARKER
        hooks.tables = {"pickup": 0x120000, "vendor": 0x120028}
        hooks.locations = {"pickup": {17: "pen pickup"}, "vendor": {26: "PDA purchase"}}
        memory.data[0x120011] = 1
        memory.data[0x120042] = 2
        self.assertEqual(hooks.poll(), ["PDA purchase"])
        self.assertEqual(hooks.poll(), [])
        memory.data[0x120011] = 2
        self.assertEqual(hooks.poll(), ["pen pickup"])
        memory.data[0x110000] = 0
        self.assertEqual(hooks.poll(), [])
        self.assertFalse(hooks.installed)

    def test_same_module_reload_requires_rebinding_before_inventory(self):
        from unittest.mock import Mock

        from ..core.core import Core
        memory = Memory()
        core = Core(memory)
        hooks = core.location_hooks
        hooks.module = 0
        hooks.marker_address = 0x110000
        hooks.installed = True
        core.case.case_menu.screen_address = 0x100000
        hooks.sync_checked = Mock()
        self.assertFalse(core._bind_native_locations())
        self.assertFalse(hooks.installed)
        hooks.sync_checked.assert_not_called()
        self.assertEqual(memory.writes, [])

    def test_core_sends_native_checks_once_without_granting_items(self):
        from unittest.mock import Mock

        from ..core.core import Core
        memory = Memory()
        core = Core(memory)
        core.location_hooks.poll = Mock(return_value=["clankpda", "throwTie"])
        core.send_location = Mock()
        core._read_native_locations()
        core._read_native_locations()
        self.assertEqual(core.send_location.call_count, 2)
        self.assertEqual(memory.writes, [])
