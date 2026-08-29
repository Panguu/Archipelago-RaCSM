from typing import TYPE_CHECKING

from ..constants.shrink_ray import OUTPOST_OMEGA_GRINDRAIL_BIT, SHRINK_RAY_PUZZLE_BITS
from .address_maps import SHRINK_RAY_GATE_ADDRESS, SHRINK_RAY_SKIP_ADDRESSES

if TYPE_CHECKING:
    from ..pypine import Pine

SHRINK_RAY_SKIP_LOCATION_NAMES: list[str] = list(SHRINK_RAY_PUZZLE_BITS)


class ShrinkRaySkipInventory:
    """Pine-backed live accessor for the Shrink Ray puzzles.

    skip_all() (Shrink Ray Skips option) writes every tracked bit solved
    every tick at the shared SHRINK_RAY_GATE_ADDRESS bitmask, AND — for
    puzzles confirmed to need it (SHRINK_RAY_SKIP_ADDRESSES) — an extra 1
    written to that puzzle's own separate bypass address, since the shared
    bitmask bit alone doesn't actually unlock/bypass at least Kalidon Enter
    Factory in-game. Only the puzzles present in SHRINK_RAY_SKIP_ADDRESSES
    get that extra write; the rest rely on the bitmask alone until
    confirmed otherwise. check() (Shrink Ray Locations option) is separate,
    pull-based completion tracking against the same SHRINK_RAY_GATE_ADDRESS
    bitmask, same shape as ChallengeInventory/SkyboardInventory: reports
    each bit's 0->1 transition as a newly completed AP location. Skips and
    Locations are mutually exclusive options (see world.py's
    generate_early), so the two never run against each other.
    """

    def __init__(self, pine: "Pine") -> None:
        self.pine = pine
        self.completed: set[str] = set()

    def _read(self) -> int:
        return self.pine.read_int16(SHRINK_RAY_GATE_ADDRESS) or 0

    def skip_all(self) -> None:
        solve_mask = 0
        for bit in SHRINK_RAY_PUZZLE_BITS.values():
            solve_mask |= bit
        self.pine.write_int16(SHRINK_RAY_GATE_ADDRESS, self._read() | solve_mask)
        for address in SHRINK_RAY_SKIP_ADDRESSES.values():
            self.pine.write_int8(address, 1)

    def force_outpost_omega_open(self) -> None:
        """Unconditionally keeps the Outpost Omega grindrail gate solved,
        independent of the Shrink Ray Skips/Locations options — called every
        tick regardless of their state."""
        self.pine.write_int16(SHRINK_RAY_GATE_ADDRESS, self._read() | OUTPOST_OMEGA_GRINDRAIL_BIT)

    def check(self) -> list[str]:
        raw = self._read()
        newly: list[str] = []
        for name, bit in SHRINK_RAY_PUZZLE_BITS.items():
            if name in self.completed:
                continue
            # Kalidon Enter Factory (and any other puzzle in
            # SHRINK_RAY_SKIP_ADDRESSES) doesn't reliably flip its shared
            # gate bit when solved naturally — its own bypass address reads
            # 1 once truly solved, confirmed live in-game, so check that too.
            skip_address = SHRINK_RAY_SKIP_ADDRESSES.get(name)
            solved_via_skip_address = skip_address is not None and self.pine.read_int8(skip_address) != 0
            if (raw & bit) or solved_via_skip_address:
                self.completed.add(name)
                newly.append(name)
        return newly

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        self.completed.update(name for name in checked_locations if name in SHRINK_RAY_PUZZLE_BITS)

    def __repr__(self) -> str:
        return f"ShrinkRaySkipInventory(completed={len(self.completed)}/{len(SHRINK_RAY_PUZZLE_BITS)})"
