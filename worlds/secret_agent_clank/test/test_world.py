import unittest

from Options import OptionError
from test.general import setup_multiworld

from ..world import SecretAgentClankWorld
from .bases import SecretAgentClankTestBase


class TestGeneration(SecretAgentClankTestBase):
    """Smoke test: the world generates successfully with default options."""
    options = {}


class TestGenerationWithSkillPoints(SecretAgentClankTestBase):
    """Smoke test: the world generates successfully with Skill Points on."""
    options = {"skill_points": True}


class TestGenerationWithCutscenes(SecretAgentClankTestBase):
    """Smoke test: the world generates successfully with All Cutscenes on."""
    options = {"all_cutscenes": True}


class TestGenerationInfobotsPlanets(SecretAgentClankTestBase):
    """Smoke test: coarser planet-level Infobots tier."""
    options = {"skill_points": True, "infobots": "planets"}


class TestGenerationProgressivePlanet(SecretAgentClankTestBase):
    """Smoke test: Progressive Planet replaces per-planet/per-case Infobots."""
    options = {"skill_points": True, "infobots": "progressive_planet"}


class TestGenerationCharacterItems(SecretAgentClankTestBase):
    """Smoke test: Character Items on, all characters enabled."""
    options = {"skill_points": True, "infobots": "character_unlocks"}


class TestGenerationCharacterDisabled(SecretAgentClankTestBase):
    """Smoke test: an operative disabled entirely via Operatives."""
    options = {
        "skill_points": True,
        "infobots": "character_unlocks",
        "operatives": {"Ratchet": 1, "Clank": 1, "Gadgetbots": 1},  # Qwark omitted -- disabled
    }


class TestGenerationGoalQwarkOpera(SecretAgentClankTestBase):
    """Smoke test: Qwark Opera goal."""
    options = {"goal": "qwark_opera"}


class TestGenerationGoalAny(SecretAgentClankTestBase):
    """Smoke test: Any goal (either victory condition)."""
    options = {"goal": "any"}


class TestGenerationEverythingOn(SecretAgentClankTestBase):
    """Smoke test: every new option combined at once."""
    options = {
        "skill_points": True,
        "infobots": "character_unlocks",
        "goal": "any",
    }


class TestGenerationWithKeycards(SecretAgentClankTestBase):
    """Smoke test: All Keycards on (goal stays default -- Chalice of Power isn't generatable yet, see TestGoalNotYetImplemented)."""
    options = {"all_keycards": True}


class TestGenerationWithAlienCodes(SecretAgentClankTestBase):
    """Smoke test: All Alien Codes on (goal stays default -- Alien Codes isn't generatable yet, see TestGoalNotYetImplemented)."""
    options = {"all_alien_codes": True}


class TestGoalCharacterMismatch(unittest.TestCase):
    """Goal options requiring a disabled character must raise OptionError instead of silently generating an unbeatable seed."""

    def test_defeat_klunk_requires_clank(self):
        with self.assertRaises(OptionError):
            setup_multiworld(SecretAgentClankWorld, options={"goal": "defeat_klunk", "operatives": {"Clank": 0}})

    def test_qwark_opera_requires_qwark(self):
        with self.assertRaises(OptionError):
            setup_multiworld(SecretAgentClankWorld, options={"goal": "qwark_opera", "operatives": {"Qwark": 0}})

    def test_any_requires_clank_or_qwark(self):
        with self.assertRaises(OptionError):
            setup_multiworld(
                SecretAgentClankWorld, options={"goal": "any", "operatives": {"Clank": 0, "Qwark": 0}},
            )

    def test_any_survives_with_only_clank(self):
        # ItemDict (Operatives) doesn't merge with the default -- Qwark
        # must be omitted (not just set to 0) and every operative meant to
        # stay enabled listed explicitly.
        setup_multiworld(
            SecretAgentClankWorld,
            options={"goal": "any", "operatives": {"Ratchet": 1, "Clank": 1, "Gadgetbots": 1}},
        )


class TestCollectibleGoals(unittest.TestCase):
    """Collectible goals do not require optional AP reward locations."""

    def test_chalice_goal_without_keycard_locations(self):
        from ..locations import KEYCARD_LOCATIONS
        mw = setup_multiworld(SecretAgentClankWorld, options={"goal": "chalice_of_power"})
        self.assertFalse(set(KEYCARD_LOCATIONS) & {loc.name for loc in mw.get_locations(1)})

    def test_chalice_goal_generates_with_keycards(self):
        setup_multiworld(SecretAgentClankWorld, options={"goal": "chalice_of_power", "all_keycards": True})

    def test_alien_goal_without_code_locations(self):
        from ..locations import ALIEN_CODE_LOCATIONS
        mw = setup_multiworld(SecretAgentClankWorld, options={"goal": "alien_codes"})
        self.assertFalse(set(ALIEN_CODE_LOCATIONS) & {loc.name for loc in mw.get_locations(1)})

    def test_alien_code_goal_generates_with_all_codes(self):
        setup_multiworld(SecretAgentClankWorld, options={"goal": "alien_codes", "all_alien_codes": True})

    def test_any_survives_with_only_qwark(self):
        setup_multiworld(
            SecretAgentClankWorld,
            options={"goal": "any", "operatives": {"Ratchet": 1, "Qwark": 1, "Gadgetbots": 1}},
        )
