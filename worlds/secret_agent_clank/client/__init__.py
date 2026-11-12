import asyncio
import logging
from argparse import Namespace

import colorama

from CommonClient import get_base_parser, gui_enabled, handle_url_arg, server_loop
from Utils import async_start, init_logging

from ..patcher.launch import prepare_iso, start_game
from .command_processor import SACCommandProcessor
from .context import SACContext, tracker_loaded
from .deathlink import DeathLinkMixin
from .game_worker import GameRuntime
from .vendor_scouts import VendorReward, VendorScouts
from .worker_bridge import GameWorker

__all__ = [
    "DeathLinkMixin",
    "GameRuntime",
    "GameWorker",
    "SACCommandProcessor",
    "SACContext",
    "VendorReward",
    "VendorScouts",
    "run_client",
]


async def _open_patch(args: Namespace) -> None:
    """Patch (once per build) and boot the ISO; connect as the patch's slot unless told otherwise."""
    try:
        patch, iso = await prepare_iso(args.patch_file, gui_enabled)
    except Exception as exc:
        logging.getLogger("Client").error(f"[SAC] Could not patch the ISO: {exc}")
        return
    args.name = args.name or patch.player_name or None
    args.connect = args.connect or patch.server or None
    start_game(iso)


async def main(args: Namespace) -> None:
    if args.patch_file:
        await _open_patch(args)
    ctx = SACContext(args.connect, args.password)
    ctx.auth = args.name
    ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")

    if tracker_loaded:
        ctx.run_generator()

    if gui_enabled:
        ctx.run_gui()
    ctx.run_cli()

    watcher = asyncio.create_task(ctx.game_watcher(), name="SAC game watcher")

    await ctx.exit_event.wait()
    watcher.cancel()
    graceful = await ctx._worker.close()
    await asyncio.gather(watcher, return_exceptions=True)
    if not graceful:
        logging.getLogger("CommonClient").warning("[SAC] Worker required forced shutdown. Restart the game if loading is held.")
    await ctx.shutdown()


def run_client(*args: str) -> None:
    init_logging("SACClient")
    parser = get_base_parser(description="Secret Agent Clank Archipelago Client")
    parser.add_argument("--name", default=None, help="Slot Name to connect as.")
    parser.add_argument("url", nargs="?", help="Archipelago connection url, or a .apsac patch file")
    parsed_args = parser.parse_args(args)
    parsed_args.patch_file = None
    if parsed_args.url and parsed_args.url.lower().endswith(".apsac"):
        parsed_args.patch_file, parsed_args.url = parsed_args.url, None
    parsed_args = handle_url_arg(parsed_args, parser)

    colorama.just_fix_windows_console()
    asyncio.run(main(parsed_args))
    colorama.deinit()
