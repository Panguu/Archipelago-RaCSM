"""Klunk's Lair's per-location rules -- every location belonging to this case is set here explicitly (mirrors worlds/rac_size_matters/rules' per-planet files, one world.set_rule() call per location, grouped by which options.py toggle gates that location's category -- a location only exists in the multiworld at all when its category's option is on, so calling get_location() on it unguarded would raise)."""
from typing import TYPE_CHECKING

from rule_builder.rules import True_

from ..constants.clank_gadgets import SACClankWeapons
from ..constants.cutscenes import SACCutsceneLocations
from ..constants.missions import SACMissionLocations
from ..constants.skillpoints import SACSkillPointLocations
from ..constants.weapons import SACRatchetWeapons
from ..options import Missions

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld


def set_klunks_lair_rules(world: "SecretAgentClankWorld") -> None:
    player = world.player
    mw = world.multiworld

    # Always-on
    world.set_rule(mw.get_location(SACRatchetWeapons.RYNO, player), True_())
    world.set_rule(mw.get_location(SACClankWeapons.KICKSPLOSION, player), True_())

    # Story mission (Missions)
    if world.options.all_missions.value == Missions.option_all:
        world.set_rule(mw.get_location(SACMissionLocations.KLUNKS_LAIR_ALL_THE_MARBLES, player), True_())
    else:
        world.set_rule(mw.get_location(SACMissionLocations.KLUNKS_LAIR_COMPLETE, player), True_())

    # Cutscene (AllCutscenes)
    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(SACCutsceneLocations.KLUNKS_LAIR_ENTERE_CUTSCENE, player), True_())
        world.set_rule(
            mw.get_location(SACCutsceneLocations.KLUNKS_LAIR_MID_FIGHT_CUTSCENE_FOR_ROBO_RATCHET, player), True_(),
        )
        world.set_rule(mw.get_location(SACCutsceneLocations.KLUNKS_LAIR_COMPLETE_CUTSCENE, player), True_())
        world.set_rule(
            mw.get_location(SACCutsceneLocations.KLUNKS_LAIR_HIGH_IMPACT_GAMES_CUTSCENE_WITH_GIANT_CLANK, player),
            True_(),
        )

    # Skill point (SkillPoints)
    if world.options.skill_points:
        world.set_rule(mw.get_location(SACSkillPointLocations.KLUNKS_LAIR_TURN_THE_TABLES, player), True_())
        world.set_rule(mw.get_location(SACSkillPointLocations.KLUNKS_LAIR_PRETTY_GOOD_LIKENESS, player), True_())
