CLANK_START_NANOTECH = 15
CLANK_NG_CAP = 60
CLANK_NG_PLUS_CAP = 85


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
