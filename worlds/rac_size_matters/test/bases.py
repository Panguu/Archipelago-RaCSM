from test.bases import WorldTestBase


class RACSizeMatterTestBase(WorldTestBase):
    game = "Ratchet & Clank: Size Matters"


ANY_PROJECTILE  = "Lacerator"
RYLLUS_ITEMS    = [ANY_PROJECTILE, "Hypershot", "Sprout-O-Matic", "Infobot: Ryllus"]
KALIDON_ITEMS   = [*RYLLUS_ITEMS, "Infobot: Kalidon"]
METALIS_ITEMS   = [*KALIDON_ITEMS, "Shrink Ray", "Infobot: Metalis"]
CHALLAX_ITEMS   = [*METALIS_ITEMS, "Polarizer", "Infobot: Challax"]
ALL_PLANETS     = [*CHALLAX_ITEMS, "Infobot: Outpost Omega", "Infobot: Dayni Moon", "Infobot: Quodrona"]
