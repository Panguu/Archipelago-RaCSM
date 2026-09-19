"""Native titanium bolt IDs (one-based), from the USA game's count table."""
from dataclasses import dataclass

from .planets import SACCases
from .types import CaseStructure, SACTags

TITANIUM_BOLT_CASES = {
    1: (SACCases.BOLTAIRE_MUSEUM, 2),
    3: (SACCases.MAX_SECURITY_CELLS, 1),
    4: (SACCases.ASYANICA_ROOFTOPS, 1),
    9: (SACCases.THE_MESS_HALL, 1),
    10: (SACCases.AZCOTAL_ALLEY, 3),
    11: (SACCases.GONDOLA_ASCENT, 1),
    13: (SACCases.HIGH_ROLLERS_CASINO, 1),
    14: (SACCases.THE_EXERCISE_YARD, 1),
    16: (SACCases.VENANTONIO_LABS, 2),
    19: (SACCases.GALACTIC_BOLT_RESERVE, 3),
    21: (SACCases.THE_SHOWERS, 1),
    22: (SACCases.SPACESHIP_GRAVEYARD, 4),
    25: (SACCases.PRISON_BREAKOUT, 1),
    29: (SACCases.UNDERWATER_BUNKER, 1),
}
# Flavor-text overrides for specific bolts -- (module, index) -> the actual
# in-game hint/description, in place of the plain numeric index. Anything
# not listed here just uses str(index), as before.
TITANIUM_BOLT_DESCRIPTIONS: dict[tuple[int, int], str] = {
    (1, 1): "JetBoot around the pillar",
    (1, 2): "Jump over the railings",
    (3, 1): "Complete Mega Challenge",
    (4, 1): "1 - Inside The Air Duct",
}

TITANIUM_BOLT_ENTRIES = {
    (module, index): CaseStructure(case, TITANIUM_BOLT_DESCRIPTIONS.get((module, index), str(index)), SACTags.TITANIUM_BOLT)
    for module, (case, count) in TITANIUM_BOLT_CASES.items()
    for index in range(1, count + 1)
}


@dataclass(frozen=True)
class SACTitaniumBoltLocations:
    BOLTAIRE_MUSEUM_1 = "Boltaire (Clank) - Boltaire Museum: T-Bolt: JetBoot Around The Pillar After The Ravine"
    BOLTAIRE_MUSEUM_2 = "Boltaire (Clank) - Boltaire Museum: T-Bolt: Jump Over The Railings in The Museum"
    MAX_SECURITY_CELLS_1 = "Prison Planet (Ratchet) - Max-Security Cells: T-Bolt: Complete Mega Challenge: Cellblock"
    ASYANICA_ROOFTOPS_1 = "Asyanica (Clank) - Asyanica Rooftops: T-Bolt: Inside The Air Duct Before The Second Tie-A-Rang Bridge"
    THE_MESS_HALL_1 = "Prison Planet (Ratchet) - The Mess Hall: T-Bolt: Complete Mega Challenge: Cafeteria"
    AZCOTAL_ALLEY_1 = "Rionosis (Clank) - Azcotal Alley: T-Bolt: Side Alley After Second Fountain"
    AZCOTAL_ALLEY_2 = "Rionosis (Clank) - Azcotal Alley: T-Bolt: Second Side Alley Along The Main Path"
    AZCOTAL_ALLEY_3 = "Rionosis (Clank) - Azcotal Alley: T-Bolt: Left Side Before End of Level"
    GONDOLA_ASCENT_1 = "Rionosis (Clank) - Gondola Ascent: T-Bolt: Chamber With Moving Gondolas"
    HIGH_ROLLERS_CASINO_1 = "The Paradis Des Tricheurs Casino (Clank) - High-Rollers Casino: T-Bolt: Omni-Key Room After Bar"
    THE_EXERCISE_YARD_1 = "Prison Planet (Ratchet) - The Exercise Yard: T-Bolt: Complete Mega Challenge: Prison Yard"
    VENANTONIO_LABS_1 = "Venantonio (Clank) - Venantonio Labs: T-Bolt: Inside Trash Drone next to The Blowtorch Briefcase Room"
    VENANTONIO_LABS_2 = "Venantonio (Clank) - Venantonio Labs: T-Bolt: Side Room Next to the Second Moveable Platforms Room"
    GALACTIC_BOLT_RESERVE_1 = "Fort Sprocket (Clank) - Galactic Bolt Reserve: T-Bolt: Mineral Side Path at The Beginning of Level Platforming"
    GALACTIC_BOLT_RESERVE_2 = "Fort Sprocket (Clank) - Galactic Bolt Reserve: T-Bolt: Under The Large Freight Elevator"
    GALACTIC_BOLT_RESERVE_3 = "Fort Sprocket (Clank) - Galactic Bolt Reserve: T-Bolt: First Vault Atop of Large Boxes in The Middle"
    THE_SHOWERS_1 = "Prison Planet (Ratchet) - The Showers: T-Bolt: Complete Mega Challenge: Shower"
    SPACESHIP_GRAVEYARD_1 = "Spaceship Graveyard (Clank) - Spaceship Graveyard: T-Bolt: Room With The Large Glass Case"
    SPACESHIP_GRAVEYARD_2 = "Spaceship Graveyard (Clank) - Spaceship Graveyard: T-Bolt: Tie-A-Rang The Large Boxes"
    SPACESHIP_GRAVEYARD_3 = "Spaceship Graveyard (Clank) - Spaceship Graveyard: T-Bolt: Pit With Many Spores"
    SPACESHIP_GRAVEYARD_4 = "Spaceship Graveyard (Clank) - Spaceship Graveyard: T-Bolt: Gap on The Right in The Last Static Spores Platforming"
    PRISON_BREAKOUT_1 = "Prison Planet (Ratchet) -  Prison Breakout!: T-Bolt: Complete Mega Challenge: Battle Royale"
    UNDERWATER_BUNKER_1 = "Hydrano (Clank) - Underwater Bunker: T-Bolt: Omni-Key Room Before End of Level"
