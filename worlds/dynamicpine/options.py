from typing import Union

from settings import Group, OptionalUserFolderPath, UserFilePath, UserFolderPath


class DynamicPineSettings(Group):
    class Pcsx2Path(UserFilePath):
        """Path to your PCSX2 executable, shared by every Dynamic Pine game.
        Used to launch the emulator automatically with PINE enabled. If this
        file can't be found, you'll be prompted to browse for it (and the
        choice is remembered)."""
        description = "PCSX2 Executable"
        is_exe = True

    class Pcsx2DataPath(UserFolderPath):
        """Root folder Dynamic Pine uses for PCSX2's portable settings data. A
        subfolder named after each game's serial (e.g. SCUS-97615) and then the
        connecting slot name is created per running instance, each with its own
        PINE-enabled PCSX2.ini, port, and memcard - kept separate from your
        regular PCSX2 install/settings, and from each other, so multiple games
        and slots can run at once."""
        description = "Dynamic Pine PCSX2 Data Directory"

    class BiosPath(OptionalUserFolderPath):
        """Folder containing your PCSX2 BIOS file(s). Shared across every PCSX2
        instance Dynamic Pine launches, so you only complete PCSX2's BIOS setup
        once instead of once per game/instance. Leave unset to let each new
        instance prompt for its own BIOS the first time it's created."""
        description = "PCSX2 BIOS Directory"

    class GameFiles(dict):
        """Paths to your own copies of each supported game's ISO, keyed by the
        game's PS2 serial. Format is:
          SCUS-97615: C:/isos/Ratchet and Clank Size Matters.iso
        with each game on its own line and indented two spaces. A game with no
        entry here can still be played - Dynamic Pine just won't be able to
        launch PCSX2 for it automatically."""

    pcsx2_path: Union[Pcsx2Path, str] = Pcsx2Path("pcsx2.exe")
    pcsx2_data_path: Union[Pcsx2DataPath, str] = Pcsx2DataPath("dynamic_pine_pcsx2_data")
    bios_path: Union[BiosPath, str] = BiosPath("")
    game_files: Union[GameFiles, dict] = {}
