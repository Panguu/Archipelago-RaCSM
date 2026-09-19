"""Native mod IDs, GadgetData slots and English labels from the USA mod catalog."""
from typing import NamedTuple

from .clank_gadgets import SACClankWeapons
from .vendor import vendor_location_name
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

class WeaponMod(NamedTuple):
    mod_id: int
    weapon: str  # SACRatchetWeapons/SACClankWeapons display name, not the WEAPON_ORDER internal
    slot: int
    name: str
    ng_plus: bool = False

    @property
    def location(self):
        return vendor_location_name(self.name)


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


def enabled_mods(characters, ng_plus):
    return tuple(mod for mod in WEAPON_MODS
                 if ('Clank' if mod.ng_plus else 'Ratchet') in characters
                 and (not mod.ng_plus or ng_plus > 0))
