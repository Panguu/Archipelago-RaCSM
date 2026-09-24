"""Per-location access rules for the rare check that needs more than 'level is
unlocked'. Every location NOT listed here defaults to unconditionally available once
its level region is reached (see location.LBPLocation.create) -- do not add an entry
just to express "true".

Add a module here only for a level with a genuine, specific exception (e.g. a bubble
that needs a second player physically present), then register its rules below. Key by
the location's stable key from locations.LOCATIONS (e.g. 'g26374/score/12345'), most
easily obtained via that level's generated Locations class + LOCATION_KEYS mapping in
constants/levels. A rule is a callable `rule(world, state) -> bool`; `world` is the
LittleBigPlanetWorld instance, so e.g. `world.options.players.value` is available for
co-op-only checks.
"""

from . import lowrider
from . import the_frozen_tundra
from . import subway
from . import the_meerkat_kingdom
from . import burning_forest
from . import get_a_grip
from . import skate_to_victory
from . import elephant_temple
from . import the_collector_s_lair
from . import great_magician_s_palace
from . import endurance_dojo
from . import sensei_s_lost_castle
from . import the_bunker
from . import the_terrible_oni_s_volcano
from . import boom_town
from . import the_mines
from . import serpent_shrine
from . import the_wedding_reception
from . import the_darkness
from . import the_construction_site
from . import swinging_safari

LOCATION_RULES = {}
LOCATION_RULES.update(lowrider.RULES)
LOCATION_RULES.update(the_frozen_tundra.RULES)
LOCATION_RULES.update(subway.RULES)
LOCATION_RULES.update(the_meerkat_kingdom.RULES)
LOCATION_RULES.update(burning_forest.RULES)
LOCATION_RULES.update(get_a_grip.RULES)
LOCATION_RULES.update(skate_to_victory.RULES)
LOCATION_RULES.update(elephant_temple.RULES)
LOCATION_RULES.update(the_collector_s_lair.RULES)
LOCATION_RULES.update(great_magician_s_palace.RULES)
LOCATION_RULES.update(endurance_dojo.RULES)
LOCATION_RULES.update(sensei_s_lost_castle.RULES)
LOCATION_RULES.update(the_bunker.RULES)
LOCATION_RULES.update(the_terrible_oni_s_volcano.RULES)
LOCATION_RULES.update(boom_town.RULES)
LOCATION_RULES.update(the_mines.RULES)
LOCATION_RULES.update(serpent_shrine.RULES)
LOCATION_RULES.update(the_wedding_reception.RULES)
LOCATION_RULES.update(the_darkness.RULES)
LOCATION_RULES.update(the_construction_site.RULES)
LOCATION_RULES.update(swinging_safari.RULES)
