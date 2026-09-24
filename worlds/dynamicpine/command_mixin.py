"""Ready-made client command for games that want their own client (not just
the hub) to expose a /launch_pcsx2 command, without every game reimplementing
launch_pcsx2's exception handling. Mix DynamicPineCommandMixin into your
game's ClientCommandProcessor alongside ClientCommandProcessor itself -
matches the *Mixin pattern rac_size_matters' RACContext already uses for
PineMixin/DeathLinkMixin/etc."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from CommonClient import CommonContext


class DynamicPineCommandMixin:
    """Requires two things from the class it's mixed into: a `ctx:
    CommonContext` (the usual ClientCommandProcessor attribute) whose `.auth`
    holds the connected slot name, and a `dynamic_pine_game_name` class
    attribute naming the game as declared to DynamicPineGame(game_ids=...) -
    typically your GAME_NAME constant.

    Example:
        class MyCommandProcessor(DynamicPineCommandMixin, ClientCommandProcessor):
            dynamic_pine_game_name = GAME_NAME
    """
    ctx: "CommonContext"
    dynamic_pine_game_name: str

    def _cmd_launch_pcsx2(self) -> bool:
        """Launch (or reconnect to) this slot's PCSX2 instance via Dynamic Pine."""
        if not self.ctx.auth:
            self.output("Not connected to a slot yet - connect first.")
            return False
        try:
            from worlds.dynamicpine import (InstanceAlreadyRunningError, NoBiosConfigured,
                                            NoIsoConfigured, NoPCSX2Executable, get_pine_port,
                                            launch_pcsx2)
        except ImportError:
            self.output("Dynamic Pine is not installed.")
            return False

        try:
            port = launch_pcsx2(self.dynamic_pine_game_name, self.ctx.auth)
        except InstanceAlreadyRunningError:
            # Already running (e.g. reconnecting) - reuse its existing
            # instance rather than treating that as a failure.
            port = get_pine_port(self.dynamic_pine_game_name, self.ctx.auth)
        except (NoPCSX2Executable, NoBiosConfigured, NoIsoConfigured) as exc:
            self.output(f"[DynamicPine] {exc}")
            return False

        if port is None:
            self.output("[DynamicPine] Not launched through the Dynamic Pine hub client - "
                       "start it from the AP Launcher instead.")
            return False
        self.output(f"[DynamicPine] PCSX2 instance ready on PINE port {port}.")
        return True
