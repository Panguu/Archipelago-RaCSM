from enum import IntFlag

from ..pcsx2_interface.pine import Pine
from .address_maps import CONTROLLER_BUTTONS_ADDRESS, CONTROLLER_PAUSE_SELECT_ADDRESS

"""
Controller Logic
Holding L1 + L2 + R1 + R2 + START is the hotkey to force-open the Planet Menu
(see PLANET_MENU_HOTKEY / ButtonState.opens_planet_menu).
"""
class PauseSelectButtons(IntFlag):
    SELECT = 0x01
    START  = 0x08
    D_PAD_UP    = 0x10
    D_PAD_DOWN  = 0x40
    D_PAD_LEFT  = 0x80
    D_PAD_RIGHT = 0x20


class ControllerButtons(IntFlag):
    L1       = 0x01
    R1       = 0x02
    L2       = 0x04
    R2       = 0x08
    TRIANGLE = 0x10
    CIRCLE   = 0x20
    CROSS    = 0x40
    SQUARE   = 0x80


# Held together, forces the Planet Menu open via MenuState.set_menu(PLANET_MENU).
PLANET_MENU_HOTKEY: tuple[PauseSelectButtons | ControllerButtons, ...] = (
    ControllerButtons.L1,
    ControllerButtons.L2,
    ControllerButtons.R1,
    ControllerButtons.R2,
    PauseSelectButtons.START,
)


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

    @property
    def opens_planet_menu(self) -> bool:
        """True while the Planet Menu hotkey combo is held."""
        return self.pressed(*PLANET_MENU_HOTKEY)

    def __repr__(self) -> str:
        return f"ButtonState(pause_sel={self.pause_sel}, buttons={self.buttons})"
