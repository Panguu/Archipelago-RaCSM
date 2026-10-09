"""Persistent Alien Code bits, independently read from native save flags."""
from ...constants.alien_codes import ALIEN_CODES_BY_MODULE
from ..global_flags import GlobalFlags, module_bit, read_module_counts

_TOTAL = sum(map(len, ALIEN_CODES_BY_MODULE.values()))


class AlienCodeInventory:
    def __init__(self, pine):
        self.pine = pine
        self.flags = GlobalFlags(pine)
        self.reported = set()
        self.valid = False
        self.found = set()

    def bind(self, symbols, *, flag_pointer_address=None):
        self.valid = False
        # Keycard Hunt validates the getter before replacing its Treehouse entry.
        if flag_pointer_address is not None:
            self.flags.pointer_address = flag_pointer_address
        elif not self.flags.bind(symbols):
            return False
        get_count = symbols.get("GLOBALVARS_GetTotalAlienCodeCount__FUi")
        if get_count is None:
            return False
        expected = {module: len(names) for module, names in ALIEN_CODES_BY_MODULE.items()}
        if read_module_counts(self.pine, get_count) != expected:
            return False
        self.valid = True
        return True

    def sync(self):
        # Do not baseline away a collection completed during level startup.
        pass

    def sync_from_ap(self, checked):
        self.reported.update(checked)

    def check(self):
        if not self.valid:
            return []
        data = self.flags.read(0x38, 15)
        if data is None:
            return []
        self.found = {name for module, names in ALIEN_CODES_BY_MODULE.items()
                      for bit, name in enumerate(names) if module_bit(data, module, bit)}
        return sorted(self.found - self.reported)

    def confirm(self, name: str) -> None:
        """Stop reporting `name`; call only once AP has accepted the check."""
        self.reported.add(name)

    @property
    def all_found(self):
        return self.valid and len(self.found) == _TOTAL
