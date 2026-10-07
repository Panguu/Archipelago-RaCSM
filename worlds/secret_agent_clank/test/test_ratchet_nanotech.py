import unittest
from pathlib import Path

from ..core.ratchet_nanotech import read_ratchet_nanotech
from ..core.symbols import RuntimeSymbols
from .test_runtime import Memory
from ..core.patches.progression import Progression


class RatchetNanotechTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).parents[1] / '.research/prison_skin_live.bin'
        if not path.exists():
            self.skipTest('Local Ratchet capture unavailable')
        self.p = Memory()
        self.p.data[:] = path.read_bytes()
        self.symbols = RuntimeSymbols.parse(self.p.data[:0x1000000], 0)
        self.save = self.p.read_int32(self.symbols['pGV'])

    def test_capture_is_read_only_and_separates_hud_from_xp(self):
        before = bytes(self.p.data)
        data = read_ratchet_nanotech(self.p, self.symbols)
        self.assertEqual((data['saved_xp'], data['xp_nanotech'], data['hud_max']), (0, 20, 20.0))
        self.assertEqual((data['ng_cap'], data['ng_plus_cap']), (60, 90))
        self.assertEqual(self.p.data, before)

    def test_thresholds_and_caps_ignore_clank_xp(self):
        for ng, xp, expected in ((0, 699, 20), (0, 700, 21), (0, 2000, 22),
                                  (0, 333600, 60), (1, 333600, 90), (2, 333600, 90)):
            with self.subTest(ng=ng, xp=xp):
                self.p.write_int32(self.save + 0xED4, ng)
                self.p.write_int32(self.save + 0x198FC, xp)
                self.p.write_int32(self.save + 0x19930, 469200)
                self.assertEqual(read_ratchet_nanotech(self.p, self.symbols)['xp_nanotech'], expected)

    def test_loading_rejected(self):
        self.p.write_int32(0x206324, 3)
        with self.assertRaisesRegex(ValueError, 'loading'):
            read_ratchet_nanotech(self.p, self.symbols)

    def test_location_reporting_uses_ratchet_xp_and_current_challenge_cap(self):
        progression = Progression(self.p)
        progression.configure({'ratchet_nanotech_checks': True, 'ng_plus': 1,
                               'progressive_challenge_mode': True})
        progression.ng_address = self.save + 0xED4
        self.p.write_int32(self.save + 0x198FC, 333600)
        self.p.write_int32(self.save + 0xED4, 1)
        self.assertEqual(len(progression.ratchet_nanotech_checks(self.symbols)), 40)
        from ..constants.challenge_mode import PROGRESSIVE_CHALLENGE_MODE
        progression.receive([PROGRESSIVE_CHALLENGE_MODE])
        self.assertEqual(len(progression.ratchet_nanotech_checks(self.symbols)), 70)
        self.p.write_int32(self.save + 0x198FC, 700)
        self.p.write_int32(self.save + 0x19930, 469200)
        self.assertEqual(progression.ratchet_nanotech_checks(self.symbols), ('Ratchet Nanotech Level 21',))
        self.p.write_int32(0x206324, 3)
        self.assertEqual(progression.ratchet_nanotech_checks(self.symbols), ())
        progression.configure({})
        self.assertEqual(progression.ratchet_nanotech_checks(self.symbols), ())

    def test_changed_table_rejected(self):
        self.p.write_int32(self.symbols['g_LevelProgressionExperienceData_Ratchet'] + 8, 99)
        with self.assertRaisesRegex(ValueError, 'table changed'):
            read_ratchet_nanotech(self.p, self.symbols)


class RatchetNanotechGenerationTests(unittest.TestCase):
    def test_option_caps_tracker_and_disabled_operative(self):
        from test.general import setup_multiworld
        from ..world import SecretAgentClankWorld
        from ..universal_tracker import setup_options_from_slot_data
        for ng, enabled, operatives, expected in (
                (0, True, {'Ratchet': 1}, 40), (1, True, {'Ratchet': 1}, 70),
                (2, True, {'Ratchet': 1}, 70), (0, False, {'Ratchet': 1}, 0),
                (0, True, {'Clank': 1}, 0)):
            with self.subTest(ng=ng, enabled=enabled, operatives=operatives):
                mw = setup_multiworld(SecretAgentClankWorld, options={
                    'ng_plus': ng, 'ratchet_nanotech_checks': enabled, 'operatives': operatives,
                    'goal': 'ratchet_prison_escape' if 'Ratchet' in operatives else 'defeat_klunk'})
                locations = [loc for loc in mw.get_locations(1) if loc.name.startswith('Ratchet Nanotech Level')]
                self.assertEqual(len(locations), expected)
                state = mw.get_all_state(False)
                self.assertTrue(all(loc.can_reach(state) for loc in locations))
                world = mw.worlds[1]
                slot = world.fill_slot_data()
                mw.re_gen_passthrough = {world.game: slot}
                world.options.ratchet_nanotech_checks.value = 0
                setup_options_from_slot_data(world)
                self.assertEqual(bool(world.options.ratchet_nanotech_checks), enabled)

    def test_challenge_checks_require_challenge_item(self):
        from test.general import setup_multiworld
        from ..world import SecretAgentClankWorld
        from ..constants.challenge_mode import PROGRESSIVE_CHALLENGE_MODE
        mw = setup_multiworld(SecretAgentClankWorld, options={
            'ratchet_nanotech_checks': True, 'ng_plus': 1, 'progressive_challenge_mode': True})
        state = mw.get_all_state(False)
        state.remove(mw.worlds[1].create_item(PROGRESSIVE_CHALLENGE_MODE))
        self.assertTrue(mw.get_location('Ratchet Nanotech Level 60', 1).can_reach(state))
        self.assertFalse(mw.get_location('Ratchet Nanotech Level 61', 1).can_reach(state))
