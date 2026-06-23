from enum import IntFlag

from ..pypine.pypine.pine import Pine
from .address_maps import CONTROLLER_BUTTONS_ADDRESS, CONTROLLER_PAUSE_SELECT_ADDRESS

"""
Controller Logic
This is currently not implemented. The idea is to open the Planet Menu, but these
addresses float around in memory, so no implementation is planned yet.
"""
class PauseSelectButtons(IntFlag):
    SELECT = 0x01
    START  = 0x08


class ControllerButtons(IntFlag):
    L1       = 0x01
    R1       = 0x02
    L2       = 0x04
    R2       = 0x08
    TRIANGLE = 0x10
    CIRCLE   = 0x20
    CROSS    = 0x40
    SQUARE   = 0x80


class ButtonState:
    """Snapshot of both controller bytes, read each tick."""

    def __init__(self, pause_sel: int, buttons: int) -> None:
        self.pause_sel = PauseSelectButtons(pause_sel & 0xFF)
        self.buttons   = ControllerButtons(buttons & 0xFF)

    @classmethod
    def read(cls, ipc: Pine) -> "ButtonState":
        return cls(
            ipc.read_int8(CONTROLLER_PAUSE_SELECT_ADDRESS),
            ipc.read_int8(CONTROLLER_BUTTONS_ADDRESS),
        )

    def pressed(self, *flags: PauseSelectButtons | ControllerButtons) -> bool:
        """Return True if every supplied flag is currently held."""
        for f in flags:
            if isinstance(f, PauseSelectButtons):
                if not (self.pause_sel & f):
                    return False
            else:
                if not (self.buttons & f):
                    return False
        return True

    def __repr__(self) -> str:
        return f"ButtonState(pause_sel={self.pause_sel}, buttons={self.buttons})"
