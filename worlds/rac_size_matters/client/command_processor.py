from typing import TYPE_CHECKING

from CommonClient import logger

from ..core.skins import Skin

try:
    from worlds.tracker.TrackerClient import TrackerCommandProcessor as ClientCommandProcessor
except ImportError:
    from CommonClient import ClientCommandProcessor

if TYPE_CHECKING:
    from .context import RACContext


class RACCommandProcessor(ClientCommandProcessor):
    """Parses commands here; anything touching the game runs as a cmd_* method in the PCSX2 worker."""

    ctx: "RACContext"

    def _cmd_reconnect(self) -> bool:
        """Reconnect to PCSX2 and re-apply received Archipelago items."""
        self.ctx.call_worker("cmd_reconnect")
        return True

    def _cmd_force_sync(self) -> bool:
        """Force the player's in-game state to match what was received from AP."""
        self.ctx.call_worker("cmd_force_sync")
        return True

    def _cmd_states(self) -> bool:
        """Print every active state."""
        self.ctx.call_worker("cmd_states")
        return True

    def _cmd_rac5_info(self) -> bool:
        """Print the current slot options, then every active state's repr."""
        self.ctx.call_worker("cmd_rac5_info")
        return True

    def _cmd_goal(self) -> bool:
        """Show completion of selected goals and the completed/total count for Pick and Mix."""
        self.ctx.call_worker("cmd_goal")
        return True

    def _cmd_vendor_refresh(self) -> bool:
        """Debug: force-rewrite the vendor item list immediately, without waiting for the next tick."""
        self.ctx.call_worker("cmd_vendor_refresh")
        return True

    def _cmd_skin(self, skin: str = "") -> bool:
        """Set a skin directly: /skin trash, /skin tuxedo, or an id 0-19."""
        names = {s.name.lower(): s for s in Skin}
        names.update({s.name.lower().removesuffix("_ratchet"): s for s in Skin})
        names.update({str(s.equip_id): s for s in Skin})
        selected = names.get(skin.lower().replace("-", "_").replace(" ", "_"))
        if selected is None:
            logger.info("[RAC] /skin default|pirate|trash|tuxedo|qwark|ninja (or 0-19). "
                        "Kangaroo and Tuxedo Ratchet include their secondary texture.")
            return False
        self.ctx.call_worker("cmd_skin", selected)
        return True

    def _cmd_skin_patch(self, state: str = "") -> bool:
        """Enable or disable the skin patch, including multiplayer skins: /skin_patch on|off.
        Reloads the current planet. Disabling equips Ratchet's default skin; item toasts and
        the connection warning share the skin hook, so they stop too while it is off."""
        choices = {"on": True, "enable": True, "off": False, "disable": False}
        state = state.lower().strip()
        if state and state not in choices:
            logger.info("[RAC] Use /skin_patch on|off.")
            return False
        self.ctx.call_worker("cmd_skin_patch", choices.get(state))
        return True

    def _cmd_apicon(self, style: str = "") -> bool:
        """Choose which Archipelago icon shows on vendor items: /apicon original (default), purple, blue, grey.
        No argument prints the current style. Applies next time a vendor item's icon is assigned."""
        self.ctx.call_worker("cmd_apicon", style.lower().strip())
        return True

    def _cmd_spawn_ghost(self) -> bool:
        """Spawn a static ghost clone of Ratchet at his current position
        (only on planets with confirmed Ghost Ratchet addresses)."""
        self.ctx.call_worker("cmd_spawn_ghost")
        return True

    def _cmd_debug(self) -> bool:
        """Toggle printing of state changes as they occur."""
        self.ctx.call_worker("cmd_debug")
        return True

    def _link_command(self, link: str, state: str) -> bool:
        state = state.strip().lower()
        if state not in ("", "on", "off", "toggle"):
            logger.info(f"[RAC] Use /{link} [on|off|toggle]; no argument shows status.")
            return False
        self.ctx.call_worker("cmd_link", link, state)
        return True

    def _cmd_deathlink(self, state: str = "") -> bool:
        """/deathlink [on|off|toggle]. No argument shows current status."""
        return self._link_command("deathlink", state)

    def _cmd_ammolink(self, state: str = "") -> bool:
        """/ammolink [on|off|toggle]. No argument shows current status."""
        return self._link_command("ammolink", state)

    def _cmd_ringlink(self, state: str = "") -> bool:
        """/ringlink [on|off|toggle]. No argument shows current status."""
        return self._link_command("ringlink", state)

    def _cmd_traplink(self, state: str = "") -> bool:
        """/traplink [on|off|toggle]. No argument shows current status."""
        return self._link_command("traplink", state)

    def _cmd_ghostlink(self, state: str = "") -> bool:
        """/ghostlink [on|off|toggle]. No argument shows current status."""
        return self._link_command("ghostlink", state)
