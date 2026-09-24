"""Read native checks before applying the received AP inventory."""
import logging
from collections.abc import Callable, Sequence

from ..constants.clank_gadgets import SACClankGadgets
from ..constants.missions import CHAPTER_ENTRIES
from ..constants.operatives import SACOperatives
from ..constants.planets import CASE_ID_TO_CASE, CASES_BY_OPERATIVE, SACCases
from ..constants.weapons import CLANK_PICKUP_TO_INTERNAL, EQUIPMENT_INTERNAL_TO_DISPLAY
from .address_maps import BOLTS_ADDRESS, CHALLENGE_MODE_ADDRESS
from .bolt_rewards import BoltRewards
from .inventories.alien_codes import AlienCodeInventory
from .inventories.case_struct import CaseStructInventory
from .inventories.case_unlocks import CaseUnlockInventory, resolve_owned_cases
from .inventories.cutscenes import CutsceneInventory
from .inventories.gadgetbot_challenges import GadgetbotChallengeInventory
from .inventories.keycards import KeycardInventory
from .inventories.missions import MissionInventory
from .inventories.planets import CaseInventory
from .inventories.ratchet_challenges import RatchetChallengeInventory
from .inventories.special_challenges import SpecialChallengeInventory
from .inventories.weapons import WEAPON_ORDER
from .main_menu import MainMenuNotice
from .native_runtime import NativeRuntime
from .notifications import ItemNotifications
from .patches import MARKER, PICKUP_LOCATIONS, VENDOR_LOCATIONS, LocationHooks
from .patches.progression import Progression
from .patches.weapon_mods import WeaponMods
from .patches.wrench import PROGRESSIVE_WRENCH, WrenchProgression
from .quick_select import QuickSelectState
from .skill_points import SkillPointState
from .titanium_bolts import TitaniumBoltState
from .traps import Traps
from .vendor_rewards import VendorRewards

logger = logging.getLogger("CommonClient")



class Core:

    def __init__(self, pine, log: Callable[[str], None] | None = None) -> None:
        self.pine = pine
        self._log = log or logger.info
        self.main_menu = MainMenuNotice(pine, self._log)
        self.bolt_rewards = BoltRewards(pine, self._log)
        self.notifications = ItemNotifications(pine)
        self.traps = Traps(pine)

        self.case = CaseInventory(pine)
        self.case.on_transition_start = self._invalidate_level
        self.case.on_death            = self._handle_death
        self.case.on_respawn          = self._handle_respawn

        self.case_unlocks  = CaseUnlockInventory(pine)
        self.case_struct   = CaseStructInventory(pine)
        # Owned by self.case (CaseInventory) -- its address is derived from
        # weapon_array and rebound every case transition alongside
        # ratchet_items/clank_items, see core/planets.py's set_case() and
        # core/address_maps/ps2.py's VENDOR_SCREEN_STATE_OFFSET. Aliased
        # here so existing call sites (e.g. client/command_processor.py's
        # `w.vendor`) don't need to change.
        self.vendor        = self.case.vendor
        self.location_hooks = LocationHooks(pine)
        self.native_runtime = NativeRuntime(pine, self.location_hooks, self._log)
        self.vendor_rewards = VendorRewards(pine, self.vendor, self._log)
        self.native_runtime.presentation = self.vendor_rewards.text
        self.wrench = WrenchProgression(pine)
        self.native_runtime.wrench = self.wrench
        self.progression = Progression(pine)
        self.native_runtime.progression = self.progression
        self.weapon_mods = WeaponMods(pine)
        self.native_runtime.weapon_mods = self.weapon_mods
        self._native_locations_enabled = True
        self._native_pause_notice = False
        self.missions      = MissionInventory(pine)
        self.cutscenes      = CutsceneInventory(pine)
        self.gadgetbot_challenges = GadgetbotChallengeInventory(pine)
        self.special_challenges   = SpecialChallengeInventory(pine)
        self.ratchet_challenges   = RatchetChallengeInventory(pine)
        self.titanium_bolts = TitaniumBoltState(pine)
        self.skill_points   = SkillPointState(pine)
        self.alien_codes    = AlienCodeInventory(pine)
        self.keycards = KeycardInventory(pine)
        self.goal = 0
        self.character_unlocks = False
        self.progressive_planets: list[str] | None = None
        self._goal_sent = False
        self.quick_select   = QuickSelectState(pine)

        # True AP ownership per character, as of the last apply_inventory()
        # call -- kept so _reapply_all_inventories() (fired from
        # on_respawn/became_ready) always has an up-to-date answer without
        # needing its own copy passed in each time.
        self._ap_owned: dict[str, dict[str, bool]] = {"ratchet": {}, "clank": {}}
        # Case names owned via AP, as of the last apply_inventory() call --
        # same reasoning as _ap_owned above, kept so tick() can pass it to
        # missions.enforce_owned_first_missions() every tick without
        # needing its own copy of received_names.
        self._owned_cases: set[str] = set()
        self._inventory_initialized = False
        self._checked_items: set[str] = set()

        # Returns whether `name` was actually a location in this seed and
        # got queued -- tick() below only confirm()s a detector's find
        # (stopping it from being re-reported) when this returns True, so
        # a rejected name (wrong options, or server_locations not
        # populated yet right after connecting) is retried next tick
        # instead of silently dropped forever. Defaults to "nothing sent"
        # rather than "always accepted" for the same reason.
        self.send_location:      Callable[[str], bool] = lambda _: False
        self.send_deathlink:     Callable[[int], None]  = lambda _: None
        self.death_amnesty:      Callable[[], int]      = lambda: 1
        self.death_link_enabled: Callable[[], bool]     = lambda: False
        self.on_goal:            Callable[[], None]     = lambda: None
        # Fired once, the tick a case transition completes.
        self.on_case_ready:      Callable[[], None]     = lambda: None
        # options.py's Missions -- False (the option's own default) means
        # level_completion granularity, True means all. Read by
        # missions.check() every tick (see below).
        self.missions_all:       Callable[[], bool]     = lambda: False
        self._death_count: int = 0

    def wire(
        self,
        send_location:      Callable[[str], bool],
        send_deathlink:      Callable[[int], None]  | None = None,
        death_amnesty:       Callable[[], int]       | None = None,
        death_link_enabled:  Callable[[], bool]      | None = None,
        on_goal:             Callable[[], None]      | None = None,
        on_case_ready:       Callable[[], None]      | None = None,
        missions_all:        Callable[[], bool]      | None = None,
        on_bolt_state_changed: Callable[[dict, "dict | None"], None] | None = None,
    ) -> None:
        self.send_location = send_location
        if send_deathlink is not None:
            self.send_deathlink = send_deathlink
        if death_amnesty is not None:
            self.death_amnesty = death_amnesty
        if death_link_enabled is not None:
            self.death_link_enabled = death_link_enabled
        if on_goal is not None:
            self.on_goal = on_goal
        if on_case_ready is not None:
            self.on_case_ready = on_case_ready
        if missions_all is not None:
            self.missions_all = missions_all
        if on_bolt_state_changed is not None:
            self.bolt_rewards.on_state_changed = on_bolt_state_changed

    # -- AP inventory application ---------------------------------------------

    def apply_inventory(
        self, *, ratchet: dict[str, bool], clank: dict[str, bool], received_names: Sequence[str] = (),
    ) -> None:
        """Cache received items."""
        self._inventory_initialized = True
        self.progression.receive(received_names)
        self.weapon_mods.received = set(received_names)
        self.wrench.count = min(5, list(received_names).count(PROGRESSIVE_WRENCH))
        self.bolt_rewards.received = list(received_names).count("Bolts")
        self._ap_owned = {"ratchet": dict(ratchet), "clank": dict(clank)}
        # Pure function of received_names alone -- no pine/game-state
        # dependency, so compute (and cache for tick()'s
        # enforce_owned_first_missions() call) regardless of is_ready,
        # same as _ap_owned above.
        self._owned_cases = resolve_owned_cases(list(received_names), character_unlocks=self.character_unlocks,
                                                progressive_planets=self.progressive_planets)
        self.native_runtime.owned_cases = frozenset(self._owned_cases)

    def _invalidate_level(self) -> None:
        self.traps.last_tick = None
        self.vendor_rewards.invalidate()
        # The old module may already have been freed when its case id changes.
        # Invalidate cached addresses without writing through the old bindings.
        self.missions.invalidate_resolved_addresses()
        self.missions.table_base = None
        self.notifications.binding = None
        self.alien_codes.valid = False
        self.ratchet_challenges.invalidate()
        self.titanium_bolts.valid = False
        self.keycards.flags.pointer_address = None
        self.keycards.root_pointer = None
        self._native_pause_notice = False

    def set_native_locations(self, enabled: bool) -> None:
        """Compatibility command: an AP session may not disable interception."""
        if not enabled:
            raise RuntimeError("Native pickup/vendor interception is mandatory; it cannot be disabled")
        self._native_locations_enabled = True

    def _owned_equipment(self) -> dict[str, bool]:
        """Resolve AP ownership once for both native hooks and inventory writes."""
        owned = dict(self._ap_owned["ratchet"])
        owned.update(self.wrench.entitlements())
        owned.update(self.progression.ownership())
        for display, internal in CLANK_PICKUP_TO_INTERNAL.items():
            owned[internal] = bool(owned.get(internal) or self._ap_owned["clank"].get(display))
        return owned

    def _entitlements(self):
        owned = self._owned_equipment()
        return {slot: bool(owned[name]) for slot, name in enumerate(WEAPON_ORDER) if name in owned}

    def close(self):
        """Release resident loader code before dropping the PINE connection."""
        try:
            if (self.traps.managed and self.case.is_ready
                    and self.pine.get_game_id() == "SCUS-97623"):
                self.traps.restore(self.case.symbols)
        finally:
            try:
                if self.vendor_rewards.icon.installed and self.case.is_ready and self.pine.get_game_id() == "SCUS-97623":
                    self.vendor_rewards.close()
            finally:
                self.native_runtime.close()
        self.main_menu.shown = False

    def _bind_native_locations(self) -> bool:
        hooks = self.location_hooks
        if hooks.installed and hooks.is_current():
            hooks.sync_checked(self._checked_items)
            return True
        hooks.installed = False
        screen = self.case.case_menu.screen_address
        if screen is None or self.pine.read_int32(screen) not in (8, 14, 16):
            if not self._native_pause_notice:
                self._log("[SAC] Open Case Files to activate native vendor/pickup checks for this level.")
                self._native_pause_notice = True
            return False
        if (hooks.module == self.case.case_id and hooks.marker_address is not None
                and self.pine.read_bytes(hooks.marker_address, len(MARKER)) == MARKER):
            # A cancelled transition may invalidate bindings without unloading
            # the patched module. Reuse its journal instead of patching twice.
            hooks.installed = True
            hooks.sync_checked(self._checked_items)
            return True
        hooks.prepare(self.case.symbols, pickup_locations=PICKUP_LOCATIONS,
                      vendor_locations=VENDOR_LOCATIONS, checked=self._checked_items)
        hooks.install(screen)
        self._native_pause_notice = False
        self._log("[SAC] Native vendor/pickup checks active for this level.")
        return True

    def _read_native_locations(self) -> None:
        for name in self.location_hooks.poll():
            # Native slot names become AP location names; named pickups pass through.
            name = EQUIPMENT_INTERNAL_TO_DISPLAY.get(name, name)
            if name not in self._checked_items and self.send_location(name):
                self._checked_items.add(name)

    def _strip_all_inventories(self) -> None:
        self.case.ratchet_items.strip_all()
        self.case.clank_items.strip_all()

    def _reapply_all_inventories(self) -> None:
        self.case.ratchet_items.apply_all(self._owned_equipment())
        self.case.clank_items.apply_all(self._ap_owned["clank"])

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        self._checked_items.update(checked_locations)
        self.missions.sync_from_ap(checked_locations)
        self.cutscenes.sync_from_ap(checked_locations)
        self.gadgetbot_challenges.sync_from_ap(checked_locations)
        self.special_challenges.sync_from_ap(checked_locations)
        self.ratchet_challenges.sync_from_ap(checked_locations)
        self.alien_codes.sync_from_ap(checked_locations)
        self.titanium_bolts.sync_from_ap(checked_locations)
        self.keycards.sync_from_ap(checked_locations)

    # -- Traps ---------------------------------------------------------------

    def activate_trap(self, trap_name: str) -> bool:
        if not self.case.is_ready or not self._inventory_initialized:
            return False
        return self.traps.activate(trap_name, self.case.symbols)

    @property
    def owned_cases(self) -> frozenset[str]:
        """Case names currently unlocked via AP, as of the last apply_inventory() call
        (see _owned_cases' own docstring) -- client/context.py uses this to withhold
        vendor scouting, and native_runtime/hooks.sync_vendor_cases() to hide a
        locked case's vendor offers in-game, until that case is actually unlocked."""
        return frozenset(self._owned_cases)

    # -- Bolts / NG+ (plain global values, CONFIRMED live addresses) -------

    @property
    def bolts(self) -> int:
        return self.pine.read_int32(BOLTS_ADDRESS)

    @bolts.setter
    def bolts(self, value: int) -> None:
        self.pine.write_int32(BOLTS_ADDRESS, value)

    @property
    def challenge_mode(self) -> int:
        return self.pine.read_int8(CHALLENGE_MODE_ADDRESS)

    @challenge_mode.setter
    def challenge_mode(self, value: int) -> None:
        self.pine.write_int8(CHALLENGE_MODE_ADDRESS, value)

    # -- Notifications ---------------------------------------------------------

    def notify(self, text: str) -> None:
        logger.info(f"[SAC] {text}")

    # -- Tick --------------------------------------------------------------

    def tick(self) -> None:
        if self.main_menu.poll():
            self.case.is_ready = False
            self._invalidate_level()
            self.location_hooks.installed = False
            # Arm the loader for New Game when AP inventory is available,
            # but never bind gameplay memory using the stale last case ID.
            if self._inventory_initialized:
                self.native_runtime.service(self._checked_items, self._entitlements())
            return
        # Installation targets the incoming DLL while CURRENT_CASE can still
        # identify the outgoing one. Polling then would invalidate fresh hooks.
        if not self.native_runtime.awaiting_start:
            self._read_native_locations()
        if self._inventory_initialized:
            generation = self.native_runtime.generation
            native_ready = self.native_runtime.service(self._checked_items, self._entitlements())
            if self.native_runtime.generation != generation:
                # A same-module reset can finish between host polls. Force
                # every binding to refresh even when all addresses look valid.
                self.case.is_ready = False
                self._invalidate_level()
            if not native_ready:
                # Still observe transitions so old bindings cannot survive a
                # same-module reload. No inventory writes while held/loading.
                self.case.check_transition()
                return
        became_ready = self.case.check_transition()
        self.case.check_death()

        if not self.case.is_ready or not self._inventory_initialized:
            return

        screen = self.case.case_menu.screen_address
        playing = screen is not None and self.pine.read_int32(screen) == 0
        self.traps.tick(self.case.symbols, playing)

        current_case = CASE_ID_TO_CASE.get(self.case.case_id)
        table_base = self.case.symbols.get("g_MISSION_LEVEL_LIST")
        became_ready = became_ready or self.missions.table_base != table_base

        if became_ready:
            case_label = current_case.name if current_case else f"unknown case 0x{self.case.case_id:X}"
            logger.info(f"[SAC] Case changed -> {case_label} (id={self.case.case_id})")
            # g_pMissionLevelList's resolved address (and everything
            # derived from it) is only valid for the level it was
            # resolved on -- see MissionInventory.invalidate_resolved_
            # addresses(). Without this, missions.check()/
            # enforce_owned_first_missions() below would keep reusing the
            # previous level's now-stale addresses instead of re-scanning
            # for this one.
            self.missions.invalidate_resolved_addresses()
            self.missions.table_base = table_base
            self.case.ratchet_items.sync()
            self.titanium_bolts.sync()
            self.skill_points.sync()
            self.gadgetbot_challenges.sync()
            self.special_challenges.sync()
            self.ratchet_challenges.sync()
            self.alien_codes.sync()
            self.alien_codes.bind(self.case.symbols)
            self.ratchet_challenges.bind(self.case.symbols)
            self.titanium_bolts.bind(self.case.symbols)
            if not self.notifications.bind(self.case.symbols):
                self._log("[SAC] Native receipt HUD layout could not be validated for this module.")
            self.keycards.bind(self.case.symbols)
            self.on_case_ready()
        newly_accessible = self.case.case_menu.unlock_owned_missions(self._owned_cases)
        menu_screen = self.case.case_menu.screen_address
        if newly_accessible and menu_screen is not None and self.pine.read_int32(menu_screen) == 14:
            self._log("[SAC] New cases available: " + ", ".join(sorted(newly_accessible))
                      + ". Fully close and reopen Case Files to refresh the list.")
        self.case.case_menu.apply_access(self._owned_cases)

        for name in self.missions.check_all(all_missions=self.missions_all()):
            if self.send_location(name):
                self.missions.confirm(name)
        for name in self.cutscenes.check():
            if self.send_location(name):
                self.cutscenes.confirm(name)
        for name in self.gadgetbot_challenges.check():
            if self.send_location(name):
                self.gadgetbot_challenges.confirm(name)
        for name in self.special_challenges.check():
            if self.send_location(name):
                self.special_challenges.confirm(name)
        for name in self.ratchet_challenges.check():
            if self.send_location(name):
                self.ratchet_challenges.confirm(name)
        for name in self.skill_points.check():
            if self.send_location(name):
                self.skill_points.confirm(name)
        for name in self.alien_codes.check():
            if self.send_location(name):
                self.alien_codes.confirm(name)
        for name in self.keycards.check():
            if self.send_location(name):
                self.keycards.confirm(name)
        if len(self.keycards.found) == 3:
            self._owned_cases.add(SACCases.HIGH_TREEHOUSE)
        self._check_goal()

        for name in self.titanium_bolts.check():
            if self.send_location(name):
                self.titanium_bolts.confirm(name)

        for name in self.vendor.poll_purchases():
            name = EQUIPMENT_INTERNAL_TO_DISPLAY.get(name, name)
            if name not in self._checked_items and self.send_location(name):
                self._checked_items.add(name)

        for name in self.case.ratchet_items.check():
            if name in VENDOR_LOCATIONS.values():
                continue
            if self.location_hooks.installed and name in {
                    "fountainpen" if n == f"{SACClankGadgets.BLACK_OUT_PEN} (Pickup)" else n
                    for n in PICKUP_LOCATIONS.values()}:
                continue
            if name == "fountainpen":
                name = f"{SACClankGadgets.BLACK_OUT_PEN} (Pickup)"
            elif name not in self._ap_owned["ratchet"]:
                continue
            else:
                name = EQUIPMENT_INTERNAL_TO_DISPLAY.get(name, name)
            if name not in self._checked_items and self.send_location(name):
                self._checked_items.add(name)
        for name in self.case.clank_items.check():
            name = f"{name} (Pickup)"
            if name not in self._checked_items and self.send_location(name):
                self._checked_items.add(name)
        self._reapply_all_inventories()

        self.progression.sync()
        self.weapon_mods.sync()
        self.wrench.sync()
        self.bolt_rewards.deliver()
        self.vendor_rewards.tick(self.case.symbols)
        self.notifications.tick()

    def _check_goal(self):
        complete = self.missions._reported
        klunk = (f"{SACCases.KLUNKS_LAIR} Complete" in complete or
                 self.missions.completed.get(CHAPTER_ENTRIES[SACCases.KLUNKS_LAIR][-1].name, False))
        qwark = all(f"{case.name} Complete" in complete or
                    (bool(CHAPTER_ENTRIES.get(case.name)) and
                     all(self.missions.completed.get(entry.name, False) for entry in CHAPTER_ENTRIES[case.name]))
                    for case in CASES_BY_OPERATIVE[SACOperatives.QWARK])
        reached = {0: klunk, 1: qwark, 2: klunk or qwark,
                   3: self.keycards.chalice_collected, 4: self.alien_codes.all_found}.get(self.goal, False)
        if reached and not self._goal_sent:
            self.on_goal()
            self._goal_sent = True

    def _handle_death(self) -> None:
        self._strip_all_inventories()
        if not self.death_link_enabled():
            return
        self._death_count += 1
        if self._death_count > self.death_amnesty():
            cause = int(self.case.ratchet.movement_state)
            self.send_deathlink(cause)

    def _handle_respawn(self) -> None:
        self._death_count = 0
        self._reapply_all_inventories()

    def __repr__(self) -> str:
        return f"Core(case_id={self.case.case_id}, is_ready={self.case.is_ready})"
