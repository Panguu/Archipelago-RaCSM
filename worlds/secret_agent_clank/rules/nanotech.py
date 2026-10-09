"""Editable access rules for Clank and Ratchet Nanotech level checks, tiered by cases reached."""
from typing import TYPE_CHECKING

from rule_builder.rules import CanReachRegion, False_, Has, Rule

from ..constants import CASES_BY_OPERATIVE, SACOperatives
from ..constants.challenge_mode import PROGRESSIVE_CHALLENGE_MODE
from ..constants.nanotech import CLANK_NG_CAP, CLANK_START_NANOTECH, RATCHET_NG_CAP, RATCHET_START_NANOTECH
from .rule_helpers import AtLeast, HasEnemyAccess, region_names

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld

NANOTECH_LEVELS_PER_CASE = 10
"""Each Clank case with reachable enemies puts this many more Clank Nanotech levels in logic."""

RATCHET_NANOTECH_LEVELS_PER_CASE = 15
"""Each reachable Ratchet case puts this many more Ratchet Nanotech levels in logic."""


def nanotech_cases_required(level: int) -> int:
    """Clank cases with enemy access needed for `level`: 16-25 need one, 26-35 two, and so on."""
    return -(-(level - CLANK_START_NANOTECH) // NANOTECH_LEVELS_PER_CASE)


def ratchet_nanotech_cases_required(level: int) -> int:
    """Ratchet cases needed for `level`: 21-35 need one, 36-50 two, and so on."""
    return -(-(level - RATCHET_START_NANOTECH) // RATCHET_NANOTECH_LEVELS_PER_CASE)


def nanotech_access_rule(world: "SecretAgentClankWorld", level: int) -> Rule:
    rule = HasEnemyAccess(world, nanotech_cases_required(level))
    if world.options.progressive_challenge_mode and level > CLANK_NG_CAP:
        rule = rule & Has(PROGRESSIVE_CHALLENGE_MODE)
    return rule


def ratchet_nanotech_access_rule(world: "SecretAgentClankWorld", level: int) -> Rule:
    existing = region_names(world)
    cases = [CanReachRegion(case.name) for case in CASES_BY_OPERATIVE[SACOperatives.RATCHET] if case.name in existing]
    rule = AtLeast(min(ratchet_nanotech_cases_required(level), len(cases)), *cases) if cases else False_()
    if world.options.progressive_challenge_mode and level > RATCHET_NG_CAP:
        rule = rule & Has(PROGRESSIVE_CHALLENGE_MODE)
    return rule
