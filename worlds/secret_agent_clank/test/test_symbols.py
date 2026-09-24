import unittest

from ..core.symbols import forbid, require


class RequireForbidTests(unittest.TestCase):
    def setUp(self):
        self.symbols = {"a": 0x100000, "b": 0x100004}

    def test_require_single_returns_the_address(self):
        self.assertEqual(require(self.symbols, "a"), 0x100000)

    def test_require_multiple_returns_a_tuple_in_order(self):
        self.assertEqual(require(self.symbols, "b", "a"), (0x100004, 0x100000))

    def test_require_missing_names_the_export_in_the_error(self):
        with self.assertRaises(ValueError) as ctx:
            require(self.symbols, "a", "missing_one", "b", "missing_two")
        self.assertIn("missing_one", str(ctx.exception))
        self.assertIn("missing_two", str(ctx.exception))
        self.assertNotIn("'a'", str(ctx.exception))

    def test_require_works_with_a_real_runtime_symbols_instance(self):
        from ..core.symbols import RuntimeSymbols
        symbols = RuntimeSymbols(pine=None)
        symbols.values = dict(self.symbols)
        self.assertEqual(require(symbols, "a"), 0x100000)

    def test_forbid_passes_when_none_present(self):
        forbid(self.symbols, "nonexistent")

    def test_forbid_raises_naming_the_present_export(self):
        with self.assertRaises(ValueError) as ctx:
            forbid(self.symbols, "a", "nonexistent")
        self.assertIn("a", str(ctx.exception))
        self.assertNotIn("nonexistent", str(ctx.exception))
