from __future__ import annotations

import asyncio
import logging
import webbrowser

import colorama

import Utils
from CommonClient import get_base_parser, gui_enabled, server_loop

from .backend import BASE_URL, find_installed_patched_swf, install_patched_swf
from .client import OddCoupleContext

logger = logging.getLogger("OddCoupleClient")


def launch(*launch_args: str) -> None:
    colorama.just_fix_windows_console()
    asyncio.run(main(*launch_args))
    colorama.deinit()


async def main(*launch_args: str) -> None:
    Utils.init_logging("OddCoupleClient", exception_logger="Client")

    parser = get_base_parser()
    parser.add_argument("diff_file", default="", type=str, nargs="?",
                        help="Path to a .apoddcouple Archipelago patch file")
    args = parser.parse_args(launch_args)

    swf_path = None
    if args.diff_file:
        import Patch
        logger.info("Patch file was supplied - patching the local odd_couple.swf...")
        meta, swf_path = Patch.create_rom_file(args.diff_file)
        if meta.get("server") and not args.connect:
            args.connect = meta["server"]
        logger.info(f"Wrote patched swf to {swf_path}")

    ctx = OddCoupleContext(args.connect, args.password)
    ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")

    if gui_enabled and not getattr(args, "nogui", False):
        ctx.run_gui()
    ctx.run_cli()

    # Embedded server - no external project, subprocess, or virtualenv needed.
    ctx.local_server.start_http()
    await ctx.local_server.start_ws()

    # The frontend always loads the one fixed patched-swf filename itself, so
    # there's nothing to pass through the URL - just make sure that file
    # actually exists, installing the freshly patched one if we have it, or
    # warning if neither this run nor an earlier one ever installed it.
    if swf_path:
        install_patched_swf(swf_path)
    elif not find_installed_patched_swf():
        logger.warning("No patched swf installed yet - open a .apoddcouple file to generate one.")
    webbrowser.open(BASE_URL)

    await ctx.exit_event.wait()
    ctx.local_server.stop()
    await ctx.shutdown()
