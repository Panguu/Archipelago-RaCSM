from typing import ClassVar

from worlds.AutoWorld import World
from worlds.LauncherComponents import Component, Type, components

from .options import DynamicPineSettings

DYNAMIC_PINE_VERSION = "v0.1.0"


def launch_client(*args) -> None:
    from worlds.LauncherComponents import launch
    from .client import run_client
    launch(run_client, name="Dynamic Pine client", args=args)


class DynamicPineWorld(World):
    """Not a playable game - registers Dynamic Pine's shared host.yaml settings,
    the same trick Universal Tracker's TrackerWorld uses."""
    settings: ClassVar[DynamicPineSettings]
    settings_key = "dynamic_pine_options"

    # to make auto world register happy so we can register our settings
    game = "Dynamic Pine"
    hidden = True
    item_name_to_id = {}
    location_name_to_id = {}


components.append(Component("Dynamic Pine", None, func=launch_client, component_type=Type.CLIENT))
