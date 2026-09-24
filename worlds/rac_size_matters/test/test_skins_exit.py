"""Execute the new callbacks against bounded retail instruction fixtures."""

import unittest
from types import SimpleNamespace

from ..core.patches import asm as m, inside_clank_exit, item_toast, skins
from ..core.patches.asm import packed
from ..core.patches.loader_gate import LoaderGate
from ..core.skins import Skin, SkinInventory
from .test_native_patches import CPU, SKIN_EXIT_FIXTURES, Memory, plans


def prepare(name="pokitaru"):
    p = Memory()
    f = SKIN_EXIT_FIXTURES[name]
    if name != "pokitaru":
        p.data = bytearray(0x2000000)
        for address, data in f["segments"]:
            p.write_bytes(address, bytes.fromhex(data))
        p.writes.clear()
    kwargs = dict(code_start=f["base"], code=p.read_bytes(f["base"], 0x240000), arena=f["arena"])
    skin = skins.prepare(p, **kwargs, menu=f["menu"])
    exit_plan = (
        inside_clank_exit.prepare(p, **kwargs, gate=SimpleNamespace(pine=p, held_module=lambda: (9, f["base"])))
        if f["planet"] == 9
        else None
    )
    return p, f, skin, exit_plan


class SkinExitTests(unittest.TestCase):
    def test_retail_layouts_install_and_restore(self):
        for name in SKIN_EXIT_FIXTURES:
            with self.subTest(name=name):
                p, _, skin, exit_plan = prepare(name)
                original = bytes(p.data)
                for plan in (skin, exit_plan):
                    if plan:
                        plan.install()
                        plan._validate(True)
                        plan.restore()
                self.assertEqual(p.data, original)

    def test_trash_row_is_not_skipped_and_all_unlock_bits_include_it(self):
        p, _, plan, _ = prepare()
        plan.install()
        gate = plan.edits[0].address
        cpu = CPU(p)
        cpu.r[m.V1] = cpu.r[m.S4] = 6  # Trash's native model id
        cpu.r[m.S0] = 0x1000
        cpu.run(gate, stop=gate + 12)
        inv = SkinInventory(p)
        inv.set(Skin.TRASH_RATCHET)
        self.assertEqual(inv.unlocked, 0x7F)
        self.assertEqual(inv.equipped, 3)

    def test_each_skin_calls_native_loader_without_changing_menu(self):
        for selected in (s for s in Skin if s.equip_id < 7):
            with self.subTest(skin=selected):
                p, f, plan, _ = prepare()
                plan.install()
                p.write_int32(LoaderGate.STATE, 6)
                # Decode the original save-pointer load reused by the callback.
                payload = plan.edits[1].replacement
                index = payload.index(packed(0x8C43F32C))
                upper = int.from_bytes(payload[index - 4 : index], "little") & 65535
                p.write_int32((upper << 16) - 0xCD4, 0x1F4AB00)
                inv = SkinInventory(p)
                inv.set(selected)
                inv.apply_pending(plan, allowed=False)
                self.assertEqual(p.read_int8(plan.request), 255)
                inv.apply_pending(plan, allowed=True)
                cpu = CPU(p)
                cpu.r[m.V0] = 1  # successful native loader stubs
                cpu.run(plan.entry, stubs=(plan.begin, plan.finish))
                self.assertEqual(cpu.calls, [plan.begin, plan.finish])
                self.assertEqual(p.read_int8(0x1F4C77E), skins.MODEL_IDS[selected.equip_id])
                self.assertEqual(p.read_int8(plan.request), 255)
                self.assertEqual(p.read_bytes(f["menu"], 8), bytes(8))
                self.assertEqual(inv.equipped, selected.equip_id)
                cpu.calls.clear()
                cpu.run(plan.entry, stubs=(plan.begin, plan.finish))
                self.assertFalse(cpu.calls)

    def test_skin_request_waits_for_loading_and_menus(self):
        for state, menu, next_menu in [(5, 0, 0), (6, 3, 0), (6, 0, 3)]:
            p, f, plan, _ = prepare()
            plan.install()
            p.write_int32(LoaderGate.STATE, state)
            p.write_int32(f["menu"], menu)
            p.write_int32(f["menu"] + 4, next_menu)
            p.write_int8(plan.request, 6)
            cpu = CPU(p)
            cpu.run(plan.entry, stubs=(plan.begin, plan.finish))
            self.assertFalse(cpu.calls)
            self.assertEqual(p.read_int8(plan.request), 6)

    def test_game_menu_selection_survives_next_level_setup(self):
        p, _, plan, _ = prepare()
        plan.install()
        inv = SkinInventory(p)
        inv.equipped = Skin.TRASH_RATCHET.equip_id
        inv.apply_pending(plan, allowed=True)
        inv.setup()
        self.assertEqual(inv.equipped, 3)
        inv.apply_pending(plan, allowed=True)
        self.assertEqual(p.read_int8(plan.request), 6)

    def test_failed_begin_does_not_finish_or_change_active_model(self):
        p, _, plan, _ = prepare()
        plan.install()
        p.write_int32(LoaderGate.STATE, 6)
        p.write_int8(plan.request, 6)
        p.write_bytes(plan.begin, packed(m.jr(m.RA), m.addiu(m.V0, m.ZERO, 0)))
        p.write_int8(0x1F4C77E, 4)
        cpu = CPU(p)
        cpu.run(plan.entry, stubs=(plan.finish,))
        self.assertFalse(cpu.calls)
        self.assertEqual(p.read_int8(0x1F4C77E), 4)

    def test_frame_hook_runs_when_toast_is_empty(self):
        p, f, skin, _ = prepare()
        vendor, _, _ = plans(p)
        toast = item_toast.prepare(
            p,
            code_start=f["base"],
            code=p.read_bytes(f["base"], 0x240000),
            small_box=p.fixture["small_box"],
            starter=vendor.starter,
            frame_hook=skin.entry,
        )
        vendor.install()
        skin.install()
        toast.install()
        entry = vendor.starter + 32
        draw = (p.read_int32(entry + 16) & 0x3FFFFFF) << 2
        cpu = CPU(p)
        cpu.run(entry, stubs=(skin.entry, draw))
        self.assertEqual(cpu.calls, [skin.entry, draw])
        self.assertEqual(p.read_int32(toast.timer), 0)

    def test_inside_clank_menu_exit_never_runs_completion_evaluator(self):
        p, _, _, plan = prepare("inside_clank")
        plan.install()
        p.write_int8(0x1F4C66A, 3)  # Quodrona owned
        p.write_int32(0x1F4B3D4, 0)  # Inside Clank unfinished
        before = p.read_bytes(0x1F4AB00, 0x2000)
        cpu = CPU(p)
        cpu.r[m.A0] = 2  # selected ship destination
        cpu.r[m.A1] = 1
        cpu.run(plan.entry, stop=plan.transition)
        self.assertEqual(cpu.r[m.A0], 2)
        self.assertEqual(cpu.r[m.A1], 1)
        self.assertEqual(p.read_int32(plan.flag), 1)
        cpu.run(plan.completion, stubs=(plan.evaluator,))
        self.assertEqual(cpu.r[m.V0], 0)
        self.assertFalse(cpu.calls)
        self.assertEqual(p.read_bytes(0x1F4AB00, 0x2000), before)
        plan._validate(True)

    def test_scripted_completion_still_uses_native_evaluator(self):
        p, _, _, plan = prepare("inside_clank")
        plan.install()
        cpu = CPU(p)
        cpu.r[m.V0] = 1
        cpu.r[m.A0] = 9
        cpu.run(plan.completion, stubs=(plan.evaluator,))
        self.assertEqual(cpu.calls, [plan.evaluator])
        self.assertEqual(cpu.r[m.V0], 1)
        self.assertEqual(cpu.r[m.A0], 9)

    def test_install_rollback_and_signature_rejection(self):
        p, _, skin, _ = prepare()
        before = bytes(p.data)
        p.fail_once = skin.edits[1].address
        with self.assertRaises(OSError):
            skin.install()
        self.assertEqual(p.data, before)
        p.write_int32(skin.edits[0].address, 0)
        p.writes.clear()
        with self.assertRaises(RuntimeError):
            skin.install()
        self.assertFalse(p.writes)

    def test_inside_clank_requires_held_correct_level(self):
        p, f, _, _ = prepare("inside_clank")
        with self.assertRaises(RuntimeError):
            inside_clank_exit.prepare(
                p,
                code_start=f["base"],
                code=b"",
                arena=f["arena"],
                gate=SimpleNamespace(pine=p, held_module=lambda: (1, f["base"])),
            )
