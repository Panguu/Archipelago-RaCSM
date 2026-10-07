import struct
import unittest
from pathlib import Path
from types import SimpleNamespace

from ..core.patches import PICKUP_LOCATIONS, VENDOR_LOCATIONS, LocationHooks
from ..core.patches import mips as m
from ..core.patches.asm import jump, packed, words
from ..core.patches.vendor_catalog import VendorCatalog
from ..core.patches.vendor_tabs import VendorTabs
from ..core.symbols import RuntimeSymbols
from .mips_cpu import CPU
from .test_native_capture_plans import CaptureMemory


def _signed16(word):
    """Sign-extend an instruction's 16-bit immediate."""
    return (word & 32767) - (word & 32768)

class VendorTabsTests(unittest.TestCase):
    def test_initial_tab_uses_live_available_stock(self):
        p = self.memory()
        entry, mode, descriptors, flags, builder = range(0x110000, 0x160000, 0x10000)
        # Includes regular stock, a locked row, and a Titan upgrade.
        for states, expected in (((2, 1, 4), 1), ((1, 1, 4), 0),
                                  ((2, 1, 3), 0), ((2, 2, 4), 1)):
            with self.subTest(states=states):
                for i, (state, unchecked) in enumerate(zip(states, (1, 255, 3))):
                    p.write_int8(flags + i, state)
                    p.write_bytes(descriptors + i * 8, struct.pack('<2I', flags + i, unchecked << 24))
                p.write_bytes(entry, VendorTabs.initial_tab_routine(mode, descriptors, 3, builder))
                p.write_int8(mode, 1 - expected)
                before = p.read_bytes(flags, 3)
                cpu = CPU(p)
                saved = cpu.r[16:]
                cpu.run(entry, stop=builder)
                self.assertEqual(p.read_int8(mode), expected)
                self.assertEqual(p.read_bytes(flags, 3), before)
                self.assertEqual(cpu.r[16:], saved)
                first, second = VendorTabs.split_initial_tab(
                    VendorTabs.initial_tab_routine(mode, descriptors, 3, builder), entry, entry + 0x1000)
                p.write_bytes(entry, first)
                p.write_bytes(entry + 0x1000, second)
                p.write_int8(mode, 1 - expected)
                CPU(p).run(entry, stop=builder)
                self.assertEqual(p.read_int8(mode), expected)
        p.write_bytes(entry, VendorTabs.initial_tab_routine(mode, descriptors, 0, builder))
        CPU(p).run(entry, stop=builder)
        self.assertEqual(p.read_int8(mode), 1)

    def memory(self):
        p = CaptureMemory()
        p.data.extend(bytes(0x2000000 - len(p.data)))
        p.write_int32 = lambda a, v: p.batch_write_int32([(a, v)])
        p.write_int8 = lambda a, v: p.batch_write_int8([(a, v)])
        return p

    def test_physical_press_edges_switch_once_and_consume_confirm(self):
        p = self.memory()
        entry, mode, pressed, analog, builder, dirty = range(0x110000, 0x170000, 0x10000)
        p.write_bytes(entry, VendorTabs.input_routine(mode, pressed, analog, builder, dirty))
        p.write_int8(mode, 0)
        state = {'pressed': 0, 'analog': 0}
        rebuilds = []

        def physical(cpu):
            self.assertEqual(cpu.r[4], 0x16C4)
            cpu.r[2] = state['pressed']
            cpu.r[4] = 0xBAD

        def original(cpu):
            self.assertEqual(cpu.r[4], 0x16C4)
            cpu.r[2] = state['analog']

        def rebuild(cpu):
            rebuilds.append(p.read_int8(mode))
            for reg in range(2, 16):
                cpu.r[reg] = 0xBAD

        def run(buttons, expected_mode, expected_input, analog_buttons=0):
            state.update(pressed=buttons, analog=analog_buttons)
            cpu = CPU(p)
            cpu.r[4] = 0x16C4
            saved = cpu.r[29:]
            cpu.run(entry, stubs={pressed: physical, analog: original, builder: rebuild})
            self.assertEqual(p.read_int8(mode), expected_mode)
            self.assertEqual(cpu.r[2], expected_input)
            self.assertEqual(cpu.r[29:], saved)

        run(8 | 0x80, 1, 0, 8 | 0x80)
        self.assertEqual(rebuilds, [1])
        self.assertEqual(p.read_int8(dirty), 1)
        run(0, 1, 8, 8)  # Holding Down / analog motion does not rebuild.
        run(8, 1, 8, 8)  # Pressing the current tab again does not rebuild.
        run(12, 1, 12, 12)  # Opposite physical directions together are ignored.
        run(4, 0, 0, 4)
        run(0, 0, 4, 4)  # Analog Up does not switch tabs.
        run(0x80, 0, 0x80, 0x80)  # Normal buying input passes through.
        self.assertEqual(rebuilds, [1, 0])

    def test_controller_address_sign_extends_and_rejects_changed_getter(self):
        p = self.memory()
        address = 0x110000
        symbols = {'CONTROLLER_GetButtonsDown__FUi': address}
        p.write_bytes(address, packed([m.lui(m.V1, 0x68), m.jr(m.RA),
                                      m.lw(m.V0, 0x8210, m.V1), 0]))
        self.assertEqual(VendorTabs.controller_address(p, symbols), 0x678210)
        p.write_int32(address + 8, m.lbu(m.V0, 0x8210, m.V1))
        with self.assertRaisesRegex(RuntimeError, 'getter changed'):
            VendorTabs.controller_address(p, symbols)

    def capture(self, name='sac_finished.p2s.ram'):
        path = Path(__file__).parents[1] / '.research' / name
        if not path.exists():
            self.skipTest('Local retail RAM capture unavailable')
        p = self.memory()
        p.data[:] = path.read_bytes()
        symbols = RuntimeSymbols.parse(p.data[:0x1000000], 0)
        buy = symbols['SCRNVENDOR_ProcessPurchase__Fv']
        builder = (p.read_int32(buy + 0x338) & 0x3FFFFFF) << 2
        return p, symbols, builder

    def test_relocated_ammo_retains_every_call_and_branch_target(self):
        for name in ('prison_skin_snapshot.bin', 'SAC.p2s.ram', 'sac_finished.p2s.ram'):
            with self.subTest(capture=name):
                p, symbols, builder = self.capture(name)
                original = p.read_bytes(builder, 0x738)
                targets = tuple(symbols[n] + 8 for n, _, _ in VendorTabs.STORAGE[:2])
                relocated = VendorTabs.relocate_ammo(original, targets, builder + 0x738)
                mapping = {offset: target + offset - low
                           for (low, high), target in zip(((0x70, 0x178), (0x178, 0x284)), targets)
                           for offset in range(low, high, 4)}
                mapping[0x284] = targets[1] + 0x10C
                for (low, high), target, code in zip(((0x70, 0x178), (0x178, 0x284)), targets, relocated):
                    for offset, before, after in zip(range(low, high, 4), words(original[low:high]), words(code)):
                        op = before >> 26
                        if op in (1, 4, 5, 6, 7, 20, 21, 22, 23) or (op == 17 and before >> 21 & 31 == 8):
                            expected = mapping[offset + 4 + 4 * _signed16(before)]
                            self.assertEqual(mapping[offset] + 4 + 4 * _signed16(after), expected)
                            self.assertEqual(before >> 16, after >> 16)
                        else:
                            self.assertEqual(before, after)
                    self.assertEqual(words(code)[-2:], [jump(targets[1] if high == 0x178 else builder + 0x738), 0])

    def test_captured_controller_reads_current_and_previous_frame(self):
        p, symbols, _ = self.capture()
        address = VendorTabs.controller_address(p, symbols)
        for current, previous, active, expected in ((8, 0, 1, 8), (8, 8, 1, 0),
                                                     (4, 0, 1, 4), (4, 0, 0, 0)):
            p.write_int32(address, current)
            p.write_int32(address + 4, previous)
            cpu = CPU(p)
            cpu.r[m.A0] = 0x16C4
            cpu.run(symbols['CONTROLLER_GetButtonsPressed__FUi'], stubs={
                symbols['CONTROLLER_CheckContextActive__FUi']: lambda c: c.r.__setitem__(2, active)})
            self.assertEqual(cpu.r[m.V0], expected)

    def test_capture_tab_dispatch_reset_and_empty_ammo(self):
        p, symbols, builder = self.capture()
        hooks = LocationHooks(p)
        hooks.prepare(symbols, pickup_locations=PICKUP_LOCATIONS, vendor_locations=VENDOR_LOCATIONS,
                      entitlements={})
        catalog = VendorCatalog(p)
        edits = catalog.prepare(symbols, hooks)
        for patch in hooks.patches + edits:
            p.write_bytes(patch.address, patch.replacement)
        mode = catalog.tabs.mode_address
        upper = p.read_int32(builder + 4) & 65535
        add = symbols['ICONMENU_AddItem__FP9tICONMENUUiUiUiUiUiUi']
        rows = []
        cpu = CPU(p)
        cpu.r[23] = upper << 16
        cpu.run(builder + 0x70, stop=builder + 0x738, stubs={add: lambda c: rows.append(c.r[7])}, max_steps=5000)
        self.assertEqual(rows, [0] * len(VENDOR_LOCATIONS))
        p.write_int8(mode, 1)
        cpu = CPU(p)
        cpu.r[23] = upper << 16
        # Native ammo rejects every gadget when none belongs to this operative.
        cpu.run(builder + 0x70, stop=builder + 0x738,
                stubs={symbols['GADGET_IsGadgetOfChar__F8PLR_TYPE7eGADGET']: lambda c: c.r.__setitem__(2, 0)},
                max_steps=5000)
        self.assertEqual(rows, [0] * len(VENDOR_LOCATIONS))
        reset = (p.read_int32(symbols['SCRNVENDOR_Init__Fv'] + 0x5C) & 0x3FFFFFF) << 2
        CPU(p).run(reset, stop=builder)
        self.assertEqual(p.read_int8(mode), 0)
        for slot in hooks.locations['vendor']:
            p.write_int8(hooks.tables['vendor'] + slot, 2)
        CPU(p).run(reset, stop=builder)
        self.assertEqual(p.read_int8(mode), 1)

    def test_unknown_ammo_or_storage_layout_fails_before_writes(self):
        for corrupt in ('ammo', 'storage'):
            p, symbols, builder = self.capture()
            if corrupt == 'ammo':
                p.data[builder + 0xC4] ^= 1
            else:
                p.data[symbols[VendorTabs.STORAGE[0][0]] + 0x30] ^= 1
            before = bytes(p.data)
            with self.assertRaisesRegex(RuntimeError, 'changed'):
                VendorTabs().prepare(p, symbols, SimpleNamespace(patches=[], extra_ranges=[]), builder,
                                     p.read_bytes(builder, 0x738), builder + 0x78)
            self.assertEqual(p.data, before)

    def test_native_ammo_prices_ownership_and_purchase_preserve_ap_flags(self):
        p, symbols, builder = self.capture()
        original = p.read_bytes(builder, 0x738)
        hooks = LocationHooks(p)
        hooks.prepare(symbols, pickup_locations=PICKUP_LOCATIONS, vendor_locations=VENDOR_LOCATIONS,
                      entitlements={})
        catalog = VendorCatalog(p)
        edits = catalog.prepare(symbols, hooks)
        for patch in hooks.patches + edits:
            p.write_bytes(patch.address, patch.replacement)
        p.write_int8(catalog.tabs.mode_address, 1)

        def pair(high, low):
            lower = p.read_int32(low) & 65535
            return ((p.read_int32(high) & 65535) << 16) + (lower - 65536 if lower & 32768 else lower)

        buy = symbols['SCRNVENDOR_ProcessPurchase__Fv']
        save = p.read_int32(pair(buy + 0x2C, buy + 0x40))
        price = pair(buy + 0x48, buy + 0x58)
        quantity = pair(buy + 0xD0, buy + 0xD8)
        data, definition, row_pointer = 0x180000, 0x180100, 0x180200
        conversion = (words(original[0x1B0:0x1B4])[0] & 0x3FFFFFF) << 2
        flags = p.read_bytes(hooks.tables['vendor'], 40)
        state = {'owned': True, 'hidden': False, 'screen': 8}
        rows = []
        stubs = {
            symbols['GADGET_IsGadgetOfChar__F8PLR_TYPE7eGADGET']: lambda c: c.r.__setitem__(2, int(c.r[5] == 5)),
            symbols['GADGET_PlayerHasGadget__FUi']: lambda c: c.r.__setitem__(2, int(state['owned'])),
            symbols['GADGET_PlayerHasButItIsHidden__FUi']: lambda c: c.r.__setitem__(2, int(state['hidden'])),
            symbols['GADGET_GetData__FUi']: lambda c: c.r.__setitem__(2, data),
            symbols['GADGET_GetDataDef__FUi']: lambda c: c.r.__setitem__(2, definition),
            symbols['PAUSEMODE_GetCurrentPauseScreen__Fv']: lambda c: c.r.__setitem__(2, state['screen']),
            symbols['ICONMENU_AddItem__FP9tICONMENUUiUiUiUiUiUi']: lambda c: rows.append(tuple(c.r[5:11])),
            conversion: lambda c: c.r.__setitem__(2, int(c.float(12))),
        }

        def build(ammo, bolts, owned=True, hidden=False, screen=8):
            state.update(owned=owned, hidden=hidden, screen=screen)
            rows.clear()
            p.write_int32(data + 0x60, ammo)
            p.write_int32(definition + 0x40, 20)
            p.write_int32(definition + 0x3C, 5)
            p.write_int32(definition + 0x2C, 51)
            p.write_int32(save + 0xEC8, bolts)
            cpu = CPU(p)
            cpu.r[m.S7] = (p.read_int32(builder + 4) & 65535) << 16
            cpu.r[m.FP] = (p.read_int32(builder + 0x60) & 65535) << 16
            cpu.run(builder + 0x70, stop=builder + 0x738, stubs=stubs, max_steps=5000)
            self.assertEqual(p.read_bytes(hooks.tables['vendor'], 40), flags)
            return list(rows)

        self.assertEqual(build(7, 100), [(51, 2, 1, 5, 13, 0), (3, 2, 2, 0xFFFFFFFF, 65, 0)])
        self.assertEqual(build(7, 12), [(51, 2, 1, 5, 2, 0), (3, 2, 2, 0xFFFFFFFF, 10, 0)])
        self.assertEqual(build(7, 100, screen=16), [(51, 2, 1, 5, 2, 0), (3, 2, 2, 0xFFFFFFFF, 100, 0)])
        for args in ((20, 100), (7, 0), (7, 100, False), (7, 100, True, True)):
            self.assertEqual(build(*args), [])
        build(7, 100)
        p.write_bytes(row_pointer, struct.pack('<7I', 1, *rows[0]))
        p.write_int32(price, 65)
        p.write_int32(quantity, 13)
        stubs.update({
            symbols['ICONMENU_GetCurrentItemNode__FP9tICONMENU']: lambda c: c.r.__setitem__(2, row_pointer),
            symbols['SCRNVENDOR_IsMaxAmmoItem__FP14tICONMENU_NODE']: lambda c: c.r.__setitem__(2, 0),
            symbols['SCRNVENDOR_IsAmmo__FP14tICONMENU_NODE']: lambda c: c.r.__setitem__(2, 1),
        })
        CPU(p).run(buy, stop=buy + 0x338, stubs=stubs)
        self.assertEqual(p.read_int32(save + 0xEC8), 35)
        self.assertEqual(p.read_int32(data + 0x60), 20)
        self.assertEqual(p.read_bytes(hooks.tables['vendor'], 40), flags)
