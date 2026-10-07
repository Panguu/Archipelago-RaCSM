import unittest

from Options import OptionError
from test.general import setup_multiworld

from ..locations import ALIEN_CODE_LOCATIONS, KEYCARD_LOCATIONS
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
    """Smoke test: many options combined."""
    options = {
        "skill_points": True,
        "infobots": "character_unlocks",
        "goal": "any",
    }


class TestGenerationWithKeycards(SecretAgentClankTestBase):
    """Smoke test: combined collectible checks on."""
    options = {"keycards_and_alien_codes": True}


class TestCombinedCollectibles(unittest.TestCase):
    def test_toggle_controls_both_categories_and_tracker_preserves_legacy_seeds(self):
        from ..options import SecretAgentClankOptions
        from ..universal_tracker import setup_options_from_slot_data
        self.assertNotIn('all_keycards', SecretAgentClankOptions.type_hints)
        self.assertNotIn('all_alien_codes', SecretAgentClankOptions.type_hints)
        for enabled in (False, True):
            mw = setup_multiworld(SecretAgentClankWorld, options={'keycards_and_alien_codes': enabled})
            names = {loc.name for loc in mw.get_locations(1)}
            for category in (KEYCARD_LOCATIONS, ALIEN_CODE_LOCATIONS):
                self.assertEqual(set(category) & names, set(category) if enabled else set())
            world = mw.worlds[1]
            slot = world.fill_slot_data()
            self.assertEqual(slot['keycards_and_alien_codes'], enabled)
            mw.re_gen_passthrough = {world.game: slot}
            setup_options_from_slot_data(world)
            self.assertEqual(world.options.keycard_checks_enabled, enabled)
            self.assertEqual(world.options.alien_code_checks_enabled, enabled)
            del slot['keycards_and_alien_codes']
            for cards, codes in ((True, False), (False, True)):
                slot.update(all_keycards=cards, all_alien_codes=codes)
                setup_options_from_slot_data(world)
                for category, expected in ((KEYCARD_LOCATIONS, cards), (ALIEN_CODE_LOCATIONS, codes)):
                    self.assertTrue(all(loc.available(world.options) == expected for loc in category.values()))


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
        # Operatives replaces the default, so list every operative that stays enabled.
        setup_multiworld(
            SecretAgentClankWorld,
            options={"goal": "any", "operatives": {"Ratchet": 1, "Clank": 1, "Gadgetbots": 1}},
        )


class TestCollectibleGoals(unittest.TestCase):
    """Collectible goals do not require optional AP reward locations."""

    def test_chalice_goal_without_keycard_locations(self):
        mw = setup_multiworld(SecretAgentClankWorld, options={"goal": "chalice_of_power"})
        self.assertFalse(set(KEYCARD_LOCATIONS) & {loc.name for loc in mw.get_locations(1)})

    def test_chalice_goal_generates_with_keycards(self):
        setup_multiworld(SecretAgentClankWorld, options={"goal": "chalice_of_power", "keycards_and_alien_codes": True})

    def test_alien_goal_without_code_locations(self):
        mw = setup_multiworld(SecretAgentClankWorld, options={"goal": "alien_codes"})
        self.assertFalse(set(ALIEN_CODE_LOCATIONS) & {loc.name for loc in mw.get_locations(1)})

    def test_alien_code_goal_generates_with_all_codes(self):
        setup_multiworld(SecretAgentClankWorld, options={"goal": "alien_codes", "keycards_and_alien_codes": True})

    def test_any_survives_with_only_qwark(self):
        setup_multiworld(
            SecretAgentClankWorld,
            options={"goal": "any", "operatives": {"Ratchet": 1, "Qwark": 1, "Gadgetbots": 1}},
        )
