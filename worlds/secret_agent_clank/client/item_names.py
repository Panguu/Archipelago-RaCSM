"""Translate historical AP equipment names without reinterpreting numeric IDs."""
from ..constants.weapons import EQUIPMENT_INTERNAL_TO_DISPLAY, CLANK_PICKUP_TO_INTERNAL
from ..constants.weapon_progression import PROGRESSIVE_TO_INTERNAL

# Earlier seeds classified several Clank tools as Ratchet unlocks.
LEGACY_EQUIPMENT_NAMES = {
    f"Unlock: {character} {internal}": display
    for internal, display in EQUIPMENT_INTERNAL_TO_DISPLAY.items()
    for character in ("Ratchet", "Clank")
}
LEGACY_EQUIPMENT_NAMES.update({
    old: EQUIPMENT_INTERNAL_TO_DISPLAY[internal]
    for old, internal in {
        "Unlock: Clank Bowtie": "throwTie",
        "Unlock: Clank Cufflink": "CuffLink",
        "Unlock: Clank Tanglevine": "TangleVine",
        "Unlock: Clank Flamethrower Briefcase": "FlamethrowerPen",
        "Unlock: Clank HoloKnuckles": "HoloKnuckles",
        "Unlock: Clank PDA": "clankpda",
    }.items()
})
LEGACY_EQUIPMENT_NAMES.update({
    name.rsplit(": ", 1)[-1]: name for name in CLANK_PICKUP_TO_INTERNAL
})
_PROGRESSIVE_BY_INTERNAL = {internal: name for name, internal in PROGRESSIVE_TO_INTERNAL.items()}
LEGACY_EQUIPMENT_NAMES.update({
    "Progressive: " + old.removeprefix("Unlock: "): _PROGRESSIVE_BY_INTERNAL[internal]
    for old, current in list(LEGACY_EQUIPMENT_NAMES.items()) if old.startswith("Unlock: ")
    for internal, display in EQUIPMENT_INTERNAL_TO_DISPLAY.items()
    if display == current and internal in _PROGRESSIVE_BY_INTERNAL
})


def canonical_item_name(server_name: str) -> str:
    return LEGACY_EQUIPMENT_NAMES.get(server_name, server_name)
