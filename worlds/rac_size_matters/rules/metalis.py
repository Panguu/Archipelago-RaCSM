from __future__ import annotations

from typing import TYPE_CHECKING

from rule_builder.rules import HasAll, True_

from ..constants import (
    Rac5ClankChallenges,
    Rac5CutsceneLocations,
    Rac5Gadgets,
    Rac5Locations,
    Rac5SkillPoints,
    Rac5TBolts,
)
from ..locations import enabled_clank_challenge_names

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_metalis_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    if world.options.enable_clank_challenge_skill_points:
        world.set_rule(mw.get_location(Rac5SkillPoints.METALIS_SHUTOUT, player), True_())
        world.set_rule(mw.get_location(Rac5SkillPoints.METALIS_GLADIATOR, player), True_())

    # METALIS_WAR's own trigger is completing the Buzzsaw Blitz clank
    # challenge, so with clank challenges off it's never created at all
    # (see regions.py) — nothing to set a rule on in that case.
    if world.options.all_missions and world.options.clank_challenges.value >= 1:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.METALIS_WAR, player), True_())

    # Giant Clank Metalis: locked out entirely by the Giant Clank option
    # (see regions.py/GIANT_CLANK_LOCATIONS and
    # PlanetInventory.giant_clank_allowed) — when on, reachable as soon as
    # Metalis itself is (the "To Metalis" entrance rule already requires the
    # Metalis infobot), no additional item needed to trigger/complete it.
    if world.options.giant_clank:
        if world.options.all_missions:
            world.set_rule(mw.get_location(Rac5CutsceneLocations.METALIS_ESCAPE, player), True_())
        world.set_rule(mw.get_location(Rac5Locations.METALIS_GLOVES, player), True_())
        if world.options.skill_points.value >= 2:
            world.set_rule(mw.get_location(Rac5SkillPoints.METALIS_TERROR, player), True_())

    world.set_rule(
        mw.get_location(Rac5TBolts.METALIS_DOOR, player),
        HasAll(Rac5Gadgets.POLARIZER, Rac5Gadgets.HYPERSHOT),
    )

    # Clank Challenges — item rewards (clank_challenges >= 1) and individual
    # completions (clank_challenges >= 2), both further filtered by
    # ClankChallengeGroups — must match regions.py's own filtering, or
    # set_rule() below would target a Location that was never created.
    enabled_names = enabled_clank_challenge_names(dict(world.options.clank_challenge_groups.value))
    if world.options.clank_challenges.value >= 1:
        for name in (
            Rac5ClankChallenges.METALIS_BUZZSAW, Rac5ClankChallenges.METALIS_REVENGE,
            Rac5ClankChallenges.METALIS_UBER, Rac5ClankChallenges.METALIS_NIGHT,
        ):
            if name in enabled_names:
                world.set_rule(mw.get_location(name, player), True_())

    if world.options.clank_challenges.value >= 2:
        for name in (
            Rac5ClankChallenges.METALLIS_TEAM, Rac5ClankChallenges.METALIS_CHARGE,
            Rac5ClankChallenges.METALIS_BOOGALOO, Rac5ClankChallenges.METALIS_SHOWDOWN,
            Rac5ClankChallenges.METALIS_LEAGUE, Rac5ClankChallenges.METALIS_BRACKET,
            Rac5ClankChallenges.METALIS_DIVISION, Rac5ClankChallenges.METALIS_PROFESSIONAL,
            Rac5ClankChallenges.METALIS_GAP, Rac5ClankChallenges.METALIS_TELEPORTERS,
            Rac5ClankChallenges.METALIS_BRAIN,
        ):
            if name in enabled_names:
                world.set_rule(mw.get_location(name, player), True_())

