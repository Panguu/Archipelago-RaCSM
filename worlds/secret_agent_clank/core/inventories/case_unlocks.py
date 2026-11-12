from ...constants import (
    CASE_NAME_TO_INFOBOT,
    PROGRESSIVE_PLANET_ITEM_NAME,
)


def resolve_owned_cases(received_names: list[str], *, planet_cases: dict[str, list[str]] | None = None) -> set[str]:
    """Every case name the player currently has logical access to, derived from received item names alone."""
    owned: set[str] = set()

    for case_name, infobot in CASE_NAME_TO_INFOBOT.items():
        if infobot in received_names:
            owned.add(case_name)

    for planet, cases in (planet_cases or {}).items():
        owned.update(cases[:received_names.count(PROGRESSIVE_PLANET_ITEM_NAME[planet])])
    return owned
