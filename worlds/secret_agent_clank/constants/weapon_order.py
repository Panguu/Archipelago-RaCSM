"""Native WEAPON_ORDER slot layout for the shared Ratchet/Clank GadgetData array -- the
single source of truth for every internal (non-display) weapon/gadget slot name, so no
other module hand-types one of these strings a second time."""
from enum import IntEnum

# Positional slot order (index == raw weapon-table slot id). None = blank
# slot (0) or a slot with no name ever observed in-game (1) -- neither gets
# a WeaponAddresses entry from core/inventories/weapons.py's build_weapons(),
# matching rac_size_matters/core/weapons.py's `if name is not None` filtering.
WEAPON_ORDER: list["str | None"] = [
    None,                          # slot 0   blank
    None,                          # slot 1   unknown/unnamed (category 2, no name)
    "blaster",                     # slot 2
    "shardgun",                    # slot 3
    "beemineglove",                # slot 4
    "shockrocket",                 # slot 5
    "walloper",                    # slot 6
    "plasmawhip",                  # slot 7
    "porkbomb",                    # slot 8
    "minelauncher",                # slot 9
    "ryno",                        # slot 10
    "throwTie",                    # slot 11
    "CuffLink",                    # slot 12
    "TangleVine",                  # slot 13
    "HoloKnuckles",                # slot 14
    "FlamethrowerPen",             # slot 15
    "LightningUmbrella",           # slot 16
    "fountainpen",                 # slot 17
    "hypnowatch",                  # slot 18
    "QwarkBlaster",                # slot 19
    "Vacuum",                      # slot 20
    "GiantQwarkBlaster",           # slot 21
    "hypershot",                   # slot 22   category 1 (tool/item, not a weapon)
    "ratchetpda",                  # slot 23   category 1
    "holomonocle",                 # slot 24   category 1
    "sunglasses",                  # slot 25   category 1
    "clankpda",                    # slot 26   category 1
    "bolttransfer",                # slot 27   category 3 (wrench ability)
    "wrenchpower_firebomb",        # slot 28   category 3
    "wrenchpower_triplewave",      # slot 29   category 3
    "wrenchpower_crystallix",      # slot 30   category 3
    "wrenchpower_wildburst",       # slot 31   category 3
    "jetboots",                    # slot 32   category 3
    "omnikey",                     # slot 33   category 3
    "mapomatic",                   # slot 34   category 3
    "boltgrabber",                 # slot 35   category 3
    "boxbreaker",                  # slot 36   category 3
    "superkick",                   # slot 37   category 3
    "kickblast",                   # slot 38   category 3
    "kicksplosion",                # slot 39   category 3
]

# One member per named WEAPON_ORDER slot (the two None/blank slots have no
# member) -- built directly from WEAPON_ORDER itself so a member can never
# drift out of sync with the string it names. Lets callers write
# WeaponSlot.SHOCKROCKET instead of retyping "shockrocket" by hand.
WeaponSlot = IntEnum(
    "WeaponSlot", {name.upper(): index for index, name in enumerate(WEAPON_ORDER) if name is not None},
)
