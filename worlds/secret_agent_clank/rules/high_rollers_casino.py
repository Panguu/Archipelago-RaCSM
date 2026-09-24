"""High-Rollers Casino's per-location rules -- every location belonging to this case is set here explicitly (mirrors worlds/rac_size_matters/rules' per-planet files, one world.set_rule() call per location, grouped by which options.py toggle gates that location's category -- a location only exists in the multiworld at all when its category's option is on, so calling get_location() on it unguarded would raise)."""
from typing import TYPE_CHECKING

from rule_builder.rules import True_

from ..constants.alien_codes import SACAlienCodeLocations
from ..constants.clank_gadgets import SACClankGadgets
from ..constants.cutscenes import SACCutsceneLocations
from ..constants.missions import SACMissionLocations
from ..constants.skillpoints import SACSkillPointLocations
from ..constants.titanium_bolts import SACTitaniumBoltLocations
from ..constants.weapons import SACRatchetWeapons
from ..options import Missions
from .rule_helpers import Has

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld


def set_high_rollers_casino_rules(world: "SecretAgentClankWorld") -> None:
    player = world.player
    mw = world.multiworld
    _base = Has(SACClankGadgets.HOLOMONOCLE)

    # Always-on
    world.set_rule(mw.get_location(SACRatchetWeapons.PORKBOMB, player), _base)
    world.set_rule(mw.get_location(SACClankGadgets.HYPNOWATCH, player), _base)
    world.set_rule(mw.get_location(SACClankGadgets.HOLOMONOCLE, player), True_())
    world.set_rule(mw.get_location(SACTitaniumBoltLocations.HIGH_ROLLERS_CASINO_1, player), _base & Has(SACClankGadgets.OMNIKEY))

    # Story mission (Missions)
    if world.options.all_missions.value == Missions.option_all:
        world.set_rule(mw.get_location(SACMissionLocations.HIGH_ROLLERS_CASINO_EXPLORE_PARADISE, player), _base)
        world.set_rule(mw.get_location(SACMissionLocations.HIGH_ROLLERS_CASINO_PARADISE_EXPLOITED, player), _base)
    else:
        world.set_rule(mw.get_location(SACMissionLocations.HIGH_ROLLERS_CASINO_COMPLETE, player), _base)

    # Cutscene (AllCutscenes)
    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(SACCutsceneLocations.HIGH_ROLLERS_CASINO_ENTER_CUTSCENE, player), _base)
        world.set_rule(mw.get_location(SACCutsceneLocations.HIGH_ROLLERS_CASINO_COMPLETE_CUTSCENE, player), True_())

    # Skill point (SkillPoints)
    if world.options.skill_points:
        world.set_rule(mw.get_location(SACSkillPointLocations.HIGH_ROLLERS_CASINO_BEAT_THE_HOUSE, player), _base)

    # Alien code (AllAlienCodes) -- also needs Therm-Optic Shades
    if world.options.all_alien_codes:
        world.set_rule(
            mw.get_location(SACAlienCodeLocations.HIGH_ROLLERS_CASINO_COLINS_SECRET, player),
            Has(SACClankGadgets.THERM_OPTIC_SHADES),
        )
        world.set_rule(
            mw.get_location(SACAlienCodeLocations.HIGH_ROLLERS_CASINO_SHANES_SECRET, player),
            _base & Has(SACClankGadgets.THERM_OPTIC_SHADES),
        )
        world.set_rule(
            mw.get_location(SACAlienCodeLocations.HIGH_ROLLERS_CASINO_THE_PING_PONG_SECRET, player),
            _base & Has(SACClankGadgets.THERM_OPTIC_SHADES),
        )
