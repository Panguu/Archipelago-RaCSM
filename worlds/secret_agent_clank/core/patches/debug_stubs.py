"""Exact retail no-op debug stubs eligible for reclaimed hook storage."""
from dataclasses import dataclass

from ...constants.native_functions import DebugDrawFunctions
from . import mips as m
from .asm import packed
from .mips import jr

TEXT_SIGNATURE = packed([
    m.addiu(m.SP, m.SP, -112), m.sd(m.A3, 72, m.SP), m.sd(m.T0, 80, m.SP), m.sd(m.T1, 88, m.SP),
    m.sd(m.T2, 96, m.SP), m.sd(m.T3, 104, m.SP), m.swc1(m.F12, 56, m.SP), m.swc1(m.F14, 60, m.SP),
    m.swc1(m.F16, 64, m.SP), m.swc1(m.F18, 68, m.SP), jr(m.RA), m.addiu(m.SP, m.SP, 112),
])
VECTOR_SIGNATURE = packed([
    m.addiu(m.SP, m.SP, -112), m.sd(m.A2, 64, m.SP), m.sd(m.A3, 72, m.SP), m.sd(m.T0, 80, m.SP),
    m.sd(m.T1, 88, m.SP), m.sd(m.T2, 96, m.SP), m.sd(m.T3, 104, m.SP), m.swc1(m.F12, 48, m.SP),
    m.swc1(m.F14, 52, m.SP), m.swc1(m.F16, 56, m.SP), m.swc1(m.F18, 60, m.SP), jr(m.RA),
    m.addiu(m.SP, m.SP, 112),
])
STYLED_SIGNATURE = packed([
    m.addiu(m.SP, m.SP, -96), m.sd(m.T0, 64, m.SP), m.sd(m.T1, 72, m.SP), m.sd(m.T2, 80, m.SP),
    m.sd(m.T3, 88, m.SP), m.swc1(m.F12, 48, m.SP), m.swc1(m.F14, 52, m.SP), m.swc1(m.F16, 56, m.SP),
    m.swc1(m.F18, 60, m.SP), jr(m.RA), m.addiu(m.SP, m.SP, 96),
])


@dataclass(frozen=True)
class DebugStub:
    symbol: str
    signature: bytes


# Order is also the frontend STUBS order in StartingCase.
DEBUG_STUBS = (
    DebugStub(DebugDrawFunctions.PRINT_TEXT, TEXT_SIGNATURE),
    DebugStub(DebugDrawFunctions.PRINT_VECTOR_TEXT, VECTOR_SIGNATURE),
    DebugStub(DebugDrawFunctions.PRINT_DROP_TEXT, STYLED_SIGNATURE),
    DebugStub(DebugDrawFunctions.PRINT_OUTLINE_TEXT, STYLED_SIGNATURE),
)
