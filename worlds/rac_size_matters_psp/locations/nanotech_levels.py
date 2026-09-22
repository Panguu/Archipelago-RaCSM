from rule_builder.rules import True_

from ..rules._helpers import HasGoodExpPlanet


def access_rule(world, *, level):
    if level > 20 and world.options.nanotech_experience_multiplier.value <= 8:
        return HasGoodExpPlanet()
    return True_()
