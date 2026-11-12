import logging
from collections.abc import Callable, Sequence

from .address_maps import BOLTS_ADDRESS
from .bolt_rewards import BoltRewards
from .inventories import (
    AlienCodeInventory,
    CaseInventory,
    CutsceneInventory,
    GadgetbotChallengeInventory,
    KeycardInventory,
    MissionInventory,
    RatchetChallengeInventory,
    SpecialChallengeInventory,
    resolve_owned_cases,
)
from .main_menu import MainMenuNotice
from .notifications import ItemNotifications
from ..constants import (
    CASES_BY_OPERATIVE,
    CASE_ID_TO_CASE,
    CHAPTER_ENTRIES,
    CLANK_PICKUP_TO_INTERNAL,
    EQUIPMENT_INTERNAL_TO_DISPLAY,
    MISSION_COMPLETE_NAME,
    PICKUP_LOCATIONS,
    PICKUP_LOCATION_BY_INTERNAL,
    PROGRESSIVE_WRENCH,
    VENDOR_LOCATIONS,
    VENDOR_LOCATION_NAMES,
    WEAPON_ORDER,
    GoalOptions,
    SACCases,
    SACCheats,
    SACFiller,
    SACMissionLocations,
    SACOperatives,
    SACTraps,
    vendor_unlocked_cases,
)
from .patches import LocationHooks, Progression, WeaponMods, WrenchProgression
from .permanent_runtime import PermanentRuntime
from .quick_select import QuickSelectState
from .ring_link import RingLink
from .skill_points import SkillPointState
from .skins import Skins
from .stealth import StealthState
from .titanium_bolts import TitaniumBoltState
from .traps import Traps
from .vendor_rewards import VendorRewards
from .xp_fillers import boost_nanotech, boost_weapon, equipped_weapon
from ..patcher.release import load_runtime_build

logger = logging.getLogger("CommonClient")

_HOOKED_PICKUP_NAMES = frozenset(WEAPON_ORDER[slot] for slot in PICKUP_LOCATIONS)


class Core:

    def __init__(self, pine, log: Callable[[str], None] | None = None,
                 debug: Callable[[str], None] | None = None, *, permanent_build=None) -> None:
        self.pine = pine
        self._log = log or logger.info
        self._debug = debug or logger.debug
        self.main_menu = MainMenuNotice(pine, self._debug)
        self.bolt_rewards = BoltRewards(pine, self._debug)
        self.ring_link = RingLink(pine, lambda: self.progression.ng_plus)
        self.bolt_rewards.on_balance_changed = self.ring_link.record
        self.notifications = ItemNotifications(pine)
        self.traps = Traps(pine)
        self.ratchet_pack = False
        self._ratchet_pack_pending = False

        self.case = CaseInventory(pine)
        self.case.on_transition_start = self._invalidate_level
        self.case.on_death            = self._handle_death
        self.case.on_respawn          = self._handle_respawn

        self.vendor        = self.case.vendor
        self.location_hooks = LocationHooks(pine)
        self.location_hooks.permanent = True
        if permanent_build is None:
            permanent_build = load_runtime_build()
        self.native_runtime = PermanentRuntime(pine, self.location_hooks, self._log, self._debug, permanent_build)
        self.skins = Skins(pine)
        self.native_runtime.skins = self.skins
        self.vendor_rewards = VendorRewards(pine, self.vendor, self._debug)
        self.native_runtime.presentation = self.vendor_rewards.text
        self.wrench = WrenchProgression(pine)
        self.native_runtime.wrench = self.wrench
        self.stealth = StealthState(pine)
        self.progression = Progression(pine)
        self.progression.stealth = self.stealth
        self.progression.mission_failure = self.case.mission_failure
        self.native_runtime.progression = self.progression
        self.weapon_mods = WeaponMods(pine)
        self.native_runtime.weapon_mods = self.weapon_mods
        self.missions      = MissionInventory(pine)
        self.native_runtime.on_mission_complete = self._record_mission_completion
        self.cutscenes      = CutsceneInventory(pine)
        self.gadgetbot_challenges = GadgetbotChallengeInventory(pine)
        self.special_challenges   = SpecialChallengeInventory(pine)
        self.ratchet_challenges   = RatchetChallengeInventory(pine)
        self.titanium_bolts = TitaniumBoltState(pine)
        self.skill_points   = SkillPointState(pine)
        self.alien_codes    = AlienCodeInventory(pine)
        self.keycards = KeycardInventory(pine)
        self.native_runtime.keycard_hunt = self.keycards.hunt
        self.goal = GoalOptions.DEFEAT_KLUNK
        self.pick_and_mix_goals = None
        self.planet_cases: dict[str, list[str]] | None = None
        self._goal_sent = False
        self.quick_select   = QuickSelectState(pine)

        self._ap_owned: dict[str, dict[str, bool]] = {"ratchet": {}, "clank": {}}
        self._owned_cases: set[str] = set()
        self._vendor_cases: frozenset[str] = frozenset()
        self.vendor_logic = None
        self._inventory_initialized = False
        self._checked_items: set[str] = set()

        self.send_location:      Callable[[str], bool] = lambda _: False
        self.send_deathlink:     Callable[[str], None]  = lambda _: None
        self.death_amnesty:      Callable[[], int]      = lambda: 0
        self.death_link_enabled: Callable[[], bool]     = lambda: False
        self.on_goal:            Callable[[], None]     = lambda: None
        self.on_case_ready:      Callable[[], None]     = lambda: None
        self.missions_all:       Callable[[], bool]     = lambda: False
        self._death_count: int = 0

    def wire(
        self,
        send_location:      Callable[[str], bool],
        send_deathlink:      Callable[[str], None]  | None = None,
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

    def apply_inventory(
        self, *, ratchet: dict[str, bool], clank: dict[str, bool], received_names: Sequence[str] = (),
    ) -> None:
        self._inventory_initialized = True
        self.progression.receive(received_names)
        self.keycards.hunt.receive(received_names)
        self.weapon_mods.received = set(received_names)
        self.wrench.count = min(5, list(received_names).count(PROGRESSIVE_WRENCH))
        self.bolt_rewards.received = list(received_names).count(SACFiller.BOLTS)
        if SACCheats.RATCHET_PACK in received_names and not self.ratchet_pack:
            self.ratchet_pack = self._ratchet_pack_pending = True
        self._ap_owned = {"ratchet": dict(ratchet), "clank": dict(clank)}
        self._owned_cases = resolve_owned_cases(list(received_names), planet_cases=self.planet_cases)
        if self.alien_codes.all_found:
            self._owned_cases.add(SACCases.HIGH_TREEHOUSE)
        self.native_runtime.owned_cases = frozenset(self._owned_cases)
        self._vendor_cases = vendor_unlocked_cases(self._owned_cases, received_names)
        self.native_runtime.vendor_cases = self._vendor_cases
        self.native_runtime.available_vendor_locations = (
            self.vendor_logic.available(received_names) if self.vendor_logic is not None else None)

    def _invalidate_level(self) -> None:
        self.traps.last_tick = None
        self.vendor_rewards.invalidate()
        self.missions.invalidate_resolved_addresses()
        self.missions.table_base = None
        self.notifications.binding = None
        self.alien_codes.valid = False
        self.ratchet_challenges.invalidate()
        self.titanium_bolts.valid = False
        self.keycards.flags.pointer_address = None
        self.keycards.root_pointer = None

    def _owned_equipment(self) -> dict[str, bool]:
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
        """Stop managing the game. The ISO's loader patch stays in place."""
        try:
            if (self.traps.managed and self.case.is_ready
                    and self.pine.get_game_id() == "SCUS-97623"):
                self.traps.restore(self.case.symbols)
        finally:
            try:
                if self.case.is_ready and self.pine.get_game_id() == "SCUS-97623":
                    self.vendor_rewards.close()
            finally:
                self.native_runtime.close()
        self.main_menu.shown = False

    def _send_once(self, name: str) -> None:
        """Send a location check unless already sent; a rejected send is retried on a later tick."""
        if name not in self._checked_items and self.send_location(name):
            self._checked_items.add(name)

    def _report_checks(self, inventory, names) -> None:
        """Send each newly found name, confirming it with its inventory only once AP accepts it."""
        for name in names:
            if self.send_location(name):
                inventory.confirm(name)

    def _read_native_locations(self) -> None:
        for name in self.location_hooks.poll():
            self._send_once(EQUIPMENT_INTERNAL_TO_DISPLAY.get(name, name))

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

    def activate_effect(self, name: str) -> bool:
        """False if it can't be applied yet, so it's retried later."""
        if not self.case.is_ready or not self._inventory_initialized:
            return False
        if name == SACTraps.GADGETRON_DEBT:
            debt = self.traps.gadgetron_debt()
            self.ring_link.record("traps", -debt)
            self._log(f"[SAC] Gadgetron Debt Trap! Gadgetron took {debt:,} bolts.")
            return True
        if name == SACTraps.ONE_HP:
            if not self.case.active_player.lower_health(1.0):
                return False
            self._log("[SAC] One HP Trap! You're down to 1 HP.")
            return True
        if name == SACFiller.NANOTECH_XP:
            return self._nanotech_xp()
        if name == SACFiller.WEAPON_XP:
            return self._weapon_xp()
        return self.traps.activate(name, self.case.symbols)

    def _nanotech_xp(self) -> bool:
        # Ratchet's cases give Ratchet the XP; every other case gives it to Clank.
        case = CASE_ID_TO_CASE.get(self.case.case_id)
        operative = SACOperatives.RATCHET if case and case.operative == SACOperatives.RATCHET else SACOperatives.CLANK
        try:
            gained = boost_nanotech(self.pine, self.case.symbols, operative)
        except ValueError:
            return False  # still loading
        if gained:
            self._log(f"[SAC] Nanotech XP: {operative} gained {gained:,} XP.")
        else:
            self._log(f"[SAC] Nanotech XP: {operative}'s nanotech is already at its cap.")
        return True

    def _weapon_xp(self) -> bool:
        player = self.case.active_player.current_player()
        if player is None:
            return False
        weapon = equipped_weapon(self.pine, self.case.symbols, player)
        if weapon is None:
            self._log("[SAC] Weapon XP: you aren't holding a weapon that levels up, so it had no effect.")
            return True
        name = EQUIPMENT_INTERNAL_TO_DISPLAY.get(weapon.internal, weapon.internal)
        progression = self.progression
        # Manual progressive weapons only keep XP below the received level.
        if progression.enabled and (not progression.manual
                                    or weapon.level >= progression.levels.get(weapon.internal, 0) - 1):
            self._log(f"[SAC] Weapon XP: {name} levels up from Progressive Weapons, so it had no effect.")
            return True
        gained = boost_weapon(self.pine, weapon)
        if gained:
            self._log(f"[SAC] Weapon XP: {name} gained {gained:,} XP.")
        else:
            self._log(f"[SAC] Weapon XP: {name} can't gain any more XP right now.")
        return True

    def bolt_balance(self) -> int | None:
        if not self.case.is_ready or not self._inventory_initialized:
            return None
        return self.pine.read_int32(BOLTS_ADDRESS)

    def receive_ring_link(self, amount: int) -> bool:
        if not self.case.is_ready or not self._inventory_initialized:
            return False
        self.ring_link.receive(amount)
        return True

    def reset_traps(self) -> bool:
        if not self.case.is_ready:
            return False
        return self.traps.reset(self.case.symbols)

    @property
    def owned_cases(self) -> frozenset[str]:
        return frozenset(self._owned_cases)

    @property
    def vendor_cases(self) -> frozenset[str]:
        return self._vendor_cases

    def tick(self) -> None:
        self.case.check_mission_failure()
        self.stealth.poll()
        if self.main_menu.poll():
            self.case.is_ready = False
            self._invalidate_level()
            self.location_hooks.installed = False
            if self._inventory_initialized:
                self.native_runtime.service(self._checked_items, self._entitlements())
            return
        if not self.native_runtime.awaiting_start:
            self._read_native_locations()
        if self._inventory_initialized:
            generation = self.native_runtime.generation
            native_ready = self.native_runtime.service(self._checked_items, self._entitlements())
            if self.native_runtime.generation != generation:
                self.case.is_ready = False
                self._invalidate_level()
            if not native_ready:
                self.case.check_transition(allow_bind=False)
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
            self._debug(f"[SAC] Case changed -> {case_label} (id={self.case.case_id})")
            self.missions.invalidate_resolved_addresses()
            self.missions.table_base = table_base
            self.case.ratchet_items.sync()
            self.titanium_bolts.sync()
            self.skill_points.sync()
            self.gadgetbot_challenges.sync()
            self.special_challenges.sync()
            self.ratchet_challenges.sync()
            self.alien_codes.sync()
            hunt = self.keycards.hunt
            self.alien_codes.bind(self.case.symbols, flag_pointer_address=(
                hunt.pointer_address if (hunt.enabled or hunt.enable_address is not None) and self.case.case_id == 31 else None))
            self.ratchet_challenges.bind(self.case.symbols)
            self.titanium_bolts.bind(self.case.symbols)
            if not self.notifications.bind(self.case.symbols):
                self._debug("[SAC] Native receipt HUD layout could not be validated for this module.")
            self.keycards.bind(self.case.symbols)
            if not self.native_runtime.vendor_enabled_for_module(self.case.case_id):
                self.vendor.set_addr(None)
            self.on_case_ready()
        if self.ratchet_pack and (became_ready or self._ratchet_pack_pending):
            self._ratchet_pack_pending = not self.traps.grant_ratchet_pack(self.case.symbols)
        self._report_checks(self.alien_codes, self.alien_codes.check())
        if self.alien_codes.all_found:
            self._owned_cases.add(SACCases.HIGH_TREEHOUSE)
        newly_accessible = self.case.case_menu.unlock_owned_missions(self._owned_cases)
        menu_screen = self.case.case_menu.screen_address
        if newly_accessible and menu_screen is not None and self.pine.read_int32(menu_screen) == 14:
            self._debug("[SAC] New cases available: " + ", ".join(sorted(newly_accessible))
                      + ". Fully close and reopen Case Files to refresh the list.")
        self.case.case_menu.apply_access(self._owned_cases)

        self._report_checks(self.missions, self.missions.check_all(all_missions=self.missions_all()))
        for inventory in (self.cutscenes, self.gadgetbot_challenges, self.special_challenges,
                          self.ratchet_challenges, self.skill_points, self.keycards):
            self._report_checks(inventory, inventory.check())
        self._check_goal()

        self._report_checks(self.titanium_bolts, self.titanium_bolts.check())

        for name in self.vendor.poll_purchases():
            location = VENDOR_LOCATION_NAMES.get(EQUIPMENT_INTERNAL_TO_DISPLAY.get(name, name))
            if location is not None:
                self._send_once(location)

        for name in self.case.ratchet_items.check():
            if name in VENDOR_LOCATIONS.values():
                continue
            if self.location_hooks.installed and name in _HOOKED_PICKUP_NAMES:
                continue
            if name in PICKUP_LOCATION_BY_INTERNAL:
                self._send_once(PICKUP_LOCATION_BY_INTERNAL[name])
        for name in self.case.clank_items.check():
            self._send_once(f"{name} (Pickup)")
        self._reapply_all_inventories()

        self.progression.sync()
        for name in (*self.progression.level_checks(), *self.progression.nanotech_checks(self.case.symbols),
                     *self.progression.ratchet_nanotech_checks(self.case.symbols), *self.stealth.checks()):
            self._send_once(name)
        self.weapon_mods.sync()
        self.wrench.sync()
        self.bolt_rewards.deliver()
        self.vendor_rewards.tick(self.case.symbols)
        self.notifications.tick()

    def _record_mission_completion(self, case_name):
        mission = CHAPTER_ENTRIES[case_name][0].name
        self.missions.completed[mission] = True
        name = mission if self.missions_all() else MISSION_COMPLETE_NAME[case_name]
        self._report_checks(self.missions, [name])

    def _check_goal(self):
        complete = self.missions._reported
        klunk = (MISSION_COMPLETE_NAME[SACCases.KLUNKS_LAIR] in complete or
                 self.missions.completed.get(CHAPTER_ENTRIES[SACCases.KLUNKS_LAIR][-1].name, False))
        butterqwark = (MISSION_COMPLETE_NAME[SACCases.MADAM_BUTTERQWARK] in complete or
                       self.missions.completed.get(SACMissionLocations.MADAM_BUTTERQWARK_QWARKOGRAPHY_CH_3, False))
        all_qwark = all(MISSION_COMPLETE_NAME[case.name] in complete or
                        (bool(CHAPTER_ENTRIES.get(case.name)) and
                         all(self.missions.completed.get(entry.name, False) for entry in CHAPTER_ENTRIES[case.name]))
                        for case in CASES_BY_OPERATIVE[SACOperatives.QWARK])
        gadgetbots = all(MISSION_COMPLETE_NAME[case.name] in complete or
                         all(self.missions.completed.get(entry.name, False)
                             for entry in CHAPTER_ENTRIES[case.name])
                         for case in CASES_BY_OPERATIVE[SACOperatives.GADGETBOTS])
        ratchet = all(self.ratchet_challenges.completed.values())
        conditions = {
            GoalOptions.DEFEAT_KLUNK: klunk,
            GoalOptions.QWARK_OPERA: butterqwark,
            GoalOptions.ALL_GADGETBOTS: gadgetbots,
            GoalOptions.RATCHET_PRISON_ESCAPE: ratchet,
            GoalOptions.THESE_ARE_THE_REAL_ADVENTURES_OF_CAPTAIN_QWARK: all_qwark,
            GoalOptions.CHALICE_OF_POWER: self.keycards.chalice_collected,
            GoalOptions.ALIEN_CODES: self.alien_codes.all_found,
        }
        conditions[GoalOptions.ANY] = any(conditions.values())
        reached = (bool(self.pick_and_mix_goals) and
                   all(conditions.get(goal, False) for goal in self.pick_and_mix_goals)
                   if self.pick_and_mix_goals is not None else conditions.get(self.goal, False))
        if reached and not self._goal_sent:
            self.on_goal()
            self._goal_sent = True

    def _handle_death(self, cause: str) -> None:
        self._strip_all_inventories()
        if not self.death_link_enabled():
            return
        self._death_count += 1
        if self._death_count > self.death_amnesty():
            self._death_count = 0
            self.send_deathlink(cause)

    def _handle_respawn(self) -> None:
        self._reapply_all_inventories()

    def __repr__(self) -> str:
        return f"Core(case_id={self.case.case_id}, is_ready={self.case.is_ready})"
