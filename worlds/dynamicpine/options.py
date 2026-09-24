from typing import Union

from settings import Group, OptionalUserFolderPath, UserFilePath, UserFolderPath


# Class docstrings here are written into host.yaml as the settings' comments
class DynamicPineSettings(Group):
    class Pcsx2Path(UserFilePath):
        """Path to your PCSX2 executable, shared by every Dynamic Pine game."""
        description = "PCSX2 Executable"
        is_exe = True

    class Pcsx2DataPath(UserFolderPath):
        """Folder for Dynamic Pine's per-game, per-slot PCSX2 data (ini, port, memcard),
        kept separate from your regular PCSX2 settings."""
        description = "Dynamic Pine PCSX2 Data Directory"

    class BiosPath(OptionalUserFolderPath):
        """Folder containing your PCSX2 BIOS file(s), shared by every instance.
        Leave unset to be prompted for it on first launch."""
        description = "PCSX2 BIOS Directory"

    class GameFiles(dict):
        """Your game ISOs keyed by PS2 serial, each as named entries (e.g. US/EU) -
        easiest managed from the Dynamic Pine hub's ISO dropdown."""

    class SelectedIsos(dict):
        """Which named ISO from game_files each game launches with, keyed by PS2 serial."""

    pcsx2_path: Union[Pcsx2Path, str] = Pcsx2Path("pcsx2.exe")
    pcsx2_data_path: Union[Pcsx2DataPath, str] = Pcsx2DataPath("dynamic_pine_pcsx2_data")
    bios_path: Union[BiosPath, str] = BiosPath("")
    game_files: Union[GameFiles, dict] = {}
    selected_isos: Union[SelectedIsos, dict] = {}
