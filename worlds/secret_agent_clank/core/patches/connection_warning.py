"""Game-side heartbeat watchdog, independent of the client after installation."""
from ..notifications import ItemNotifications
from ..symbols import require
from . import mips as m
from .asm import Patch, jump, packed, words
from .vendor_presentation import triangle_storage

HEARTBEAT_FRAMES = 180
MESSAGE = b"Disconnected from Archipelago\nReconnect the AP client\0"


class ConnectionWarning:
    def __init__(self, pine):
        self.pine = pine
        self.heartbeat = self.entry = None

    @staticmethod
    def routine(heartbeat, message, show, render, original, cooldown):
        code = [*m.li32(m.T0, heartbeat), m.lw(m.T1, 0, m.T0),
                m.beq(m.T1, m.ZERO, 5), m.NOP,
                m.addiu(m.T1, m.T1, -1), m.sw(m.T1, 0, m.T0),
                0, m.NOP,
                m.addiu(m.SP, m.SP, -16), m.sd(m.RA, 0, m.SP),
                *m.li32(m.T0, cooldown), m.sw(m.ZERO, 0, m.T0),
                *m.li32(m.A0, message), m.addiu(m.A1, m.ZERO, 0),
                jump(show, True), m.addiu(m.A2, m.ZERO, 60),
                m.ld(m.RA, 0, m.SP), m.addiu(m.SP, m.SP, 16)]
        # Replay the displaced prologue on both paths with the original RA/SP.
        code[7] = m.beq(m.ZERO, m.ZERO, len(code) - 8)
        code += [*words(original), jump(render + 8), m.NOP]
        return packed(code)

    def prepare(self, symbols, hooks):
        self.heartbeat = self.entry = None
        p = self.pine
        notifications = ItemNotifications(p)
        if not notifications.bind(symbols):
            raise RuntimeError("Connection warning HUD layout changed")
        cooldown = notifications.binding[2]
        show, render = require(symbols, "HUD_ShowOneLiner__FPCcbi", "HUD_RenderOneLiner__Fv")
        original = p.read_bytes(render, 8)
        first, second = words(original)
        if first != m.addiu(m.SP, m.SP, -32) or second & 0xFFE00000 != 0xFFA00000:
            raise RuntimeError("Connection warning render prologue changed")
        storage, native = triangle_storage(p, symbols)
        # Vendor text uses the head of this verified no-op function. Reserve
        # only the tail; reject overlap with any other native patch.
        entry = storage + 152
        heartbeat, message = storage + 252, storage + 256
        code = self.routine(heartbeat, message, show, render, original, cooldown)
        if len(code) > heartbeat - entry:
            raise RuntimeError("Connection warning exceeds verified storage")
        payload = code.ljust(heartbeat - entry, b"\0") + packed([0]) + MESSAGE
        if entry + len(payload) > storage + len(native):
            raise RuntimeError("Connection warning message exceeds verified storage")
        edits = [Patch(entry, p.read_bytes(entry, len(payload)), payload),
                 Patch(render, original, packed([jump(entry), m.NOP]))]
        if not any(x.address == storage for x in hooks.patches):
            edits.insert(0, Patch(storage, native[:8], packed([m.jr(m.RA), m.NOP])))
        for edit in edits:
            if any(edit.address < x.address + len(x.replacement)
                   and x.address < edit.address + len(edit.replacement) for x in hooks.patches):
                raise RuntimeError("Connection warning storage is occupied")
        self.entry, self.heartbeat = entry, heartbeat
        self.code = code
        return edits

    def refresh(self, connected):
        if self.heartbeat is None:
            return
        if self.pine.read_bytes(self.entry, len(self.code)) != self.code:
            raise RuntimeError("Connection warning code changed")
        self.pine.write_int32(self.heartbeat, HEARTBEAT_FRAMES if connected else 0)
