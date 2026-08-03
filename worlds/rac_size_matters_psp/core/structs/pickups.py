import ctypes

from .base import MemoryStruct
from ..address_maps import ARMOUR_BASE


class ArmourStruct(MemoryStruct):

    BASE_ADDRESS = ARMOUR_BASE
    _pack_ = 1
    _fields_ = [
        ("chestplate",   ctypes.c_uint8),
        ("helmet",       ctypes.c_uint8),
        ("gloves_left",  ctypes.c_uint8),
        ("gloves_right", ctypes.c_uint8),
        ("boots_left",   ctypes.c_uint8),
        ("boots_right",  ctypes.c_uint8),
        ("wildfire",     ctypes.c_uint8),
        ("sludge",       ctypes.c_uint8),
        ("crystallix",   ctypes.c_uint8),
        ("electroshock", ctypes.c_uint8),
        ("mega_bomb",    ctypes.c_uint8),
        ("hyperborean",  ctypes.c_uint8),
        ("chameleon",    ctypes.c_uint8),
    ]

    SLOT_FIELDS: tuple[str, ...] = (
        "chestplate", "helmet", "gloves_left", "gloves_right", "boots_left", "boots_right",
    )
    SET_FIELDS: tuple[str, ...] = (
        "wildfire", "sludge", "crystallix", "electroshock", "mega_bomb", "hyperborean", "chameleon",
    )
