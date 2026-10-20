"""Execute the rebuilt menu and confirmation branches using retail excerpts."""
import unittest

from ..core.patches import ship_menu
from .test_native_patches import CPU, SHIP_FIXTURES, Memory


class ShipMenuTests(unittest.TestCase):
    def prepare(self, fixture):
        memory = Memory()
        memory.data[:] = bytes(len(memory.data))
        for address, data in SHIP_FIXTURES[fixture]["segments"]:
            memory.data[address:address + len(data) // 2] = bytes.fromhex(data)
        plan = ship_menu.prepare(memory, code_start=0xD00000,
                                 code=memory.read_bytes(0xD00000, 0x400000))
        return memory, plan

    def test_special_destination_never_reads_story_statistics_or_atlas(self):
        for fixture in SHIP_FIXTURES:
            with self.subTest(fixture=fixture):
                memory, plan = self.prepare(fixture)
                stats, atlas = plan.edits[-2].address, plan.edits[-1].address
                total = (memory.read_int32(stats) & 0x3FFFFFF) << 2
                plan.install()
                for planet in (*range(1, 12), 24):
                    cpu = CPU(memory)
                    cpu.r[19] = 0x1800000
                    memory.write_int32(cpu.r[19] + 0xD0, planet)
                    calls = []
                    cpu.run(stats, stop=stats + (0x1EC if planet == 24 else 8),
                            stubs={total: lambda c: calls.append(c.r[4])})
                    self.assertEqual(calls, [] if planet == 24 else [planet])
                    cpu = CPU(memory)
                    cpu.r[3] = 0x1800000
                    memory.write_int32(cpu.r[3] + 0xD0, planet)
                    # Stop before the first table lookup for supported rows,
                    # or at the next iteration for Treehouse.
                    cpu.run(atlas + 12, stop=atlas + (112 if planet == 24 else 28))
                    self.assertEqual(cpu.r[4], planet - 1)

    def test_menu_rows_and_travel_on_all_snapshots(self):
        for fixture in SHIP_FIXTURES:
            with self.subTest(fixture=fixture):
                memory, plan = self.prepare(fixture)
                loop, tail, _, route = (edit.address for edit in plan.edits[:4])
                call = lambda address: (memory.read_int32(address) & 0x3FFFFFF) << 2
                unlock, group, name, add = [call(loop + offset) for offset in (4, 44, 56, 96)]
                setter = call(route + 36)
                original = bytes(memory.data)
                plan.install()
                cases = [(unlocked, treehouse)
                         for unlocked in ({1, 2, 5, 6, 9}, set(range(1, 11)), {1}, {1, 5}, {1, 6})
                         for treehouse in (1, 0)]
                for unlocked, treehouse in cases:
                    # The client flips the flag at runtime as the Treehouse infobot arrives.
                    memory.write_int32(plan.treehouse_flag, treehouse)
                    rows = []
                    cpu = CPU(memory)
                    cpu.r[17], cpu.r[18], cpu.r[19], cpu.r[20] = 1, 0xFFFFFFFF, 0x1800000, 1

                    def availability(c): c.r[2] = int(c.r[4] in unlocked)
                    def title(c): c.r[2] = 0x1900000 + c.r[4] * 32
                    def append(c):
                        rows.append((c.r[6], c.r[7], c.r[5]))
                        c.r[2] = 1

                    cpu.run(loop, stop=loop + 120,
                            stubs={unlock: availability, group: lambda c: None, name: title, add: append})
                    expected = [p for p in range(1, 11) for _ in range(2 if p == 6 else 1)
                                if (6 if p == 5 else p) in unlocked] + [24] * treehouse
                    self.assertEqual([p for p, _, _ in rows], expected)
                    if 6 in unlocked:
                        omega = [row for row in rows if row[0] == 6]
                        self.assertEqual([row[1] for row in omega], [1, 0])
                        self.assertEqual(memory.read_bytes(omega[0][2], 5), b"MOO1\0")
                        self.assertEqual(memory.read_bytes(omega[1][2], 5), b"MOO2\0")
                    for planet, marker, _ in rows:
                        destination = 23 if planet == 6 and marker == 0 else planet
                        for current in (1, 6, 23):
                            c = CPU(memory)
                            c.r[4], c.r[3], c.r[16] = planet, current, 0x1801000
                            memory.write_int32(c.r[16] + 0xD4, marker)
                            selected = []
                            cancel = route - 0x54
                            def cancelled(c): c.r[31] = route + 76
                            c.run(route, stop=route + 76,
                                  stubs={setter: lambda c: selected.append(c.r[4]), cancel: cancelled})
                            self.assertEqual(selected, [] if current == destination else [destination])
                plan.restore()
                for edit in plan.edits:
                    self.assertEqual(memory.read_bytes(edit.address, len(edit.original)),
                                     original[edit.address:edit.address + len(edit.original)])

    def test_treehouse_flag_initial_value(self):
        for unlocked in (True, False):
            memory = Memory()
            memory.data[:] = bytes(len(memory.data))
            for address, data in SHIP_FIXTURES["pokitaru"]["segments"]:
                memory.data[address:address + len(data) // 2] = bytes.fromhex(data)
            plan = ship_menu.prepare(memory, code_start=0xD00000, code=memory.read_bytes(0xD00000, 0x400000),
                                     treehouse_unlocked=unlocked)
            plan.install()
            self.assertEqual(memory.read_int32(plan.treehouse_flag), int(unlocked))

    def test_changed_instructions_rejected_without_writes(self):
        memory, plan = self.prepare("pokitaru")
        memory.write_int32(plan.edits[3].address, 0)
        memory.writes.clear()
        with self.assertRaises(RuntimeError):
            ship_menu.prepare(memory, code_start=0xD00000,
                              code=memory.read_bytes(0xD00000, 0x400000))
        self.assertEqual(memory.writes, [])

    def test_install_failure_restores_prior_edits(self):
        memory, plan = self.prepare("pokitaru")
        original = bytes(memory.data)
        memory.fail_once = plan.edits[-1].address
        with self.assertRaises(OSError):
            plan.install()
        self.assertEqual(bytes(memory.data), original)
