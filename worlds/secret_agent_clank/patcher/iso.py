"""We only ever patch one known disc, and the patcher checks its SHA-256 before
using it, so this doesn't try to handle ISO9660 features that disc doesn't use.
"""
from collections.abc import Callable
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import BinaryIO

SECTOR = 2048
CHUNK = 1024 * 1024

# Called with a status message and how far through it is, from 0.0 to 1.0.
Progress = Callable[[str, float], None]


def scaled(progress: Progress | None, start: float, end: float) -> Progress | None:
    """Make a step's own 0-1 progress cover just the start-end part of the whole bar."""
    if progress is None:
        return None
    return lambda message, fraction: progress(message, start + (end - start) * fraction)


@dataclass
class DiscFile:
    offset: int  # where the file's data starts
    size: int
    record: int  # where its directory record is, so it can be moved or resized


def _extent(record: bytes) -> tuple[int, int]:
    # ISO9660 stores numbers twice (little- then big-endian); the little half is enough.
    sector = int.from_bytes(record[2:6], "little")
    size = int.from_bytes(record[10:14], "little")
    return sector * SECTOR, size


def _write_both_endian(out: BinaryIO, offset: int, value: int) -> None:
    out.seek(offset)
    out.write(value.to_bytes(4, "little") + value.to_bytes(4, "big"))


class ISOImage:
    """The files on a disc image, by path (e.g. "/BIN/LEVEL1.REL;1")."""

    def __init__(self, stream: BinaryIO):
        self.stream = stream
        self.files: dict[str, DiscFile] = {}
        descriptor = self._read(16 * SECTOR, SECTOR)
        if descriptor[:6] != b"\x01CD001":
            raise ValueError("Not an ISO9660 disc image")
        self._read_directory(descriptor[156:190], "")

    def _read(self, offset: int, size: int) -> bytes:
        self.stream.seek(offset)
        return self.stream.read(size)

    def _read_directory(self, record: bytes, path: str) -> None:
        offset, size = _extent(record)
        data = self._read(offset, size)
        position = 0
        while position < size:
            length = data[position]
            if length == 0:
                # Records don't cross sectors; the rest of this sector is padding.
                position = (position // SECTOR + 1) * SECTOR
                continue
            entry = data[position:position + length]
            name = entry[33:33 + entry[32]]
            if name not in (b"\x00", b"\x01"):  # skip "." and ".."
                child = f"{path}/{name.decode('ascii')}"
                if entry[25] & 2:
                    self._read_directory(entry, child)
                else:
                    self.files[child] = DiscFile(*_extent(entry), record=offset + position)
            position += length

    def read_file(self, path: str) -> bytes:
        file = self.files[path]
        return self._read(file.offset, file.size)


def sha256_file(path: str | Path, progress: Progress | None = None, message: str = "Hashing") -> str:
    digest = hashlib.sha256()
    total = Path(path).stat().st_size
    with open(path, "rb") as stream:
        while block := stream.read(CHUNK):
            digest.update(block)
            if progress:
                progress(message, stream.tell() / total)
    return digest.hexdigest()


def write_patched_iso(source: str | Path, target: str | Path, replacements: dict[str, bytes],
                      progress: Progress | None = None) -> None:
    """Copy the disc at `source` to `target`, swapping in the given files.

    A replacement that fits keeps its file's place on the disc. One that has
    grown is moved to the end of the disc, so no other file has to move.
    """
    with open(source, "rb") as src, open(target, "wb") as out:
        iso = ISOImage(src)
        total = src.seek(0, 2)
        src.seek(0)
        while block := src.read(CHUNK):
            out.write(block)
            if progress:
                progress("Copying the ISO", src.tell() / total)

        end = total
        # Build-time dictionaries and sorted .apsac manifests have different
        # insertion orders. Appended extents must be deterministic for hashes.
        for path, data in sorted(replacements.items()):
            file = iso.files[path]
            if len(data) <= file.size:
                offset = file.offset
                out.seek(offset)
                out.write(data + bytes(file.size - len(data)))
            else:
                offset = end
                end += (len(data) + SECTOR - 1) // SECTOR * SECTOR  # round up to whole sectors
                out.seek(offset)
                out.write(data)
            _write_both_endian(out, file.record + 2, offset // SECTOR)
            _write_both_endian(out, file.record + 10, len(data))

        out.truncate(end)
        _write_both_endian(out, 16 * SECTOR + 80, end // SECTOR)  # volume size
