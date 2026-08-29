from test.bases import WorldTestBase


class RACSizeMatterTestBase(WorldTestBase):
    game = "Ratchet & Clank: Size Matters"


# Shared item sets used across test files. RYLLUS_ITEMS omits the Pokitaru/Ryllus
# infobot since it's always precollected as the fixed start in these tests.
ANY_PROJECTILE  = "Lacerator"
RYLLUS_ITEMS    = [ANY_PROJECTILE, "Hypershot", "Sprout-O-Matic"]
KALIDON_ITEMS   = [*RYLLUS_ITEMS, "Infobot: Kalidon"]
METALIS_ITEMS   = [*KALIDON_ITEMS, "Shrink Ray", "Infobot: Metalis"]
CHALLAX_ITEMS   = [*METALIS_ITEMS, "Polarizer", "Infobot: Challax"]
ALL_PLANETS     = [*CHALLAX_ITEMS, "Infobot: Outpost Omega", "Infobot: Dayni Moon", "Infobot: Quodrona"]
