from worlds.LauncherComponents import (
    Component,
    SuffixIdentifier,
    Type,
    components,
    icon_paths,
    launch_subprocess,
)
from .patcher import SACPatch  # noqa: F401 (registers .apsac with Patch.py)
from .world import SecretAgentClankWorld  # noqa: F401 (registers the world)


def run_client(*args: str):
    # Imported when launched, so generating seeds doesn't load the client and Kivy.
    from .client import run_client as client_main
    launch_subprocess(client_main, name="SACClient", args=args)


components.append(Component(
    "Secret Agent Clank Client",
    func=run_client,
    component_type=Type.CLIENT,
    file_identifier=SuffixIdentifier(SACPatch.patch_file_ending),
    description="Launch the Client for connecting to Secret Agent Clank. "
                "Open a .apsac to patch the ISO (first time per build) and connect as that slot.",
    icon="sac_icon",
))

icon_paths["sac_icon"] = f"ap:{__name__}/icon/Secret_Agent_Clank_AP.png"
