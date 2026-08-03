"""Tests for planet/region access rules."""
from .bases import (
    ALL_PLANETS,
    ANY_PROJECTILE,
    CHALLAX_ITEMS,
    KALIDON_ITEMS,
    METALIS_ITEMS,
    RACSizeMatterTestBase,
)

_BASE = {"starting_weapons": 0, "starting_gadgets": 0}


class TestRegionAccess(RACSizeMatterTestBase):
    run_default_tests = False
    options = _BASE

    def test_pokitaru_always_reachable(self) -> None:
        self.assertTrue(self.can_reach_region("Pokitaru"))

    def test_ryllus_always_reachable_even_without_weapon(self) -> None:
        # Ryllus has no entrance access_rule: the game force-unlocks it via the
        # Pokitaru intro cutscene, so it's reachable from the start regardless
        # of items (see core/planets.py PlanetUnlockState._ryllus_released).
        self.assertTrue(self.can_reach_region("Ryllus"))

    def test_ryllus_reachable_with_projectile(self) -> None:
        self.collect_by_name([ANY_PROJECTILE])
        self.assertTrue(self.can_reach_region("Ryllus"))

    def test_kalidon_unreachable_without_gadgets(self) -> None:
        self.collect_by_name([ANY_PROJECTILE])
        self.assertFalse(self.can_reach_region("Kalidon"))

    def test_kalidon_reachable_with_items(self) -> None:
        self.collect_by_name(KALIDON_ITEMS)
        self.assertTrue(self.can_reach_region("Kalidon"))

    def test_metalis_unreachable_without_shrink_ray(self) -> None:
        self.collect_by_name(KALIDON_ITEMS)
        self.assertFalse(self.can_reach_region("Metalis"))

    def test_metalis_reachable_with_items(self) -> None:
        self.collect_by_name(METALIS_ITEMS)
        self.assertTrue(self.can_reach_region("Metalis"))

    def test_challax_unreachable_without_polarizer(self) -> None:
        self.collect_by_name(METALIS_ITEMS)
        self.assertFalse(self.can_reach_region("Challax"))

    def test_challax_reachable_with_items(self) -> None:
        self.collect_by_name(CHALLAX_ITEMS)
        self.assertTrue(self.can_reach_region("Challax"))

    def test_quodrona_unreachable_with_nothing(self) -> None:
        self.assertFalse(self.can_reach_region("Quodrona"))

    def test_quodrona_reachable_with_all_items(self) -> None:
        self.collect_by_name(ALL_PLANETS)
        self.assertTrue(self.can_reach_region("Quodrona"))

    def test_later_planets_blocked_without_progression(self) -> None:
        for planet in ("Kalidon", "Metalis", "Dreamtime", "Outpost Omega",
                       "Challax", "Dayni Moon", "Inside Clank", "Quodrona"):
            self.assertFalse(self.can_reach_region(planet),
                             f"{planet} reachable with no items")

    def test_ryllus_reachable_with_hypershot_only(self) -> None:
        self.collect_by_name(["Hypershot"])
        self.assertTrue(self.can_reach_region("Ryllus"))

    def test_kalidon_not_reachable_without_hypershot(self) -> None:
        self.collect_by_name([ANY_PROJECTILE, "Sprout-O-Matic"])
        self.assertFalse(
            self.can_reach_region("Kalidon"),
            "Kalidon reachable without Hypershot",
        )

    def test_kalidon_not_reachable_without_sprout(self) -> None:
        self.collect_by_name([ANY_PROJECTILE, "Hypershot"])
        self.assertFalse(
            self.can_reach_region("Kalidon"),
            "Kalidon reachable without Sprout-O-Matic",
        )
