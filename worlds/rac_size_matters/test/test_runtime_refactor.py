import hashlib
import json
import random
import unittest
from collections import defaultdict
from pathlib import Path

from ..core.armour import ArmourPiece, ArmourSnapshot, ArmourStruct
from ..core.memory import MemoryWindow
from ..core.patches.asm import Patch
from ..core.patches.plan import Plan
from ..core.weapons import WEAPON_STRUCT_SIZE, WeaponInventory
from ..locations import ALL_LOCATIONS
from ..locations.observation import LocationObservation


class Memory:
    def __init__(self):
        self.data = defaultdict(int)
        self.reads = []
        self.writes = []

    def get_game_id(self):
        return "SCUS-97615"

    def read_bytes(self, address, size):
        self.reads.append((address, size))
        return bytes(self.data[index] for index in range(address, address + size))

    def write_bytes(self, address, data):
        for index, value in enumerate(data, address):
            self.data[index] = value

    def batch_read(self, requests):
        self.reads.append(tuple(requests))
        return [sum(self.data[address + index] << (index * 8) for index in range(size)) for size, address in requests]

    def batch_write(self, writes):
        self.writes.append(tuple(writes))
        for size, address, data in writes:
            assert size == len(data)
            self.write_bytes(address, data)


class TestRuntimeRefactor(unittest.TestCase):
    def inventory(self):
        memory = Memory()
        inventory = WeaponInventory(memory)
        inventory.set_base(0x1000)
        return memory, inventory

    def test_weapon_check_uses_one_read_and_preserves_level_jumps(self):
        memory, inventory = self.inventory()
        memory.write_bytes(0x1045, b"\x01")
        memory.write_bytes(0x102D, (4).to_bytes(4, "little"))
        changed = inventory.check()
        self.assertEqual(changed["weapons"], ["lacerator"])
        self.assertEqual(changed["levels"], [("lacerator", level) for level in range(2, 6)])
        self.assertEqual(changed["titans"], ["lacerator"])
        self.assertEqual(memory.reads, [(0x1000, 23 * WEAPON_STRUCT_SIZE)])
        self.assertEqual(memory.writes, [])
        self.assertFalse(any(inventory.check().values()))

    def test_grants_and_resync_share_one_read_and_write(self):
        memory, inventory = self.inventory()
        with inventory.memory():
            inventory.set("lacerator", True)
            inventory.set_mod("lacerator", "mod_slot_one", True)
            inventory.sync_slots()
        self.assertEqual(len(memory.reads), 1)
        self.assertEqual(len(memory.writes), 1)
        self.assertTrue(inventory.entries["lacerator"].raw_owned)
        self.assertTrue(inventory.entries["lacerator"].raw_mods.mod_slot_one)
        self.assertFalse(any(inventory.check().values()))

    def test_memory_window_leaves_unrelated_game_changes_untouched(self):
        memory = Memory()
        window = MemoryWindow.read_bytes(memory, 0x1000, 32)
        window.write(0x1004, 123, 4)
        memory.write_bytes(0x1008, b"\xaa\xbb\xcc\xdd")
        window.flush(memory)
        self.assertEqual(memory.read_bytes(0x1008, 4), b"\xaa\xbb\xcc\xdd")
        self.assertEqual(memory.read_bytes(0x1004, 4), (123).to_bytes(4, "little"))
        self.assertEqual(len(memory.writes), 1)

    def test_unchanged_fields_do_not_write(self):
        memory, inventory = self.inventory()
        inventory.sync_slots()
        inventory.sync()
        self.assertEqual(memory.writes, [])

    def test_failed_operation_discards_snapshot(self):
        memory, inventory = self.inventory()
        with self.assertRaises(RuntimeError), inventory.memory():
            inventory.set("lacerator", True)
            raise RuntimeError("interrupted")
        self.assertEqual(memory.writes, [])
        self.assertIsNone(inventory._weapon_addrs["lacerator"].window)
        self.assertFalse(inventory.get("lacerator"))

    def test_rebinding_does_not_reuse_old_memory(self):
        memory, inventory = self.inventory()
        inventory.sync_slots()
        inventory.set_base(0x2000)
        memory.write_bytes(0x2045, b"\x01")
        self.assertEqual(inventory.check()["weapons"], ["lacerator"])
        self.assertEqual(memory.reads[-1][0], 0x2000)

    def test_armour_snapshot_preserves_boot_normalization(self):
        snapshot = ArmourSnapshot.read_bytes(bytes([1, 2, 3, 3, 0, 0, 0xA7, 0, 0, 0, 0, 0, 0]))
        self.assertEqual(snapshot.wildfire, ArmourPiece.ALL)
        self.assertIsNone(snapshot.boots_left)
        with self.assertRaises(ValueError):
            ArmourSnapshot.read_bytes(b"\x00")
        memory = Memory()
        armour = ArmourStruct()
        armour.pine = memory
        armour.read()
        self.assertEqual(memory.reads, [(ArmourStruct.BASE_ADDRESS, 13)])

    def test_location_snapshot_reads_sources_once(self):
        memory = Memory()
        mission = next(location for location in ALL_LOCATIONS.values() if location.completed.source == "missions")
        memory.write_bytes(mission.completed.key, mission.completed.mask.to_bytes(2, "little"))
        snapshot = LocationObservation.read_bytes(memory, mission.completed.planet_id, True)
        self.assertEqual(len(memory.reads), 1)
        self.assertTrue(mission.completed(snapshot))
        wrong_planet = LocationObservation(planet_id=99, missions=snapshot.missions)
        self.assertFalse(mission.completed(wrong_planet))

    def test_disabled_patch_and_plan_do_not_write(self):
        memory = Memory()
        plan = Plan(memory, [Patch(0x100, b"\0", b"\1", enabled=False)])
        plan.install()
        self.assertEqual(memory.data[0x100], 0)

        disabled = Plan(memory, [Patch(0x100, b"\0", b"\1")], enabled=False)
        disabled.install()
        self.assertFalse(disabled.installed)
        self.assertEqual(memory.data[0x100], 0)

    def test_weapon_behavior_matches_pre_refactor_trace(self):
        class DenseMemory(Memory):
            def __init__(self):
                super().__init__()
                self.data = bytearray(0x10000)

            def read_bytes(self, address, size):
                return bytes(self.data[address : address + size])

            def write_bytes(self, address, data):
                self.data[address : address + len(data)] = data

        memory = DenseMemory()
        inventory = WeaponInventory(memory)
        inventory.set_base(0x1000)
        expected = iter(json.loads((Path(__file__).parent / "fixtures/weapon_behavior.json").read_text()))
        rng = random.Random(97615)
        fields = (
            "weapons",
            "gadgets",
            "mods",
            "_raw_weapons",
            "_raw_gadgets",
            "_raw_mods",
            "_raw_level",
            "_prev_experience",
            "_pinned_experience",
            "titan_purchased",
            "level_caps",
        )
        for tick in range(250):
            for address in inventory._weapon_addrs.values():
                changes = [
                    (0x2D, 4, rng.randrange(8)),
                    (0x35, 4, rng.randrange(300000)),
                    (0x45, 1, rng.randrange(2)),
                    (0x3D, 1, rng.randrange(2)),
                ]
                for offset, size, value in changes:
                    memory.write_bytes(address.base + offset, value.to_bytes(size, "little"))
            inventory.progressive_mode = rng.randrange(3)
            inventory.challenge_mode = rng.randrange(3)
            inventory.experience_multiplier = rng.randrange(1, 5)
            inventory.level_caps = {name: rng.randrange(-1, 8) for name in inventory._weapon_addrs}
            for method in ("check", "apply_experience_boost", "apply_progressive_leveling", "sync_slots", "sync"):
                result = getattr(inventory, method)()
                state = {field: dict(getattr(inventory, field)) for field in fields}
                for field in ("mods", "_raw_mods"):
                    state[field] = {name: dict(slots) for name, slots in state[field].items()}
                payload = {"memory": memory.data.hex(), "result": result, "state": state}
                actual = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
                self.assertEqual(next(expected), actual, (tick, method))
