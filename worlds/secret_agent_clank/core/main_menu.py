"""Resident title-module detection; CURRENT_CASE stays stale on the title screen."""
from .patches.loader_gate import LoaderGate


def is_main_menu(pine):
    # Verified on the title screen: loader target 0, finished loader state 5,
    # completed relocation, no pending travel, and initialized game state.
    # Read twice so crossing a transition cannot combine two different states.
    addresses = (LoaderGate.TARGET, LoaderGate.STATE, LoaderGate.STATUS,
                 0x206324, 0x206338)
    expected = [0, 5, 1, 0xFFFFFFFF, 3]
    return (pine.batch_read_int32(addresses) == expected
            and pine.batch_read_int32(addresses) == expected)


class MainMenuNotice:
    def __init__(self, pine, log):
        self.pine, self.log = pine, log
        self.shown = False

    def poll(self):
        at_menu = is_main_menu(self.pine)
        if at_menu and not self.shown:
            self.log("[SAC] Start a new game")
        self.shown = at_menu
        return at_menu
