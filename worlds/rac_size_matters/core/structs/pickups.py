import ctypes

from ...interface_orchestrator.structs.base import MemoryStruct
from ..address_maps import (
    ARMOUR_BASE,
    ARMOUR_SET_COLLECTED_ADDR,
    CLANK_CHALLENGE_BASE,
    CLANK_CHALLENGE_SIZE,
    SKILL_POINTS_BASE,
    SKYBOARD_BASE,
    TITANIUM_BOLT_BASE,
)

# Armour

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


class ArmourSetCollectedStruct(MemoryStruct):
    """Two bytes starting at ARMOUR_SET_COLLECTED_ADDR.

    Byte 0 (0x21F4B442) — pure armour sets collected:
        bit 0 (0x01) = Wildfire      bit 4 (0x10) = Mega Bomb
        bit 1 (0x02) = Sludge Mk9   bit 5 (0x20) = Hyperborean
        bit 2 (0x04) = Crystallix   bit 6 (0x40) = Chameleon
        bit 3 (0x08) = Electroshock

    Byte 1 (0x21F4B443) — hybrid combos equipped:
        bit 0 (0x01) = Shock Crystal   bit 3 (0x08) = Ice II
        bit 1 (0x02) = Wildburst       bit 4 (0x10) = Stalker
        bit 2 (0x04) = Triple Wave
    """
    BASE_ADDRESS = ARMOUR_SET_COLLECTED_ADDR
    _pack_ = 1
    _fields_ = [
        ("pure_sets",   ctypes.c_uint8),
        ("hybrid_sets", ctypes.c_uint8),
    ]


# Weapons / gadgets

class WeaponStruct(MemoryStruct):

    BASE_ADDRESS = 0
    _pack_ = 1
    _fields_ = [
        ("mod_slot_one",     ctypes.c_uint8),
        ("mod_slot_two",     ctypes.c_uint8),
        ("mod_slot_three",   ctypes.c_uint8),
        ("mod_unlock_one",   ctypes.c_uint8),  # 0/1 — slot purchasable in vendor
        ("mod_unlock_two",   ctypes.c_uint8),
        ("mod_unlock_three", ctypes.c_uint8),
        ("_pad",             ctypes.c_uint8 * 2),
        ("unlocked",         ctypes.c_uint8),
    ]

    _MOD_FIELD_OFFSET = 0x3D
    _UNLOCK_FIELD_OFFSET = 0x45

class GadgetStruct(MemoryStruct):

    BASE_ADDRESS = 0
    _pack_ = 1
    _fields_ = [
        ("icon",     ctypes.c_uint32),
        ("_pad",     ctypes.c_uint8 * 0x24),
        ("unlocked", ctypes.c_uint8),
    ]

    _ICON_FIELD_OFFSET = 0x1D
    _UNLOCK_FIELD_OFFSET = 0x45

def make_weapon_struct_cls(name: str, weapon_base: int) -> type[WeaponStruct]:
    return type(
        f"WeaponStruct_{name}",
        (WeaponStruct,),
        {"BASE_ADDRESS": weapon_base + WeaponStruct._MOD_FIELD_OFFSET},
    )

def make_gadget_struct_cls(name: str, gadget_base: int) -> type[GadgetStruct]:
    return type(
        f"GadgetStruct_{name}",
        (GadgetStruct,),
        {"BASE_ADDRESS": gadget_base + GadgetStruct._ICON_FIELD_OFFSET},
    )


# Skill points

class SkillPointsStruct(MemoryStruct):

    BASE_ADDRESS = SKILL_POINTS_BASE
    _pack_ = 1
    _fields_ = [
        ("low",  ctypes.c_uint32),  # bits 0-31
        ("high", ctypes.c_uint8),   # bits 32-39
    ]

    @property
    def bitmask(self) -> int:
        return self.low | (self.high << 32)

    @bitmask.setter
    def bitmask(self, value: int) -> None:
        self.low  = value & 0xFFFFFFFF
        self.high = (value >> 32) & 0xFF


# Titanium bolts

class TitaniumBoltStruct(MemoryStruct):

    BASE_ADDRESS = TITANIUM_BOLT_BASE
    _pack_ = 1
    _fields_ = [
        ("pickup", ctypes.c_uint8),
        ("_pad",   ctypes.c_uint8 * 4),
        ("total",  ctypes.c_uint8),
    ]


# Challenges

class ClankChallengeStruct(MemoryStruct):

    BASE_ADDRESS = CLANK_CHALLENGE_BASE
    _pack_ = 1
    _fields_ = [
        ("_body", ctypes.c_uint8 * CLANK_CHALLENGE_SIZE),
    ]

class SkyboardStruct(MemoryStruct):

    BASE_ADDRESS = SKYBOARD_BASE
    _pack_ = 1
    _fields_ = [
        ("kalidon_low",        ctypes.c_uint8),
        ("kalidon_high",       ctypes.c_uint8),
        ("outpost_omega_low",  ctypes.c_uint8),
        ("outpost_omega_high", ctypes.c_uint8),
    ]
