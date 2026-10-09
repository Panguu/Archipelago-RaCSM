"""SACLocation: one record per AP location, with its case, category and access rule; CaseRegion groups a case's."""
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from enum import Enum, auto
from typing import TYPE_CHECKING

from rule_builder.rules import Rule

from ..constants.planets import CASE_NAME_TO_OPERATIVE, CASE_NAME_TO_PLANET
from ..constants.skill_point_requirements import EXTRA_SKILL_POINT_OPERATIVES, SKILL_POINT_DIFFICULTY
from ..constants.vendor import NG_PLUS_VENDOR_ITEMS
from ..options import Missions

if TYPE_CHECKING:
    from ..options import SecretAgentClankOptions
    from ..world import SecretAgentClankWorld

BASE_ID = 77_800_000


class SACLocationType(Enum):
    RATCHET_WEAPON = auto()
    CLANK_WEAPON = auto()
    CLANK_GADGET = auto()
    GADGET_PICKUP = auto()
    GADGETBOT_CHALLENGE = auto()
    SPECIAL_CHALLENGE = auto()
    RATCHET_CHALLENGE = auto()
    TITANIUM_BOLT = auto()
    CASE_COMPLETE = auto()
    MISSION = auto()
    SKILL_POINT = auto()
    CUTSCENE = auto()
    KEYCARD = auto()
    ALIEN_CODE = auto()
    VENDOR = auto()
    TITAN_VENDOR = auto()
    MOD_VENDOR = auto()
    WEAPON_LEVEL = auto()
    NANOTECH = auto()
    STEALTH_TAKEDOWN = auto()


# Order of location types within a case region: pickups first, then missions and
# each optional category.
_REGION_TYPE_ORDER: tuple[SACLocationType, ...] = (
    SACLocationType.RATCHET_WEAPON, SACLocationType.CLANK_WEAPON, SACLocationType.CLANK_GADGET,
    SACLocationType.GADGET_PICKUP, SACLocationType.GADGETBOT_CHALLENGE, SACLocationType.SPECIAL_CHALLENGE,
    SACLocationType.RATCHET_CHALLENGE, SACLocationType.TITANIUM_BOLT, SACLocationType.CASE_COMPLETE,
    SACLocationType.MISSION, SACLocationType.SKILL_POINT, SACLocationType.CUTSCENE,
    SACLocationType.KEYCARD, SACLocationType.ALIEN_CODE,
)


@dataclass(frozen=True, slots=True)
class SACLocation:
    name: str
    type: SACLocationType
    # A fixed rule, or a function of the world for option-dependent rules; None means
    # reachable with its region.
    rule: "Rule | Callable[[SecretAgentClankWorld], Rule] | None" = None
    # SACCases constant, filled in by CaseRegion; None outside the case regions (vendor, levels, ...).
    case: str | None = None

    def resolve_rule(self, world: "SecretAgentClankWorld") -> "Rule | None":
        return self.rule if self.rule is None or isinstance(self.rule, Rule) else self.rule(world)

    def available(self, options: "SecretAgentClankOptions") -> bool:
        """Whether this location exists at all under the given options (the category toggles)."""
        match self.type:
            case SACLocationType.VENDOR:
                return self.name.removeprefix("Vendor: ") not in NG_PLUS_VENDOR_ITEMS or bool(options.ng_plus.value)
            case SACLocationType.CASE_COMPLETE:
                return options.all_missions.value != Missions.option_all
            case SACLocationType.MISSION:
                return options.all_missions.value == Missions.option_all
            case SACLocationType.SKILL_POINT:
                return (options.skill_points.value >= SKILL_POINT_DIFFICULTY[self.name]
                        and all(options.operatives.value.get(operative, 0) for operative in self.operatives))
            case SACLocationType.CUTSCENE:
                return bool(options.all_cutscenes)
            case SACLocationType.KEYCARD:
                return options.keycard_checks_enabled and self.operatives_enabled(options)
            case SACLocationType.ALIEN_CODE:
                return options.alien_code_checks_enabled and self.operatives_enabled(options)
        return True

    def operatives_enabled(self, options: "SecretAgentClankOptions") -> bool:
        """Whether every operative this location needs is enabled."""
        return all(options.operatives.value.get(operative, 0) for operative in self.operatives)

    @property
    def operatives(self) -> frozenset[str]:
        """Operatives that must be enabled to play this location: its case's, plus any a skill point also needs."""
        if self.case is None:
            return frozenset()
        return frozenset({CASE_NAME_TO_OPERATIVE[self.case], *EXTRA_SKILL_POINT_OPERATIVES.get(self.name, ())})

    @property
    def region_order(self) -> int:
        return _REGION_TYPE_ORDER.index(self.type)


class CaseRegion:
    """One case's AP region: the case, and every location played in it."""

    def __init__(self, case: str, locations: Iterable[SACLocation]) -> None:
        self.case = case
        self.locations: tuple[SACLocation, ...] = tuple(replace(location, case=case) for location in locations)

    @property
    def planet(self) -> str:
        return CASE_NAME_TO_PLANET[self.case]

    def __repr__(self) -> str:
        return f"CaseRegion({self.case!r}, {len(self.locations)} locations)"
