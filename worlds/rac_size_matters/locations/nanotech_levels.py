from functools import partial

from rule_builder.options import OptionFilter
from rule_builder.rules import And

from ..options import ChallengeMode
from ..rules._helpers import HasChallengeMode, HasExpAccess, HasGoodExpPlanet
from .model import Completion, LocationOptions, Rac5Categories, Rac5CompletionSources, Rac5Locations

# The player starts at Nanotech Level 5; levels above 50 only exist in Challenge Mode.
FIRST_LEVEL = 6
LAST_NORMAL_LEVEL = 50
LAST_LEVEL = 75
FIRST_DEFINITION_ORDER = 243


def access_rule(world, *, level):
    rules = [HasExpAccess()]
    if level > 20 and world.options.nanotech_experience_multiplier.value <= 8:
        rules.append(HasGoodExpPlanet())
    if level > LAST_NORMAL_LEVEL:
        rules.append(HasChallengeMode(world, 1))
    return rules[0] if len(rules) == 1 else And(*rules)


def _location(level: int) -> Rac5Locations:
    challenge_mode = level > LAST_NORMAL_LEVEL
    return Rac5Locations(
        f"Nanotech Level: {level}",
        "Menu",
        partial(access_rule, level=level),
        Completion(Rac5CompletionSources.NANOTECH_LEVELS, level),
        options=LocationOptions(
            requirements=(OptionFilter(ChallengeMode, (1, 2), "in"),) if challenge_mode else (),
            nanotech_level=level,
        ),
        categories=frozenset(
            (Rac5Categories.NANOTECH_LEVEL, Rac5Categories.CHALLENGE_MODE_NANOTECH_LEVEL)
            if challenge_mode
            else (Rac5Categories.NANOTECH_LEVEL,)
        ),
        level=level,
        definition_order=FIRST_DEFINITION_ORDER + level - FIRST_LEVEL,
    )


LOCATIONS = tuple(_location(level) for level in range(FIRST_LEVEL, LAST_LEVEL + 1))
