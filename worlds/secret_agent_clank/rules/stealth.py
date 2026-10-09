"""Editable access rules for per-case Clank stealth takedown checks."""
from rule_builder.rules import CanReachRegion

from ..constants import SACCases
from ..locations.asyanica_rooftops import COMPLETE_RULE as ASYANICA_ROOFTOPS_COMPLETE_RULE
from ..locations.galactic_bolt_reserve import STEALTH_RULE as GALACTIC_BOLT_RESERVE_STEALTH_RULE

# Case -> extra items its stealth takedown enemies need. Unlisted cases only
# need the case itself.
STEALTH_CASE_RULES = {
    SACCases.ASYANICA_ROOFTOPS: ASYANICA_ROOFTOPS_COMPLETE_RULE,
    SACCases.GALACTIC_BOLT_RESERVE: GALACTIC_BOLT_RESERVE_STEALTH_RULE,
}


def stealth_access_rule(world, case):
    rule = CanReachRegion(case)
    if case in STEALTH_CASE_RULES:
        rule = rule & STEALTH_CASE_RULES[case]
    return rule
