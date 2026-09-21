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

    def test_menu_rows_and_travel_on_all_snapshots(self):
        for fixture in SHIP_FIXTURES:
            with self.subTest(fixture=fixture):
                memory, plan = self.prepare(fixture)
                loop, tail, _, route = (edit.address for edit in plan.edits)
                call = lambda address: (memory.read_int32(address) & 0x3FFFFFF) << 2
                unlock, group, name, add = [call(loop + offset) for offset in (4, 44, 56, 96)]
                setter = call(route + 36)
                original = bytes(memory.data)
                plan.install()
                for unlocked in ({1, 2, 5, 6, 9}, set(range(1, 11)), {1}, {1, 5}, {1, 6}):
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
                                if (6 if p == 5 else p) in unlocked]
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
