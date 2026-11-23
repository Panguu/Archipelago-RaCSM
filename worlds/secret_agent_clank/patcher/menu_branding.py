"""Swaps the main-menu logo by changing only PIC1's pixels and palette. Everything
else in the frontend archive is left as it was.
"""
import copy
from collections import Counter
import hashlib
import io
from importlib.resources import files
import zipfile

import Utils


MEMBER = "GUI/CommonFrontEnd.san.cooked"
WIDTH, HEIGHT = 512, 256
LOGO_WIDTH, LOGO_HEIGHT = 216, 24
LOGO_X, LOGO_Y = 36, 189
PIXELS = 0xCC8 + 0x1A200
PALETTE = PIXELS + WIDTH * HEIGHT
# Filled from the clean USA asset, not from a patched or emulator texture dump.
SOURCE_SHA256 = "a68c974b39e090f61400a827b33b29f0560fdf311d278c26852955c763c3d697"
BRANDS = ("archipelago", "multiworldgg")


def app_branding() -> str:
    """Which main-menu logo to use, from the app this is running in.

    MultiworldGG sets Utils.instance_name to "MultiworldGG"; Archipelago has no
    instance_name at all, hence getattr.
    """
    app_name = getattr(Utils, "instance_name", None) or "Archipelago"
    return "multiworldgg" if app_name == "MultiworldGG" else "archipelago"


def palette_offset(index):
    physical = (index & ~24) | ((index & 8) << 1) | ((index & 16) >> 1)
    return PALETTE + physical * 4


def patch_multiworldgg(data, root):
    """Reserve 31 rare background colours for the supplied full-colour logo."""
    pixels = root.joinpath("multiworldgg-wordmark.indices").read_bytes()
    colours = root.joinpath("multiworldgg-wordmark.clut").read_bytes()
    if len(pixels) != 264 * 22 or max(pixels) > 31 or len(colours) != 128:
        raise ValueError("Invalid MultiWorldGG menu wordmark")
    usage = Counter(data[PIXELS:PALETTE])
    reserved = sorted(range(256), key=lambda i: (usage[i], i))[:31]
    kept = sorted(set(range(256)) - set(reserved))
    palette = [data[palette_offset(i):palette_offset(i) + 3] for i in range(256)]
    remap = bytearray(range(256))
    for index in reserved:
        remap[index] = min(kept, key=lambda candidate: sum(
            (a - b) ** 2 for a, b in zip(palette[index], palette[candidate])))
    result = bytearray(data)
    result[PIXELS:PALETTE] = data[PIXELS:PALETTE].translate(bytes(remap))
    for colour, index in enumerate(reserved, 1):
        offset = palette_offset(index)
        result[offset:offset + 4] = colours[colour * 4:colour * 4 + 4]
    for offset, pixel in enumerate(pixels):
        if pixel:
            y, x = divmod(offset, 264)
            result[PIXELS + (LOGO_Y + y) * WIDTH + LOGO_X + x] = reserved[pixel - 1]
    return bytes(result)


def patch_background(data: bytes, branding="archipelago") -> bytes:
    if branding not in BRANDS:
        raise ValueError(f"Unknown menu branding: {branding}")
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
        raise ValueError("Unexpected USA frontend background; refusing to patch")
    root = files(__package__.split('.patcher')[0]).joinpath("icon")
    if branding == "multiworldgg":
        return patch_multiworldgg(data, root)
    mask = root.joinpath("archipelago-wordmark.indices").read_bytes()
    if len(mask) != LOGO_WIDTH * LOGO_HEIGHT or set(mask) != {0, 1}:
        raise ValueError("Invalid Archipelago menu wordmark")
    # CSM1 palettes swap bits 3 and 4 of the logical palette index.
    def brightness(index):
        r, g, b = data[palette_offset(index):palette_offset(index) + 3]
        return 299 * r + 587 * g + 114 * b

    light = max(range(256), key=brightness)
    dark = min(range(256), key=brightness)
    result = bytearray(data)
    for shift, colour in ((1, dark), (0, light)):
        for offset, pixel in enumerate(mask):
            if pixel:
                y, x = divmod(offset, LOGO_WIDTH)
                result[PIXELS + (LOGO_Y + y + shift) * WIDTH + LOGO_X + x + shift] = colour
    return bytes(result)


def patch_menu_archive(data: bytes, branding="archipelago") -> bytes:
    """Add the new logo file to the end of the ZIP and point the central directory
    at it. The old copy is still in the file but nothing refers to it, and every
    other entry is left untouched.
    """
    stream = io.BytesIO(data)
    with zipfile.ZipFile(stream, "a") as archive:
        matches = [info for info in archive.infolist() if info.filename == MEMBER]
        if len(matches) != 1:
            raise ValueError("Expected one frontend asset in IMAGE.ZIP")
        info = matches[0]
        replacement = patch_background(archive.read(info), branding)
        archive.filelist.remove(info)
        del archive.NameToInfo[MEMBER]
        archive.writestr(copy.copy(info), replacement)
    return stream.getvalue()
