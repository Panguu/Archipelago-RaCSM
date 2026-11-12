import json
import os
from pathlib import Path
import struct
import unittest

from ..core import Core
from ..core.patches.asm import packed
from ..core.patches.identity import WrongPatchedGame
from ..core.patches.iso_startup_barrier import ISOStartupBarrier
from ..core.patches.snr2 import SNR2Module, resident_exports
from ..patcher.iso import ISOImage
from ..core.patches.frontend_build import FRONTEND_NULL_IMPORTS
from ..patcher.filenames import EXECUTABLE
from .test_runtime import Memory


@unittest.skipUnless(os.environ.get("SAC_TEST_BUILD") and os.environ.get("SAC_TEST_ISO"),
                     "Set SAC_TEST_BUILD and SAC_TEST_ISO for generated runtime checks")
class TestPermanentRuntime(unittest.TestCase):
    def test_every_compiled_module_binds_without_live_code_writes(self):
        root = Path(os.environ["SAC_TEST_BUILD"])
        build = json.loads((root / "data" / "sac-runtime.json").read_text())
        with Path(os.environ["SAC_TEST_ISO"]).open("rb") as source:
            imports = resident_exports(ISOImage(source).read_file(EXECUTABLE))
        for module_string, record in build["modules"].items():
            module = int(module_string)
            with self.subTest(module=module):
                memory = Memory()
                memory.data = bytearray(0x2000000)
                memory.get_game_id = lambda: "SCUS-97623"
                memory._send_request = lambda request: struct.pack("<IBI", 18, 0, 9) + build["elf_crc"].encode() + b"\0"
                base = 0x328B00
                compiled = (root / f"module-{module}.rel").read_bytes()
                module_imports = {**imports, **dict.fromkeys(FRONTEND_NULL_IMPORTS, 0)} if module == 0 else imports
                loaded, _ = SNR2Module(compiled).relocate(base, module_imports)
                memory.write_bytes(base, loaded)
                memory.write_bytes(ISOStartupBarrier.SIGNATURE_START, ISOStartupBarrier.CODE)
                for address, value in ((ISOStartupBarrier.STATE, 4), (ISOStartupBarrier.STATUS, 1),
                                       (ISOStartupBarrier.TARGET, module), (ISOStartupBarrier.HANDLE, base),
                                       (ISOStartupBarrier.REQUEST, module), (0x206328, module)):
                    memory.write_int32(address, value)
                core = Core(memory, permanent_build=build)
                runtime = core.native_runtime
                before = bytes(memory.data)
                self.assertFalse(runtime.service(set(), {}))
                self.assertEqual(bytes(memory.data), before)
                self.assertFalse(runtime.service(set(), {}))
                self.assertEqual(memory.read_int32(ISOStartupBarrier.REQUEST), 0xFFFFFFFF)
                self.assertEqual(memory.read_bytes(ISOStartupBarrier.SIGNATURE_START, 44), ISOStartupBarrier.CODE)
                allowed = [(ISOStartupBarrier.REQUEST, 4)]
                if module == 0:
                    allowed.append((runtime.frontend_config, 12))
                else:
                    hooks = core.location_hooks
                    allowed += [(table, 32 if kind == "mods" else 20 if kind == "titan" else 40)
                                for kind, table in hooks.tables.items()]
                    allowed += [(hooks.entitlement_table, 41), (core.progression.config_address, 12),
                                (core.progression.cap_address, 40), (core.progression.pickup_challenge_address, 4),
                                (core.wrench.ownership_address, 4), (core.skins.config_address, 4),
                                (core.keycards.hunt.table, 8), (runtime.connection_warning.heartbeat, 4)]
                    if core.stealth.binding:
                        allowed.append((core.stealth.binding[1], 4))
                    if runtime.vendor_catalog is not None:
                        allowed += [(address, 1) for address, _, _ in runtime.vendor_catalog.case_descriptors]
                mask = bytearray(len(memory.data))
                for address, size in allowed:
                    if address is not None:
                        mask[address:address + size] = bytes([1]) * size
                for index, (old, new) in enumerate(zip(before, memory.data)):
                    if old != new and not mask[index]:
                        self.fail(f"Unexpected native write at {index:#x}")
                # An incompatible savestate must be rejected before table writes.
                memory.data[base + record["identity_offset"]] ^= 1
                before = bytes(memory.data)
                with self.assertRaises(WrongPatchedGame):
                    runtime.service(set(), {})
                runtime.close()
                self.assertEqual(bytes(memory.data), before)
