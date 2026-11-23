from .compiled_memory import load_plan
import unittest
from pathlib import Path

from test.general import setup_multiworld

from ..constants import (
    CHALLENGE_MODS,
    EQUIPMENT_DISPLAY_TO_INTERNAL,
    PICKUP_LOCATIONS,
    VENDOR_LOCATIONS,
    WEAPON_MODS,
    WEAPON_ORDER,
    enabled_mods,
)
from ..core.patches import LocationHooks, WeaponMods
from ..core import RuntimeSymbols
from ..world import SecretAgentClankWorld
from .test_native_capture_plans import CaptureMemory


class WeaponModTests(unittest.TestCase):
    def run_leaf(self, p, address, mod_id):
        regs = [0] * 32
        regs[5] = mod_id
        for offset in range(0, 24, 4):
            word = p.read_int32(address + offset)
            op, rs, rt, rd = word >> 26, (word >> 21) & 31, (word >> 16) & 31, (word >> 11) & 31
            imm = word & 65535
            signed = imm - 65536 if imm & 32768 else imm
            if op == 15:
                regs[rt] = imm << 16
            elif op == 13:
                regs[rt] = regs[rs] | imm
            elif op == 9:
                regs[rt] = (regs[rs] + signed) & 0xFFFFFFFF
            elif op == 0 and word & 63 == 33:
                regs[rd] = regs[rs] + regs[rt]
            elif op == 36:
                regs[rt] = p.read_int8(regs[rs] + signed)
            elif op == 40:
                p.data[regs[rs] + signed] = regs[rt] & 255
            else:
                self.assertEqual(word, 0x03E00008)
                self.assertEqual(offset, 16)
        return regs[2]

    def test_catalog_filters_characters_and_postgame(self):
        self.assertEqual(len(enabled_mods({"Ratchet": 1, "Clank": 1}, 0)), 14)
        self.assertEqual(len(enabled_mods({"Ratchet": 1, "Clank": 1}, 1)), 17)
        self.assertEqual(len(enabled_mods({"Clank": 1}, 2)), 3)
        self.assertEqual(enabled_mods({"Qwark": 1}, 2), ())
        self.assertEqual(len({mod.mod_id for mod in WEAPON_MODS}), 19)
        self.assertEqual(len({(mod.weapon, mod.slot) for mod in WEAPON_MODS}), 19)

    def test_ap_receipt_does_not_complete_purchase_or_grant_weapon(self):
        capture = Path(__file__).parents[1] / ".research/showers_forced_graveyard.bin"
        if not capture.exists():
            self.skipTest("Local Graveyard capture not present")
        p = CaptureMemory()
        p.data[:] = capture.read_bytes()
        symbols = RuntimeSymbols.parse(p.data[:0x1000000], 0)
        hooks = LocationHooks(p)
        hooks.prepare(symbols, pickup_locations=PICKUP_LOCATIONS,
                      vendor_locations=VENDOR_LOCATIONS, entitlements={})
        mods = WeaponMods(p)
        mods.configure({"operatives": {"Ratchet": 1, "Clank": 1}, "ng_plus": 1, "weapon_mod_ids": [mod.mod_id for mod in WEAPON_MODS]})
        hooks.patches.extend(mods.prepare(symbols, hooks, 22, set(), True))
        load_plan(hooks)
        mod = WEAPON_MODS[0]
        gadget = mods.base + WEAPON_ORDER.index(EQUIPMENT_DISPLAY_TO_INTERNAL[mod.weapon]) * 0x74
        p.batch_write_int32([(gadget + 0x70, 0)])
        mods.received = {mod.name}
        mods.sync()
        self.assertEqual(p.read_int8(gadget + 0x68 + mod.slot), 1)
        self.assertEqual(p.read_int32(gadget + 0x70), 0)
        self.assertEqual(p.read_int8(hooks.tables["mods"] + mod.mod_id), 1)
        self.assertNotIn(mod.location, hooks.poll())
        buy = symbols["SCRNVENDOR_ProcessPurchase__Fv"]
        recorder = (p.read_int32(buy + 0x10C) & 0x3FFFFFF) << 2
        self.assertEqual(self.run_leaf(p, buy + 0x13C, mod.mod_id), 0)
        self.run_leaf(p, recorder, mod.mod_id)
        self.assertEqual(self.run_leaf(p, buy + 0x13C, mod.mod_id), 1)
        mods.received.clear()
        mods.sync()
        self.assertEqual(p.read_int8(gadget + 0x68 + mod.slot), 0)
        self.assertIn(mod.location, hooks.poll())
        self.assertEqual(hooks.poll(), [])

    def test_challenge_mods_are_pooled_items_for_ratchet(self):
        for operatives, goal, expected in (({"Ratchet": 1, "Clank": 1}, "defeat_klunk", 1),
                                           ({"Ratchet": 1}, "ratchet_prison_escape", 1),
                                           ({"Clank": 1}, "defeat_klunk", 0)):
            with self.subTest(operatives=operatives):
                m = setup_multiworld(SecretAgentClankWorld, seed=1, options={"operatives": operatives, "goal": goal})
                names = [item.name for item in (*m.itempool, *m.precollected_items[1])]
                for mod in CHALLENGE_MODS:
                    self.assertEqual(names.count(mod.name), expected, mod.name)

    def test_challenge_rewards_are_owned_only_once_received(self):
        p = CaptureMemory()
        mods = WeaponMods(p)
        mods.configure({"operatives": {"Ratchet": 1}, "ng_plus": 0, "weapon_mod_ids": []})
        mods.base, mods.mod_list, mods.module = 0x600000, 0x700000, 7
        writes = [(0x206328, 7), (0x206324, 0xFFFFFFFF), (0x206338, 3)]
        slots = {}
        for mod in WEAPON_MODS:
            definition = 0x710000 + mod.mod_id * 16
            gadget = mods.base + WEAPON_ORDER.index(EQUIPMENT_DISPLAY_TO_INTERNAL[mod.weapon]) * 0x74
            writes += [(mods.mod_list + mod.mod_id * 4, definition), (gadget + 0x30 + mod.slot * 4, definition)]
            slots[mod.name] = gadget + 0x68 + mod.slot
        p.batch_write_int32(writes)
        p.batch_write_int8([(slots[mod.name], 1) for mod in CHALLENGE_MODS])
        mods.sync()
        self.assertEqual([p.read_int8(slots[mod.name]) for mod in CHALLENGE_MODS], [0, 0])
        mods.received = {CHALLENGE_MODS[0].name}
        mods.sync()
        self.assertEqual([p.read_int8(slots[mod.name]) for mod in CHALLENGE_MODS], [1, 0])

