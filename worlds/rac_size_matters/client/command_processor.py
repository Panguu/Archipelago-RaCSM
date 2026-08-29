from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from CommonClient import logger

try:
    from worlds.tracker.TrackerClient import TrackerCommandProcessor as ClientCommandProcessor
except ImportError:
    from CommonClient import ClientCommandProcessor

if TYPE_CHECKING:
    from .context import RACContext


class RACCommandProcessor(ClientCommandProcessor):
    ctx: RACContext

    def _cmd_reconnect(self) -> bool:
        """Reconnect to PCSX2 and re-apply received Archipelago items."""
        asyncio.create_task(self.ctx.reconnect_pine())
        return True

    def _cmd_force_sync(self) -> bool:
        """Force the player's in-game state to match what was received from AP."""
        asyncio.create_task(self.ctx.force_sync())
        return True

    def _cmd_states(self) -> bool:
        """Print every active state."""
        w = self.ctx._wiring
        for state in (
            w.armour, w.bolts, w.player_bolts, w.planet_unlock, w.quick_select,
            w.clank, w.skyboard, w.shrink_ray, w.skill_points, w.missions, w.skin,
            w.planet, w.planet.weapons, w.planet.player, w.planet.menu,
            w.weapon_vendor, w.mod_vendor, w.vendor,
        ):
            logger.info(repr(state))
        return True

    def _cmd_rac5_info(self) -> bool:
        """Print the current slot options, then every active state's repr."""
        ctx = self.ctx
        options = "\n".join(f"{key}: {value}" for key, value in ctx.slot_data.items())
        logger.info(f"[RAC] Options:\n{options}")

        w = ctx._wiring
        states = (
            w.armour, w.bolts, w.player_bolts, w.planet_unlock, w.quick_select,
            w.clank, w.skyboard, w.shrink_ray, w.skill_points, w.missions, w.skin,
            w.planet, w.planet.weapons, w.planet.player, w.planet.menu,
            w.weapon_vendor, w.mod_vendor, w.vendor,
        )
        logger.info("[RAC] States: " + " ".join(repr(state) for state in states))
        return True

    def _cmd_vendor_refresh(self) -> bool:
        """Debug: force-rewrite the vendor item list immediately, without waiting for the next tick."""
        w = self.ctx._wiring
        w.vendor.force_refresh()
        logger.info(f"[RAC] {w.vendor!r}")
        return True

    def _cmd_spawn_ghost(self) -> bool:
        """Spawn a static ghost clone of Ratchet at his current position
        (only on planets with confirmed Ghost Ratchet addresses)."""
        w = self.ctx._wiring
        if w.spawn_ghost_ratchet():
            logger.info("[RAC] Ghost Ratchet spawned.")
        else:
            logger.info("[RAC] Ghost Ratchet isn't available on this planet yet.")
        return True

    def _cmd_debug(self) -> bool:
        """Toggle printing of state changes as they occur."""
        self.ctx._debug_messages = not self.ctx._debug_messages
        state = "enabled" if self.ctx._debug_messages else "disabled"
        logger.info(f"[RAC] Debug messages {state}.")
        return True

    def _cmd_enable_deathlink(self) -> bool:
        """Enable DeathLink for this session."""
        asyncio.create_task(self.ctx._set_death_link_enabled(True))
        return True

    def _cmd_disable_deathlink(self) -> bool:
        """Disable DeathLink for this session."""
        asyncio.create_task(self.ctx._set_death_link_enabled(False))
        return True

    def _cmd_enable_ammolink(self) -> bool:
        """Enable AmmoLink for this session."""
        asyncio.create_task(self.ctx._set_ammo_link_enabled(True))
        return True

    def _cmd_disable_ammolink(self) -> bool:
        """Disable AmmoLink for this session."""
        asyncio.create_task(self.ctx._set_ammo_link_enabled(False))
        return True

    def _cmd_enable_boltlink(self) -> bool:
        """Enable BoltLink for this session."""
        asyncio.create_task(self.ctx._set_bolt_link_enabled(True))
        return True

    def _cmd_disable_boltlink(self) -> bool:
        """Disable BoltLink for this session."""
        asyncio.create_task(self.ctx._set_bolt_link_enabled(False))
        return True

    def _cmd_enable_ghostlink(self) -> bool:
        """Enable GhostLink for this session."""
        asyncio.create_task(self.ctx._set_ghost_link_enabled(True))
        return True

    def _cmd_disable_ghostlink(self) -> bool:
        """Disable GhostLink for this session."""
        asyncio.create_task(self.ctx._set_ghost_link_enabled(False))
        return True

    def _cmd_ghost_link_interval(self, seconds: str = "") -> bool:
        """Override the ghost_link_update_interval YAML option for this session without regenerating.
        0 stops broadcasting your own position; no argument shows the current value."""
        if not seconds:
            logger.info(f"[RAC] GhostLink update interval: {self.ctx._ghost_link_interval}s")
            return True
        try:
            value = float(seconds)
        except ValueError:
            logger.warning(f"[RAC] Invalid interval {seconds!r} — must be a number of seconds.")
            return True
        if value < 0:
            logger.warning("[RAC] Interval can't be negative.")
            return True
        self.ctx._ghost_link_interval = value
        logger.info(f"[RAC] GhostLink update interval set to {value}s.")
        return True
