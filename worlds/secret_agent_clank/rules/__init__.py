"""One rules file per case (SAC's atomic content unit -- see constants/planets.py's Planet/Case docstring), mirroring worlds/rac_size_matters/rules' one-file-per-planet layout at SAC's finer per-case granularity, PLUS entrances.py mirroring that world's own entrances.py."""
from typing import TYPE_CHECKING

from rule_builder.rules import Has

from ..constants import SACCases
from .a_fiction_full_of_dollars import set_a_fiction_full_of_dollars_rules
from .asyanica_rooftops import set_asyanica_rooftops_rules
from .azcotal_alley import set_azcotal_alley_rules
from .boltaire_gem_wing import set_boltaire_gem_wing_rules
from .boltaire_museum import set_boltaire_museum_rules
from .bulkhead_lock import set_bulkhead_lock_rules
from .countess_villa import set_countess_villa_rules
from .dams_edge_hydrano import set_dams_edge_hydrano_rules
from .entrances import set_entrance_rules
from .galactic_bolt_reserve import set_galactic_bolt_reserve_rules
from .glaciara_ski_slopes import set_glaciara_ski_slopes_rules
from .gondola_ascent import set_gondola_ascent_rules
from .high_rollers_casino import set_high_rollers_casino_rules
from .high_stakes_room import set_high_stakes_room_rules
from .inside_the_a_eye import set_inside_the_a_eye_rules
from .klunks_lair import set_klunks_lair_rules
from .larger_than_life import set_larger_than_life_rules
from .madam_butterqwark import set_madam_butterqwark_rules
from .max_security_cells import set_max_security_cells_rules
from .prison_breakout import set_prison_breakout_rules
from .rooftop_deathtrap import set_rooftop_deathtrap_rules
from .rule_helpers import HasCase, HasCharacter, HasPlanet
from .saint_qwark import set_saint_qwark_rules
from .spaceship_graveyard import set_spaceship_graveyard_rules
from .suck_and_jive import set_suck_and_jive_rules
from .the_exercise_yard import set_the_exercise_yard_rules
from .the_mess_hall import set_the_mess_hall_rules
from .the_quasar_fields import set_the_quasar_fields_rules
from .the_showers import set_the_showers_rules
from .underwater_bunker import set_underwater_bunker_rules
from .venantonio_canals import set_venantonio_canals_rules
from .venantonio_labs import set_venantonio_labs_rules
from .vendor_access import set_vendor_rules

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld

__all__ = ["HasCase", "HasCharacter", "HasPlanet", "set_rules"]


def set_rules(world: "SecretAgentClankWorld") -> None:
    world.set_completion_rule(Has("Victory"))

    set_entrance_rules(world)

    enabled = {r.name for r in world.multiworld.get_regions(world.player)}
    for case, apply_rules in (
        (SACCases.BOLTAIRE_MUSEUM, set_boltaire_museum_rules),
        (SACCases.BOLTAIRE_GEM_WING, set_boltaire_gem_wing_rules),
        (SACCases.MAX_SECURITY_CELLS, set_max_security_cells_rules),
        (SACCases.ROOFTOP_DEATHTRAP, set_rooftop_deathtrap_rules),
        (SACCases.ASYANICA_ROOFTOPS, set_asyanica_rooftops_rules),
        (SACCases.LARGER_THAN_LIFE, set_larger_than_life_rules),
        (SACCases.COUNTESS_VILLA, set_countess_villa_rules),
        (SACCases.GLACIARA_SKI_SLOPES, set_glaciara_ski_slopes_rules),
        (SACCases.THE_MESS_HALL, set_the_mess_hall_rules),
        (SACCases.AZCOTAL_ALLEY, set_azcotal_alley_rules),
        (SACCases.GONDOLA_ASCENT, set_gondola_ascent_rules),
        (SACCases.SUCK_AND_JIVE, set_suck_and_jive_rules),
        (SACCases.HIGH_ROLLERS_CASINO, set_high_rollers_casino_rules),
        (SACCases.THE_EXERCISE_YARD, set_the_exercise_yard_rules),
        (SACCases.HIGH_STAKES_ROOM, set_high_stakes_room_rules),
        (SACCases.VENANTONIO_LABS, set_venantonio_labs_rules),
        (SACCases.VENANTONIO_CANALS, set_venantonio_canals_rules),
        (SACCases.MADAM_BUTTERQWARK, set_madam_butterqwark_rules),
        (SACCases.GALACTIC_BOLT_RESERVE, set_galactic_bolt_reserve_rules),
        (SACCases.INSIDE_THE_A_EYE, set_inside_the_a_eye_rules),
        (SACCases.THE_SHOWERS, set_the_showers_rules),
        (SACCases.SPACESHIP_GRAVEYARD, set_spaceship_graveyard_rules),
        (SACCases.SAINT_QWARK, set_saint_qwark_rules),
        (SACCases.THE_QUASAR_FIELDS, set_the_quasar_fields_rules),
        (SACCases.PRISON_BREAKOUT, set_prison_breakout_rules),
        (SACCases.DAMS_EDGE_HYDRANO, set_dams_edge_hydrano_rules),
        (SACCases.A_FICTION_FULL_OF_DOLLARS, set_a_fiction_full_of_dollars_rules),
        (SACCases.BULKHEAD_LOCK, set_bulkhead_lock_rules),
        (SACCases.UNDERWATER_BUNKER, set_underwater_bunker_rules),
        (SACCases.KLUNKS_LAIR, set_klunks_lair_rules),
    ):
        if case in enabled:
            apply_rules(world)
    set_vendor_rules(world)
