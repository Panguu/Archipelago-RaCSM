from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import RACSMITEM, RACSMSKILLPOINT, RACSMTBOLT, RACSMVENDORLOCATION, RacSMCutsceneLocations
from ._helpers import has_projectile_weapon, has_weapon

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_pokitaru_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    # ── Skill Points ──────────────────────────────────────────────────────────
    if world.options.skill_points.value >= 1:
        mw.get_location(RACSMSKILLPOINT.POKITARU_TRAIN, player).access_rule = \
            lambda state: has_projectile_weapon(state, player)
        mw.get_location(RACSMSKILLPOINT.POKITARU_BOAT, player).access_rule = lambda _: True
        mw.get_location(RACSMSKILLPOINT.POKITARU_COWS, player).access_rule = \
            lambda state: has_weapon(state, player, RACSMITEM.MOOTATOR)

    # ── Missions ──────────────────────────────────────────────────────────────
    if world.options.all_missions:
        mw.get_location(RacSMCutsceneLocations.POKITARU_FIGHT, player).access_rule = lambda _: True

    # ── Titanium Bolts ────────────────────────────────────────────────────────
    mw.get_location(RACSMTBOLT.POKITARU_ZIPLINE, player).access_rule = lambda _: True
    mw.get_location(RACSMTBOLT.POKITARU_HUT,     player).access_rule = lambda _: True

    # ── Vendors ───────────────────────────────────────────────────────────────
    # Weapons and gadgets freely accessible on arrival.
    mw.get_location(RACSMVENDORLOCATION.POKITARU_LACERATOR,  player).access_rule = lambda _: True
    mw.get_location(RACSMVENDORLOCATION.POKITARU_ACID,       player).access_rule = lambda _: True
    mw.get_location(RACSMVENDORLOCATION.POKITARU_CONCUSSION, player).access_rule = lambda _: True
    mw.get_location(RACSMVENDORLOCATION.POKITARU_HYPERSHOT,  player).access_rule = lambda _: True
