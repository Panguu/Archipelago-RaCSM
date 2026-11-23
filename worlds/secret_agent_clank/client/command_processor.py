from typing import TYPE_CHECKING

from CommonClient import logger
from Utils import async_start

try:
    from worlds.tracker.TrackerClient import TrackerCommandProcessor as ClientCommandProcessor
except ImportError:
    from CommonClient import ClientCommandProcessor

if TYPE_CHECKING:
    from .context import SACContext


class SACCommandProcessor(ClientCommandProcessor):
    ctx: "SACContext"

    def _cmd_debug(self, mode: str = "") -> bool:
        """Show diagnostic messages such as hook loads and case changes. /debug [on|off] (toggles by default)."""
        if mode.lower() not in ("", "on", "off"):
            logger.warning("[SAC] Usage: /debug [on|off]")
            return False
        self.ctx.debug_logging = not self.ctx.debug_logging if not mode else mode.lower() == "on"
        logger.info(f"[SAC] Debug messages {'on' if self.ctx.debug_logging else 'off'}.")
        return True

    def _cmd_reconnect(self) -> bool:
        """Reconnect to PCSX2 and re-apply received Archipelago items."""
        async_start(self.ctx.reconnect_pine())
        return True

    async def _worker_command(self, command, payload=None):
        try:
            result = await self.ctx._worker.request(command, payload)
            if isinstance(result, dict):
                for key, value in result.items():
                    logger.info(f"[SAC] {key}: {value}")
            elif isinstance(result, list):
                for row in result:
                    logger.info(f"[SAC] {row}")
            elif result is not None:
                logger.info(f"[SAC] {result}")
        except Exception as exc:
            logger.warning(f"[SAC] {command}: {exc}")

    def _cmd_sac_info(self) -> bool:
        """Print slot options and a snapshot from the game worker."""
        logger.info(f"[SAC] Options: {self.ctx.slot_data}")
        async_start(self._worker_command("diagnostic", ("sac_info",)))
        return True

    def _cmd_reset_trap(self) -> bool:
        """Turn off every active trap and clear its remaining time."""
        async_start(self._reset_traps())
        return True

    async def _reset_traps(self) -> None:
        try:
            reset = await self.ctx._worker.request("reset_traps")
        except Exception as exc:
            logger.warning(f"[SAC] reset_trap: {exc}")
            return
        if reset:
            logger.info("[SAC] Traps reset.")
        else:
            logger.warning("[SAC] Could not reset traps; load into a case first.")

    def _cmd_ringlink(self, mode: str = "toggle") -> bool:
        """Turn Ring Link on or off for this session. /ringlink [toggle|on|off|status]"""
        mode = mode.lower()
        if mode not in ("toggle", "on", "off", "status"):
            logger.warning("[SAC] Usage: /ringlink [toggle|on|off|status]")
            return False
        if mode == "status":
            logger.info(f"[SAC] Ring Link is {'enabled' if self.ctx._ring_link_enabled else 'disabled'}.")
            return True
        enable = not self.ctx._ring_link_enabled if mode == "toggle" else mode == "on"
        async_start(self.ctx._set_ring_link_enabled(enable))
        return True

    def _cmd_traplink(self, mode: str = "toggle") -> bool:
        """Turn Trap Link on or off for this session. /traplink [toggle|on|off|status]"""
        mode = mode.lower()
        if mode not in ("toggle", "on", "off", "status"):
            logger.warning("[SAC] Usage: /traplink [toggle|on|off|status]")
            return False
        if mode == "status":
            logger.info(f"[SAC] Trap Link is {'enabled' if self.ctx._trap_link_enabled else 'disabled'}.")
            return True
        enable = not self.ctx._trap_link_enabled if mode == "toggle" else mode == "on"
        async_start(self.ctx._set_trap_link_enabled(enable))
        return True

    def _cmd_deathlink_mode(self, mode: str) -> bool:
        """Turn DeathLink on or off for this session. /deathlink_mode [toggle|on|off|status]"""
        mode = mode.lower()
        if mode not in ("toggle", "on", "off", "status"):
            logger.warning("[SAC] Usage: /deathlink_mode [toggle|on|off|status]")
            return False
        if mode == "status":
            logger.info(f"[SAC] DeathLink is {'enabled' if self.ctx._death_link_enabled else 'disabled'}.")
            return True
        enable = not self.ctx._death_link_enabled if mode == "toggle" else mode == "on"
        async_start(self.ctx._set_death_link_enabled(enable))
        return True
