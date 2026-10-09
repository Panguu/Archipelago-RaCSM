"""Clank progression, verified against the USA PS2 native progression table.

See docs/nanotech.md for the native cap and per-operative save layout evidence.
"""
CLANK_START_NANOTECH = 15
CLANK_NG_CAP = 60
CLANK_NG_PLUS_CAP = 85
CLANK_XP_SAVE_OFFSET = 0x19930
CLANK_XP_THRESHOLDS = (0, 700, 2200, 4100, 6300, 8900, 11700, 14700, 18000, 21500, 25200, 29100, 33200, 37400, 41800, 46400, 51100, 56000, 61000, 66200, 71500, 76900, 82500, 88200, 94000, 100000, 106000, 112200, 118500, 124900, 131400, 138100, 144800, 151700, 158600, 165700, 172800, 180100, 187500, 194900, 202500, 210100, 217900, 225700, 233600, 241700, 249800, 258000, 266300, 274600, 283100, 291600, 300300, 309000, 317800, 326600, 335600, 344600, 353600, 363000, 372200, 381600, 391000, 400500, 410100, 419800, 429500, 439300, 449200, 459200, 469200)


def nanotech_levels(ng_plus):
    return range(CLANK_START_NANOTECH + 1, (CLANK_NG_PLUS_CAP if ng_plus else CLANK_NG_CAP) + 1)


def nanotech_location_name(level):
    return f"Clank Nanotech Level {level}"


RATCHET_START_NANOTECH = 20
RATCHET_NG_CAP = 60
RATCHET_NG_PLUS_CAP = 90


def ratchet_nanotech_levels(ng_plus):
    return range(RATCHET_START_NANOTECH + 1, (RATCHET_NG_PLUS_CAP if ng_plus else RATCHET_NG_CAP) + 1)


def ratchet_nanotech_location_name(level):
    return f"Ratchet Nanotech Level {level}"
