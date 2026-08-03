"""Archipelago world for Ratchet & Clank: Size Matters (PSP)"""
from worlds.LauncherComponents import (
    Component,
    SuffixIdentifier,
    Type,
    components,
    icon_paths,
    launch_subprocess,
)

from .world import (
    RACSizeMatterWorld,  # noqa: F401 — registers world
)


def run_client(_url: str | None = None):
    """Launch the R&C: Size Matters PSP Archipelago client."""
    from .client import run_client as _run
    launch_subprocess(_run, name="RACSmPSPClient")


components.append(Component(
    "Ratchet & Clank: Size Matters PSP Client",
    func=run_client,
    component_type=Type.CLIENT,
    file_identifier=SuffixIdentifier(".aprsmpsp"),
    icon="rsm_psp_icon",
    description="Launch the Client for connecting to Ratchet & Clank: Size Matters (PSP)",
))

icon_paths["rsm_psp_icon"] = f"ap:{__name__}/images/Size_Matters_Icon.png"
