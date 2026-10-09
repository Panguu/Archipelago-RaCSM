"""Native mod IDs, GadgetData slots and English labels from the USA mod catalog."""
from typing import NamedTuple

from .clank_gadgets import SACClankWeapons
from .vendor import SACVendor
from .weapons import SACRatchetWeapons


class SACWeaponMods:
    DUAL_LACERATORS_SEEKER = "Dual Lacerators (Ratchet): Seeker Mod"
    DUAL_LACERATORS_HUNTER = "Dual Lacerators (Ratchet): Hunter Mod"
    SHARD_GUN_ICY_HALO = "Shard Gun (Ratchet): Ice Halo Mod"
    SHARD_GUN_CHARGE_UP = "Shard Gun (Ratchet) Charge-Up Mod"
    BEE_MINE_MK_II_EXPLOSIVE_NATURE = "Bee Mine Mk. II (Ratchet): Explosive Nature Mod"
    BEE_MINE_MK_II_KILLER_HONEY = "Bee Mine Mk. II (Ratchet): Killer Honey Mod"
    SHOCK_ROCKET_STATIC_CHARGE = "Shock Rocket (Ratchet): Static Charge Mod"
    SHOCK_ROCKET_TASER = "Shock Rocket (Ratchet): Taser Mod"
    WALLOPER_LIGHTNING_SPEED = "Walloper (Ratchet): Lightning Speed Mod"
    WALLOPER_EARTHQUAKE = "Walloper (Ratchet): Earthquake Mod"
    PLASMA_WHIP_FLAME_TRAILS = "Plasma Whip (Ratchet): Flame Trails Mod"
    PLASMA_WHIP_FIRE_SNAKE = "Plasma Whip (Ratchet): Fire Snake Mod"
    PORK_BOMB_GUN_WAR_PIGS = "Pork Bomb Gun (Ratchet): War Pigs Mod"
    PORK_BOMB_GUN_TASTY_PIGS = "Pork Bomb Gun (Ratchet): Tasty Pigs Mod"
    MINE_LAUNCHER_ORDNANCE = "Mine Launcher (Ratchet): Ordnance Mod"
    MINE_LAUNCHER_PERSISTENCE = "Mine Launcher (Ratchet): Persistence Mod"
    BLOWTORCH_BRIEFCASE_MOLTEN_BOLT = "Blowtorch Briefcase (Clank): Molten Bolt Mod"
    THUNDERSTORM_UMBRELLA_XENOS_CAPACITOR = "Thunderstorm Umbrella (Clank): Xeno's Capacitor Mod"
    THUNDERSTORM_UMBRELLA_THUNDERCLOUD = "Thunderstorm Umbrella (Clank): Thundercloud Mod"

# Mod name -> SACVendor location; the CHALLENGE_MOD_IDS rewards are not sold and have none.
MOD_VENDOR_LOCATION_NAMES: dict[str, str] = {
    SACWeaponMods.DUAL_LACERATORS_SEEKER: SACVendor.ASYANICA_ROOFTOPS_DUAL_LACERATOR_SEEKER,
    SACWeaponMods.DUAL_LACERATORS_HUNTER: SACVendor.ASYANICA_ROOFTOPS_DUAL_LACERATOR_HUNTER,
    SACWeaponMods.SHARD_GUN_ICY_HALO: SACVendor.ASYANICA_ROOFTOPS_DUAL_SHARD_GUN_ICE_HALO,
    SACWeaponMods.BEE_MINE_MK_II_EXPLOSIVE_NATURE: SACVendor.AZCOTAL_ALLEY_BEE_MINE_MK_II_EXPLOSIVE_NATURE,
    SACWeaponMods.BEE_MINE_MK_II_KILLER_HONEY: SACVendor.HIGH_ROLLERS_CASINO_BEE_MINE_MK_II_KILLER_HONEY,
    SACWeaponMods.SHOCK_ROCKET_STATIC_CHARGE: SACVendor.SPACESHIP_GRAVEYARD_SHOCK_ROCKET_STATIC_CHARGE,
    SACWeaponMods.SHOCK_ROCKET_TASER: SACVendor.PRISON_BREAKOUT_SHOCK_ROCKET_TASER,
    SACWeaponMods.WALLOPER_LIGHTNING_SPEED: SACVendor.ASYANICA_ROOFTOPS_WALLOPER_LIGHTNING_SPEED,
    SACWeaponMods.PLASMA_WHIP_FLAME_TRAILS: SACVendor.PRISON_BREAKOUT_PLASMA_WHIP_FLAME_TRAILS,
    SACWeaponMods.PLASMA_WHIP_FIRE_SNAKE: SACVendor.SPACESHIP_GRAVEYARD_SHOCK_PLASMA_WHIP_FIRE_SNAKE,
    SACWeaponMods.PORK_BOMB_GUN_WAR_PIGS: SACVendor.THE_SHOWERS_PORK_BOMB_GUN_WAR_PIGS,
    SACWeaponMods.PORK_BOMB_GUN_TASTY_PIGS: SACVendor.SPACESHIP_GRAVEYARD_SHOCK_ROCKET_PORK_BOMB_GUN_TASTY_PIGS,
    SACWeaponMods.MINE_LAUNCHER_ORDNANCE: SACVendor.AZCOTAL_ALLEY_MINE_LAUNCHER_ORDNANCE,
    SACWeaponMods.MINE_LAUNCHER_PERSISTENCE: SACVendor.AZCOTAL_ALLEY_MINE_LAUNCHER_PERSISTENCE,
    SACWeaponMods.BLOWTORCH_BRIEFCASE_MOLTEN_BOLT: SACVendor.CHALLENGE_MODE_BLOWTORCH_BRIEFCASE_MOLTEN_BOLT,
    SACWeaponMods.THUNDERSTORM_UMBRELLA_XENOS_CAPACITOR: SACVendor.CHALLENGE_MODE_THUNDERSTORM_UMBRELLA_XENOS_CAPACITOR,
    SACWeaponMods.THUNDERSTORM_UMBRELLA_THUNDERCLOUD: SACVendor.CHALLENGE_MODE_THUNDERSTORM_UMBRELLA_THUNDERCLOUD,
}


class WeaponMod(NamedTuple):
    mod_id: int
    weapon: str  # SACRatchetWeapons/SACClankWeapons display name, not the WEAPON_ORDER internal
    slot: int
    name: str
    ng_plus: bool = False

    @property
    def location(self) -> str | None:
        return MOD_VENDOR_LOCATION_NAMES.get(self.name)


WEAPON_MODS = (
    WeaponMod(1, SACRatchetWeapons.BLASTER, 0, SACWeaponMods.DUAL_LACERATORS_SEEKER),
    WeaponMod(2, SACRatchetWeapons.BLASTER, 1, SACWeaponMods.DUAL_LACERATORS_HUNTER),
    WeaponMod(4, SACRatchetWeapons.SHARDGUN, 0, SACWeaponMods.SHARD_GUN_ICY_HALO),
    WeaponMod(5, SACRatchetWeapons.SHARDGUN, 1, SACWeaponMods.SHARD_GUN_CHARGE_UP),
    WeaponMod(7, SACRatchetWeapons.BEEMINEGLOVE, 0, SACWeaponMods.BEE_MINE_MK_II_EXPLOSIVE_NATURE),
    WeaponMod(8, SACRatchetWeapons.BEEMINEGLOVE, 1, SACWeaponMods.BEE_MINE_MK_II_KILLER_HONEY),
    WeaponMod(10, SACRatchetWeapons.SHOCKROCKET, 0, SACWeaponMods.SHOCK_ROCKET_STATIC_CHARGE),
    WeaponMod(11, SACRatchetWeapons.SHOCKROCKET, 1, SACWeaponMods.SHOCK_ROCKET_TASER),
    WeaponMod(13, SACRatchetWeapons.WALLOPER, 0, SACWeaponMods.WALLOPER_LIGHTNING_SPEED),
    WeaponMod(14, SACRatchetWeapons.WALLOPER, 1, SACWeaponMods.WALLOPER_EARTHQUAKE),
    WeaponMod(16, SACRatchetWeapons.PLASMAWHIP, 0, SACWeaponMods.PLASMA_WHIP_FLAME_TRAILS),
    WeaponMod(17, SACRatchetWeapons.PLASMAWHIP, 1, SACWeaponMods.PLASMA_WHIP_FIRE_SNAKE),
    WeaponMod(19, SACRatchetWeapons.PORKBOMB, 0, SACWeaponMods.PORK_BOMB_GUN_WAR_PIGS),
    WeaponMod(20, SACRatchetWeapons.PORKBOMB, 1, SACWeaponMods.PORK_BOMB_GUN_TASTY_PIGS),
    WeaponMod(22, SACRatchetWeapons.MINELAUNCHER, 0, SACWeaponMods.MINE_LAUNCHER_ORDNANCE),
    WeaponMod(23, SACRatchetWeapons.MINELAUNCHER, 1, SACWeaponMods.MINE_LAUNCHER_PERSISTENCE),
    WeaponMod(25, SACClankWeapons.FLAMETHROWERPEN, 0, SACWeaponMods.BLOWTORCH_BRIEFCASE_MOLTEN_BOLT, True),
    WeaponMod(28, SACClankWeapons.LIGHTNINGUMBRELLA, 0, SACWeaponMods.THUNDERSTORM_UMBRELLA_XENOS_CAPACITOR, True),
    WeaponMod(29, SACClankWeapons.LIGHTNINGUMBRELLA, 1, SACWeaponMods.THUNDERSTORM_UMBRELLA_THUNDERCLOUD, True),
)


# No Shelter and Past Due award these mods; they are not shop purchases.
CHALLENGE_MOD_IDS = frozenset({5, 14})
VENDOR_MODS = tuple(mod for mod in WEAPON_MODS if mod.mod_id not in CHALLENGE_MOD_IDS)

def enabled_mods(characters, ng_plus):
    return tuple(mod for mod in VENDOR_MODS
                 if ('Clank' if mod.ng_plus else 'Ratchet') in characters
                 and (not mod.ng_plus or ng_plus > 0))
