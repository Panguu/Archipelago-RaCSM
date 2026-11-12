"""ISO9660 paths verified against the SCUS-97623 USA disc.

Paths include the ISO9660 version suffix; module IDs are not consecutive.
Keep disc layout knowledge here rather than in native patch builders.
"""
from types import MappingProxyType
from typing import Final

SYSTEM_CNF: Final = "/SYSTEM.CNF;1"
EXECUTABLE: Final = "/SCUS_976.23;1"
FRONTEND: Final = "/BIN/FE.REL;1"
IMAGE_ARCHIVE: Final = "/IMAGE.ZIP;1"

LEVEL_FILES: Final = MappingProxyType({
    1: "/BIN/LEVEL1.REL;1",
    2: "/BIN/LEVEL2.REL;1",
    3: "/BIN/LEVEL3.REL;1",
    4: "/BIN/LEVEL4.REL;1",
    5: "/BIN/LEVEL5.REL;1",
    7: "/BIN/LEVEL7.REL;1",
    8: "/BIN/LEVEL8.REL;1",
    9: "/BIN/LEVEL9.REL;1",
    10: "/BIN/LEVEL10.REL;1",
    11: "/BIN/LEVEL11.REL;1",
    13: "/BIN/LEVEL13.REL;1",
    14: "/BIN/LEVEL14.REL;1",
    15: "/BIN/LEVEL15.REL;1",
    16: "/BIN/LEVEL16.REL;1",
    17: "/BIN/LEVEL17.REL;1",
    18: "/BIN/LEVEL18.REL;1",
    19: "/BIN/LEVEL19.REL;1",
    20: "/BIN/LEVEL20.REL;1",
    21: "/BIN/LEVEL21.REL;1",
    22: "/BIN/LEVEL22.REL;1",
    23: "/BIN/LEVEL23.REL;1",
    24: "/BIN/LEVEL24.REL;1",
    25: "/BIN/LEVEL25.REL;1",
    26: "/BIN/LEVEL26.REL;1",
    27: "/BIN/LEVEL27.REL;1",
    28: "/BIN/LEVEL28.REL;1",
    29: "/BIN/LEVEL29.REL;1",
    30: "/BIN/LEVEL30.REL;1",
    31: "/BIN/LEVEL31.REL;1",
    32: "/BIN/LEVEL32.REL;1",
})
MODULE_FILES: Final = MappingProxyType({0: FRONTEND, **LEVEL_FILES})
