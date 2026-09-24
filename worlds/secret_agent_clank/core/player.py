"""Movement/health accessor for one of SAC's three playable characters (Ratchet, Clank, Qwark)."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..pypine import Pine


class CharacterState:
    # TODO: unconfirmed -- the other RaC worlds use a small int (e.g. 0 idle,
    # 2 running) for movement_state and a distinct set of values above some
    # threshold for "dead". Left unset until SAC's actual dead-state value(s)
    # are found live, so is_dead fails closed (never reports dead) rather
    # than guessing wrong and silently mis-triggering death handling.
    DEAD_STATE_VALUES: frozenset[int] = frozenset()

    def __init__(self, pine: "Pine") -> None:
        self.pine = pine
        self.state_addr:  int | None = None
        self.health_addr: int | None = None

    def set_addrs(self, state_addr: int | None, health_addr: int | None) -> None:
        self.state_addr = state_addr
        self.health_addr = health_addr

    @property
    def movement_state(self) -> int:
        if self.state_addr is None:
            return 0
        return self.pine.read_int32(self.state_addr)

    @property
    def health(self) -> float:
        if self.health_addr is None:
            return 0.0
        return self.pine.read_float(self.health_addr)

    @health.setter
    def health(self, value: float) -> None:
        if self.health_addr is None:
            return
        self.pine.write_float(self.health_addr, value)

    @property
    def is_dead(self) -> bool:
        if self.state_addr is None or not self.DEAD_STATE_VALUES:
            return False
        return self.movement_state in self.DEAD_STATE_VALUES

    def __repr__(self) -> str:
        return f"CharacterState(state_addr={self.state_addr!r}, health_addr={self.health_addr!r})"
