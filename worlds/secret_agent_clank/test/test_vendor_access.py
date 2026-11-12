import unittest
from unittest.mock import patch

from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from rule_builder.rules import False_, Has, True_
from test.general import gen_steps, setup_multiworld
from worlds.AutoWorld import call_all

from ..constants import (
    ALL_CASES,
    CASE_NAME_TO_CASE,
    CASE_NAME_TO_INFOBOT,
    NG_PLUS_VENDOR_ITEMS,
    TITAN_LOCATIONS,
    VENDOR_CASES,
    VENDOR_MODS,
    VENDOR_REQUIREMENT_ITEMS,
    Case,
    SACCases,
    SACClankGadgets,
    SACClankWeapons,
    SACProgressiveClankWeapons,
    SACPickups,
    SACRatchetWeapons,
    vendor_location_name,
    vendor_unlocked_cases,
)
from ..core.inventories import resolve_owned_cases
from ..rules import vendor_access
from ..world import SecretAgentClankWorld


def pick_starting_cases(world, prefer):
    """Patch the world's random.choice so starting-case picks follow `prefer` (case name -> bool)."""
    choose = world.random.choice

    def choice(seq):
        if seq and all(isinstance(item, tuple) and all(isinstance(case, Case) for case in item) for item in seq):
            return max(seq, key=lambda pair: sum(prefer(case.name) for case in pair))
        return choose(seq)
    return patch.object(world.random, "choice", side_effect=choice)


def setup_vendor_world(world_type, options=None):
    m = setup_multiworld(world_type, steps=("generate_early", "create_regions"), options={
        "starting_weapons": 0, "starting_gadgets": 0, **(options or {})})
    with pick_starting_cases(m.worlds[1], lambda name: name in (SACCases.BOLTAIRE_MUSEUM, SACCases.KLUNKS_LAIR)):
        for step in gen_steps[2:]:
            call_all(m, step)
    return m


class VendorAccessTests(unittest.TestCase):
    def test_ratchet_vendor_stock_requires_pda_and_has_reachable_stock(self):
        for mode in ("cases", "progressive_planet"):
            with self.subTest(mode=mode):
                m = setup_multiworld(SecretAgentClankWorld, seed=12345, options={
                    'operatives': {'Ratchet': 1}, 'goal': 'ratchet_prison_escape',
                    'nanotech_checks': False, 'infobots': mode, 'ng_plus': 1})
                world = m.worlds[1]
                self.assertTrue(world.has_vendor)
                locations = [loc for loc in m.get_locations(1) if loc.name in VENDOR_CASES]
                self.assertTrue(locations)
                state = m.get_all_state(False)
                for location in locations:
                    self.assertTrue(location.can_reach(state), location.name)
                while state.has(SACRatchetWeapons.RATCHETPDA, 1):
                    state.remove(world.create_item(SACRatchetWeapons.RATCHETPDA))
                ratchet_stock = [location for location in locations
                                 if CASE_NAME_TO_CASE[VENDOR_CASES[location.name]].operative == "Ratchet"]
                self.assertTrue(ratchet_stock)
                for location in ratchet_stock:
                    self.assertFalse(location.can_reach(state), location.name)
                distribute_items_restrictive(m)
                self.assertTrue(m.fulfills_accessibility())

    def test_seed_options_filter_shared_catalog(self):
        for ng_plus in (0, 1, 2):
            for operatives in ({"Clank": 1}, {"Clank": 1, "Ratchet": 1}):
                with self.subTest(ng_plus=ng_plus, operatives=operatives):
                    m = setup_vendor_world(SecretAgentClankWorld, options={
                        "ng_plus": ng_plus, "operatives": operatives})
                    names = {loc.name for loc in m.get_locations(1) if loc.name in VENDOR_CASES}
                    for name in NG_PLUS_VENDOR_ITEMS:
                        enabled = bool(ng_plus) and (name.endswith("(Clank)") or "Ratchet" in operatives)
                        self.assertEqual(vendor_location_name(name) in names, enabled, name)
                    if "Ratchet" not in operatives:
                        self.assertFalse(any("(Ratchet)" in name for name in names))
                    for mod in VENDOR_MODS:
                        enabled = bool(ng_plus) if mod.ng_plus else "Ratchet" in operatives
                        self.assertEqual(mod.location in names, enabled, mod.location)
                    self.assertEqual(len(m.itempool), len(m.get_unfilled_locations(1)))

    def test_titan_requires_its_source_case_vendor(self):
        requirements = {name: False_() for name in vendor_access.VENDOR_REQUIREMENTS}
        requirements[SACCases.ASYANICA_ROOFTOPS] = True_()
        requirements[SACCases.BOLTAIRE_MUSEUM] = Has(SACClankGadgets.JETBOOTS)
        with patch.dict(vendor_access.VENDOR_REQUIREMENTS, requirements, clear=True):
            m = setup_vendor_world(SecretAgentClankWorld, options={"ng_plus": 1})
        world = m.worlds[1]
        state = CollectionState(m)
        titan = m.get_location(TITAN_LOCATIONS["blaster"], 1)
        state.collect(world.create_item(CASE_NAME_TO_INFOBOT[SACCases.ASYANICA_ROOFTOPS]))
        self.assertFalse(titan.can_reach(state))
        state.collect(world.create_item(SACClankGadgets.JETBOOTS))
        self.assertTrue(titan.can_reach(state))
        self.assertFalse(m.get_location(SACPickups.BOLTAIRE_MUSEUM_DUAL_LACERATORS, 1).can_reach(state))
        self.assertFalse(state.has(SACRatchetWeapons.BLASTER, 1))

    def test_normal_vendor_check_inherits_shared_item_gate(self):
        requirements = {name: False_() for name in vendor_access.VENDOR_REQUIREMENTS}
        requirements[SACCases.BOLTAIRE_MUSEUM] = Has(SACClankGadgets.JETBOOTS)
        with patch.dict(vendor_access.VENDOR_REQUIREMENTS, requirements, clear=True):
            m = setup_vendor_world(SecretAgentClankWorld)
        state = CollectionState(m)
        location = m.get_location(vendor_location_name(SACClankWeapons.HOLOKNUCKLES), 1)
        self.assertFalse(location.can_reach(state))
        state.collect(m.worlds[1].create_item(SACClankGadgets.JETBOOTS))
        self.assertTrue(location.can_reach(state))

    def test_purchase_types_require_their_specific_case(self):
        requirements = {name: False_() for name in vendor_access.VENDOR_REQUIREMENTS}
        requirements[SACCases.ASYANICA_ROOFTOPS] = Has(SACClankGadgets.JETBOOTS)
        requirements[SACCases.GALACTIC_BOLT_RESERVE] = True_()
        requirements[SACCases.AZCOTAL_ALLEY] = True_()
        with patch.dict(vendor_access.VENDOR_REQUIREMENTS, requirements, clear=True):
            m = setup_vendor_world(SecretAgentClankWorld, options={"ng_plus": 1})
        world = m.worlds[1]
        state = CollectionState(m)
        names = (vendor_location_name(SACRatchetWeapons.SHOCKROCKET),
                 vendor_location_name(SACClankGadgets.BOLTGRABBER),
                 vendor_location_name(SACClankGadgets.CLANKPDA), TITAN_LOCATIONS["shockrocket"], VENDOR_MODS[0].location)
        for name in names:
            self.assertEqual(m.get_location(name, 1).parent_region.name, VENDOR_CASES[name])
            self.assertFalse(m.get_location(name, 1).can_reach(state))
        state.collect(world.create_item(CASE_NAME_TO_INFOBOT[SACCases.ASYANICA_ROOFTOPS]))
        state.collect(world.create_item(SACClankGadgets.JETBOOTS))
        self.assertTrue(m.get_location(VENDOR_MODS[0].location, 1).can_reach(state))
        for name in names[:-1]:
            self.assertFalse(m.get_location(name, 1).can_reach(state), name)
        state.collect(world.create_item(SACCases.GALACTIC_BOLT_RESERVE))
        for name in (names[0], names[1], names[3]):
            self.assertTrue(m.get_location(name, 1).can_reach(state), name)
        self.assertFalse(m.get_location(names[2], 1).can_reach(state))
        state.collect(world.create_item(SACCases.AZCOTAL_ALLEY))
        self.assertTrue(m.get_location(names[2], 1).can_reach(state))
        self.assertFalse(state.has(SACRatchetWeapons.SHOCKROCKET, 1))
        self.assertFalse(state.has(CASE_NAME_TO_INFOBOT[SACCases.INSIDE_THE_A_EYE], 1))

    def test_all_catalog_gates_match_client_case_ownership_in_every_access_mode(self):
        for mode in ("cases", "progressive_planet"):
            m = setup_multiworld(SecretAgentClankWorld, seed=12345,
                                 options={"ng_plus": 1, "infobots": mode})
            world = m.worlds[1]
            locations = [loc for loc in m.get_locations(1) if loc.name in VENDOR_CASES]
            self.assertEqual({loc.name for loc in locations}, set(VENDOR_CASES))
            self.assertTrue(all("(Clank)" in case or "(Ratchet)" in case
                                for case in VENDOR_CASES.values()))
            for loc in locations:
                world.set_rule(loc, vendor_access.CaseOwnershipRule(VENDOR_CASES[loc.name]))
            state = CollectionState(m)
            received = [item.name for item in m.precollected_items[1]]
            items = [item for item in m.itempool if item.name.startswith("Case File")
                     or item.name.startswith("Progressive")]
            for item in [None, *items]:
                if item is not None:
                    state.collect(item)
                    received.append(item.name)
                owned = resolve_owned_cases(received, planet_cases=world.planet_cases)
                for loc in locations:
                    self.assertEqual(loc.access_rule(state), VENDOR_CASES[loc.name] in owned,
                                     (mode, loc.name, received))

    def test_every_purchase_needs_enemy_access(self):
        with patch.object(vendor_access, "HasEnemyAccess", False_):
            m = setup_vendor_world(SecretAgentClankWorld, options={"ng_plus": 1})
        state = m.get_all_state(False)
        locations = [loc for loc in m.get_locations(1) if loc.name in VENDOR_CASES]
        self.assertTrue(locations)
        for location in locations:
            self.assertFalse(location.can_reach(state), location.name)

    def test_client_vendor_table_matches_generation_requirements(self):
        for case in ALL_CASES:
            has_vendor = not isinstance(vendor_access.VENDOR_REQUIREMENTS[case.name], False_)
            self.assertEqual(case.name in VENDOR_REQUIREMENT_ITEMS, has_vendor, case.name)
        self.assertTrue(set(VENDOR_CASES.values()) <= set(VENDOR_REQUIREMENT_ITEMS))
        owned = {SACCases.HIGH_ROLLERS_CASINO, SACCases.BOLTAIRE_GEM_WING, SACCases.ASYANICA_ROOFTOPS}
        self.assertEqual(vendor_unlocked_cases(owned, [SACClankGadgets.HOLOMONOCLE]),
                         {SACCases.ASYANICA_ROOFTOPS})
        self.assertEqual(vendor_unlocked_cases(owned, [SACClankGadgets.HOLOMONOCLE, SACClankWeapons.CUFFLINK]),
                         {SACCases.ASYANICA_ROOFTOPS, SACCases.HIGH_ROLLERS_CASINO})

    def test_casino_vendor_accepts_progressive_cufflink_unlock(self):
        owned = {SACCases.HIGH_ROLLERS_CASINO}
        progressive = SACProgressiveClankWeapons.CUFFLINK
        self.assertEqual(vendor_unlocked_cases(owned, [progressive]), set())
        self.assertEqual(vendor_unlocked_cases(owned, [SACClankGadgets.HOLOMONOCLE]), set())
        self.assertEqual(vendor_unlocked_cases(set(), [SACClankGadgets.HOLOMONOCLE, progressive]), set())
        for count in (1, 4, 8):
            self.assertEqual(vendor_unlocked_cases(
                owned, [SACClankGadgets.HOLOMONOCLE] + [progressive] * count), owned)

    def test_reported_four_checks_reachable_with_all_items(self):
        m = setup_vendor_world(SecretAgentClankWorld, options={"ng_plus": 1})
        state = m.get_all_state(False)
        for name in (vendor_location_name(SACClankGadgets.CLANKPDA),
                     vendor_location_name(SACRatchetWeapons.SHOCKROCKET),
                     vendor_location_name(SACClankGadgets.BOLTGRABBER), TITAN_LOCATIONS["shockrocket"]):
            self.assertTrue(m.get_location(name, 1).can_reach(state), name)
        self.assertEqual(len(m.itempool), len(m.get_unfilled_locations(1)))
