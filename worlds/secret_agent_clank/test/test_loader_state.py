import unittest
from unittest.mock import Mock
from ..core.patches.loader_state import LoaderStateReader
from .test_runtime import Memory


class LoaderSamplingTests(unittest.TestCase):
    def setUp(self):
        self.p = Memory()
        self.startup_barrier = LoaderStateReader(self.p)
        self.startup_barrier.attached = True
        self.startup_barrier.validate = Mock()

    def test_only_completed_state_four_is_held(self):
        self.p.write_int32(LoaderStateReader.TARGET, 1)
        self.p.write_int32(LoaderStateReader.HANDLE, 0x200000)
        for state, status, expected in ((5, 1, None), (4, 0xFFFFFFFF, None), (4, 1, 1)):
            self.p.write_int32(LoaderStateReader.STATE, state)
            self.p.write_int32(LoaderStateReader.STATUS, status)
            self.assertEqual(self.startup_barrier.held_module(), expected)

    def test_settled_module_requires_same_target_and_handle_on_two_polls(self):
        self.p.batch_write_int32([(LoaderStateReader.STATE, 4), (LoaderStateReader.STATUS, 1),
                                 (LoaderStateReader.TARGET, 1), (LoaderStateReader.HANDLE, 0x200000)])
        self.assertIsNone(self.startup_barrier.held_module(settled=True))
        self.p.write_int32(LoaderStateReader.HANDLE, 0x210000)
        self.assertIsNone(self.startup_barrier.held_module(settled=True))
        self.assertEqual(self.startup_barrier.held_module(settled=True), 1)
        self.p.write_int32(LoaderStateReader.TARGET, 2)
        self.assertIsNone(self.startup_barrier.held_module(settled=True))
        self.assertEqual(self.startup_barrier.held_module(settled=True), 2)

    def test_target_or_handle_changing_between_reads_is_not_held(self):
        for after in ([4, 1, 2, 0x200000], [4, 1, 1, 0x210000]):
            self.p.batch_read_int32 = Mock(side_effect=[[4, 1, 1, 0x200000], after])
            self.assertIsNone(self.startup_barrier.held_module())

    def test_recheck_rejects_same_module_replaced_after_settling(self):
        self.p.batch_write_int32([(LoaderStateReader.STATE, 4), (LoaderStateReader.STATUS, 1),
                                 (LoaderStateReader.TARGET, 1), (LoaderStateReader.HANDLE, 0x200000)])
        self.assertIsNone(self.startup_barrier.held_module(settled=True))
        self.assertEqual(self.startup_barrier.held_module(settled=True), 1)
        self.p.write_int32(LoaderStateReader.HANDLE, 0x210000)
        self.assertIsNone(self.startup_barrier.held_module())

    def test_leaving_held_state_restarts_settling(self):
        self.p.batch_write_int32([(LoaderStateReader.STATE, 4), (LoaderStateReader.STATUS, 1),
                                 (LoaderStateReader.TARGET, 1), (LoaderStateReader.HANDLE, 0x200000)])
        self.assertIsNone(self.startup_barrier.held_module(settled=True))
        self.p.write_int32(LoaderStateReader.STATUS, 0)
        self.assertIsNone(self.startup_barrier.held_module(settled=True))
        self.p.write_int32(LoaderStateReader.STATUS, 1)
        self.assertIsNone(self.startup_barrier.held_module(settled=True))
        self.assertEqual(self.startup_barrier.held_module(settled=True), 1)
