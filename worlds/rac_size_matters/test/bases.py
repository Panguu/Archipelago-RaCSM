from test.bases import WorldTestBase


class RACSizeMatterTestBase(WorldTestBase):
    game = "Ratchet & Clank: Size Matters"


# Shared item sets used across test files.
# Ryllus has no entrance access_rule (the game force-unlocks it via the
# Pokitaru intro cutscene before AP gating can apply), so RYLLUS_ITEMS is
# just a baseline of gadgets, not a Ryllus access requirement. Every planet
# after that is gated by its "Infobot: <Planet>" item (see rules/entrances.py).
ANY_PROJECTILE  = "Lacerator"
RYLLUS_ITEMS    = [ANY_PROJECTILE, "Hypershot", "Sprout-O-Matic"]
KALIDON_ITEMS   = [*RYLLUS_ITEMS, "Infobot: Kalidon"]
METALIS_ITEMS   = [*KALIDON_ITEMS, "Shrink Ray", "Infobot: Metalis"]
CHALLAX_ITEMS   = [*METALIS_ITEMS, "Polarizer", "Infobot: Challax"]
ALL_PLANETS     = [*CHALLAX_ITEMS, "Infobot: Outpost Omega", "Infobot: Dayni Moon", "Infobot: Quodrona"]
