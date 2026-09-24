"""LittleBigPlanet Location construction: every check defaults to available as soon as
its level region is reached. A location only gets a stricter rule if one is registered
in .rules, keyed by its stable location key (see locations.LOCATIONS)."""
from BaseClasses import Location


class LBPLocation(Location):
    game = 'LittleBigPlanet'

    @classmethod
    def create(cls, world, loc, region):
        """Build a location from a locations.py location dict, applying any
        registered per-location access rule for its key."""
        if __package__:
            from .rules import LOCATION_RULES
        else:
            from rules import LOCATION_RULES
        location = cls(world.player, loc['name'], loc['id'], region)
        rule = LOCATION_RULES.get(loc['key'])
        if rule:
            location.access_rule = lambda state, w=world, r=rule: r(w, state)
        return location
