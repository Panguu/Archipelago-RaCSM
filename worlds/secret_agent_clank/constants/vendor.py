"""SAC's single shop, reached from Clank's pause menu.

Base offers live here; weapon mods and Titan/Proto upgrades are in weapon_mods.py and
weapon_progression.py. Every purchase is named by its SACVendor constant.
"""
from dataclasses import dataclass

from .clank_gadgets import SACClankGadgets, SACClankWeapons, SACProtoWeapons
from .weapons import SACRatchetWeapons, SACTitanWeapons


@dataclass(frozen=True)
class SACVendorWeapons:
    """Equipment whose only native source is the vendor."""
    SHOCKROCKET       = SACRatchetWeapons.SHOCKROCKET
    PLASMAWHIP        = SACRatchetWeapons.PLASMAWHIP
    PORKBOMB          = SACRatchetWeapons.PORKBOMB
    RYNO              = SACRatchetWeapons.RYNO
    KICKBLAST         = SACRatchetWeapons.KICKBLAST
    HOLOKNUCKLES      = SACClankWeapons.HOLOKNUCKLES
    LIGHTNINGUMBRELLA = SACClankWeapons.LIGHTNINGUMBRELLA
    SUPERKICK         = SACClankWeapons.SUPERKICK
    KICKSPLOSION      = SACClankWeapons.KICKSPLOSION
    HYPNOWATCH        = SACClankGadgets.HYPNOWATCH
    CLANKPDA          = SACClankGadgets.CLANKPDA
    BOLTGRABBER       = SACClankGadgets.BOLTGRABBER


VENDOR_WEAPONS: tuple[str, ...] = tuple(
    value for name, value in vars(SACVendorWeapons).items() if not name.startswith("_")
)

# Purchases introduced only in challenge mode.
NG_PLUS_VENDOR_ITEMS = frozenset({SACRatchetWeapons.RYNO, SACClankWeapons.KICKSPLOSION})

class SACVendor:
    """String constants for Agency Vendor purchases"""
    BOLTAIRE_MUSEUM_HOLO_KNUCKLES = "Boltaire (Clank) - Boltaire Museum: Agency Vendor: Holo-Knuckles - 23,000"
    BOLTAIRE_MUSEUM_CLANK_FU_KICK = "Boltaire (Clank) - Boltaire Museum: Agency Vendor: Clank Fu Kick - 7,000"
    ASYANICA_ROOFTOPS_DUAL_LACERATOR_SEEKER = "Asyanica (Clank) - Asyanica Rooftops: Agency Vendor: Dual Lacerators Seeker Mod - 15,000"
    ASYANICA_ROOFTOPS_DUAL_LACERATOR_HUNTER = "Asyanica (Clank) - Asyanica Rooftops: Agency Vendor: Dual Lacerators Hunter Mod - 10,000"
    ASYANICA_ROOFTOPS_DUAL_SHARD_GUN_ICE_HALO = "Asyanica (Clank) - Asyanica Rooftops: Agency Vendor: Shard Gun Ice Halo Mod - 10,000"
    ASYANICA_ROOFTOPS_WALLOPER_LIGHTNING_SPEED = "Asyanica (Clank) - Asyanica Rooftops: Agency Vendor: Walloper Lightning Speed Mod - 10,000"
    AZCOTAL_ALLEY_AGENCY_PDA = "Rionosis (Clank) - Azcotal Alley: Agency Vendor: Agency PDA - 35,000"
    AZCOTAL_ALLEY_BEE_MINE_MK_II_EXPLOSIVE_NATURE = "Rionosis (Clank) - Azcotal Alley: Agency Vendor: Bee Mine Mk. II Explosive Nature Mod - 15,000"
    AZCOTAL_ALLEY_MINE_LAUNCHER_ORDNANCE = "Rionosis (Clank) - Azcotal Alley: Agency Vendor: Mine Launcher Ordnance Mod - 20,000"
    AZCOTAL_ALLEY_MINE_LAUNCHER_PERSISTENCE = "Rionosis (Clank) - Azcotal Alley: Agency Vendor: Mine Launcher Persistence Mod - 15,000"
    HIGH_ROLLERS_CASINO_HYPNO_WATCH = "The Paradis Des Tricheurs Casino (Clank) - High-Rollers Casino: Agency Vendor: Hypno-Watch - 23,000"
    HIGH_ROLLERS_CASINO_PORK_BOBM_GUN = "The Paradis Des Tricheurs Casino (Clank) - High-Rollers Casino: Agency Vendor: Pork Bomb Gun - 35,000"
    HIGH_ROLLERS_CASINO_BEE_MINE_MK_II_KILLER_HONEY = "The Paradis Des Tricheurs Casino (Clank) - High-Rollers Casino: Agency Vendor: Bee Mine Mk. II Killer Honey Mod - 15,000"
    VENANTONIO_LABS_PLASMA_WHIP = "Venantonio (Clank) - Venantonio Labs: Agency Vendor: Plasma Whip - 35,000"
    VENANTONIO_LABS_CLANK_FU_HOT_FOOT = "Venantonio (Clank) - Venantonio Labs: Agency Vendor: Clank Fu Hot Foot - 10,000"
    VENANTONIO_LABS_THUNDERSTORM_UMBRELLA = "Venantonio (Clank) - Venantonio Labs: Agency Vendor: Thunderstorm Umbrella - 30,000"
    GALACTIC_BOLT_RESERVE_SHOCK_ROCKET = "Fort Sprocket (Clank) - Galactic Bolt Reserve: Agency Vendor: Shock Rocket - 55,000"
    GALACTIC_BOLT_RESERVE_BOLT_GRABBER = "Fort Sprocket (Clank) - Galactic Bolt Reserve: Agency Vendor: Bolt Grabber - 30,000"
    THE_SHOWERS_PORK_BOMB_GUN_WAR_PIGS = "Prison Planet (Ratchet) - The Showers: Agency Vendor: Pork Bomb Gun War Pigs Mod - 25,000"
    SPACESHIP_GRAVEYARD_SHOCK_ROCKET_PORK_BOMB_GUN_TASTY_PIGS = "Spaceship Graveyard (Clank) - Spaceship Graveyard: Agency Vendor: Pork Bomb Gun Tasty Pigs Mod - 25,000"
    SPACESHIP_GRAVEYARD_SHOCK_ROCKET_STATIC_CHARGE = "Spaceship Graveyard (Clank) - Spaceship Graveyard: Agency Vendor: Shock Rocket Static Charge Mod - 25,000"
    SPACESHIP_GRAVEYARD_SHOCK_PLASMA_WHIP_FIRE_SNAKE = "Spaceship Graveyard (Clank) - Spaceship Graveyard: Agency Vendor: Plasma Whip Fire Snake Mod - 25,000"
    PRISON_BREAKOUT_SHOCK_ROCKET_TASER = "Prison Planet (Ratchet) - Prison Breakout!: Agency Vendor: Shock Rocket Taser Mod - 35,000"
    PRISON_BREAKOUT_PLASMA_WHIP_FLAME_TRAILS = "Prison Planet (Ratchet) - Prison Breakout!: Agency Vendor: Plasma Whip Flame Trails Mod - 35,000"

    # Challenge mode vendor locations
    BOLTAIRE_MUSEUM_PROTO_WHIRLWIND_THROWTIE = "Boltaire (Clank) - Boltaire Museum: Agency Vendor: Proto Whirlwind Throwtie - 400,000"
    BOLTAIRE_MUSEUM_CLANK_PROTO_HARDLIGHT_FIST = "Boltaire (Clank) - Boltaire Museum: Agency Vendor: Proto Hardlight Fist - 200,000"
    BOLTAIRE_MUSEUM_TITAN_DUAL_VINDICATORS = "Boltaire (Clank) - Boltaire Museum: Agency Vendor: Titan Dual Vindicators - 400,000"
    MAX_SECURITY_CELLS_TITAN_SHARD_CANNON = "Prison Planet (Ratchet) - Max-Security Cells: Agency Vendor: Titan Shard Cannon - 200,000"
    MAX_SECURITY_CELLS_TITAN_MARAUDER = "Prison Planet (Ratchet) - Max-Security Cells: Agency Vendor: Titan Marauder - 200,000"
    ASYANICA_ROOFTOPS_PROTO_WRIST_MORTAR = "Asyanica (Clank) - Asyanica Rooftops: Agency Vendor: Proto Wrist Mortar - 400,000"
    ASYANICA_ROOFTOPS_TITAN_ORDNANCE_LAUNCHER = "Asyanica (Clank) - Asyanica Rooftops: Agency Vendor: Titan Ordnance Launcher - 600,000"
    AZCOTAL_ALLEY_PROTO_KUDZU_TANGLE = "Rionosis (Clank) - Azcotal Alley: Agency Vendor: Proto Kudzu Tangle - 400,000"
    AZCOTAL_ALLEY_TITAN_KILLER_BEE_MINE = "Rionosis (Clank) - Azcotal Alley: Agency Vendor: Titan Killer Bee Mine - 400,000"
    HIGH_ROLLERS_CASINO_TITAN_MEAT_MORTAR = "The Paradis Des Tricheurs Casino (Clank) - High-Rollers Casino: Agency Vendor: Titan Meat Mortar - 400,000"
    VENANTONIO_LABS_PROTO_LIGHTNING_ROD = "Venantonio (Clank) - Venantonio Labs: Agency Vendor: Proto Lightning Rod - 50,000"
    VENANTONIO_LABS_PROTO_HELLFIRE_HAVERSACK = "Venantonio (Clank) - Venantonio Labs: Agency Vendor: Proto Hellfire Haversack - 50,000"
    VENANTONIO_LABS_TITAN_PLASMA_CORD = "Venantonio (Clank) - Venantonio Labs: Agency Vendor: Titan Plasma Cord - 400,000"
    GALACTIC_BOLT_RESERVE_TITAN_ELECTRO_ROCKET = "Fort Sprocket (Clank) - Galactic Bolt Reserve: Agency Vendor: Titan Electro Rocket - 600,000"
    CHALLENGE_MODE_RYNO = "Challenge Mode (Clank): Agency Vendor: RYNO - 2,000,000"
    CHALLENGE_MODE_HOT_FOOT_21_BETA = "Challenge Mode (Clank): Agency Vendor: Hot Foor 2.1 Beta - 200,000"
    CHALLENGE_MODE_BLOWTORCH_BRIEFCASE_MOLTEN_BOLT = "Challenge Mode (Clank): Agency Vendor: Blowtorch Briefcase Molten Bolt Mod - 100,000"
    CHALLENGE_MODE_THUNDERSTORM_UMBRELLA_XENOS_CAPACITOR = "Challenge Mode (Clank): Agency Vendor: Thunderstorm Umbrella Xeno's Capacitor Mod - 100,000"
    CHALLENGE_MODE_THUNDERSTORM_UMBRELLA_THUNDERCLOUD = "Challenge Mode (Clank): Agency Vendor: Thunderstorm Umbrella Thundercloud Mod - 200,000"


# Equipment display name -> SACVendor location; weapon mods map theirs in weapon_mods.py.
VENDOR_LOCATION_NAMES: dict[str, str] = {
    SACClankGadgets.CLANKPDA: SACVendor.AZCOTAL_ALLEY_AGENCY_PDA,
    SACClankWeapons.HOLOKNUCKLES: SACVendor.BOLTAIRE_MUSEUM_HOLO_KNUCKLES,
    SACClankWeapons.SUPERKICK: SACVendor.BOLTAIRE_MUSEUM_CLANK_FU_KICK,
    SACRatchetWeapons.PORKBOMB: SACVendor.HIGH_ROLLERS_CASINO_PORK_BOBM_GUN,
    SACClankGadgets.HYPNOWATCH: SACVendor.HIGH_ROLLERS_CASINO_HYPNO_WATCH,
    SACRatchetWeapons.SHOCKROCKET: SACVendor.GALACTIC_BOLT_RESERVE_SHOCK_ROCKET,
    SACClankGadgets.BOLTGRABBER: SACVendor.GALACTIC_BOLT_RESERVE_BOLT_GRABBER,
    SACRatchetWeapons.RYNO: SACVendor.CHALLENGE_MODE_RYNO,
    SACClankWeapons.KICKSPLOSION: SACVendor.CHALLENGE_MODE_HOT_FOOT_21_BETA,
    SACRatchetWeapons.PLASMAWHIP: SACVendor.VENANTONIO_LABS_PLASMA_WHIP,
    SACRatchetWeapons.KICKBLAST: SACVendor.VENANTONIO_LABS_CLANK_FU_HOT_FOOT,
    SACClankWeapons.LIGHTNINGUMBRELLA: SACVendor.VENANTONIO_LABS_THUNDERSTORM_UMBRELLA,
    SACTitanWeapons.SHOCKROCKET: SACVendor.GALACTIC_BOLT_RESERVE_TITAN_ELECTRO_ROCKET,
    SACTitanWeapons.PLASMAWHIP: SACVendor.VENANTONIO_LABS_TITAN_PLASMA_CORD,
    SACTitanWeapons.PORKBOMB: SACVendor.HIGH_ROLLERS_CASINO_TITAN_MEAT_MORTAR,
    SACTitanWeapons.BLASTER: SACVendor.BOLTAIRE_MUSEUM_TITAN_DUAL_VINDICATORS,
    SACTitanWeapons.SHARDGUN: SACVendor.MAX_SECURITY_CELLS_TITAN_SHARD_CANNON,
    SACTitanWeapons.BEEMINEGLOVE: SACVendor.AZCOTAL_ALLEY_TITAN_KILLER_BEE_MINE,
    SACTitanWeapons.WALLOPER: SACVendor.MAX_SECURITY_CELLS_TITAN_MARAUDER,
    SACTitanWeapons.MINELAUNCHER: SACVendor.ASYANICA_ROOFTOPS_TITAN_ORDNANCE_LAUNCHER,
    SACProtoWeapons.THROWTIE: SACVendor.BOLTAIRE_MUSEUM_PROTO_WHIRLWIND_THROWTIE,
    SACProtoWeapons.CUFFLINK: SACVendor.ASYANICA_ROOFTOPS_PROTO_WRIST_MORTAR,
    SACProtoWeapons.TANGLEVINE: SACVendor.AZCOTAL_ALLEY_PROTO_KUDZU_TANGLE,
    SACProtoWeapons.FLAMETHROWERPEN: SACVendor.VENANTONIO_LABS_PROTO_HELLFIRE_HAVERSACK,
    SACProtoWeapons.HOLOKNUCKLES: SACVendor.BOLTAIRE_MUSEUM_CLANK_PROTO_HARDLIGHT_FIST,
    SACProtoWeapons.LIGHTNINGUMBRELLA: SACVendor.VENANTONIO_LABS_PROTO_LIGHTNING_ROD,
}


def vendor_location_name(display_name: str) -> str:
    return VENDOR_LOCATION_NAMES[display_name]


NG_PLUS_VENDOR_LOCATIONS = frozenset(vendor_location_name(name) for name in NG_PLUS_VENDOR_ITEMS)
