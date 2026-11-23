from dataclasses import dataclass

from rule_builder.rules import CanReachRegion, False_, Has, HasAll, Rule, TWorld
from typing_extensions import override

from ..constants import (
    ALL_CASES,
    EQUIPMENT_DISPLAY_TO_INTERNAL,
    VENDOR_REQUIREMENT_ITEMS,
    InfobotsOptions,
)
from ..constants import VENDOR_LOCATIONS
from .rule_helpers import HasEnemyAccess, HasProgressivePlanet, region_names

VENDOR_ONLY_ITEM_NAMES: frozenset[str] = frozenset(
    name for name, internal in EQUIPMENT_DISPLAY_TO_INTERNAL.items()
    if internal in VENDOR_LOCATIONS.values()
)

VENDOR_REQUIREMENTS = {
    case.name: HasAll(*VENDOR_REQUIREMENT_ITEMS[case.name]) if case.name in VENDOR_REQUIREMENT_ITEMS else False_()
    for case in ALL_CASES
}


@dataclass
class CaseOwnershipRule(Rule[TWorld], game="Secret Agent Clank"):
    """Whether the player owns the case, worked out the same way as the client does."""

    cases: str

    @override
    def _instantiate(self, world: TWorld) -> Rule.Resolved:
        rule = Has(self.cases)
        if world.options.infobots == InfobotsOptions.PROGRESSIVE_PLANET:
            rule = rule | HasProgressivePlanet(world, self.cases)
        return rule.resolve(world)


@dataclass
class VendorCaseRule(Rule[TWorld], game="Secret Agent Clank"):
    cases: str

    @override
    def _instantiate(self, world: TWorld) -> Rule.Resolved:
        if self.cases not in region_names(world):
            return False_().resolve(world)
        # Buying anything needs bolts, so the player has to be able to reach enemies.
        rule = CanReachRegion(self.cases) & VENDOR_REQUIREMENTS.get(self.cases, False_()) & HasEnemyAccess()
        return (rule & CaseOwnershipRule(self.cases)).resolve(world)

