import asyncio
import time

from CommonClient import logger

from ..constants import Rac5Traps
from ..constants.options import Rac5Options
from ..core.traps import ALL_TRAPS, activate_trap, traps_ready

# Use interoperable names on the wire while retaining native AP item names.
TRAP_LINK_NAMES = {
    Rac5Traps.TRAP_REVERSE_CONTROLS: "Confusion Trap",
    Rac5Traps.TRAP_MIRROR_LEVEL: "Mirror Trap",
    Rac5Traps.TRAP_FEVERDREAMTIME: "Fuzzy Trap",
    Rac5Traps.TRAP_WEAPON_SWITCHING: "Tool Swap Trap",
    Rac5Traps.TRAP_BRIGHTNESS: "Invert Colors Trap",
    Rac5Traps.TRAP_RESET_LEVEL: "Teleport Trap",
    Rac5Traps.TRAP_NO_CLANK: "No Clank Trap",
    Rac5Traps.TRAP_GADGETRON_DEBT: "Gadgetron Debt Trap",
    Rac5Traps.TRAP_DROPPED_AMMO: "Dropped Ammo Trap",
}
TRAP_LINK_ALIASES = {name: name for name in ALL_TRAPS}
TRAP_LINK_ALIASES.update({wire: native for native, wire in TRAP_LINK_NAMES.items()})
TRAP_LINK_ALIASES.update({
    "Reverse Controls Trap": Rac5Traps.TRAP_REVERSE_CONTROLS,
    "Bolt Confusion Trap": Rac5Traps.TRAP_REVERSE_CONTROLS,
    "Flip Horizontal Trap": Rac5Traps.TRAP_MIRROR_LEVEL,
    "Gadget Shuffle Trap": Rac5Traps.TRAP_WEAPON_SWITCHING,
})


class TrapLinkMixin:
    async def _set_trap_link_enabled(self, enabled: bool) -> None:
        self._trap_link_enabled = enabled
        await self._update_link_tag("TrapLink", enabled)
        self._log(f"[RAC] TrapLink {'enabled' if enabled else 'disabled'}.")

    def _send_trap_link(self, item_name: str) -> None:
        if not self._trap_link_enabled or not self.ap_connected or not self.auth:
            return
        asyncio.create_task(self.send_msgs([{
            "cmd": "Bounce", "tags": ["TrapLink"],
            "data": {"time": time.time(), "source": self.auth, "trap_name": TRAP_LINK_NAMES[item_name]},
        }]))

    async def _receive_trap_link(self, data: dict) -> None:
        source, timestamp, name = data.get("source"), data.get("time"), data.get("trap_name")
        if (not self._trap_link_enabled or not self.ap_connected or not isinstance(source, str)
                or source == self.auth or type(timestamp) not in (int, float) or not isinstance(name, str)):
            return
        native = TRAP_LINK_ALIASES.get(name)
        if native is None or self.slot_data.get(Rac5Options.TRAP_WEIGHT, {}).get(native, 1) <= 0:
            return
        async with self._pine_lock:
            if not self.pine_connected or not traps_ready(self.pine):
                return
            key = (source, timestamp, name)
            if key in self._trap_link_seen:
                return
            if len(self._trap_link_seen) >= 1024:
                self._trap_link_seen.clear()
            self._trap_link_seen.add(key)
            # Deliberately bypass the AP item receive/send path: no bounce loops.
            if native == Rac5Traps.TRAP_DROPPED_AMMO:
                activate_trap(self.pine, native, weapons=self._wiring.planet.weapons)
            elif native == Rac5Traps.TRAP_GADGETRON_DEBT:
                before = self._wiring.player_bolts.get()
                activate_trap(self.pine, native, debt_percent=self.slot_data.get(
                    Rac5Options.GADGETRON_DEBT_PERCENT, 20))
            else:
                activate_trap(self.pine, native)
            if native == Rac5Traps.TRAP_GADGETRON_DEBT:
                after = self._wiring.player_bolts.get()
                self._wiring.player_bolts.rebaseline(after)
                logger.info(f"[RAC] Gadgetron Debt Trap: -{before - after:,} bolts ({after:,} remaining).")
