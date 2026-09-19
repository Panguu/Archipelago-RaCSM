"""Case: one record per case, gathering everything that belongs to it (its own
identity plus every category's locations/items for it) in one place. CaseStructure:
a single per-case, bit-flag-tracked location -- pairs a short event title with its
Case, memory address and completion bit."""
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rule_builder.rules import False_, Has, True_

    from .missions import SACMissionEntry


@dataclass(frozen=True)
class SACTags:
    """String constants for CaseStructure.category -- shared across every category module instead of each one hand-typing its own local _CATEGORY."""

    ALIEN_CODE = "Alien Code"
    GADGETBOT_CHALLENGE = "Gadgetbot Challenge"
    KEYCARD = "Keycard"
    RATCHET_CHALLENGE = "Ratchet Challenge"
    SKILL_POINT = "Skill Point"
    SPECIAL_CHALLENGE = "Special Challenge"
    TITANIUM_BOLT = "T-Bolt"


@dataclass(frozen=True)
class Case:
    """One case's full identity plus every category's locations/items for it.

    The base fields (name/case_id/planet/operative/menu_id) are set at
    construction, same as before this merged CaseStructure's per-category
    data in -- everything else is a property that looks its category's own
    module up on demand (not at import time), so this class never has to
    import every category module directly (several of them already import
    SACCases from constants/planets.py, and planets.py is what builds
    ALL_CASES; importing them back here at module scope would cycle).
    A case with nothing in a given category (e.g. no vendor route) simply
    gets an empty tuple / None back, not a KeyError.
    """
    name: str
    case_id: int
    planet: str       # SACPlanets constant
    operative: str    # SACOperatives constant
    menu_id: "int | None" = None

    @property
    def missions(self) -> "tuple[SACMissionEntry, ...]":
        from .missions import CHAPTER_ENTRIES
        return tuple(CHAPTER_ENTRIES.get(self.name, ()))

    @property
    def cutscenes(self) -> "tuple[CaseStructure, ...]":
        from .cutscenes import CUTSCENES
        return tuple(entry for entry in CUTSCENES if entry.case_name == self.name)

    @property
    def ratchet_challenges(self) -> "tuple[CaseStructure, ...]":
        from .ratchet_challenges import RATCHET_CHALLENGES
        return tuple(entry for entry in RATCHET_CHALLENGES if entry.case_name == self.name)

    @property
    def gadgetbot_challenges(self) -> "tuple[CaseStructure, ...]":
        from .gadgetbot_challenges import GADGETBOT_CHALLENGES
        return tuple(entry for entry in GADGETBOT_CHALLENGES if entry.case_name == self.name)

    @property
    def special_challenges(self) -> "tuple[CaseStructure, ...]":
        from .special_challenges import SPECIAL_CHALLENGES
        return tuple(entry for entry in SPECIAL_CHALLENGES if entry.case_name == self.name)

    @property
    def skill_points(self) -> "tuple[CaseStructure, ...]":
        from .skillpoints import SKILL_POINTS
        return tuple(entry for entry in SKILL_POINTS if entry.case_name == self.name)

    @property
    def titanium_bolts(self) -> "tuple[CaseStructure, ...]":
        from .titanium_bolts import TITANIUM_BOLT_ENTRIES
        return tuple(entry for entry in TITANIUM_BOLT_ENTRIES.values() if entry.case_name == self.name)

    @property
    def keycards(self) -> "tuple[CaseStructure, ...]":
        from .keycards import KEYCARDS
        return tuple(entry for entry in KEYCARDS if entry.case_name == self.name)

    @property
    def alien_codes(self) -> "tuple[CaseStructure, ...]":
        from .alien_codes import ALIEN_CODES
        return tuple(entry for entry in ALIEN_CODES if entry.case_name == self.name)

    @property
    def weapons(self) -> tuple[str, ...]:
        from .weapons import WEAPONS_BY_CASE
        return WEAPONS_BY_CASE.get(self.name, ())

    @property
    def gadgets(self) -> tuple[str, ...]:
        from .weapons import GADGETS_BY_CASE
        return GADGETS_BY_CASE.get(self.name, ())

    @property
    def clank_gadget_pickups(self) -> "tuple[str, ...]":
        from .clank_gadgets import CLANK_GADGET_BY_CASE_ID
        return CLANK_GADGET_BY_CASE_ID.get(self.case_id, ())

    @property
    def vendor_purchases(self) -> "Has | True_ | False_ | None":
        """This case's vendor-route access rule, or None if it has no vendor route at all."""
        from ..rules.vendor_access import VENDOR_REQUIREMENTS
        return VENDOR_REQUIREMENTS.get(self.name)


@dataclass(frozen=True)
class CaseStructure:
    case_name: str          # SACCases constant
    event_name: str         # short title -- the one part every entry must hand-type
    category: str = ""      # e.g. "Gadgetbot Challenge", "Skill Point" -- "" for missions/cutscenes
    event_flag: int = 0      # bitmask within event_address's byte; 0 = not confirmed live yet
    event_address: int = 0   # 0 = not confirmed live yet
    # The real AP location name -- a category's SACXLocations constant (e.g.
    # SACSkillPointLocations), applied by with_display_names() below once the
    # whole tuple/dict is built. None falls back to __str__'s generic form.
    display_name: "str | None" = None

    @property
    def operative(self) -> str:
        from .planets import CASE_NAME_TO_OPERATIVE
        return CASE_NAME_TO_OPERATIVE.get(self.case_name, self.case_name)

    def check_flag(self, flag_value: int) -> bool:
        """Check if this event's completion bit is set in the given byte."""
        return bool(flag_value & self.event_flag)

    def __str__(self) -> str:
        if self.display_name is not None:
            return self.display_name
        middle = f"{self.category}: " if self.category else ""
        return f"{self.operative}: {self.case_name}: {middle}{self.event_name}"


def with_display_names(
    entries: tuple[CaseStructure, ...], names_cls: type,
) -> tuple[CaseStructure, ...]:
    """Attach each entry's real AP location name from names_cls (a SACXLocations-style
    class of hand-typed display strings), matched purely by declaration order -- both
    the entries tuple and names_cls's attributes must already correspond 1:1, in the
    same order (verified live via a length check, since the two are hand-authored
    separately and can drift)."""
    names = [value for name, value in vars(names_cls).items() if not name.startswith("_")]
    if len(names) != len(entries):
        raise ValueError(
            f"{names_cls.__name__} has {len(names)} entries, but {len(entries)} CaseStructure entries exist")
    return tuple(replace(entry, display_name=name) for entry, name in zip(entries, names))


def group_by_case(entries: tuple[CaseStructure, ...]) -> dict[str, tuple[str, ...]]:
    """Group a flat tuple of CaseStructure entries into case_name -> tuple of full display names, in declaration order -- the shape locations.py's *_BY_CASE loops expect (see e.g."""
    by_case: dict[str, list[str]] = {}
    for entry in entries:
        by_case.setdefault(entry.case_name, []).append(str(entry))
    return {case: tuple(names) for case, names in by_case.items()}
