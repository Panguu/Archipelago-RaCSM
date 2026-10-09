"""Titanium bolt locations, keyed by the USA game's per-module count table."""
from dataclasses import dataclass


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
    PRISON_BREAKOUT_1 = "Prison Planet (Ratchet) - Prison Breakout!: T-Bolt: Complete Mega Challenge: Battle Royale"
    UNDERWATER_BUNKER_1 = "Hydrano (Clank) - Underwater Bunker: T-Bolt: Omni-Key Room Before End of Level"


# Native module ID -> its bolts, in native bolt-ID order (IDs are one-based).
TITANIUM_BOLTS_BY_MODULE: dict[int, tuple[str, ...]] = {
    1: (SACTitaniumBoltLocations.BOLTAIRE_MUSEUM_1, SACTitaniumBoltLocations.BOLTAIRE_MUSEUM_2),
    3: (SACTitaniumBoltLocations.MAX_SECURITY_CELLS_1,),
    4: (SACTitaniumBoltLocations.ASYANICA_ROOFTOPS_1,),
    9: (SACTitaniumBoltLocations.THE_MESS_HALL_1,),
    10: (SACTitaniumBoltLocations.AZCOTAL_ALLEY_1, SACTitaniumBoltLocations.AZCOTAL_ALLEY_2, SACTitaniumBoltLocations.AZCOTAL_ALLEY_3),
    11: (SACTitaniumBoltLocations.GONDOLA_ASCENT_1,),
    13: (SACTitaniumBoltLocations.HIGH_ROLLERS_CASINO_1,),
    14: (SACTitaniumBoltLocations.THE_EXERCISE_YARD_1,),
    16: (SACTitaniumBoltLocations.VENANTONIO_LABS_1, SACTitaniumBoltLocations.VENANTONIO_LABS_2),
    19: (SACTitaniumBoltLocations.GALACTIC_BOLT_RESERVE_1, SACTitaniumBoltLocations.GALACTIC_BOLT_RESERVE_2, SACTitaniumBoltLocations.GALACTIC_BOLT_RESERVE_3),
    21: (SACTitaniumBoltLocations.THE_SHOWERS_1,),
    22: (SACTitaniumBoltLocations.SPACESHIP_GRAVEYARD_1, SACTitaniumBoltLocations.SPACESHIP_GRAVEYARD_2, SACTitaniumBoltLocations.SPACESHIP_GRAVEYARD_3, SACTitaniumBoltLocations.SPACESHIP_GRAVEYARD_4),
    25: (SACTitaniumBoltLocations.PRISON_BREAKOUT_1,),
    29: (SACTitaniumBoltLocations.UNDERWATER_BUNKER_1,),
}
