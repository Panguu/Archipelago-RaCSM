"""Uses a tiny hand-made disc image instead of the game."""
import io
from pathlib import Path
import tempfile
import unittest

from ..patcher.iso import ISOImage, write_patched_iso
from ..patcher.filenames import EXECUTABLE, LEVEL_FILES, MODULE_FILES
from ..constants.native_modules import CASE_MODULES


def both(value, size):
    return value.to_bytes(size, "little") + value.to_bytes(size, "big")


def record(name, sector, size, directory=False):
    result = bytearray(33 + len(name) + (not len(name) % 2))
    result[0] = len(result)
    result[2:10] = both(sector, 4)
    result[10:18] = both(size, 4)
    result[25] = 2 if directory else 0
    result[28:32] = both(1, 2)
    result[32] = len(name)
    result[33:33 + len(name)] = name
    return result


def fixture():
    image = bytearray(24 * 2048)
    descriptor = bytearray(2048)
    descriptor[:7] = b"\x01CD001\x01"
    descriptor[80:88] = both(24, 4)
    descriptor[128:132] = both(2048, 2)
    descriptor[156:190] = record(b"\0", 20, 2048, True)
    image[16 * 2048:17 * 2048] = descriptor
    image[17 * 2048:17 * 2048 + 7] = b"\xffCD001\x01"
    root = record(b"\0", 20, 2048, True) + record(b"\1", 20, 2048, True)
    root += record(b"BIN", 21, 2048, True)
    root += record(b"SCUS_976.23;1", 23, 4)
    image[20 * 2048:20 * 2048 + len(root)] = root
    directory = record(b"\0", 21, 2048, True) + record(b"\1", 20, 2048, True)
    directory += record(b"LEVEL1.REL;1", 22, 8)
    image[21 * 2048:21 * 2048 + len(directory)] = directory
    image[22 * 2048:22 * 2048 + 8] = b"SNR2abcd"
    image[23 * 2048:23 * 2048 + 4] = b"\x7fELF"
    return bytes(image)


class TestISO(unittest.TestCase):
    def patch(self, replacements):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        source, output = Path(folder.name) / "clean.iso", Path(folder.name) / "patched.iso"
        source.write_bytes(fixture())
        write_patched_iso(source, output, replacements)
        self.assertEqual(source.read_bytes(), fixture())
        return output

    def test_nested_file(self):
        iso = ISOImage(io.BytesIO(fixture()))
        self.assertEqual(iso.read_file(LEVEL_FILES[1]), b"SNR2abcd")
        self.assertEqual(iso.read_file(EXECUTABLE), b"\x7fELF")

    def test_not_an_iso(self):
        with self.assertRaises(ValueError):
            ISOImage(io.BytesIO(bytes(24 * 2048)))

    def test_file_that_fits_stays_in_place(self):
        output = self.patch({LEVEL_FILES[1]: b"SNR2AP"})
        with output.open("rb") as stream:
            iso = ISOImage(stream)
            self.assertEqual(iso.read_file(LEVEL_FILES[1]), b"SNR2AP")
            self.assertEqual(iso.files[LEVEL_FILES[1]].offset, 22 * 2048)
        self.assertEqual(output.stat().st_size, len(fixture()))

    def test_grown_file_moves_to_the_end(self):
        data = b"SNR2" + bytes(range(256)) * 20
        output = self.patch({LEVEL_FILES[1]: data})
        with output.open("rb") as stream:
            iso = ISOImage(stream)
            self.assertEqual(iso.read_file(LEVEL_FILES[1]), data)
            self.assertEqual(iso.files[LEVEL_FILES[1]].offset, len(fixture()))
            self.assertEqual(iso.files[EXECUTABLE].offset, 23 * 2048)
            self.assertEqual(iso.read_file(EXECUTABLE), b"\x7fELF")
        volume_sectors = int.from_bytes(output.read_bytes()[16 * 2048 + 80:16 * 2048 + 84], "little")
        self.assertEqual(volume_sectors * 2048, output.stat().st_size)

    def test_paths_cover_native_modules(self):
        self.assertLessEqual(set(CASE_MODULES.values()), set(LEVEL_FILES))
        self.assertEqual(len(MODULE_FILES), 31)
        with self.assertRaises(TypeError):
            LEVEL_FILES[1] = "wrong"

    def test_expanded_files_are_independent_of_dictionary_order(self):
        replacements = {EXECUTABLE: b"ELF" * 1000, LEVEL_FILES[1]: b"SNR2" * 1000}
        forward = self.patch(replacements).read_bytes()
        backward = self.patch(dict(reversed(list(replacements.items())))).read_bytes()
        self.assertEqual(forward, backward)
