"""Native watchdog: a missed client heartbeat leaves a persistent HUD warning."""
from . import mips as m
from .asm import Patch, jump, packed
from .plan import Plan

HEARTBEAT_FRAMES = 180
MESSAGE = b"\x90\x03DISCONNECTED FROM ARCHIPELAGO\0"


def prepare(pine, *, arena, font, colour, text):
    # Vendor reserves [arena, arena + 0x800). Skins occupy +0x100..+0x1f1
    # and Inside Clank's exit occupies +0x300..+0x364.
    entry, heartbeat, message = arena + 0x400, arena + 0x4C0, arena + 0x4C4
    words = [
        *m.li32(m.T0, heartbeat), m.lw(m.T1, 0, m.T0),
        m.beq(m.T1, m.ZERO, 5), m.NOP,
        m.addiu(m.T1, m.T1, -1), m.sw(m.T1, 0, m.T0), m.jr(m.RA), m.NOP,
        m.addiu(m.SP, m.SP, -16), m.sd(m.RA, 0, m.SP),
        m.daddu(m.A0, m.ZERO, m.ZERO), jump(font), m.daddu(m.A1, m.ZERO, m.ZERO),
        m.lui(m.A0, 0xFFFF), jump(colour), m.ori(m.A0, m.A0, 0xFFFF),
        *m.li32(m.A2, message), m.addiu(m.A0, m.ZERO, 0xEF),
        jump(text), m.addiu(m.A1, m.ZERO, 0x30),
        m.ld(m.RA, 0, m.SP), m.jr(m.RA), m.addiu(m.SP, m.SP, 16),
    ]
    payload = packed(*words).ljust(heartbeat - entry, b'\0') + packed(0) + MESSAGE
    plan = Plan(pine, [Patch(entry, pine.read_bytes(entry, len(payload)), payload)])
    plan.mutable_data = ((heartbeat, 4),)
    plan.entry, plan.heartbeat, plan.message = entry, heartbeat, message
    return plan


def refresh(plan, connected):
    plan._validate(replacement=True)
    plan.pine.write_int32(plan.heartbeat, HEARTBEAT_FRAMES if connected else 0)
