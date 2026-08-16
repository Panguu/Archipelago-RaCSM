"""Tests for the Giant Clank option: the Metalis/Challax Giant Clank sequence
locations (armour pickup, story mission, and skill point checks)."""
from ..locations import (
    ARMOUR_PICKUP_LOCATIONS,
    CHALLENGE_MODE_1_ARMOUR_LOCATIONS,
    CHALLENGE_MODE_2_ARMOUR_LOCATIONS,
    GIANT_CLANK_LOCATIONS,
)
from .bases import RACSizeMatterTestBase

# Challenge Mode is off by default in both classes below, so its 8 armour
# pieces (4 Hyperborean, 4 Chameleon) are always excluded regardless of
# Giant Clank — same reasoning as GIANT_CLANK_LOCATIONS itself.
_CHALLENGE_MODE_ARMOUR_LOCATIONS = CHALLENGE_MODE_1_ARMOUR_LOCATIONS | CHALLENGE_MODE_2_ARMOUR_LOCATIONS


class TestGiantClankDisabled(RACSizeMatterTestBase):
    options = {"giant_clank": 0, "skill_points": 2}

    def test_giant_clank_locations_excluded(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for name in GIANT_CLANK_LOCATIONS:
            self.assertNotIn(name, names)

    def test_other_armour_pickups_still_present(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for name in ARMOUR_PICKUP_LOCATIONS:
            if name in GIANT_CLANK_LOCATIONS or name in _CHALLENGE_MODE_ARMOUR_LOCATIONS:
                continue
            self.assertIn(name, names)

    def test_item_count_matches_location_count(self) -> None:
        self.assertEqual(
            len(self.multiworld.itempool),
            len(self.multiworld.get_unfilled_locations(self.player)),
        )


class TestGiantClankEnabled(RACSizeMatterTestBase):
    options = {"giant_clank": 1, "skill_points": 2}

    def test_giant_clank_locations_present(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for name in GIANT_CLANK_LOCATIONS:
            self.assertIn(name, names)

    def test_all_armour_pickups_present(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for name in ARMOUR_PICKUP_LOCATIONS:
            if name in _CHALLENGE_MODE_ARMOUR_LOCATIONS:
                continue
            self.assertIn(name, names)

    def test_item_count_matches_location_count(self) -> None:
        self.assertEqual(
            len(self.multiworld.itempool),
            len(self.multiworld.get_unfilled_locations(self.player)),
        )
