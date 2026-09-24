from typing import TYPE_CHECKING

from .api import get_pine_port
from .launcher import (InstanceAlreadyRunningError, NoBiosConfigured, NoIsoConfigured, NoPCSX2Executable,
                       launch_pcsx2)

if TYPE_CHECKING:
    from CommonClient import CommonContext


class DynamicPineCommandMixin:
    # Needs ctx.auth set to the slot name and dynamic_pine_game_name set on the class
    ctx: "CommonContext"
    dynamic_pine_game_name: str

    def _cmd_launch_pcsx2(self) -> bool:
        """Launch (or reconnect to) this slot's PCSX2 instance via Dynamic Pine."""
        if not self.ctx.auth:
            self.output("Not connected to a slot yet - connect first.")
            return False

        try:
            port = launch_pcsx2(self.dynamic_pine_game_name, self.ctx.auth)
        except InstanceAlreadyRunningError:
            # Already running (e.g. reconnecting) - reuse it rather than failing
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
