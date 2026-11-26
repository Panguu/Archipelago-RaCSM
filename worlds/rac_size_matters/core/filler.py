"""One-shot filler rewards, delivered through the persisted filler checkpoint."""
from bisect import bisect_right

from ..constants import Rac5Filler
from ..data.weapons import WEAPON_DATA
from . import address_maps
from .player_health_exp import NANOTECH_XP_THRESHOLDS
from .vendor import WEAPON_VENDOR_IDS
from .weapons import PROGRESSIVE_AUTOMATIC, exp_threshold_for_level


def grant_filler(core, name: str) -> None:
    if name == Rac5Filler.NANOTECH_EXP:
        xp = core.player_health_exp
        current = max(0, xp.get())
        index = bisect_right(NANOTECH_XP_THRESHOLDS, current)
        max_level = 75 if core.pine.read_int8(address_maps.CHALLENGE_MODE_BASE) else 50
        if index >= max_level - 4:
            return
        step = NANOTECH_XP_THRESHOLDS[index] - NANOTECH_XP_THRESHOLDS[index - 1]
        value = min(current + max(1, step // 10), NANOTECH_XP_THRESHOLDS[max_level - 5])
        xp.set(value)
        xp.rebaseline(value)
        return
    if name not in (Rac5Filler.WEAPON_EXP, Rac5Filler.REFILL_AMMO):
        return
    weapons = core.planet.weapons
    current_id = core.planet.weapon_cycler.current_weapon
    weapon = next((key for key, value in WEAPON_VENDOR_IDS.items()
                   if value == current_id and key in WEAPON_DATA), None)
    if weapon is None or not weapons.has_weapon(weapon):
        return
    level = weapons.get_level(weapon)
    if name == Rac5Filler.REFILL_AMMO:
        capacity = WEAPON_DATA[weapon].vendor_ammo
        amount = capacity.titan if level >= 4 and capacity.titan is not None else capacity.base
        weapons.set_ammo(weapon, max(weapons.get_ammo(weapon), amount))
        return
    if weapons.progressive_mode == PROGRESSIVE_AUTOMATIC:
        return
    ceiling = weapons.level_ceiling(weapon)
    if ceiling is not None and level >= ceiling:
        return
    threshold = exp_threshold_for_level(weapon, level + 2)
    if threshold is None or level >= WEAPON_DATA[weapon].max_level - 1:
        return
    value = min(threshold, weapons.get_experience(weapon) + max(1, threshold // 4))
    weapons.set_experience(weapon, value)
    weapons._prev_experience[weapon] = value
