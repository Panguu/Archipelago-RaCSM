"""Rule builders, matching worlds/rac_size_matters/rules/_helpers.py's HasWeapon/HasGadget/HasInfobot pattern (rule_builder.rules objects applied via world.set_rule(), not plain lambdas)."""
from typing import TYPE_CHECKING

from rule_builder.rules import Has, True_

from ..constants import (
    CASE_NAME_TO_INFOBOT,
    CHARACTER_ITEM_NAME,
    PLANET_ACCESS_ITEM_NAME,
    PROGRESSIVE_CHARACTER_ITEM_NAME,
)
from ..constants.clank_gadgets import SACClankWeapons
from ..constants.operatives import ALL_OPERATIVES, SACOperatives
from ..constants.planets import CASES_BY_OPERATIVE
from ..items import PROGRESSIVE_PLANET_ITEM_NAME
from ..options import Infobots

if TYPE_CHECKING:
    from ..constants.planets import Case
    from ..world import SecretAgentClankWorld


def HasPlanet(world: "SecretAgentClankWorld", planet: str) -> Has | True_:
    if (world.options.infobots == Infobots.option_progressive_planet):
        planets = world.progressive_planets
        return Has(PROGRESSIVE_PLANET_ITEM_NAME, planets.index(planet) + 1) if planet in planets else True_()
    if world.options.infobots in (Infobots.option_cases, Infobots.option_character_unlocks):
        return True_()
    item = PLANET_ACCESS_ITEM_NAME.get(planet)
    return Has(item) if item else True_()


def HasCase(world: "SecretAgentClankWorld", case_name: str) -> Has | True_:
    if (world.options.infobots == Infobots.option_progressive_planet) or world.options.infobots != Infobots.option_cases:
        return True_()
    item = CASE_NAME_TO_INFOBOT.get(case_name)
    return Has(item) if item else True_()


def HasProjectileWeapon() -> Has:
    return Has(SACClankWeapons.THROWTIE) | Has(SACClankWeapons.LIGHTNINGUMBRELLA) | Has(SACClankWeapons.CUFFLINK)


def HasCharacter(world: "SecretAgentClankWorld", character: str) -> Has | True_:
    if not (world.options.infobots == Infobots.option_character_unlocks):
        return True_()
    if character in CHARACTER_ITEM_NAME:
        return Has(CHARACTER_ITEM_NAME[character])
    return Has(PROGRESSIVE_CHARACTER_ITEM_NAME[character])


def disabled_operatives(world: "SecretAgentClankWorld") -> set[str]:
    """Operatives removed entirely via options.py's Operatives option -- shared by regions.py's create_regions() (to skip their cases' regions/locations outright) and entrances.py's set_entrance_rules() (to skip setting a rule on an entrance that was never created)."""
    return {
        operative for operative in ALL_OPERATIVES
        if operative not in world.options.operatives.value
    }


def case_access_rule(world: "SecretAgentClankWorld", case: "Case") -> Has | True_:
    rule = HasPlanet(world, case.planet) & HasCase(world, case.name)
    if case.operative != SACOperatives.SPECIAL_MISSIONS:
        if (world.options.infobots == Infobots.option_character_unlocks
                and case.operative in PROGRESSIVE_CHARACTER_ITEM_NAME):
            # 0-based index into that operative's own case list -- the Nth
            # case needs N PRIOR copies already owned, same convention as
            # HasPlanet's Progressive Planet count above. count = index + 1
            # was self-referential: the last case's own Progressive copy is
            # itself one of the exact number of copies that formula demanded
            # to reach it, an unreachable location no fill could ever place
            # that copy into (confirmed live via
            # test_qwark_only_fills_with_an_accessible_native_start's
            # Fill.FillError).
            count = list(CASES_BY_OPERATIVE[case.operative]).index(case)
            rule = rule & (Has(PROGRESSIVE_CHARACTER_ITEM_NAME[case.operative], count) if count else True_())
        else:
            rule = rule & HasCharacter(world, case.operative)
    # The seed precollects its starting case file in every access mode.
    # Explicit case files agree with resolve_owned_cases client-side.
    item = CASE_NAME_TO_INFOBOT.get(case.name)
    return rule | Has(item) if item else rule
