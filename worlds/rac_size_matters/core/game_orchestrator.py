from __future__ import annotations

import asyncio
import threading
import time
from collections.abc import Callable
from typing import Any

from CommonClient import logger

from ..interface_orchestrator import Orchestrator
from ..pypine.pypine.pine import Pine
from .address_maps import (
    CURRENT_PLANET_ADDRESS,
    MENU_ADDR_BY_PLANET_ID,
    PLAYER_ADDRS,
    WEAPON_ARRAY_BASE_BY_PLANET,
)
from .address_maps.global_map import build_global_address_map
from .address_maps.planet_map import build_planet_address_map
from .armour import ArmourSetCollectedState, ArmourState
from .challenges import ClankChallengeState, SkyboardChallengeState
from .display_text import DisplayedTextBoxState, DisplayTextBoxState, SmallTextBoxAddrs
from .memory.pine_interface import PineInterface
from .menu import MenuState
from .missions import MissionsState
from .planets import Planet, Planets, PlanetState, PlanetUnlockState
from .player import PlayerState
from .quick_select import QuickSelectState
from .skill_points import SkillPointState
from .skins import SkinState
from .structs.game import TRANSITION_GATE_IDLE, TransitionGateStruct
from .titanium_bolts import TitaniumBoltState
from .vendor import ModVendorState, VendorUnlockState, WeaponVendorState
from .weapons import WeaponState

_TEXT_BOX_BY_PLANET = {tb.planet_id: tb for tb in SmallTextBoxAddrs}

POLL_INTERVAL: float = 0.1

# Quick select is re-applied on this cadence as a failsafe, independent of the
# event-driven apply() calls in _guarded_reapply.
QUICK_SELECT_WRITE_INTERVAL_S: float = 5.0

# How often _poll_loop re-validates PCSX2 is still running the expected game.
# Without this, swapping discs/games in PCSX2 mid-session (without closing
# the emulator) leaves the socket open and this loop keeps reading our fixed
# addresses out of whatever game is now loaded, silently misreporting its
# memory as Size Matters state changes instead of disconnecting.
GAME_ID_CHECK_INTERVAL_S: float = 2.0

# Outpost Omega (both visits) has its own quick-select/skyboard logic to follow,
# so the periodic write never runs there at all.
_OUTPOST_OMEGA_1_ID: int = 0x06

PLANET_NAMES: dict[int, str] = {
    p.planet_id: p.name
    for p in vars(Planets).values()
    if isinstance(p, Planet)
}

_OUTPOST_OMEGA_IDS: frozenset[int] = frozenset({_OUTPOST_OMEGA_1_ID, Planets.OUTPOST_OMEGA_2.planet_id})

# Mixins import PLANET_NAMES / POLL_INTERVAL from this module, so they must be
# imported only after those names are defined above.
from .orchestration._ap_sync import APSyncMixin
from .orchestration._hooks import HooksMixin
from .orchestration._planet_lifecycle import PlanetLifecycleMixin


class GameOrchestrator(APSyncMixin, PlanetLifecycleMixin, HooksMixin):

    def __init__(
        self, pine: Pine, log: Callable[[str], None] | None = None,
        expected_game_id: str | None = None,
        on_wrong_game: Callable[[str], None] | None = None,
    ) -> None:
        self._pine       = pine
        self._pine_iface = PineInterface(pine)
        self._global_map = build_global_address_map()
        self._log        = log or logger.info
        self._expected_game_id = expected_game_id
        self._on_wrong_game: Callable[[str], None] = on_wrong_game or (lambda _: None)
        self._last_game_id_check: float = 0.0

        # Guards the vendor weapon/gadget/mod memory region against a race
        # between this orchestrator's poll loop (preload/open/close zero+
        # restore writes) and the client's _apply_player_inventory_sync,
        # which runs on a separate executor thread. Both write the same
        # addresses; without this, an in-flight AP-ownership write can land
        # after a vendor-state zero, re-showing a mod that wasn't purchased
        # at this vendor.
        self.vendor_write_lock = threading.Lock()

        self._orchestrator = Orchestrator(
            self._pine_iface, self._global_map, poll_rate=POLL_INTERVAL
        )
        acc     = self._orchestrator.accessor
        storage = self._orchestrator.storage

        self.armour             = ArmourState(acc, self._global_map, storage)
        self.armour_sets        = ArmourSetCollectedState(acc, self._global_map, storage)
        self.bolts              = TitaniumBoltState(acc, self._global_map, storage)
        self.skill_points       = SkillPointState(acc, self._global_map, storage, log=self._log)
        self.planet_unlock      = PlanetUnlockState(acc, self._global_map, storage)
        self.quick_select       = QuickSelectState(acc, self._global_map, storage)
        self.clank              = ClankChallengeState(acc, self._global_map, storage)
        self.skyboard           = SkyboardChallengeState(acc, self._global_map, storage)
        self.weapons            = WeaponState(acc, self._global_map, storage, log=self._log)
        self.vendor_unlock      = VendorUnlockState(self.weapons, self.planet_unlock)
        self.skin               = SkinState()
        self.player             = PlayerState(acc, self._global_map, storage)
        self.menu               = MenuState(acc, self._global_map, storage, log=self._log)
        self.weapon_vendor      = WeaponVendorState(acc, self._global_map, storage)
        self.mod_vendor         = ModVendorState(acc, self._global_map, storage)
        self.display_text       = DisplayTextBoxState(acc, self._global_map, storage)
        self.displayed_text_box = DisplayedTextBoxState(acc, self._global_map, storage)
        self.missions           = MissionsState(acc, self._global_map, storage)

        self._send_location:      Callable[[str], None]  = lambda _: None
        self._send_deathlink:     Callable[[int], None]  = lambda _: None
        self._kill_player:        Callable[[], None]     = lambda: None
        self._reapply_inv:        Callable[[], None]     = lambda: None
        self._death_amnesty:      Callable[[], int]      = lambda: 1
        self._death_link_enabled: Callable[[], bool]     = lambda: False
        self._on_goal:            Callable[[], None]     = lambda: None
        self._on_vendor_open:     Callable[[], None]     = lambda: None
        self._on_vendor_close:    Callable[[], None]     = lambda: None
        self._on_pause_close:     Callable[[], None]     = lambda: None
        self._on_bonus_weapon_pickup: Callable[[str], None] = lambda _: None

        self.planet_states: dict[int, PlanetState] = self._build_planet_states(acc, storage)

        state_registry: dict[str, Any] = {
            "armour":             self.armour,
            "armour_sets":        self.armour_sets,
            "bolts":              self.bolts,
            "skill_points":       self.skill_points,
            "planet_unlock":      self.planet_unlock,
            "quick_select":       self.quick_select,
            "clank":              self.clank,
            "skyboard":           self.skyboard,
            "weapons":            self.weapons,
            "player":             self.player,
            "menu":               self.menu,
            "weapon_vendor":      self.weapon_vendor,
            "mod_vendor":         self.mod_vendor,
            "display_text":       self.display_text,
            "displayed_text_box": self.displayed_text_box,
            "missions":           self.missions,
        }
        for pid, ps in self.planet_states.items():
            state_registry[f"planet_{pid:#04x}"] = ps
        self._orchestrator.register_states(state_registry)

        for state in (
            self.armour, self.armour_sets, self.bolts, self.skill_points, self.planet_unlock,
            self.quick_select, self.clank, self.skyboard, self.weapons, self.player,
            self.menu, self.weapon_vendor, self.mod_vendor, self.display_text, self.displayed_text_box,
            self.missions,
        ):
            state.enter()
        for ps in self.planet_states.values():
            ps.enter()

        self._poll_task: asyncio.Task | None      = None
        self._swap_task: asyncio.Task | None      = None
        self._active_planet_id: int               = 0
        self._checked_locations: set[str]         = set()
        self._initial_load_done: bool             = False
        self._first_swap_done: bool               = False
        self._death_count: int                    = 0
        self._transitioning: bool                 = False
        self._gate_value: int                     = TRANSITION_GATE_IDLE
        self._gate_pending_planet_id: int         = 0
        self._last_gate_debug: float              = 0.0
        self._pickup_detection_active: bool       = False
        self._last_quick_select_write: float      = 0.0

    def wire(
        self,
        send_location:      Callable[[str], None],
        send_deathlink:     Callable[[int], None],
        kill_player:        Callable[[], None],
        reapply_inv:        Callable[[], None],
        death_amnesty:      Callable[[], int],
        death_link_enabled: Callable[[], bool] = lambda: False,
        on_goal:            Callable[[], None]  = lambda: None,
        on_vendor_open:     Callable[[], None]  = lambda: None,
        on_vendor_close:    Callable[[], None]  = lambda: None,
        on_pause_close:     Callable[[], None]  = lambda: None,
        on_bonus_weapon_pickup: Callable[[str], None] = lambda _: None,
    ) -> None:
        self._send_location      = lambda name: send_location(name) if self._initial_load_done else None
        self._send_deathlink     = send_deathlink
        self._kill_player        = kill_player
        self._death_amnesty      = death_amnesty
        self._death_link_enabled = death_link_enabled
        self._on_goal            = on_goal
        self._on_vendor_open     = on_vendor_open
        self._on_vendor_close    = on_vendor_close
        self._on_pause_close     = on_pause_close
        self._on_bonus_weapon_pickup = on_bonus_weapon_pickup

        _raw_reapply = reapply_inv

        def _guarded_reapply() -> None:
            # writes_blocked only matters for planet-specific addresses (weapons/
            # gadgets), which _raw_reapply already gates internally. Quick select
            # and vendor unlock are global addresses, safe at any time.
            if self.is_picking_up:
                return
            _raw_reapply()
            self.quick_select.apply()
            if not self.vendor_active:
                self.vendor_unlock.apply(self._orchestrator.accessor)

        self._reapply_inv = _guarded_reapply
        self._wire_hooks()

    async def start(self) -> None:
        self.planet_unlock.sync()
        try:
            raw = self._orchestrator.accessor.read_raw(CURRENT_PLANET_ADDRESS, 1)
            self._active_planet_id = raw[0] if raw else 0
        except Exception:
            self._active_planet_id = 0

        try:
            gate_raw = self._orchestrator.accessor.read_raw(TransitionGateStruct.BASE_ADDRESS, 4)
            self._gate_value = (
                int.from_bytes(gate_raw, "little") if gate_raw and len(gate_raw) >= 4 else TRANSITION_GATE_IDLE
            )
        except Exception:
            self._gate_value = TRANSITION_GATE_IDLE
        self._register_transition_gate()

        if self._active_planet_id in self.planet_states:
            self._log(
                f"[RAC] Connection on {PLANET_NAMES.get(self._active_planet_id, hex(self._active_planet_id))} "
                f"-- zeroing quick select and triggering planet_enter immediately."
            )
            self.quick_select.zero()
            self.planet_states[self._active_planet_id].planet_enter()
        # else: not on a known planet yet — _on_initial_planet_load() zeroes
        # quick select itself on the first transition into one.

        self._poll_task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        if self._poll_task:
            self._poll_task.cancel()
            self._poll_task = None
        if self._swap_task:
            self._swap_task.cancel()
            self._swap_task = None

        for state in (
            self.armour, self.armour_sets, self.bolts, self.skill_points, self.planet_unlock,
            self.quick_select, self.clank, self.skyboard, self.weapons, self.player,
            self.menu, self.weapon_vendor, self.mod_vendor, self.display_text, self.displayed_text_box,
            self.missions,
        ):
            state.exit()
        for ps in self.planet_states.values():
            ps.exit()

        self._initial_load_done      = False
        self._first_swap_done        = False
        self._transitioning          = False
        self._gate_value              = TRANSITION_GATE_IDLE
        self._gate_pending_planet_id  = 0
        self.planet_unlock.reset_session()

    # -- Properties -----------------------------------------------------------

    @property
    def vendor_active(self) -> bool:
        return self.weapon_vendor.active or self.mod_vendor.active

    @property
    def is_picking_up(self) -> bool:
        return self.player.is_picking_up or self._pickup_detection_active

    @property
    def is_transitioning(self) -> bool:
        return self._transitioning

    @property
    def is_in_menu(self) -> bool:
        from .menu import MenuStateValue
        return self.menu.current != MenuStateValue.CLOSED

    @property
    def writes_blocked(self) -> bool:
        """True while mid-transition, per the 0x1EDDAD4 transition gate."""
        return self._transitioning

    # -- Poll loop ------------------------------------------------------------

    async def _poll_loop(self) -> None:
        # Stays on the event loop thread intentionally — poll()'s callback
        # chain (transition gate -> planet_enter -> _on_planet_enter, etc.)
        # calls asyncio.create_task() synchronously and assumes it's running
        # on the event loop thread. Moving this to run_in_executor breaks
        # that with "RuntimeError: no running event loop". The GUI freeze
        # this used to cause was actually the duplicate-Pine-object bug
        # (two sockets fighting over one PCSX2 slot) — see Pine.rebind.
        while True:
            try:
                if self._maybe_check_wrong_game():
                    return
                self._orchestrator.poll()
                self._maybe_apply_quick_select()
                self._debug_print_transition_gate()
            except Exception as exc:
                logger.warning(f"[RAC] Poll error: {exc}")
            await asyncio.sleep(POLL_INTERVAL)

    def _maybe_check_wrong_game(self) -> bool:
        """Throttled re-check that PCSX2 is still running the expected game.

        Returns True (and fires on_wrong_game) if it isn't, so the caller can
        stop polling instead of continuing to read another game's memory.
        """
        if self._expected_game_id is None:
            return False
        now = time.monotonic()
        if now - self._last_game_id_check < GAME_ID_CHECK_INTERVAL_S:
            return False
        self._last_game_id_check = now
        try:
            game_id = self._pine.get_game_id()
        except Exception:
            return False
        if game_id == self._expected_game_id:
            return False
        self._on_wrong_game(game_id)
        return True

    def _maybe_apply_quick_select(self) -> None:
        """Periodic failsafe re-write of the quick select snapshot.

        Skips entirely on Outpost Omega (own logic to follow) or an unknown
        planet, and defers while picking up an item, the purchase vendor is
        open, or the player has the Quick Select pause-menu tab open (writing
        now would fight their live edits). Quick select is a global address,
        so it isn't gated by writes_blocked (that only matters for
        planet-specific addresses).
        """
        if self._active_planet_id in _OUTPOST_OMEGA_IDS:
            return
        if self._active_planet_id not in PLANET_NAMES:
            return
        if self.is_picking_up:
            return
        if self.menu.is_vendor or self.menu.is_quick_select_menu:
            return
        now = time.monotonic()
        if now - self._last_quick_select_write < QUICK_SELECT_WRITE_INTERVAL_S:
            return
        self._last_quick_select_write = now
        self.quick_select.apply()

    # -- Planet state builder -------------------------------------------------

    def _build_planet_states(self, acc, storage) -> dict[int, PlanetState]:
        states: dict[int, PlanetState] = {}
        for planet_id in PLAYER_ADDRS:
            name       = PLANET_NAMES.get(planet_id, f"Planet {planet_id:#04x}")
            planet_map = build_planet_address_map(planet_id)

            ps = PlanetState(
                accessor=acc,
                addresses=planet_map,
                storage=storage,
                name=name,
                planet_id=planet_id,
                menu_addr=MENU_ADDR_BY_PLANET_ID.get(planet_id),
                log=self._log,
            )

            ps.add_enter_callback(lambda pid=planet_id: self._on_planet_enter(pid))
            ps.add_exit_callback(lambda pid=planet_id: self._on_planet_exit(pid))
            ps.set_armour(self.armour)
            ps.set_player_state(self.player)
            ps.set_vendor_write_lock(self.vendor_write_lock)

            if planet_id in WEAPON_ARRAY_BASE_BY_PLANET:
                ps.set_weapon_state(self.weapons)

            if planet_id in MENU_ADDR_BY_PLANET_ID:
                ps.set_menu_state(self.menu, self.weapon_vendor, self.mod_vendor)
                ps.set_vendor_unlock(self.vendor_unlock)

            tb = _TEXT_BOX_BY_PLANET.get(planet_id)
            if tb:
                ps.set_display_text_box(self.display_text, tb)
                ps.set_displayed_text_box(self.displayed_text_box)

            ps.set_inventory_callbacks(
                reapply_inv           = lambda: self._reapply_inv(),
                get_checked_locations = lambda: self._checked_locations,
            )
            states[planet_id] = ps
        return states

    def _current_planet_id(self) -> int:
        return self._active_planet_id
