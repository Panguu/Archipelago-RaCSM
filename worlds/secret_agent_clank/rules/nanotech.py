"""Editable access rules for Clank Nanotech level checks, tiered by Clank cases reached."""
from typing import TYPE_CHECKING

from rule_builder.rules import Has, Rule

from ..constants import CASES_BY_OPERATIVE, SACOperatives
from ..constants.challenge_mode import PROGRESSIVE_CHALLENGE_MODE
from ..constants.nanotech import CLANK_NG_CAP
from .rule_helpers import HasEnemyAccess, can_reach_all_cases

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld

NANOTECH_EARLY_CAP = 30
"""Levels up to this need one Clank case with enemies; above it (incl. NG+) need every Clank case."""


def nanotech_late_rule(world: "SecretAgentClankWorld") -> Rule:
    return can_reach_all_cases(world, (case.name for case in CASES_BY_OPERATIVE[SACOperatives.CLANK]))


def nanotech_access_rule(world: "SecretAgentClankWorld", level: int) -> Rule:
    if level <= NANOTECH_EARLY_CAP:
        return HasEnemyAccess(world)
    rule = nanotech_late_rule(world)
    if world.options.progressive_challenge_mode and level > CLANK_NG_CAP:
        rule = rule & Has(PROGRESSIVE_CHALLENGE_MODE)
    return rule


def ratchet_nanotech_access_rule(world: "SecretAgentClankWorld", level: int) -> Rule:
    from rule_builder.rules import CanReachRegion, False_
    cases = CASES_BY_OPERATIVE[SACOperatives.RATCHET]
    if level <= NANOTECH_EARLY_CAP:
        rule = False_()
        for case in cases:
            rule = rule | CanReachRegion(case.name)
    else:
        rule = can_reach_all_cases(world, (case.name for case in cases))
    if world.options.progressive_challenge_mode and level > 60:
        rule = rule & Has(PROGRESSIVE_CHALLENGE_MODE)
    return rule
