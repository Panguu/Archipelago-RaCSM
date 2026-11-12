from dataclasses import dataclass


@dataclass(frozen=True)
class SACCheats:
    BIG_HEADED_CLANK = "Big Headed Clank"
    BIG_HEADED_RATCHET = "Big Headed Ratchet"
    MIRRORED_LEVELS = "Mirrored Levels"
    WEAPON_SWITCHING = "Weapon Switching"
    BIG_HEADED_ENEMIES = "Big Headed Enemies"
    SUPER_BLOOM = "Super Bloom"
    OLD_TIMEY = "Old Timey"
    EXPAT_EXCHANGE = "Expat Exchange"
    BOLT_CONFUSION = "Bolt Confusion"
    PUMPKIN_HEADS = "Pumpkin Heads"
    SNOWMAN_HEADS = "Snowman Heads"
    KAPOW = "Kapow"
    RATCHET_PACK = "Ratchet Pack"


CHEAT_SKILL_POINT_THRESHOLD: dict[str, int] = {
    SACCheats.BIG_HEADED_CLANK: 4,
    SACCheats.BIG_HEADED_RATCHET: 8,
    SACCheats.MIRRORED_LEVELS: 12,
    SACCheats.WEAPON_SWITCHING: 16,
    SACCheats.BIG_HEADED_ENEMIES: 20,
    SACCheats.SUPER_BLOOM: 24,
    SACCheats.OLD_TIMEY: 26,
    SACCheats.EXPAT_EXCHANGE: 28,
    SACCheats.BOLT_CONFUSION: 32,
    SACCheats.PUMPKIN_HEADS: 40,
    SACCheats.SNOWMAN_HEADS: 45,
    SACCheats.KAPOW: 50,
    SACCheats.RATCHET_PACK: 65,
}


@dataclass(frozen=True)
class SACTraps:
    WEAPON_SWITCHING = "Weapon Switching Trap"
    MIRRORED_LEVELS = "Mirrored Levels Trap"
    BOLT_CONFUSION = "Bolt Confusion Trap"
    BIG_HEADED = "Big Headed Trap"
    GADGETRON_DEBT = "Gadgetron Debt Trap"
    ONE_HP = "One HP Trap"


ALL_TRAPS: tuple[str, ...] = (
    SACTraps.WEAPON_SWITCHING, SACTraps.MIRRORED_LEVELS, SACTraps.BOLT_CONFUSION,
    SACTraps.BIG_HEADED, SACTraps.GADGETRON_DEBT, SACTraps.ONE_HP,
)
GADGETRON_DEBT_PERCENT = 8


TRAP_CHEATS: dict[str, tuple[str, ...]] = {
    SACTraps.WEAPON_SWITCHING: (SACCheats.WEAPON_SWITCHING,),
    SACTraps.MIRRORED_LEVELS: (SACCheats.MIRRORED_LEVELS,),
    SACTraps.BOLT_CONFUSION: (SACCheats.BOLT_CONFUSION,),
    SACTraps.BIG_HEADED: (SACCheats.BIG_HEADED_CLANK, SACCheats.BIG_HEADED_RATCHET),
}

# Only the cheat traps last a while; Gadgetron Debt and One HP happen once.
TRAP_DURATIONS: dict[str, int] = dict.fromkeys(TRAP_CHEATS, 30)
