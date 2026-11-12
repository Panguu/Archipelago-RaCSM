"""Local patcher settings; no ISO is required on generation servers."""
import settings

from .patcher.filenames import EXECUTABLE
from .patcher.iso import ISOImage


class SecretAgentClankSettings(settings.Group):
    class ISOFile(settings.UserFilePath):
        """Clean USA SCUS-97623 ISO. Patching always writes a separate copy."""
        description = "Secret Agent Clank (USA) ISO"

        @classmethod
        def validate(cls, path: str) -> None:
            # Cheap disc check when browsing; patching verifies the full hash.
            with open(path, "rb") as stream:
                if EXECUTABLE not in ISOImage(stream).files:
                    raise ValueError("Not the USA (SCUS-97623) Secret Agent Clank disc")

    class ISOStart(str):
        """
        Set this to false to never boot the patched ISO after opening a .apsac,
        true to open it with the operating system's default program,
        or a path to the program to open it with (such as pcsx2-qt.exe).
        """

    iso_file: ISOFile = ISOFile("Secret Agent Clank (USA) (En,Fr,De,Es,It).iso")
    iso_start: ISOStart | bool = False
