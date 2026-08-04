"""Dynamic Pine hub client entry point: starts the CommonClient async loop
around DynamicPineContext (see context.py for what the hub actually does -
one tab per installed Dynamic Pine game, with controls to launch PCSX2
instances and each game's own client). The games' own clients are untouched -
the hub only starts them (as subprocesses when the GUI is running), and
everything from there onwards is their existing logic."""
from __future__ import annotations

import asyncio

from CommonClient import get_base_parser, gui_enabled

from .context import DynamicPineContext

__all__ = ["run_client"]


async def main() -> None:
    # No server_loop task on purpose - the hub has nothing to say to an AP
    # server. The games' own clients it launches handle their own connections.
    ctx = DynamicPineContext(None, None)

    if gui_enabled:
        ctx.run_gui()
    ctx.run_cli()

    await ctx.exit_event.wait()
    await ctx.shutdown()


def run_client(*args: str) -> None:
    from Utils import init_logging

    init_logging("DynamicPineClient")

    # Marks this process (and, since it's inherited, any game client this hub
    # later spawns via launch_game_client) as legitimately "Dynamic Pine" -
    # launch_pcsx2 refuses to do anything without it. Set as early as
    # possible so it's in place before anything below could spawn a child.
    from .api import mark_launched_via_hub
    mark_launched_via_hub()

    # Base parser kept so standard flags like --nogui work; any connection args
    # it accepts are simply ignored.
    parser = get_base_parser(description="Dynamic Pine hub client")
    parser.parse_args(args)

    import colorama

    colorama.just_fix_windows_console()
    asyncio.run(main())
    colorama.deinit()
