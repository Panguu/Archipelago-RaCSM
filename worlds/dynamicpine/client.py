import asyncio

import colorama

from CommonClient import get_base_parser, gui_enabled
from Utils import init_logging

from .api import mark_launched_via_hub
from .context import DynamicPineContext

__all__ = ["run_client"]


async def main() -> None:
    # No server_loop - the hub never connects to an AP server itself
    ctx = DynamicPineContext(None, None)

    if gui_enabled:
        ctx.run_gui()
    ctx.run_cli()

    await ctx.exit_event.wait()
    await ctx.shutdown()


def run_client(*args: str) -> None:
    init_logging("DynamicPineClient")

    # Inherited by every client the hub spawns; launch_pcsx2 refuses to run without it
    mark_launched_via_hub()

    parser = get_base_parser(description="Dynamic Pine hub client")
    parser.parse_args(args)

    colorama.just_fix_windows_console()
    asyncio.run(main())
    colorama.deinit()
