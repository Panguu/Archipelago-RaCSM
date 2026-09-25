from dataclasses import dataclass, field
from itertools import count

from BaseClasses import Location
from rule_builder.rules import Has, Rule


BASE_ID = 1_240_000_000
_LOCATION_IDS = count(BASE_ID)


class Kind:
    SCORE = 'score'
    PRIZE = 'prize'
    KEY = 'key'
    STICKER_SWITCH = 'sticker_switch'
    COMPLETE = 'complete'
    ACE = 'ace'
    ALL_PRIZES = 'all_prizes'
    REWARD = 'reward'


@dataclass(eq=False)
class LBPLocationData:
    name: str
    level: str
    kind: str
    code: int = field(init=False, default_factory=lambda: next(_LOCATION_IDS))
    uid: int | None = None
    plan: str | None = None
    target_slot: str | None = None
    condition: str | None = None
    players: int = 1
    rule: Rule | None = None

    def access_rule(self, world) -> Rule:
        rule = world.level_rule(self.level)
        if self.kind == Kind.STICKER_SWITCH:
            rule = rule & Has(world.plan_item_name(self.plan))
        if self.rule is not None:
            rule = rule & self.rule
        return rule


class LBPLocation(Location):
    game = 'LittleBigPlanet'
    data: LBPLocationData | None = None
