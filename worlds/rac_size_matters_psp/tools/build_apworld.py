"""Build the PSP apworld without research captures, test data, or local state."""
from fnmatch import fnmatch
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def build():
    root = Path(__file__).resolve().parents[1]
    patterns = [line.strip() for line in (root / "apworld.ignore").read_text().splitlines()
                if line.strip() and not line.startswith("#")]
    destination = root / "build" / "rac_size_matters_psp.apworld"
    destination.parent.mkdir(exist_ok=True)
    with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root)
            if not path.is_file() or path.is_symlink():
                continue
            if any(fnmatch(part, pattern) for part in relative.parts for pattern in patterns):
                continue
            archive.write(path, (Path(root.name) / relative).as_posix())
    with ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Corrupt apworld archive")
        for required in ("__init__.py", "client/__main__.py", "requirements.txt", "archipelago.json"):
            if f"{root.name}/{required}" not in archive.namelist():
                raise RuntimeError(f"Missing required package file: {required}")
        print(f"Built {destination} ({len(archive.namelist())} files)")


if __name__ == "__main__":
    build()
