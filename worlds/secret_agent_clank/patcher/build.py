"""Developer tool: build a new patch from a clean ISO.

    python -m worlds.secret_agent_clank.patcher.build --iso CLEAN.iso --output NEW_FOLDER

The output folder gets a patched test ISO for each main-menu branding
(Archipelago and MultiworldGG, about 4.5 GB each), a test .apsac, the compiled
modules for debugging, and a data/ folder. Once the test ISOs have been played
through in PCSX2, replace the world's data/ with that one to ship the build.
"""
import argparse
import hashlib
import json
from pathlib import Path

import bsdiff4

from ..core.native_runtime import CLANK_MODULES
from ..core.patches.snr2 import resident_exports
from ..core.patches.identity import stamp_executable, executable_crc
from ..core.patches.iso_startup_barrier import patch_resident_loader
from ..core.patches.level_build import compile_level
from ..core.patches.frontend_build import compile_frontend
from .container import BUILD_FILE, SACPatch
from .filenames import EXECUTABLE, MODULE_FILES, IMAGE_ARCHIVE
from .menu_branding import BRANDS, patch_menu_archive
from .iso import ISOImage, sha256_file, write_patched_iso


ABI = 1


def source_revision():
    root = Path(__file__).parents[1]
    digest = hashlib.sha256()
    sources = [*root.joinpath("core").rglob("*.py"), *root.joinpath("constants").rglob("*.py"),
               *root.joinpath("patcher").glob("*.py")]
    for path in sorted(sources):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    for path in sorted(root.joinpath("icon").iterdir()):
        if path.suffix in (".indices", ".clut"):
            digest.update(path.read_bytes())
    return digest.hexdigest()


def make_patch(build_id: str, source_sha256: str, result_sha256: dict[str, str],
               files: dict[str, tuple[bytes, bytes]],
               branded_files: dict[str, dict[str, tuple[bytes, bytes]]]) -> SACPatch:
    """Diff each disc file, given as (original, patched), into a patch.

    `files` are the same for every branding. `branded_files` holds each
    branding's own files, and `result_sha256` each branding's patched disc hash.
    """
    patch = SACPatch()
    patch.build = dict(build_id=build_id, abi=ABI, source_sha256=source_sha256,
                       result_sha256=result_sha256, files=[])
    entries = [(path, change, None) for path, change in sorted(files.items())]
    entries += [(path, change, branding) for branding, changes in branded_files.items()
                for path, change in sorted(changes.items())]
    for index, (path, (original, patched), branding) in enumerate(entries):
        payload = f"files/{index:02}.bsdiff4"
        entry = dict(path=path, payload=payload)
        if branding:
            entry["branding"] = branding
        patch.build["files"].append(entry)
        patch.deltas[payload] = bsdiff4.diff(original, patched)
    return patch


def build_iso(source, output):
    source, output = Path(source), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    build_id = "sac-iso-v1-" + source_revision()[:24]
    manifest = {"abi": ABI, "build_id": build_id, "modules": {}}
    replacements = {}
    source_hash = sha256_file(source)
    with source.open("rb") as stream:
        iso = ISOImage(stream)
        executable = iso.read_file(EXECUTABLE)
        imports = resident_exports(executable)
        with_loader, manifest["loader_routine"] = patch_resident_loader(executable)
        patched_executable = stamp_executable(with_loader, build_id=build_id, abi=ABI)
        manifest["elf_crc"] = executable_crc(patched_executable)
        replacements[EXECUTABLE] = executable, patched_executable
        print("Branding the main-menu background", flush=True)
        archive = iso.read_file(IMAGE_ARCHIVE)
        branded = {branding: {IMAGE_ARCHIVE: (archive, patch_menu_archive(archive, branding))}
                   for branding in BRANDS}
        for module, filename in MODULE_FILES.items():
            print(f"Compiling module {module}: {filename}", flush=True)
            data = iso.read_file(filename)
            identity = b"SACISO1\0" + hashlib.sha256(f"{build_id}:{module}".encode()).digest()
            if module == 0:
                result, binding = compile_frontend(data, imports, identity=identity, with_bindings=True)
            else:
                vendor = module in CLANK_MODULES or module in (3, 9, 14, 21, 25)
                result, binding = compile_level(data, imports, module, vendor, identity=identity, with_bindings=True)
            replacements[filename] = data, result
            manifest["modules"][str(module)] = binding
            # Kept for debugging. Never ship these: they are full game files.
            (output / f"module-{module}.rel").write_bytes(result)
    manifest["source_sha256"] = source_hash
    data = output / "data"
    data.mkdir()
    (data / "sac-runtime.json").write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    result_hashes = {}
    for branding, changes in branded.items():
        target = output / f"Secret Agent Clank - {branding}.iso"
        write_patched_iso(source, target, {path: result for path, (_, result) in {**replacements, **changes}.items()})
        result_hashes[branding] = sha256_file(target)
    patch = make_patch(build_id, source_hash, result_hashes, replacements, branded)
    (data / "patch" / "files").mkdir(parents=True)
    (data / "patch" / BUILD_FILE).write_text(json.dumps(patch.build, indent=1), encoding="utf-8")
    for name, delta in patch.deltas.items():
        (data / "patch" / name).write_bytes(delta)
    patch.write(str(output / f"Secret Agent Clank{patch.patch_file_ending}"))
    print(f"Built {build_id}; PCSX2 CRC {manifest['elf_crc']}; output {output}", flush=True)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    build_iso(args.iso, args.output)


if __name__ == "__main__":
    main()
