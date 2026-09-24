"""Boltaire Museum's per-location rules -- every location belonging to this case is set here explicitly (mirrors worlds/rac_size_matters/rules' per-planet files, one world.set_rule() call per location, grouped by which options.py toggle gates that location's category -- a location only exists in the multiworld at all when its category's option is on, so calling get_location() on it unguarded would raise)."""
from typing import TYPE_CHECKING

from rule_builder.rules import Has, HasAll, True_

from ..constants.alien_codes import SACAlienCodeLocations
from ..constants.clank_gadgets import SACClankGadgets, SACClankWeapons, SACGadgetPickupLocations
from ..constants.cutscenes import SACCutsceneLocations
from ..constants.missions import SACMissionLocations
from ..constants.skillpoints import SACSkillPointLocations
from ..constants.titanium_bolts import SACTitaniumBoltLocations
from ..constants.weapons import SACRatchetWeapons
from ..options import Missions

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld


def set_boltaire_museum_rules(world: "SecretAgentClankWorld") -> None:
    player = world.player
    mw = world.multiworld
    _finish_mission = HasAll(SACClankGadgets.BLACK_OUT_PEN, SACClankWeapons.THROWTIE, SACClankGadgets.JETBOOTS)
    # Always-on
    world.set_rule(mw.get_location(SACRatchetWeapons.BLASTER, player), Has(SACClankGadgets.BLACK_OUT_PEN))
    world.set_rule(mw.get_location(SACClankWeapons.THROWTIE, player), True_())
    world.set_rule(mw.get_location(SACClankWeapons.HOLOKNUCKLES, player), True_())
    world.set_rule(mw.get_location(SACClankGadgets.JETBOOTS, player), _finish_mission)
    world.set_rule(mw.get_location(SACClankWeapons.SUPERKICK, player), True_())
    world.set_rule(mw.get_location(SACGadgetPickupLocations.BOLTAIRE_MUSEUM_BLACK_OUT_PEN, player), True_())
    world.set_rule(mw.get_location(SACGadgetPickupLocations.BOLTAIRE_MUSEUM_THERM_OPTIC_SHADES, player), True_())
    world.set_rule(mw.get_location(SACTitaniumBoltLocations.BOLTAIRE_MUSEUM_1, player), Has(SACClankGadgets.JETBOOTS))
    world.set_rule(
        mw.get_location(SACTitaniumBoltLocations.BOLTAIRE_MUSEUM_2, player),
        HasAll(SACClankGadgets.JETBOOTS, SACClankGadgets.BLACK_OUT_PEN),
    )

    # Story mission (Missions)
    if world.options.all_missions.value == Missions.option_all:
        world.set_rule(mw.get_location(SACMissionLocations.BOLTAIRE_MUSEUM_ESCAPE_THE_RAVINE, player), True_())
        world.set_rule(mw.get_location(SACMissionLocations.BOLTAIRE_MUSEUM_GET_INSIDE_THE_MUSEUM, player), True_())
        world.set_rule(mw.get_location(SACMissionLocations.BOLTAIRE_MUSEUM_NOT_THE_GUIDED_TOUR, player), _finish_mission)
    else:
        world.set_rule(mw.get_location(SACMissionLocations.BOLTAIRE_MUSEUM_COMPLETE, player), True_())

    # Cutscene (AllCutscenes)
    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(SACCutsceneLocations.BOLTAIRE_MUSEUM_ENTER_CUTSCENE, player), True_())

    # Skill point (SkillPoints)
    if world.options.skill_points:
        world.set_rule(mw.get_location(SACSkillPointLocations.BOLTAIRE_MUSEUM_FURIOUS_FISTS, player), _finish_mission)
        world.set_rule(mw.get_location(SACSkillPointLocations.BOLTAIRE_MUSEUM_SILENT_NIGHT, player), _finish_mission)

    # Alien code (AllAlienCodes) -- also needs Therm-Optic Shades
    if world.options.all_alien_codes:
        world.set_rule(
            mw.get_location(SACAlienCodeLocations.BOLTAIRE_MUSEUM_THE_LEGENDS, player),
            Has(SACClankGadgets.THERM_OPTIC_SHADES),
        )
        world.set_rule(
            mw.get_location(SACAlienCodeLocations.BOLTAIRE_MUSEUM_RONNS_SECRET, player),
            _finish_mission & Has(SACClankGadgets.THERM_OPTIC_SHADES),
        )
        world.set_rule(
            mw.get_location(SACAlienCodeLocations.BOLTAIRE_MUSEUM_BENS_SECRET, player),
            _finish_mission & Has(SACClankGadgets.THERM_OPTIC_SHADES),
        )
