"""The patch build that ships with the world, in data/.

- data/sac-runtime.json: what the client needs to know about the patched game.
- data/patch/: the patch itself, copied into every slot's .apsac.

Both come from the same `patcher.build` run; replace them together.
"""
from importlib.resources import files
import json

from .container import BUILD_FILE, SACPatch

DATA = files("worlds.secret_agent_clank").joinpath("data")


def load_runtime_build() -> dict:
    try:
        return json.loads(DATA.joinpath("sac-runtime.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise RuntimeError("This Secret Agent Clank world has no ISO build installed. "
                           "Reinstall the apworld from a release.") from None


def add_release_patch(patch: SACPatch) -> None:
    """Fill `patch` with the shipped build."""
    folder = DATA.joinpath("patch")
    patch.build = json.loads(folder.joinpath(BUILD_FILE).read_text(encoding="utf-8"))
    if patch.build["build_id"] != load_runtime_build()["build_id"]:
        raise RuntimeError("data/patch and data/sac-runtime.json are from different builds")
    patch.deltas = {file["payload"]: folder.joinpath(file["payload"]).read_bytes()
                    for file in patch.build["files"]}
