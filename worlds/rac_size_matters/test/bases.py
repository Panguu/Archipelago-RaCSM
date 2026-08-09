from test.bases import WorldTestBase


class RACSizeMatterTestBase(WorldTestBase):
    game = "Ratchet & Clank: Size Matters"


# Shared item sets used across test files.
# Pokitaru and Ryllus are both gated on "Infobot: Pokitaru and Ryllus", same
# as every other planet's own infobot (see rules/entrances.py) -- but with
# random_starting_planet off (the default in these tests), that infobot is
# always precollected as the fixed start, so RYLLUS_ITEMS only needs to list
# the gadgets actually required past that point, not the infobot itself.
ANY_PROJECTILE  = "Lacerator"
RYLLUS_ITEMS    = [ANY_PROJECTILE, "Hypershot", "Sprout-O-Matic"]
KALIDON_ITEMS   = [*RYLLUS_ITEMS, "Infobot: Kalidon"]
METALIS_ITEMS   = [*KALIDON_ITEMS, "Shrink Ray", "Infobot: Metalis"]
CHALLAX_ITEMS   = [*METALIS_ITEMS, "Polarizer", "Infobot: Challax"]
ALL_PLANETS     = [*CHALLAX_ITEMS, "Infobot: Outpost Omega", "Infobot: Dayni Moon", "Infobot: Quodrona"]
