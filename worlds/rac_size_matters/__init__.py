"""Archipelago world for Ratchet & Clank: Size Matters (PSP/PS2)"""
import importlib.util
import sys
from pathlib import Path

from worlds.LauncherComponents import (
    Component,
    SuffixIdentifier,
    Type,
    components,
    icon_paths,
    launch_subprocess,
)

# The vendored pypine submodule's pine.py annotates `get_emu_status` with
# `-> Pine.EmuStatus` but lacks `from __future__ import annotations`, so the
# bare `Pine` name doesn't exist yet while its own class body executes. We
# can't edit the submodule's tracked content, so load it ourselves with
# postponed evaluation enabled and seed it into sys.modules before anything
# does `from ..pypine.pypine.pine import Pine`.
_pine_module_name = f"{__name__}.pypine.pypine.pine"
if _pine_module_name not in sys.modules:
    _pine_path = Path(__file__).parent / "pypine" / "pypine" / "pine.py"
    _pine_spec = importlib.util.spec_from_file_location(_pine_module_name, _pine_path)
    _pine_module = importlib.util.module_from_spec(_pine_spec)
    _pine_code = compile(
        "from __future__ import annotations\n" + _pine_path.read_text(),
        str(_pine_path),
        "exec",
    )
    sys.modules[_pine_module_name] = _pine_module
    exec(_pine_code, _pine_module.__dict__)

from worlds.rac_size_matters.world import (
    RACSizeMatterWorld,  # noqa: F401 — registers world
)


def run_client(_url: str | None = None):
    """Launch the R&C: Size Matters Archipelago client."""
    from worlds.rac_size_matters.client import run_client as _run
    launch_subprocess(_run, name="RACSmClient")


components.append(Component(
    "Ratchet & Clank: Size Matters Client",
    func=run_client,
    component_type=Type.CLIENT,
    file_identifier=SuffixIdentifier(".aprsm"),
    icon="rsm_icon",
    description="Launch the Client for connecting to Ratchet & Clank: Size Matters",
))

icon_paths["rsm_icon"] = f"ap:{__name__}/images/Size_Matters_Icon.png"
