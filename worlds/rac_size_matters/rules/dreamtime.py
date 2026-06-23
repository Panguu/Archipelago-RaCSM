from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import (
    RACSMITEM,
    RACSMLOCATION,
    RACSMSKILLPOINT,
    RACSMTBOLT,
    RACSMVENDORLOCATION,
    RacSMCutsceneLocations,
)
from ._helpers import has_projectile_weapon

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_dreamtime_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    # Entrance already requires Hypershot + Sprout-O-Matic.
    _base = lambda state: (state.has(RACSMITEM.HYPERSHOT, player)
                           and state.has(RACSMITEM.SPROUT_O_MATIC, player))

    # ── Skill Points ──────────────────────────────────────────────────────────
    if world.options.skill_points.value >= 2:
        mw.get_location(RACSMSKILLPOINT.DREAMTIME_FRIENDS,       player).access_rule = _base
        mw.get_location(RACSMSKILLPOINT.DREAMTIME_NIGHT_TERRORS, player).access_rule = _base

    # ── Missions ──────────────────────────────────────────────────────────────
    if world.options.all_missions:
        mw.get_location(RacSMCutsceneLocations.DREAMTIME_COMPLETE, player).access_rule = _base

    # ── Titanium Bolts ────────────────────────────────────────────────────────
    mw.get_location(RACSMTBOLT.DREAMTIME_HAT,    player).access_rule = _base
    mw.get_location(RACSMTBOLT.DREAMTIME_GARAGE, player).access_rule = _base
    mw.get_location(RACSMTBOLT.DREAMTIME_CRAB,   player).access_rule = \
        lambda state: (_base(state) and has_projectile_weapon(state, player))

    # ── Armour ────────────────────────────────────────────────────────────────
    mw.get_location(RACSMLOCATION.DREAMTIME_CHESTPLATE, player).access_rule = _base

    # ── Vendors ───────────────────────────────────────────────────────────────
    mw.get_location(RACSMVENDORLOCATION.DREAMTIME_SUCK, player).access_rule = _base
