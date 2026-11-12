import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING

from BaseClasses import CollectionState
from rule_builder.rules import CanReachRegion, False_, Has, HasAll, HasAny, NestedRule, Or, Rule, True_, TWorld
from typing_extensions import override

from ..constants import (
    ALL_OPERATIVES,
    CASE_NAME_TO_CASE,
    CASE_NAME_TO_INFOBOT,
    PROGRESSIVE_CHALLENGE_MODE,
    PROGRESSIVE_PLANET_ITEM_NAME,
    PROGRESSIVE_WRENCH,
    InfobotsOptions,
    SACCases,
    SACClankGadgets,
    SACClankWeapons,
)
from ..options import enabled_operatives

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld


def region_names(world: "SecretAgentClankWorld") -> set[str]:
    return {region.name for region in world.multiworld.get_regions(world.player)}


@dataclass
class HasCase(Rule[TWorld], game="Secret Agent Clank"):
    cases: str

    @override
    def _instantiate(self, world: TWorld) -> Rule.Resolved:
        rule = True_()
        if world.options.infobots == InfobotsOptions.CASES and self.cases in CASE_NAME_TO_INFOBOT:
            rule = Has(CASE_NAME_TO_INFOBOT[self.cases])
        elif world.options.infobots == InfobotsOptions.PROGRESSIVE_PLANET:
            rule = HasProgressivePlanet(world, self.cases)
        return rule.resolve(world)


def HasProgressivePlanet(world: "SecretAgentClankWorld", case_name: str) -> Has | False_:
    planet = CASE_NAME_TO_CASE[case_name].planet
    order = world.planet_cases.get(planet, [])
    if case_name not in order:
        return False_()
    return Has(PROGRESSIVE_PLANET_ITEM_NAME[planet], order.index(case_name) + 1)


CLANK_ENEMY_CASES: dict[str, tuple[str, ...]] = {
    SACCases.BOLTAIRE_MUSEUM:       (),
    SACCases.ASYANICA_ROOFTOPS:     (SACClankWeapons.THROWTIE,),
    SACCases.AZCOTAL_ALLEY:         (),
    SACCases.GONDOLA_ASCENT:        (SACClankGadgets.JETBOOTS,),
    SACCases.HIGH_ROLLERS_CASINO:   (SACClankGadgets.HOLOMONOCLE,),
    SACCases.VENANTONIO_LABS:       (),
    SACCases.GALACTIC_BOLT_RESERVE: (SACClankWeapons.THROWTIE, SACClankWeapons.CUFFLINK, SACClankGadgets.JETBOOTS),
    SACCases.SPACESHIP_GRAVEYARD:   (),
    SACCases.UNDERWATER_BUNKER:     (),
}


@dataclasses.dataclass(init=False)
class AtLeast(NestedRule["SecretAgentClankWorld"], game="Secret Agent Clank"):
    """True when at least `count` of the child rules are true."""

    count: int = 1

    def __init__(self, count: int, *children: Rule, options=(), filtered_resolution: bool = False) -> None:
        super().__init__(*children, options=options, filtered_resolution=filtered_resolution)
        self.count = count

    def _instantiate(self, world: "SecretAgentClankWorld") -> Rule.Resolved:
        if self.count <= 0:
            return True_().resolve(world)
        if self.count > len(self.children):
            return False_().resolve(world)
        return self.Resolved(tuple(c.resolve(world) for c in self.children), self.count, player=world.player,
                             caching_enabled=getattr(world, "rule_caching_enabled", False))

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["count"] = self.count
        return data

    @classmethod
    def from_dict(cls, data, world_cls) -> "AtLeast":
        rule = super().from_dict(data, world_cls)
        rule.count = data["count"]
        return rule

    class Resolved(NestedRule.Resolved):
        count: int

        def _evaluate(self, state: CollectionState) -> bool:
            remaining = self.count
            for rule in self.children:
                if rule(state):
                    remaining -= 1
                    if not remaining:
                        return True
            return False

        def explain_str(self, state: CollectionState | None = None) -> str:
            return f"(at least {self.count} of: " + ", ".join(c.explain_str(state) for c in self.children) + ")"

        def __str__(self) -> str:
            return f"(at least {self.count} of: " + ", ".join(str(c) for c in self.children) + ")"


@dataclass
class EnemyCaseRule(Rule[TWorld], game="Secret Agent Clank"):
    cases: str

    @override
    def _instantiate(self, world: TWorld) -> Rule.Resolved:
        rule = CanReachRegion(self.cases)
        items = CLANK_ENEMY_CASES.get(self.cases, ())
        if items:
            rule = rule & HasAll(*items)
        return rule.resolve(world)


@dataclass
class HasEnemyAccess(Rule[TWorld], game="Secret Agent Clank"):
    """Clank can reach enemies in at least `cases` Clank cases (capped at the cases that exist)."""

    cases: int = 1

    @override
    def _instantiate(self, world: TWorld) -> Rule.Resolved:
        existing = region_names(world)
        rules = [EnemyCaseRule(case) for case in CLANK_ENEMY_CASES if case in existing]
        if not rules:
            return False_().resolve(world)
        if self.cases <= 1:
            return Or(*rules).resolve(world)
        return AtLeast(min(self.cases, len(rules)), *rules).resolve(world)


@dataclass
class HasProjectileWeapon(Rule[TWorld], game="Secret Agent Clank"):
    @override
    def _instantiate(self, world: TWorld) -> Rule.Resolved:
        return HasAny(SACClankWeapons.THROWTIE, SACClankWeapons.LIGHTNINGUMBRELLA,
                      SACClankWeapons.CUFFLINK).resolve(world)


def disabled_operatives(world: "SecretAgentClankWorld") -> set[str]:
    return {
        operative for operative in ALL_OPERATIVES
        if operative not in enabled_operatives(world.options)
    }


@dataclass
class ProgressiveChallengeModeRule(Rule[TWorld], game="Secret Agent Clank"):
    @override
    def _instantiate(self, world: TWorld) -> Rule.Resolved:
        rule = Has(PROGRESSIVE_CHALLENGE_MODE) if world.options.progressive_challenge_mode else True_()
        return rule.resolve(world)


@dataclass
class ProgressiveWrenchRule(Rule[TWorld], game="Secret Agent Clank"):
    @override
    def _instantiate(self, world: TWorld) -> Rule.Resolved:
        rule = Has(PROGRESSIVE_WRENCH) if world.options.progressive_wrench else True_()
        return rule.resolve(world)
