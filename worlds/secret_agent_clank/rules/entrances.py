from dataclasses import dataclass
from typing import TYPE_CHECKING

from rule_builder.rules import Has, HasFromListUnique, Rule, TWorld
from typing_extensions import override

from ..constants import (
    ALL_CASES,
    CASE_NAME_TO_CASE,
    CASE_NAME_TO_INFOBOT,
    CLANK_NG_CAP,
    SACCases,
    SACClankGadgets,
    SACClankWeapons,
)
from .nanotech import ClankNanotechRule
from .rule_helpers import HasCase, disabled_operatives

if TYPE_CHECKING:
    from ..world import SecretAgentClankWorld

KLUNKS_LAIR_WEAPONS: tuple[str, ...] = (
    SACClankWeapons.THROWTIE,
    SACClankWeapons.CUFFLINK,
    SACClankWeapons.TANGLEVINE,
    SACClankWeapons.FLAMETHROWERPEN,
    SACClankWeapons.HOLOKNUCKLES,
    SACClankWeapons.LIGHTNINGUMBRELLA,
)
KLUNKS_LAIR_WEAPON_COUNT = 3


@dataclass
class KlunksLairRule(Rule[TWorld], game="Secret Agent Clank"):
    @override
    def _instantiate(self, world: TWorld) -> Rule.Resolved:
        rule = HasFromListUnique(*KLUNKS_LAIR_WEAPONS, count=KLUNKS_LAIR_WEAPON_COUNT)
        if world.options.ng_plus.value or world.options.progressive_challenge_mode:
            rule = rule & Has(SACClankGadgets.CLANKPDA) & ClankNanotechRule(CLANK_NG_CAP)
        return rule.resolve(world)


@dataclass
class CaseAccessRule(Rule[TWorld], game="Secret Agent Clank"):
    cases: str

    @override
    def _instantiate(self, world: TWorld) -> Rule.Resolved:
        case = CASE_NAME_TO_CASE[self.cases]
        rule = HasCase(case.name)
        item = CASE_NAME_TO_INFOBOT.get(case.name)
        if item:
            rule = rule | Has(item)
        if case.name == SACCases.KLUNKS_LAIR:
            rule = rule & KlunksLairRule()
        return rule.resolve(world)


def set_entrance_rules(world: "SecretAgentClankWorld") -> None:
    player = world.player
    mw = world.multiworld
    disabled = disabled_operatives(world)

    for case in ALL_CASES:
        if case.operative in disabled:
            continue
        world.set_rule(mw.get_entrance(f"To {case.name}", player), CaseAccessRule(case.name))
