"""Per-case cumulative Clank stealth takedown checks."""
from .planets import SACCases

STEALTH_MAX_PER_CASE = 10
"""Highest stealth_takedown_checks value."""

# Clank cases with stealth takedowns, each with enough for the slider's maximum.
# Each gets stealth_takedown_checks checks. Location IDs follow this order, so
# add any new case at the end.
STEALTH_CASES: tuple[str, ...] = (
    SACCases.BOLTAIRE_MUSEUM,
    SACCases.ASYANICA_ROOFTOPS,
    SACCases.AZCOTAL_ALLEY,
    SACCases.HIGH_ROLLERS_CASINO,
    SACCases.GALACTIC_BOLT_RESERVE,
    SACCases.UNDERWATER_BUNKER,
)


def stealth_check_count(case, setting):
    """Checks a case gets for the stealth_takedown_checks slider value."""
    return min(setting, STEALTH_MAX_PER_CASE) if case in STEALTH_CASES else 0


def stealth_location_name(case, count):
    return f"Clank Stealth Takedowns - {case.split(': ', 1)[1]}: {count}"
