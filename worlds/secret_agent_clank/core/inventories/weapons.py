from ...constants import WEAPON_ORDER
from ...pypine import Pine


WEAPON_STRUCT_SIZE: int = 0x74

_OFFSET_NAME_PTR     = 0x00
_OFFSET_CATEGORY     = 0x04
_OFFSET_CURRENT_AMMO = 0x60
_OFFSET_OWNED_FLAG   = 0x70

_OFFSET_MOD_SLOTS = 0x68
MOD_SLOT_COUNT    = 3


class WeaponAddresses:
    def __init__(self, base: int, pine: Pine) -> None:
        self.base = base
        self.pine = pine

    def __repr__(self) -> str:
        return f"WeaponAddresses(base=0x{self.base:X})"


def build_weapons(array_base: int | None, pine: Pine) -> dict[str, WeaponAddresses]:
    if array_base is None:
        return {}
    weapons: dict[str, WeaponAddresses] = {}
    for i, name in enumerate(WEAPON_ORDER):
        if name is not None:
            weapons[name] = WeaponAddresses(array_base + i * WEAPON_STRUCT_SIZE, pine)
    return weapons


class WeaponInventory:
    """Owned flags for the GadgetData array, with the same interface as ItemInventory."""

    def __init__(self, pine: Pine) -> None:
        self.pine = pine
        self.weapons: dict[str, WeaponAddresses] = {}
        self._raw_owned: dict[str, int] = {}

    def set_base(self, array_base: int | None) -> None:
        """Rebind to a newly loaded array, or unbind when array_base is None."""
        self.weapons = build_weapons(array_base, self.pine)
        self._raw_owned = dict.fromkeys(self.weapons, 0)

    def strip_all(self) -> None:
        if not self.weapons:
            return
        ops = [(w.base + _OFFSET_OWNED_FLAG, 0) for w in self.weapons.values()]
        self.pine.batch_write_int32(ops)
        self._raw_owned = dict.fromkeys(self.weapons, 0)

    def apply_all(self, ap_owned: dict[str, bool]) -> None:
        if not self.weapons:
            return
        ops = [
            (w.base + _OFFSET_OWNED_FLAG, 1 if ap_owned.get(name, False) else 0)
            for name, w in self.weapons.items() if name in ap_owned
        ]
        self.pine.batch_write_int32(ops)
        self._raw_owned.update({name: int(bool(value)) for name, value in ap_owned.items() if name in self.weapons})

    def sync(self) -> None:
        """Baseline a newly bound table without inventing pickup events."""
        if self.weapons:
            values = self.pine.batch_read_int32([w.base + _OFFSET_OWNED_FLAG for w in self.weapons.values()])
            self._raw_owned = {name: int(bool(value)) for name, value in zip(self.weapons, values)}

    def check(self) -> list[str]:
        if not self.weapons:
            return []
        names = list(self.weapons)
        addrs = [self.weapons[name].base + _OFFSET_OWNED_FLAG for name in names]
        values = self.pine.batch_read_int32(addrs)
        changed: list[str] = []
        for name, value in zip(names, values):
            owned = 1 if value else 0
            if owned and not self._raw_owned.get(name):
                changed.append(name)
            self._raw_owned[name] = owned
        return changed

    def __repr__(self) -> str:
        return f"WeaponInventory(weapons={len(self.weapons)})"
