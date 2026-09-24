import unittest
from pathlib import Path

from ..constants.weapon_mods import WEAPON_MODS, enabled_mods
from ..constants.weapons import EQUIPMENT_DISPLAY_TO_INTERNAL
from ..core.inventories.weapons import WEAPON_ORDER
from ..core.patches import PICKUP_LOCATIONS, VENDOR_LOCATIONS, LocationHooks
from ..core.patches.weapon_mods import WeaponMods
from ..core.symbols import RuntimeSymbols
from .test_native_capture_plans import CaptureMemory


class WeaponModTests(unittest.TestCase):
    def run_leaf(self, p, address, mod_id):
        # Execute the emitted six-instruction leaf including JR's delay slot.
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
        self.assertEqual(len(enabled_mods({"Ratchet": 1, "Clank": 1}, 0)), 16)
        self.assertEqual(len(enabled_mods({"Ratchet": 1, "Clank": 1}, 1)), 19)
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
        mods.configure({"weapon_mods": True, "operatives": {"Ratchet": 1, "Clank": 1}, "ng_plus": 1})
        hooks.patches.extend(mods.prepare(symbols, hooks, 22, set(), True))
        hooks._install_plan()
        mod = WEAPON_MODS[0]
        gadget = mods.base + WEAPON_ORDER.index(EQUIPMENT_DISPLAY_TO_INTERNAL[mod.weapon]) * 0x74
        p.batch_write_int32([(gadget + 0x70, 0)])
        mods.received = {mod.name}
        mods.sync()
        self.assertEqual(p.read_int8(gadget + 0x68 + mod.slot), 1)
        self.assertEqual(p.read_int32(gadget + 0x70), 0)
        self.assertEqual(p.read_int8(hooks.tables["mods"] + mod.mod_id), 1)
        self.assertNotIn(mod.location, hooks.poll())
        # Native transaction only latches the separate table. Keeping this
        # check confirmed does not supply ownership after an AP replay.
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

    def test_older_seed_leaves_mods_vanilla(self):
        p = CaptureMemory()
        mods = WeaponMods(p)
        mods.configure({})
        mods.sync()
        self.assertFalse(mods.enabled)
        self.assertEqual(p.writes, [])
