from typing import ClassVar

from worlds.AutoWorld import World
from worlds.LauncherComponents import Component, Type, components, launch

from .options import DynamicPineSettings

DYNAMIC_PINE_VERSION = "0.1.0"


def launch_client(*args) -> None:
    # Imported here so the client/GUI code isn't loaded during world loading
    from .client import run_client
    launch(run_client, name="Dynamic Pine client", args=args)


class DynamicPineWorld(World):
    # Not a playable game - only registers the shared host.yaml settings
    settings: ClassVar[DynamicPineSettings]
    settings_key = "dynamic_pine_options"

    game = "Dynamic Pine"
    hidden = True
    item_name_to_id = {}
    location_name_to_id = {}


components.append(Component("Dynamic Pine", None, func=launch_client, component_type=Type.CLIENT))
