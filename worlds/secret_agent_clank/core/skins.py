import struct

from ..constants import (
    ALL_SKINS_MASK,
    DEFAULT_RATCHET_SKIN,
    QWARK_GIANT_SKINS,
    SKINS_BY_CHARACTER,
    SKIN_CHARACTER_STRIDE,
    SKIN_OWNED_OFFSET,
    SKIN_SAVE_OFFSET,
    UNSUPPORTED_RATCHET_SKIN,
)
from .global_flags import GlobalFlags
from .patches import Patch, jump, mips as m, packed
from .symbols import require


class Skins:
    def __init__(self, pine):
        self.pine = pine
        self.flags = GlobalFlags(pine)
        self.selected = {}
        self.config_address = None

    def configure(self, data):
        selected = {}
        for character, skins in SKINS_BY_CHARACTER.items():
            value = int(data.get(f"{character}_skin", 0))
            if character == "ratchet" and value == UNSUPPORTED_RATCHET_SKIN:
                value = DEFAULT_RATCHET_SKIN
            if value != 0 and value not in skins.values():
                raise ValueError(f"Invalid {character} skin: {value}")
            selected[character] = value
        self.selected = selected

    def prepare(self, symbols, *, arena=None):
        """Make every skin show up in the menu without the story flags, NG+, codes
        or Size Matters save some of them need. Owning them is handled by sync().
        """
        self.config_address = arena.allocate(bytes(4)) if arena is not None else None
        if not self.flags.bind(symbols):
            raise RuntimeError("Skin save pointer could not be validated")
        selected = require(symbols, "SelectedSPHeroSkinID__F8PLR_TYPE")
        words = struct.unpack("<11I", self.pine.read_bytes(selected, 44))
        low = words[4] & 0xFFFF
        pointer = ((words[3] & 0xFFFF) << 16) + (low - 0x10000 if low & 0x8000 else low)
        if (words[:3] != (0x0080302D, 0x24050034, 0x00C52818)
                or words[3] & 0xFFFF0000 != 0x3C040000
                or words[4] & 0xFFFF0000 != 0x8C830000
                or words[5:] != (0x3C020001, 0x34428000, 0x00651821,
                                  0x00621821, 0x80621900, 0x14400018)
                or pointer != self.flags.pointer_address):
            raise RuntimeError("Native skin save layout changed")
        address = require(symbols, "IsSkinUnlocked__F12SPHeroSkinId")
        original = self.pine.read_bytes(address, 16)
        if original != packed([0x27BDFFF0, 0x2483FFFE, 0xFFB00000, 0x2C620012]):
            raise RuntimeError("Native skin unlock predicate changed")
        # Robo-Ratchet stays hidden: its model isn't on the disc, and even
        # previewing it can crash the loader. The unlock check now returns
        # straight away, and its body holds a routine that runs on the game
        # thread once a new save exists but before the skin model loads.
        load = require(symbols, "HEROSKIN_LoadSelectedSpecilaSkin__Fv")
        loader = struct.unpack("<11I", self.pine.read_bytes(load + 0x0C, 44))
        low = loader[3] & 0xFFFF
        loader_pointer = ((loader[0] & 0xFFFF) << 16) + (low - 0x10000 if low & 0x8000 else low)
        if (loader[0] & 0xFFFF0000 != 0x3C020000
                or loader[2] != 0x24070034
                or loader[3] & 0xFFFF0000 != 0x8C430000
                or loader[4:] != (0x3C040001, 0x8CC50574, 0x34848000,
                                   0x8CA20044, 0x00471018, 0x00621821, 0x00641821)
                or loader_pointer != pointer):
            raise RuntimeError("Native skin loader save layout changed")
        displaced = self.pine.read_bytes(load + 0x38, 8)
        if displaced != packed([0x80631900, 0x10600003]):
            raise RuntimeError("Native skin loader changed")
        code = [*m.li32(m.T0, pointer), m.lw(m.T0, 0, m.T0),
                *m.li32(m.T1, SKIN_SAVE_OFFSET), m.addu(m.T1, m.T0, m.T1),
                m.lbu(m.T2, 0, m.T1), m.addiu(m.T3, m.ZERO, UNSUPPORTED_RATCHET_SKIN),
                m.bne(m.T2, m.T3, 2), m.addiu(m.T2, m.ZERO, DEFAULT_RATCHET_SKIN),
                m.sb(m.T2, 0, m.T1),
                *m.li32(m.T1, SKIN_OWNED_OFFSET), m.addu(m.T1, m.T0, m.T1),
                m.lw(m.T2, 0, m.T1), *m.li32(m.T3, ALL_SKINS_MASK)]
        # Owning every skin marks the save as set up. From then on the menu's
        # selection (including the default, 0) is kept across loads and restarts.
        code += [m.and_(m.T2, m.T2, m.T3)]
        initialized_branch = len(code)
        code += [0, m.NOP, m.lw(m.T2, 0, m.T1),
                m.or_(m.T2, m.T2, m.T3), m.sw(m.T2, 0, m.T1),
                *m.li32(m.T1, SKIN_SAVE_OFFSET), m.addu(m.T0, m.T0, m.T1)]
        if arena is not None:
            code += [*m.li32(m.T3, self.config_address)]
            for player_type in range(4):
                code += [m.lbu(m.T1, player_type, m.T3), m.beq(m.T1, m.ZERO, 2), m.NOP,
                         m.sb(m.T1, player_type * SKIN_CHARACTER_STRIDE, m.T0)]
        for player_type, character in enumerate(SKINS_BY_CHARACTER if arena is None else ()):
            skin = self.selected.get(character, 0)
            if skin:
                code += [m.addiu(m.T1, m.ZERO, skin),
                         m.sb(m.T1, player_type * SKIN_CHARACTER_STRIDE, m.T0)]
                if character == "qwark":
                    code += [m.addiu(m.T1, m.ZERO, QWARK_GIANT_SKINS[skin]),
                             m.sb(m.T1, 3 * SKIN_CHARACTER_STRIDE, m.T0)]
        code[initialized_branch] = m.beq(m.T2, m.T3, len(code) - initialized_branch - 1)
        code += [0x80631900, m.beq(m.V1, m.ZERO, 3), m.NOP,
                 jump(load + 0x40), m.NOP, jump(load + 0x4C), m.NOP]
        predicate = [m.xori(m.V0, m.A0, UNSUPPORTED_RATCHET_SKIN),
                     m.jr(m.RA), m.sltu(m.V0, m.ZERO, m.V0)]
        if arena is not None:
            entry = arena.allocate(packed(code))
            return [Patch(address, original[:12], packed(predicate)),
                    Patch(load + 0x38, displaced, packed([jump(entry), m.NOP]))]
        replacement = packed([*predicate, *code])
        if len(replacement) > 0xF8:
            raise RuntimeError("Skin initialization exceeds predicate storage")
        # Check the predicate's return as well as its entry before reusing it.
        if self.pine.read_bytes(address + 0xE4, 16) != packed(
                [0xDFB00000, 0xDFBF0008, 0x03E00008, 0x27BD0010]):
            raise RuntimeError("Native skin unlock predicate extent changed")
        return [Patch(address, self.pine.read_bytes(address, len(replacement)), replacement),
                Patch(load + 0x38, displaced, packed([jump(address + len(predicate) * 4), m.NOP]))]

    def sync(self):
        """Called at the loader gate, before the skin model loads, and while playing.

        The YAML defaults are only applied the first time a save's skins are
        unlocked. After that the player's menu choice is kept.
        """
        if self.config_address is not None:
            choices = [self.selected.get(character, 0) for character in SKINS_BY_CHARACTER]
            choices.append(QWARK_GIANT_SKINS.get(self.selected.get("qwark", 0), 0))
            self.pine.write_bytes(self.config_address, bytes(choices))
        pointer = self.flags.pointer_address
        if pointer is None:
            return False
        base = self.pine.read_int32(pointer)
        if not 0x100000 <= base <= 0x2000000 - SKIN_OWNED_OFFSET - 4:
            return False
        owned_address = base + SKIN_OWNED_OFFSET
        owned = self.pine.read_int32(owned_address)
        if self.pine.read_int32(pointer) != base:
            return False
        ratchet_address = base + SKIN_SAVE_OFFSET
        if self.pine.read_int8(ratchet_address) == UNSUPPORTED_RATCHET_SKIN:
            self.pine.write_int8(ratchet_address, DEFAULT_RATCHET_SKIN)
        if owned & ALL_SKINS_MASK == ALL_SKINS_MASK:
            return True
        for player_type, character in enumerate(SKINS_BY_CHARACTER):
            skin = self.selected.get(character, 0)
            if skin:
                address = base + SKIN_SAVE_OFFSET + player_type * SKIN_CHARACTER_STRIDE
                if self.pine.read_int8(address) != skin:
                    self.pine.write_int8(address, skin)
                if character == "qwark":
                    address += SKIN_CHARACTER_STRIDE
                    giant = QWARK_GIANT_SKINS[skin]
                    if self.pine.read_int8(address) != giant:
                        self.pine.write_int8(address, giant)
        # Publish initialization last so interrupted writes can be retried.
        self.pine.write_int32(owned_address, owned | ALL_SKINS_MASK)
        return True
