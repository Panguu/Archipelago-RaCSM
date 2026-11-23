import struct
import unittest

from ..core.patches.loader_state import LoaderStateReader, StartupBarrierLost
from ..core.patches.iso_startup_barrier import (
    LEASE, ROUTINE_SIZE, ISOStartupBarrier, find_routine_space, patch_resident_loader, routine_code, site_code)
from .test_runtime import Memory

ROUTINE = 0x1C0000
WAIT = 0x103D74      # where the original code branches while the level isn't ready
PROCEED = 0x103BC8   # the instruction after that branch: the level starts


def run_loader_check(memory) -> str:
    """Execute the loader site (and our routine) until it either waits or proceeds."""
    regs = [0] * 32
    pc, delayed = LoaderStateReader.SIGNATURE_START, None

    def sext(value):
        return value - 0x10000 if value & 0x8000 else value

    for _ in range(64):
        if pc in (WAIT, PROCEED) and delayed is None:  # a branch's delay slot still runs first
            return "wait" if pc == WAIT else "proceed"
        word = memory.read_int32(pc)
        op, rs, rt, imm = word >> 26, (word >> 21) & 31, (word >> 16) & 31, word & 0xFFFF
        rd, funct = (word >> 11) & 31, word & 63
        next_pc, jump_to = pc + 4, None
        if op == 0x0F:                                    # lui
            regs[rt] = (imm << 16) & 0xFFFFFFFF
        elif op == 0x23:                                  # lw
            regs[rt] = memory.read_int32((regs[rs] + sext(imm)) & 0xFFFFFFFF)
        elif op == 0x2B:                                  # sw
            struct.pack_into("<I", memory.data, (regs[rs] + sext(imm)) & 0xFFFFFFFF, regs[rt])
        elif op == 0x09:                                  # addiu
            regs[rt] = (regs[rs] + sext(imm)) & 0xFFFFFFFF
        elif op in (0x04, 0x05):                          # beq, bne
            if (regs[rs] == regs[rt]) == (op == 0x04):
                jump_to = pc + 4 + sext(imm) * 4
        elif op == 0x02:                                  # j
            jump_to = (pc & 0xF0000000) | ((word & 0x3FFFFFF) << 2)
        elif op == 0 and funct == 0x2B:                   # sltu
            regs[rd] = int(regs[rs] < regs[rt])
        elif op == 0 and funct == 0x23:                   # subu
            regs[rd] = (regs[rs] - regs[rt]) & 0xFFFFFFFF
        elif word != 0:
            raise AssertionError(f"Unexpected instruction {word:#010x} at {pc:#x}")
        regs[0] = 0
        if delayed is not None:
            next_pc, delayed = delayed, None
        if jump_to is not None:
            delayed = jump_to
        pc = next_pc
    raise AssertionError("Loader check did not finish")


class TestPermanentGate(unittest.TestCase):
    def memory(self):
        memory = Memory()
        memory.get_game_id = lambda: "SCUS-97623"
        memory.write_bytes(LoaderStateReader.SIGNATURE_START, site_code(ROUTINE))
        memory.write_bytes(ROUTINE, routine_code(ROUTINE))
        for address, value in ((LoaderStateReader.STATE, 4), (LoaderStateReader.STATUS, 1),
                               (LoaderStateReader.TARGET, 3), (LoaderStateReader.HANDLE, 0x328B00),
                               (ISOStartupBarrier.REQUEST, 3)):
            struct.pack_into("<I", memory.data, address, value)
        memory.writes.clear()
        return memory

    def test_loader_only_waits_for_a_client_that_armed_it(self):
        cases = (
            # lease, relocation status, REQUEST -> result
            (0, 0xFFFFFFFF, 3, "wait"),             # unpatched behaviour: not relocated yet
            (0, 1, 3, "proceed"),                   # no client: loads like the unpatched game
            (LEASE, 1, 3, "wait"),                  # client armed: held until it releases
            (LEASE, 1, 0xFFFFFFFF, "proceed"),      # client released
        )
        for lease, status, request, expected in cases:
            with self.subTest(lease=lease, status=status, request=request):
                memory = self.memory()
                struct.pack_into("<I", memory.data, LoaderStateReader.STATUS, status)
                struct.pack_into("<I", memory.data, ISOStartupBarrier.REQUEST, request)
                struct.pack_into("<I", memory.data, ROUTINE + ROUTINE_SIZE - 4, lease)
                self.assertEqual(run_loader_check(memory), expected)

    def test_crashed_client_only_holds_the_load_until_its_lease_runs_out(self):
        memory = self.memory()
        gate = ISOStartupBarrier(memory, ROUTINE)
        gate.attach()  # then the client dies without disconnecting
        for _ in range(LEASE):
            self.assertEqual(run_loader_check(memory), "wait")
        self.assertEqual(memory.read_int32(gate.arm_address), 0)
        self.assertEqual(run_loader_check(memory), "proceed")

    def test_a_live_client_keeps_the_load_held(self):
        memory = self.memory()
        gate = ISOStartupBarrier(memory, ROUTINE)
        for _ in range(3):
            gate.attach()  # each poll renews the lease
            for _ in range(LEASE - 1):
                self.assertEqual(run_loader_check(memory), "wait")
        self.assertEqual(run_loader_check(memory), "wait")

    def test_attach_release_detach_write_only_data(self):
        memory = self.memory()
        gate = ISOStartupBarrier(memory, ROUTINE)
        gate.attach()
        gate.attach()
        self.assertIsNone(gate.held_module(settled=True))
        self.assertEqual(gate.held_module(settled=True), 3)
        gate.release()
        gate.detach()
        self.assertEqual(memory.writes, [(gate.arm_address, LEASE), (gate.arm_address, LEASE),
                                         (gate.REQUEST, 0xFFFFFFFF), (gate.arm_address, 0)])
        self.assertEqual(memory.read_bytes(gate.SIGNATURE_START, 44), gate.code)
        self.assertEqual(run_loader_check(memory), "proceed")  # disarmed: no client needed

    def test_rearms_after_a_game_reset(self):
        memory = self.memory()
        gate = ISOStartupBarrier(memory, ROUTINE)
        gate.attach()
        struct.pack_into("<I", memory.data, gate.arm_address, 0)  # disc reloaded
        gate.attach()
        self.assertEqual(memory.read_int32(gate.arm_address), LEASE)

    def test_detach_after_failed_verification_writes_nothing(self):
        memory = self.memory()
        gate = ISOStartupBarrier(memory, ROUTINE)
        gate.attach()
        memory.writes.clear()
        gate.detach(disarm=False)
        self.assertEqual(memory.writes, [])
        self.assertFalse(gate.attached)

    def test_incomplete_or_changed_load_cannot_release(self):
        for address, value in ((LoaderStateReader.STATE, 5), (LoaderStateReader.STATUS, 0),
                               (ISOStartupBarrier.REQUEST, 2), (LoaderStateReader.HANDLE, 0)):
            with self.subTest(address=address):
                memory = self.memory()
                gate = ISOStartupBarrier(memory, ROUTINE)
                gate.attach()
                memory.writes.clear()
                struct.pack_into("<I", memory.data, address, value)
                with self.assertRaises(StartupBarrierLost):
                    gate.release()
                self.assertEqual(memory.writes, [])

    def test_vanilla_savestate_is_rejected_without_writes(self):
        memory = self.memory()
        gate = ISOStartupBarrier(memory, ROUTINE)
        gate.attach()
        memory.writes.clear()
        memory.write_bytes(gate.SIGNATURE_START, struct.pack("<11I", *LoaderStateReader.SIGNATURE))
        memory.writes.clear()
        with self.assertRaises(StartupBarrierLost):
            gate.release()
        self.assertEqual(memory.writes, [])


def fake_executable(*, padding=True, section_headers=True) -> tuple[bytes, int]:
    """A one-segment ELF with the loader site, a .text section and (optionally) padding after it."""
    data = bytearray(0x6000)
    data[:7] = b"\x7fELF\x01\x01\x01"
    struct.pack_into("<I", data, 28, 52)
    struct.pack_into("<HH", data, 42, 32, 1)
    struct.pack_into("<8I", data, 52, 1, 0x1000, 0x100000, 0x100000, 0x4000, 0x4000, 5, 4096)
    site = 0x1000 + LoaderStateReader.SIGNATURE_START - 0x100000
    data[site:site + 44] = struct.pack("<11I", *LoaderStateReader.SIGNATURE)
    # .text covers everything up to text_end; the bytes after it, to the segment end, stay zero.
    text_end = 0x103F00 if padding else 0x104000
    if section_headers:
        shoff = 0x5000
        struct.pack_into("<I", data, 32, shoff)
        struct.pack_into("<HH", data, 46, 40, 2)
        struct.pack_into("<10I", data, shoff + 40, 1, 1, 6, 0x100000, 0x1000, text_end - 0x100000, 0, 0, 8, 0)
    return bytes(data), site


class TestResidentPatch(unittest.TestCase):
    def test_installs_site_and_routine_in_padding(self):
        data, site = fake_executable()
        result, routine = patch_resident_loader(data)
        self.assertEqual(routine, 0x103F00)
        self.assertEqual(result[site:site + 44], site_code(routine))
        start = 0x1000 + routine - 0x100000
        self.assertEqual(result[start:start + ROUTINE_SIZE], routine_code(routine))
        self.assertEqual(result[start + ROUTINE_SIZE:], data[start + ROUTINE_SIZE:])
        self.assertEqual(result[:site], data[:site])
        with self.assertRaises(ValueError):
            patch_resident_loader(result)  # already patched

    def test_refuses_without_safe_free_space(self):
        for kwargs in ({"padding": False}, {"section_headers": False}):
            with self.subTest(**kwargs), self.assertRaisesRegex(ValueError, "free space"):
                find_routine_space(fake_executable(**kwargs)[0])
