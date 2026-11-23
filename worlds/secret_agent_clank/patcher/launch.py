import asyncio
import logging
import os
from pathlib import Path
import subprocess

from settings import get_settings
from Utils import open_file, user_path

from .container import SACPatch, clean_iso_path
from .menu_branding import app_branding

logger = logging.getLogger("Client")


def patched_iso_path(patch: SACPatch, branding: str) -> Path:
    """Every seed of a build uses the same patched ISO, so it's named after the build (and menu logo)."""
    suffix = "" if branding == "archipelago" else f"-{branding}"
    return Path(user_path(f"Secret Agent Clank AP {patch.build['build_id'][-12:]}{suffix}.iso"))


async def prepare_iso(patch_file: str, gui: bool) -> tuple[SACPatch, Path]:
    """Read the .apsac and return it with the path of its patched ISO, patching first if needed."""
    patch = SACPatch(patch_file)
    patch.read()
    branding = patch.choose_branding()
    if branding != app_branding():
        logger.warning(f"This patch build has no {app_branding()} menu; using the {branding} one.")
    target = patched_iso_path(patch, branding)
    if target.exists():
        logger.info(f"Using the patched ISO from an earlier seed: {target}")
        return patch, target

    source = clean_iso_path()
    if gui:
        from .ui import PatcherUI  # imported here because it starts Kivy
        window = PatcherUI(patch, source, target, branding)
        await window.async_run()
        if window.error:
            raise window.error
    else:
        last_logged = None

        def log_progress(message: str, fraction: float) -> None:
            nonlocal last_logged
            if (message, int(fraction * 10)) != last_logged:  # log every 10%
                last_logged = message, int(fraction * 10)
                logger.info(f"{message}... {fraction:.0%}")

        await asyncio.to_thread(patch.apply, source, target, branding, log_progress)
    logger.info(f"Patched ISO written to {target}")
    return patch, target


def start_game(iso: Path) -> None:
    """Boot the patched ISO, if iso_start in host.yaml says to."""
    start = get_settings().secret_agent_clank_options.iso_start
    if start is True:
        open_file(iso)
    elif start and os.path.isfile(start):
        subprocess.Popen([start, str(iso)])
    elif start:
        logger.warning(f"iso_start in host.yaml isn't a program: {start}")
        logger.info(f"Boot {iso} in PCSX2.")
    else:
        logger.info(f"Boot {iso} in PCSX2.")
