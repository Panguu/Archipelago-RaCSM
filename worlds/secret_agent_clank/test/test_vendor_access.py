import unittest
from unittest.mock import patch

from BaseClasses import CollectionState
from rule_builder.rules import False_, Has
from test.general import gen_steps, setup_multiworld
from worlds.AutoWorld import call_all

from ..constants import CASE_NAME_TO_INFOBOT
from ..constants.clank_gadgets import SACClankGadgets, SACClankWeapons
from ..constants.planets import ALL_CASES, SACCases
from ..constants.weapon_progression import TITAN_LOCATIONS
from ..constants.weapons import SACRatchetWeapons
from ..rules import vendor_access
from ..world import SecretAgentClankWorld


def setup_vendor_world(world_type, options=None):
    # Pin Museum for these vendor-route tests; production starts are random.
    m = setup_multiworld(world_type, steps=("generate_early", "create_regions"), options={
        "starting_weapons": 0, "starting_gadgets": 0, **(options or {})})
    museum = next(case for case in ALL_CASES if case.name == SACCases.BOLTAIRE_MUSEUM)
    with patch.object(m.worlds[1].random, "choice", return_value=museum):
        for step in gen_steps[2:]:
            call_all(m, step)
    return m


class VendorAccessTests(unittest.TestCase):
    def test_titan_requires_original_check_and_vendor_case_and_items(self):
        requirements = {name: False_() for name in vendor_access.VENDOR_REQUIREMENTS}
        requirements[SACCases.ASYANICA_ROOFTOPS] = Has(SACClankGadgets.JETBOOTS)
        with patch.dict(vendor_access.VENDOR_REQUIREMENTS, requirements, clear=True):
            m = setup_vendor_world(SecretAgentClankWorld, options={"ng_plus": 1})
        world = m.worlds[1]
        state = CollectionState(m)
        titan = m.get_location(TITAN_LOCATIONS["blaster"], 1)
        original = m.get_location(SACRatchetWeapons.BLASTER, 1)
        self.assertFalse(titan.can_reach(state))
        state.collect(world.create_item(CASE_NAME_TO_INFOBOT[SACCases.ASYANICA_ROOFTOPS]))
        state.collect(world.create_item(SACClankGadgets.JETBOOTS))
        self.assertFalse(original.can_reach(state))
        self.assertFalse(titan.can_reach(state))
        state.collect(world.create_item(SACClankGadgets.BLACK_OUT_PEN))
        self.assertTrue(original.can_reach(state))
        self.assertTrue(titan.can_reach(state))
        self.assertFalse(state.has(SACRatchetWeapons.BLASTER, 1))

    def test_normal_vendor_check_inherits_shared_item_gate(self):
        requirements = {name: False_() for name in vendor_access.VENDOR_REQUIREMENTS}
        requirements[SACCases.BOLTAIRE_MUSEUM] = Has(SACClankGadgets.JETBOOTS)
        with patch.dict(vendor_access.VENDOR_REQUIREMENTS, requirements, clear=True):
            m = setup_vendor_world(SecretAgentClankWorld)
        state = CollectionState(m)
        location = m.get_location(SACClankWeapons.HOLOKNUCKLES, 1)
        self.assertFalse(location.can_reach(state))
        state.collect(m.worlds[1].create_item(SACClankGadgets.JETBOOTS))
        self.assertTrue(location.can_reach(state))

    def test_offer_case_and_vendor_route_are_independent(self):
        requirements = {name: False_() for name in vendor_access.VENDOR_REQUIREMENTS}
        requirements[SACCases.ASYANICA_ROOFTOPS] = Has(SACClankGadgets.JETBOOTS)
        with patch.dict(vendor_access.VENDOR_REQUIREMENTS, requirements, clear=True):
            m = setup_vendor_world(SecretAgentClankWorld, options={"ng_plus": 1})
        world = m.worlds[1]
        names = (SACRatchetWeapons.SHOCKROCKET, SACClankGadgets.BOLTGRABBER,
                 TITAN_LOCATIONS["shockrocket"])
        for vendor_first in (False, True):
            state = CollectionState(m)
            def collect_case(case):
                state.collect(world.create_item(CASE_NAME_TO_INFOBOT[case]))
            if vendor_first:
                collect_case(SACCases.ASYANICA_ROOFTOPS)
                state.collect(world.create_item(SACClankGadgets.JETBOOTS))
            else:
                collect_case(SACCases.INSIDE_THE_A_EYE)
            for name in names:
                self.assertFalse(m.get_location(name, 1).can_reach(state))
            if vendor_first:
                collect_case(SACCases.INSIDE_THE_A_EYE)
            else:
                collect_case(SACCases.ASYANICA_ROOFTOPS)
                for name in names:
                    self.assertFalse(m.get_location(name, 1).can_reach(state))
                state.collect(world.create_item(SACClankGadgets.JETBOOTS))
            for name in names:
                self.assertTrue(m.get_location(name, 1).can_reach(state))
            self.assertFalse(state.has(SACRatchetWeapons.SHOCKROCKET, 1))

    def test_reported_four_checks_reachable_with_all_items(self):
        m = setup_vendor_world(SecretAgentClankWorld, options={"ng_plus": 1})
        state = m.get_all_state(False)
        for name in (SACClankGadgets.CLANKPDA, SACRatchetWeapons.SHOCKROCKET,
                     SACClankGadgets.BOLTGRABBER, TITAN_LOCATIONS["shockrocket"]):
            self.assertTrue(m.get_location(name, 1).can_reach(state), name)
        self.assertEqual(len(m.itempool), len(m.get_unfilled_locations(1)))
