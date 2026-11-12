"""Every slot gets its own .apsac so the client knows which slot to connect as,
but the patch inside is the same for every seed: one bsdiff4 delta per changed
disc file, listed in sac-build.json. So one patched ISO works for every seed
made with the same build.
"""
import json
from pathlib import Path
import zipfile

import bsdiff4
from settings import get_settings
from worlds.Files import APAutoPatchInterface

from .iso import ISOImage, Progress, scaled, sha256_file, write_patched_iso
from .menu_branding import app_branding

BUILD_FILE = "sac-build.json"


def clean_iso_path() -> str:
    """The clean ISO from host.yaml. Opens a file picker if it's missing, so call it on the main thread."""
    return get_settings().secret_agent_clank_options.iso_file


class SACPatch(APAutoPatchInterface):
    game = "Secret Agent Clank"
    patch_file_ending = ".apsac"
    result_file_ending = ".iso"
    # We apply the patch ourselves: AP's built-in procedures would load the
    # whole 4.5 GB ISO into memory.
    procedure = "custom"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # sac-build.json: build_id, abi, source_sha256 (clean disc), result_sha256
        # ({branding: patched disc hash}) and files: [{path, payload}], payload naming
        # the delta. A file with a "branding" key is only used for that branding (the
        # main-menu logo); the rest are shared.
        self.build: dict = {}
        self.deltas: dict[str, bytes] = {}

    def get_manifest(self):
        manifest = super().get_manifest()
        manifest["result_file_ending"] = self.result_file_ending
        return manifest

    def write_contents(self, archive: zipfile.ZipFile) -> None:
        super().write_contents(archive)
        archive.writestr(BUILD_FILE, json.dumps(self.build))
        for name, delta in self.deltas.items():
            # bsdiff4 output is already compressed.
            archive.writestr(name, delta, compress_type=zipfile.ZIP_STORED)

    def read_contents(self, archive: zipfile.ZipFile):
        manifest = super().read_contents(archive)
        self.build = json.loads(archive.read(BUILD_FILE))
        self.deltas = {file["payload"]: archive.read(file["payload"]) for file in self.build["files"]}
        return manifest

    @property
    def brandings(self) -> list[str]:
        """The main-menu logos this build can patch in."""
        return list(self.build["result_sha256"])

    def choose_branding(self) -> str:
        """This app's menu logo if the build has it, otherwise Archipelago's."""
        branding = app_branding()
        return branding if branding in self.brandings else "archipelago"

    def apply(self, source: str | Path, target: str | Path, branding: str,
              progress: Progress | None = None) -> Path:
        """Write a patched copy of the clean ISO at `source` to `target`, with `branding`'s menu logo."""
        if branding not in self.brandings:
            raise ValueError(f"This patch build has no {branding} menu (it has {', '.join(self.brandings)}).")
        source, target = Path(source), Path(target)
        if target.exists():
            raise FileExistsError(f"{target} already exists")

        clean_hash = sha256_file(source, scaled(progress, 0.0, 0.35), "Checking the clean ISO")
        if clean_hash != self.build["source_sha256"]:
            raise ValueError("This isn't a clean copy of the USA Secret Agent Clank ISO (SCUS-97623).")

        with source.open("rb") as stream:
            iso = ISOImage(stream)
            patched = {file["path"]: bsdiff4.patch(iso.read_file(file["path"]), self.deltas[file["payload"]])
                       for file in self.build["files"] if file.get("branding", branding) == branding}

        # Write to a temporary file so a half-written ISO never has the real name.
        temporary = target.with_name(target.name + ".tmp")
        try:
            write_patched_iso(source, temporary, patched, scaled(progress, 0.35, 0.65))
            result_hash = sha256_file(temporary, scaled(progress, 0.65, 1.0), "Verifying the patched ISO")
            if result_hash != self.build["result_sha256"][branding]:
                raise ValueError("The patched ISO didn't come out right. The .apsac file may be damaged.")
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        return target

    def patch(self, target: str) -> None:
        """Called by AP's generic patcher (Patch.py)."""
        self.read()
        self.apply(clean_iso_path(), target, self.choose_branding())
