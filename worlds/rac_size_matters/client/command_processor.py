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
        ctx = self.ctx
        w = ctx._wiring
        for state in (
            w.armour, w.armour_sets, w.bolts, w.planet_unlock, w.quick_select,
            w.clank, w.skyboard, w.weapons, w.player, w.menu, w.weapon_vendor, w.mod_vendor,
            w.display_text, w.displayed_text_box, w.missions,
        ):
            logger.info(repr(state))
        for state in (
            ctx._planet_state, ctx._armour_pickup_state, ctx._player_armour_state,
            ctx._armour_slot_state, ctx._player_weapon_state, ctx._player_gadget_state,
            ctx._titanium_bolt_state,
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
            w.armour, w.armour_sets, w.bolts, w.planet_unlock, w.quick_select,
            w.clank, w.skyboard, w.weapons, w.player, w.menu, w.weapon_vendor, w.mod_vendor,
            w.display_text, w.displayed_text_box, w.missions,
            ctx._planet_state, ctx._armour_pickup_state, ctx._player_armour_state,
            ctx._armour_slot_state, ctx._player_weapon_state, ctx._player_gadget_state,
            ctx._titanium_bolt_state,
        )
        logger.info("[RAC] States: " + " ".join(repr(state) for state in states))
        return True

    def _cmd_debug(self) -> bool:
        """Toggle printing of state changes as they occur."""
        self.ctx._debug_messages = not self.ctx._debug_messages
        state = "enabled" if self.ctx._debug_messages else "disabled"
        logger.info(f"[RAC] Debug messages {state}.")
        return True

    def _cmd_debug_buttons(self) -> bool:
        """Toggle printing of the controller button state whenever it changes."""
        wiring = self.ctx._wiring
        enabled = not wiring._debug_buttons_enabled
        wiring.set_debug_buttons(enabled)
        state = "enabled" if enabled else "disabled"
        logger.info(f"[RAC] Button debug logging {state}.")
        return True
