from typing import NamedTuple

from BaseClasses import ItemClassification

from .constants import (
    CASE_NAME_TO_INFOBOT,
    CLANK_GADGETS,
    EQUIPMENT_INTERNAL_TO_DISPLAY,
    GADGETS_FROM_WEAPON_TABLE,
    KEYCARD_ITEMS,
    PROGRESSIVE_CHALLENGE_MODE,
    PROGRESSIVE_PLANET_ITEM_NAME,
    PROGRESSIVE_TO_UNLOCK,
    PROGRESSIVE_WRENCH,
    RATCHET_WEAPONS,
    SACFiller,
    TITAN_ITEMS,
    WEAPON_MODS,
    WRENCH_MOD_ITEMS,
    SACCheats,
    SACRatchetWrenchWeapons,
    SACTraps,
)

BASE_ID = 77_800_000
FILLER_ITEM_NAME = SACFiller.BOLTS

PROGRESSION = ItemClassification.progression
USEFUL = ItemClassification.useful


class SACItemData(NamedTuple):
    code: int
    classification: ItemClassification


def _items(first_id: int, names, classification: ItemClassification) -> dict[str, SACItemData]:
    return {name: SACItemData(first_id + offset, classification) for offset, name in enumerate(names)}


# Equipment stored in the game's weapon array: Ratchet's weapons, then Clank's weapons and gadgets.
RATCHET_WEAPON_ITEM_TABLE = _items(BASE_ID + 0, RATCHET_WEAPONS, PROGRESSION)
CLANK_EQUIPMENT_ITEM_TABLE = _items(BASE_ID + 11, GADGETS_FROM_WEAPON_TABLE, PROGRESSION)
EQUIPMENT_ITEM_TABLE = {**RATCHET_WEAPON_ITEM_TABLE, **CLANK_EQUIPMENT_ITEM_TABLE}
# Clank gadgets the game tracks per case instead (Blackout Pen, Therm-Optic Shades).
CASE_GADGET_ITEM_TABLE = _items(BASE_ID + 26, CLANK_GADGETS, PROGRESSION)

INFOBOT_ITEM_TABLE = _items(BASE_ID + 37, CASE_NAME_TO_INFOBOT.values(), PROGRESSION)
PROGRESSIVE_PLANET_ITEM_TABLE = _items(BASE_ID + 67, PROGRESSIVE_PLANET_ITEM_NAME.values(), PROGRESSION)

RATCHET_PACK_ITEM_TABLE = _items(BASE_ID + 81, [SACCheats.RATCHET_PACK], USEFUL)
TRAP_ITEM_TABLE = {
    **_items(BASE_ID + 82, [SACTraps.WEAPON_SWITCHING, SACTraps.MIRRORED_LEVELS,
                            SACTraps.BOLT_CONFUSION, SACTraps.BIG_HEADED], ItemClassification.trap),
    # Added later, so their IDs come after the keycards and the wrench.
    **_items(BASE_ID + 140, [SACTraps.GADGETRON_DEBT, SACTraps.ONE_HP], ItemClassification.trap),
    **_items(BASE_ID + 149, [SACTraps.DAMAGE], ItemClassification.trap),
}
FILLER_ITEM_TABLE = {
    **_items(BASE_ID + 86, [SACFiller.BOLTS], ItemClassification.filler),
    **_items(BASE_ID + 142, [SACFiller.NANOTECH_XP, SACFiller.WEAPON_XP], ItemClassification.filler),
}
# Items the client applies once each, as they're received: traps and XP filler.
EFFECT_ITEMS = frozenset({*TRAP_ITEM_TABLE, SACFiller.NANOTECH_XP, SACFiller.WEAPON_XP})

PROGRESSIVE_WRENCH_ITEM_TABLE = _items(BASE_ID + 87, [PROGRESSIVE_WRENCH], PROGRESSION)
PROGRESSIVE_WEAPON_ITEM_TABLE = _items(BASE_ID + 88, PROGRESSIVE_TO_UNLOCK, PROGRESSION)
TITAN_ITEM_TABLE = _items(BASE_ID + 103, TITAN_ITEMS, PROGRESSION)
WEAPON_MOD_ITEM_TABLE = _items(BASE_ID + 117, [mod.name for mod in WEAPON_MODS], USEFUL)
CHALLENGE_MODE_ITEM_TABLE = _items(BASE_ID + 136, [PROGRESSIVE_CHALLENGE_MODE], PROGRESSION)
KEYCARD_ITEM_TABLE = _items(BASE_ID + 137, KEYCARD_ITEMS, PROGRESSION)
WRENCH_ITEM_TABLE = {
    **_items(BASE_ID + 144, [SACRatchetWrenchWeapons.WRENCH], PROGRESSION),
    **_items(BASE_ID + 145, WRENCH_MOD_ITEMS, USEFUL),
}

ALL_ITEMS: dict[str, SACItemData] = {
    **EQUIPMENT_ITEM_TABLE,
    **CASE_GADGET_ITEM_TABLE,
    **INFOBOT_ITEM_TABLE,
    **PROGRESSIVE_PLANET_ITEM_TABLE,
    **RATCHET_PACK_ITEM_TABLE,
    **TRAP_ITEM_TABLE,
    **FILLER_ITEM_TABLE,
    **PROGRESSIVE_WRENCH_ITEM_TABLE,
    **PROGRESSIVE_WEAPON_ITEM_TABLE,
    **TITAN_ITEM_TABLE,
    **WEAPON_MOD_ITEM_TABLE,
    **CHALLENGE_MODE_ITEM_TABLE,
    **KEYCARD_ITEM_TABLE,
    **WRENCH_ITEM_TABLE,
}


def _weapon_forms() -> dict[str, set[str]]:
    """Every form of each weapon: the weapon, its progressive version and its Titan/Proto upgrade."""
    forms: dict[str, set[str]] = {}
    for progressive, weapon in PROGRESSIVE_TO_UNLOCK.items():
        forms.setdefault(weapon, {weapon}).add(progressive)
    for upgrade, internal in TITAN_ITEMS.items():
        weapon = EQUIPMENT_INTERNAL_TO_DISPLAY[internal]
        forms.setdefault(weapon, {weapon}).add(upgrade)
    return forms


# Hint groups, so "!hint Cufflink Bomb" finds whichever forms of it the seed uses.
# Named without "(Clank)"/"(Ratchet)" because a group can't share its name with an item.
ITEM_NAME_GROUPS: dict[str, set[str]] = {
    weapon.rsplit(" (", 1)[0]: forms for weapon, forms in _weapon_forms().items()
}
ITEM_NAME_GROUPS["Wrench"] = {PROGRESSIVE_WRENCH, *WRENCH_ITEM_TABLE}
