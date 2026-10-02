"""Starts with no free sphere 0 location can never fill, so they're rejected as an OptionError."""
from typing import Any, ClassVar

from Options import OptionError

from .bases import RACSizeMatterTestBase


class TestNoSphereZeroLocations(RACSizeMatterTestBase):
    """Fuzz seed 9226: Outpost Omega start with every starting weapon, so nothing is reachable at the start."""
    options: ClassVar[dict[str, Any]] = {
        "starting_weapons": 13,
        "starting_gadgets": 1,
        "clank_pack": True,
        "random_starting_planet": "unweighted",
        "progressive_weapons": False,
        "progressive_mods": False,
        "progressive_armour": False,
        "enabled_weapons": {
            "RYNO": 1, "Acid Bomb Glove": 1, "Laser Tracer": 1, "Scorcher": 1, "Concussion Gun": 1,
            "Shock Rocket": 1, "Static Barrier": 1, "Agents of Doom": 1,
        },
        "clank_challenges": False,
        "skyboard_challenges": "off",
        "enable_skyboard_challenge_skill_points": True,
        "all_missions": False,
        "all_cutscenes": False,
        "shrink_ray_options": False,
        "skill_points": False,
        "armour_set_checks": True,
        "weapon_level_checks": "level_8",
        "ng_plus_items": True,
    }
    seed = 989615983

    def setUp(self) -> None:
        pass

    @property
    def run_default_tests(self) -> bool:
        return False

    def test_raises_option_error(self) -> None:
        with self.assertRaisesRegex(OptionError, "reachable at the start"):
            self.world_setup(self.seed)
