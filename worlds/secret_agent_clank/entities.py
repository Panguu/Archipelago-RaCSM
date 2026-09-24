"""SACItem/SACLocation live here, not in world.py, so regions.py can import them at module load time -- world.py imports regions.py's create_regions(), so keeping these classes in world.py would make that a circular import, forcing a lazy (function-local) import instead."""
from BaseClasses import Item, Location


class SACItem(Item):
    game: str = "Secret Agent Clank"


class SACLocation(Location):
    game: str = "Secret Agent Clank"
