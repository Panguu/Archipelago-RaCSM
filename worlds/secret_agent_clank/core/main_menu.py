"""CURRENT_CASE stays stale on the title screen."""
from .patches import LoaderStateReader


def is_main_menu(pine):
    addresses = (LoaderStateReader.TARGET, LoaderStateReader.STATE, LoaderStateReader.STATUS,
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
