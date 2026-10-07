from typing import TYPE_CHECKING

from CommonClient import logger
from Utils import async_start

try:
    from worlds.tracker.TrackerClient import TrackerCommandProcessor as ClientCommandProcessor
except ImportError:
    from CommonClient import ClientCommandProcessor

from ..constants.planets import ALL_CASES, Case

if TYPE_CHECKING:
    from .context import SACContext


class SACCommandProcessor(ClientCommandProcessor):
    ctx: "SACContext"

    def _match_case(self, case: str) -> "Case | None":
        """Case-insensitive substring match against every known case name."""
        matches = [c for c in ALL_CASES if case.lower() in c.name.lower()]
        if not matches:
            logger.warning(f"[SAC] No case matches {case!r}.")
            return None
        if len(matches) > 1:
            logger.warning(f"[SAC] {case!r} matches multiple cases: " + ", ".join(c.name for c in matches))
            return None
        return matches[0]

    def _resolve_case_id(self, case: str, command: str) -> "int | None":
        """The named case's id, or the current one when no name is given; warns and returns None if unknown."""
        if case:
            match = self._match_case(case)
            return match.case_id if match is not None else None
        if self.ctx._game_state.get("case_id") is None:
            logger.warning(f"[SAC] No current case known -- pass a case name to anchor off, e.g. /{command} museum.")
        return self.ctx._game_state.get("case_id")

    def _cmd_reconnect(self) -> bool:
        """Reconnect to PCSX2 and re-apply received Archipelago items."""
        async_start(self.ctx.reconnect_pine())
        return True

    def _cmd_native_locations(self, mode: str = "on") -> bool:
        """Native interception is mandatory; /native_locations off is rejected."""
        if mode.lower() not in ("on", "off"):
            logger.warning("[SAC] Usage: /native_locations on|off")
            return False

        async_start(self._worker_command("native_locations", mode.lower() == "on"))
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
        async_start(self._worker_command("diagnostic", ("sac_info", None)))
        return True

    def _cmd_mission_table(self) -> bool:
        """Print native mission-table rows from the game worker."""
        async_start(self._worker_command("diagnostic", ("mission_table", None)))
        return True

    def _cmd_ratchet_nanotech(self) -> bool:
        """Read Ratchet XP, Nanotech, native caps and HUD health."""
        async_start(self._worker_command("diagnostic", ("ratchet_nanotech", None)))
        return True

    def _cmd_case_states(self, case: str = "") -> bool:
        """Read the case states through the single game connection."""
        case_id = self._resolve_case_id(case, "case_states")
        if case_id is not None:
            async_start(self._worker_command("diagnostic", ("case_states", case_id)))
        return True

    def _cmd_case_struct(self, case: str = "") -> bool:
        """Read the raw case-unlock slots through the game worker."""
        case_id = self._resolve_case_id(case, "case_struct")
        if case_id is not None:
            async_start(self._worker_command("diagnostic", ("case_struct", case_id)))
        return True

    def _cmd_enable_deathlink(self) -> bool:
        """Enable DeathLink for this session."""
        async_start(self.ctx._set_death_link_enabled(True))
        return True

    def _cmd_disable_deathlink(self) -> bool:
        """Disable DeathLink for this session."""
        async_start(self.ctx._set_death_link_enabled(False))
        return True
