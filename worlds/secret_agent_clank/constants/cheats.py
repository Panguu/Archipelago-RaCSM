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
    DAMAGE = "Damage Trap"


ALL_TRAPS: tuple[str, ...] = (
    SACTraps.WEAPON_SWITCHING, SACTraps.MIRRORED_LEVELS, SACTraps.BOLT_CONFUSION,
    SACTraps.BIG_HEADED, SACTraps.GADGETRON_DEBT, SACTraps.ONE_HP, SACTraps.DAMAGE,
)
GADGETRON_DEBT_PERCENT = 8
DAMAGE_PERCENT = 25

TRAP_LINK_SEND: dict[str, str] = {
    SACTraps.MIRRORED_LEVELS: "Mirror Trap",
    SACTraps.WEAPON_SWITCHING: "Gadget Shuffle Trap",
    SACTraps.ONE_HP: "One Hit KO",
    SACTraps.GADGETRON_DEBT: "Market Crash Trap",
    SACTraps.DAMAGE: "Damage Trap",
    SACTraps.BIG_HEADED: SACTraps.BIG_HEADED,
    SACTraps.BOLT_CONFUSION: SACTraps.BOLT_CONFUSION,
}
TRAP_LINK_RECEIVE: dict[str, str] = {
    **{trap: trap for trap in ALL_TRAPS},
    **{name: trap for trap, name in TRAP_LINK_SEND.items()},
    "Flip Horizontal Trap": SACTraps.MIRRORED_LEVELS,
    "Screen Flip Trap": SACTraps.MIRRORED_LEVELS,
    "Tool Swap Trap": SACTraps.WEAPON_SWITCHING,
    "One Hit Trap": SACTraps.ONE_HP,
    "Player Money Trap": SACTraps.GADGETRON_DEBT,
    "Expensive Stocks": SACTraps.GADGETRON_DEBT,
}


TRAP_CHEATS: dict[str, tuple[str, ...]] = {
    SACTraps.WEAPON_SWITCHING: (SACCheats.WEAPON_SWITCHING,),
    SACTraps.MIRRORED_LEVELS: (SACCheats.MIRRORED_LEVELS,),
    SACTraps.BOLT_CONFUSION: (SACCheats.BOLT_CONFUSION,),
    SACTraps.BIG_HEADED: (SACCheats.BIG_HEADED_CLANK, SACCheats.BIG_HEADED_RATCHET),
}

# Only the cheat traps last a while; Gadgetron Debt, One HP and Damage happen once.
TRAP_DURATIONS: dict[str, int] = dict.fromkeys(TRAP_CHEATS, 30)
