from .weapon_order import WEAPON_ORDER, WeaponSlot


class SACPickups:
    """String constants for weapon/gadget pickup locations"""
    BOLTAIRE_MUSEUM_TIE_A_RANG = "Boltaire (Clank) - Boltaire Museum: Tie-A-Rang Pickup"
    BOLTAIRE_MUSEUM_JET_BOOTS = "Boltaire (Clank) - Boltaire Museum: Jet Boots Pickup"
    BOLTAIRE_MUSEUM_BLACKOUT_PEN = "Boltaire (Clank) - Boltaire Museum: Blackout Pen Pickup"
    BOLTAIRE_MUSEUM_DUAL_LACERATORS = "Boltaire (Clank) - Boltaire Museum: Dual Lacerators Pickup"
    BOLTAIRE_MUSEUM_THERM_OPTIC_SHADES = "Boltaire (Clank) - Boltaire Museum: Therm-Optic Shades Pickup"
    ASYANICA_ROOFTOPS_CUFFLINK_BOMB = "Asyanica (Clank) - Asyanica Rooftops: Cufflink Bomb Pickup"
    ASYANICA_ROOFTOPS_OMNI_KEY = "Asyanica (Clank) - Asyanica Rooftops: Omni-Key 5000 Pickup"
    ASYANICA_ROOFTOPS_MINE_LAUNCHER = "Asyanica (Clank) - Asyanica Rooftops: Mine Launcher Pickup"
    AZCOTAL_ALLEY_TANGLEVINE_CARNATION = "Rionosis (Clank) - Azcotal Alley: Tanglevine Carnation Pickup"
    AZCOTAL_ALLEY_BEE_MINE_MK_II = "Rionosis (Clank) - Azcotal Alley: Bee Mine Mk. II Pickup"
    HIGH_ROLLERS_CASINO_HOLO_MONOCLE = "The Paradis Des Tricheurs Casino (Clank) - High-Rollers Casino: Holo-Monocle Pickup"
    VENANTONIO_LABS_BLOWTORCH_BRIEFCASE = "Venantonio (Clank) - Venantonio Labs: Blowtorch Briefcase Pickup"
    MAX_SECURITY_CELLS_SHARDGUN = "Prison Planet (Ratchet) - Max-Security Cells: Shard Gun Pickup"
    MAX_SECURITY_CELLS_WALLOPER = "Prison Planet (Ratchet) - Max-Security Cells: Walloper Pickup"


# Pickups that only spawn in challenge mode; the item stays in the pool either way.
CHALLENGE_MODE_PICKUP_LOCATIONS = frozenset({SACPickups.BOLTAIRE_MUSEUM_THERM_OPTIC_SHADES})


# Native WEAPON_ORDER name -> the AP location the client sends when it is picked up.
PICKUP_LOCATION_BY_INTERNAL: dict[str, str] = {
    WEAPON_ORDER[slot]: name for slot, name in (
        (WeaponSlot.THROWTIE, SACPickups.BOLTAIRE_MUSEUM_TIE_A_RANG),
        (WeaponSlot.JETBOOTS, SACPickups.BOLTAIRE_MUSEUM_JET_BOOTS),
        (WeaponSlot.FOUNTAINPEN, SACPickups.BOLTAIRE_MUSEUM_BLACKOUT_PEN),
        (WeaponSlot.BLASTER, SACPickups.BOLTAIRE_MUSEUM_DUAL_LACERATORS),
        (WeaponSlot.SUNGLASSES, SACPickups.BOLTAIRE_MUSEUM_THERM_OPTIC_SHADES),
        (WeaponSlot.CUFFLINK, SACPickups.ASYANICA_ROOFTOPS_CUFFLINK_BOMB),
        (WeaponSlot.OMNIKEY, SACPickups.ASYANICA_ROOFTOPS_OMNI_KEY),
        (WeaponSlot.MINELAUNCHER, SACPickups.ASYANICA_ROOFTOPS_MINE_LAUNCHER),
        (WeaponSlot.TANGLEVINE, SACPickups.AZCOTAL_ALLEY_TANGLEVINE_CARNATION),
        (WeaponSlot.BEEMINEGLOVE, SACPickups.AZCOTAL_ALLEY_BEE_MINE_MK_II),
        (WeaponSlot.HOLOMONOCLE, SACPickups.HIGH_ROLLERS_CASINO_HOLO_MONOCLE),
        (WeaponSlot.FLAMETHROWERPEN, SACPickups.VENANTONIO_LABS_BLOWTORCH_BRIEFCASE),
        (WeaponSlot.SHARDGUN, SACPickups.MAX_SECURITY_CELLS_SHARDGUN),
        (WeaponSlot.WALLOPER, SACPickups.MAX_SECURITY_CELLS_WALLOPER),
    )
}
