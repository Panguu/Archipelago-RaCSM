import unittest

from test.general import setup_multiworld

from ..constants import (
    PROGRESSIVE_CHALLENGE_MODE,
    PROGRESSIVE_PLANET_ITEM_NAME,
    PROGRESSIVE_TO_UNLOCK,
    PROGRESSIVE_WRENCH,
    SACClankWeapons,
    SACProgressiveClankWeapons,
    SACProgressiveRatchetWeapons,
    SACRatchetWeapons,
)
from ..entities import SACItem, SACProgressiveItem
from ..items import FILLER_ITEM_NAME
from ..world import SecretAgentClankWorld


class TestProgressiveItems(unittest.TestCase):
    def world(self, **options):
        return setup_multiworld(SecretAgentClankWorld, seed=1, options=options).worlds[1]

    def test_weapon_stages_follow_ng_plus(self):
        name = SACProgressiveRatchetWeapons.BLASTER
        for ng_plus, levels in ((0, 4), (1, 8)):
            with self.subTest(ng_plus=ng_plus):
                item = self.world(ng_plus=ng_plus).create_item(name)
                self.assertIsInstance(item, SACProgressiveItem)
                self.assertEqual(item.stages[0], SACRatchetWeapons.BLASTER)
                self.assertEqual(len(item.stages), levels)
                self.assertEqual(item.stages[:2], (SACRatchetWeapons.BLASTER, f"{SACRatchetWeapons.BLASTER} V2"))

    def test_planet_stages_are_the_seeds_case_order(self):
        world = self.world(infobots="progressive_planet")
        for planet, cases in world.planet_cases.items():
            with self.subTest(planet=planet):
                self.assertEqual(world.create_item(PROGRESSIVE_PLANET_ITEM_NAME[planet]).stages, tuple(cases))

    def test_wrench_and_challenge_mode(self):
        world = self.world(ng_plus=2)
        self.assertEqual(len(world.create_item(PROGRESSIVE_WRENCH).stages), 5)
        self.assertEqual(world.create_item(PROGRESSIVE_CHALLENGE_MODE).stages, ("Challenge Mode 1", "Challenge Mode 2"))

    def test_only_enabled_progressive_items_are_generated(self):
        off = dict(progressive_weapons="off", progressive_wrench="off", progressive_challenge_mode=False,
                   infobots="cases", ng_plus=1)
        cases = (
            ("all off", {}, set()),
            # ng_plus 0 keeps weapons at 4 copies each, so the pool still fits.
            ("weapons", {"progressive_weapons": "manual", "ng_plus": 0}, set(PROGRESSIVE_TO_UNLOCK)),
            ("wrench", {"progressive_wrench": "all_progressive"}, {PROGRESSIVE_WRENCH}),
            ("challenge mode", {"progressive_challenge_mode": True}, {PROGRESSIVE_CHALLENGE_MODE}),
            ("planets", {"infobots": "progressive_planet"}, set(PROGRESSIVE_PLANET_ITEM_NAME.values())),
        )
        for label, enabled, allowed in cases:
            with self.subTest(label):
                multiworld = setup_multiworld(SecretAgentClankWorld, seed=1, options={**off, **enabled})
                items = [*multiworld.itempool, *multiworld.precollected_items[1]]
                progressive = {item.name for item in items if isinstance(item, SACProgressiveItem)}
                self.assertLessEqual(progressive, allowed)
                self.assertEqual(bool(progressive), bool(allowed))

    def test_weapon_hint_group_has_every_form(self):
        self.assertEqual(SecretAgentClankWorld.item_name_groups["Cufflink Bomb"], {
            SACClankWeapons.CUFFLINK, SACProgressiveClankWeapons.CUFFLINK, "Titan Upgrade: Proto Wrist Mortar (Clank)"})
        self.assertEqual(SecretAgentClankWorld.item_name_groups["RYNO"], {
            SACRatchetWeapons.RYNO, SACProgressiveRatchetWeapons.RYNO})  # RYNO has no Titan tier

    def test_weapon_hint_group_finds_whichever_version_is_in_the_seed(self):
        group = SecretAgentClankWorld.item_name_groups["Cufflink Bomb"]
        for setting, expected in (("off", SACClankWeapons.CUFFLINK), ("manual", SACProgressiveClankWeapons.CUFFLINK)):
            with self.subTest(progressive_weapons=setting):
                multiworld = setup_multiworld(SecretAgentClankWorld, seed=1,
                                              options={"progressive_weapons": setting, "ng_plus": 0})
                names = {item.name for item in [*multiworld.itempool, *multiworld.precollected_items[1]]}
                self.assertEqual(group & names, {expected})

    def test_other_items_stay_plain(self):
        item = self.world().create_item(FILLER_ITEM_NAME)
        self.assertIs(type(item), SACItem)
