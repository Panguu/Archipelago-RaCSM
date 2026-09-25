"""Archipelago world for LittleBigPlanet (PS3)."""
from worlds.LauncherComponents import Component, components, launch_subprocess

from .world import LittleBigPlanetWorld as LittleBigPlanetWorld


def launch_client(*args):
    from .Client import launch
    launch_subprocess(launch, name='LittleBigPlanet Client', args=args)


components.append(Component('LittleBigPlanet Client', func=launch_client, game_name='LittleBigPlanet',
                            supports_uri=True, description='RPCS3 PINE client (experimental)'))
