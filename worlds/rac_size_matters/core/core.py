from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from ..constants import Rac5CutsceneLocations, Rac5GadgetKeys, Rac5Locations
from ..locations import TITAN_INTERNAL_TO_LOCATION, WEAPON_INTERNAL_TO_LOCATION, WEAPON_LEVEL_LOOKUP
from .address_maps import NEW_PLANET_START_LOAD_ADDR
from .armour import ARMOUR_FLAG_TO_LOCATION, ArmourInventory, ArmourPiece, ArmourStruct
from .challenge_mode import ChallengeModeState
from .challenges import ChallengeInventory, SkyboardInventory
from .ghost_ratchet import GhostRatchetInventory
from .locations.mission_locations import CUTSCENE_MAP, STORY_MISSION_MAP
from .menu import MenuStateValue
from .missions import MissionInventory
from .planets import AUTO_UNLOCK_ADDRESSES, INFOBOT_UNLOCK_VALUE, PlanetInventory, PlanetUnlockState
from .player_bolts import PlayerBoltInventory
from .player_health_exp import PlayerHealthExpInventory
from .quick_select import QuickSelectState
from .shrink_ray import ShrinkRaySkipInventory
from .skill_points import SkillPointInventory
from .skins import SkinInventory
from .titanium_bolts import TitaniumBoltInventory
from .vendor import WEAPON_VENDOR_IDS, ModVendorMenu, VendorInventory, WeaponVendorMenu
from .weapons import TITAN_ELIGIBLE_WEAPONS

if TYPE_CHECKING:
    from ..pypine import Pine

logger = logging.getLogger("CommonClient")

_ARMOUR_PIECES = (ArmourPiece.CHESTPLATE, ArmourPiece.HELMET, ArmourPiece.GLOVES, ArmourPiece.BOOTS)

# lacerator/acid_bomb_glove/hypershot are excluded here — sold at Pokitaru's
# real vendor, so their forced auto-unlock is suppressed elsewhere instead.
_BONUS_TRIGGER_WEAPONS: frozenset[str] = frozenset({"concussion_gun"})
_SCRIPTED_PICKUP_GADGETS: frozenset[str] = frozenset()
# Gated to Pokitaru only, since apply_inventory() re-applies owned
# weapons/gadgets on every planet load and could be misread as a pickup elsewhere.
_POKITARU_ID: int = 0x01
_KALIDON_ID:  int = 0x03
_CHALLAX_ID:  int = 0x07
# Kalidon's skyboard race sub-level isn't in PLANET_ADDRESSES, so only the
# fixed/global skyboard and planet-unlock checks are safe here.
_KALIDON_RACE_ID: int = 0x16

# Story-required prerequisite missions once force-completed on load; now
# tracked for real, and completing one force-reloads its own planet.
_MISSION_FORCE_RELOAD: dict[str, int] = {
    Rac5CutsceneLocations.POKITARU_RESCUE: _POKITARU_ID,
    Rac5CutsceneLocations.KALIDON_SEARCH:  _KALIDON_ID,
    Rac5CutsceneLocations.CHALLAX_EXPLORE: _CHALLAX_ID,
}

# Scripted gadget handoffs with their own dedicated AP location, distinct
# from the coinciding mission/cutscene location — must fire independently.
_SCRIPTED_GADGET_LOCATIONS: dict[str, str] = {
    "sprout_o_matic": Rac5Locations.RYLLUS_SPROUT,
    "shrink_ray":     Rac5Locations.KALIDON_SHRINK,
}

# Mission/cutscene location -> its coinciding gadget-pickup location; more
# reliable than _SCRIPTED_GADGET_LOCATIONS since it fires regardless of all_cutscenes.
_MISSION_GADGET_LOCATION: dict[str, str] = {
    Rac5CutsceneLocations.RYLLUS_BUZZING: Rac5Locations.RYLLUS_SPROUT,
    Rac5CutsceneLocations.KALIDON_EXPLORE: Rac5Locations.KALIDON_SHRINK,
}

# Reuses WEAPON_VENDOR_IDS's id scheme; only Pokitaru's cycler addresses are wired up yet.
_CYCLER_ID_TO_WEAPON_NAME: dict[int, str] = {wid: name for name, wid in WEAPON_VENDOR_IDS.items()}

# Lets tick() skip send_location() for locations excluded from this seed's
# pool, since the mission bit still gets set in vanilla play regardless.
_STORY_MISSION_LOCATIONS: frozenset[str] = frozenset(STORY_MISSION_MAP.values())
_CUTSCENE_LOCATIONS:      frozenset[str] = frozenset(CUTSCENE_MAP.values())

# The game force-writes these items' unlocked bit to 1 regardless of AP
# ownership; corrected back to AP truth every tick or a bool dict's
# never-regresses rule would permanently mask a real future purchase.
_GAME_FORCED_WEAPONS: frozenset[str] = frozenset({"lacerator", "acid_bomb_glove"})
# Sold at a vendor like the weapons above, but the game also force-grants them on its own.
_GAME_FORCED_GADGETS: frozenset[str] = frozenset({
    "hypershot", "sprout_o_matic", "shrink_ray", "map_o_matic", "box_breaker",
})


class Core:
    """Initial setup + per-tick orchestration for the whole client.

    tick() pulls whatever changed from every check() into send_location() calls;
    never pokes memory directly (apply_inventory() uses the same Inventory methods).
    """

    def __init__(self, pine: Pine, log: Callable[[str], None] | None = None) -> None:
        self.pine = pine
        self._log = log or logger.info

        self.armour        = ArmourInventory(pine)
        self.quick_select  = QuickSelectState(pine)
        self.quick_select.is_ap_owned = self._is_weapon_id_ap_owned
        self.planet_unlock = PlanetUnlockState(pine)

        self.clank        = ChallengeInventory(pine)
        self.skyboard     = SkyboardInventory(pine)
        self.bolts        = TitaniumBoltInventory(pine)
        self.player_bolts = PlayerBoltInventory(pine)
        self.player_health_exp = PlayerHealthExpInventory(pine)
        self.skill_points = SkillPointInventory(pine)
        self.missions     = MissionInventory(pine)
        self.skin         = SkinInventory(pine)
        self.challenge_mode = ChallengeModeState(pine)
        self.shrink_ray    = ShrinkRaySkipInventory(pine)
        self.ghost_ratchet = GhostRatchetInventory(pine)

        # PlanetInventory is planet-agnostic — one instance rebinds itself to
        # whichever planet is loaded via check_transition().
        self.planet = PlanetInventory(pine, self.armour, self.quick_select)
        self.planet.on_death             = self._handle_death
        self.planet.on_respawn           = self._handle_respawn
        self.planet.on_equipped_armour_saved = lambda data: self.on_equipped_armour_saved(data)
        self.planet.on_pause_close       = self.quick_select.push_save

        # Slot-option gating, set directly by the client from slot_data —
        # check() just isn't called for a disabled system.
        self.clank_enabled:              bool = True
        self.clank_all_challenges:       bool = False
        self.skyboard_enabled:           bool = False
        self.shrink_ray_skips_enabled:     bool = False
        self.shrink_ray_locations_enabled: bool = False
        self.skill_points_enabled:       bool = False
        self.weapon_level_checks_enabled: bool = False
        self.nanotech_level_checks_enabled: bool = False
        # Mirrors options.py's AllMissions/AllCutscenes, gating which
        # missions.check() completions get sent as location checks.
        self.all_missions_enabled:  bool = True
        self.all_cutscenes_enabled: bool = False

        # send_location is a forwarding lambda since wire() replaces that
        # attribute after __init__ runs — vendor must call whatever it currently points to.
        self.vendor         = VendorInventory(
            pine, self.planet, self.planet_unlock, lambda loc: self.send_location(loc),
            log=self._log,
            is_weapon_ap_owned=lambda name: self._ap_owned_weapons.get(name, False),
            is_gadget_ap_owned=lambda name: self._ap_owned_gadgets.get(name, False),
            is_weapon_level_checks_enabled=lambda: self.weapon_level_checks_enabled,
        )
        self.weapon_vendor  = WeaponVendorMenu()
        self.mod_vendor     = ModVendorMenu()
        self._prev_vendor: MenuStateValue | None = None

        # True AP ownership as of the last apply_inventory() call, kept
        # separate from memory-mirrored WeaponInventory state (which includes forced writes).
        self._ap_owned_weapons: dict[str, bool] = {}
        self._ap_owned_gadgets: dict[str, bool] = {}

        # Deathlink / goal
        self.send_location:      Callable[[str], None] = lambda _: None
        self.send_deathlink:     Callable[[int], None]  = lambda _: None
        self.death_amnesty:      Callable[[], int]      = lambda: 1
        self.death_link_enabled: Callable[[], bool]     = lambda: False
        self.on_goal:            Callable[[], None]     = lambda: None
        self._death_count: int = 0

        # on_initial_load fires only on the very first main_menu True->False
        # edge; on_planet_ready fires on every transition, prompting apply_inventory().
        self.on_planet_ready:  Callable[[], None] = lambda: None
        self.on_initial_load:  Callable[[], None] = lambda: None
        self._initial_load_done: bool = False

        # Vendor menu open/close — for hint-sending and armour-set-check
        # rescanning, neither of which this file owns.
        self.on_vendor_open:  Callable[[], None] = lambda: None
        self.on_vendor_close: Callable[[], None] = lambda: None

        # Equipped-armour persistence — fired by PlanetInventory.on_equipped_armour_saved
        # (wired above), which only ever happens on a pause-menu-close.
        self.on_equipped_armour_saved: Callable[[dict[str, int]], None] = lambda _: None

        self.on_bonus_weapon_pickup:    Callable[[str], None] = lambda _: None
        self.on_scripted_gadget_pickup: Callable[[str], None] = lambda _: None

    def wire(
        self,
        send_location:             Callable[[str], None],
        send_deathlink:            Callable[[int], None]           | None = None,
        death_amnesty:             Callable[[], int]               | None = None,
        death_link_enabled:        Callable[[], bool]              | None = None,
        on_goal:                   Callable[[], None]               | None = None,
        on_planet_ready:           Callable[[], None]               | None = None,
        on_initial_load:           Callable[[], None]               | None = None,
        on_vendor_open:            Callable[[], None]               | None = None,
        on_vendor_close:           Callable[[], None]               | None = None,
        on_equipped_armour_saved:  Callable[[dict[str, int]], None] | None = None,
        on_bonus_weapon_pickup:    Callable[[str], None]            | None = None,
        on_scripted_gadget_pickup: Callable[[str], None]            | None = None,
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
        if on_planet_ready is not None:
            self.on_planet_ready = on_planet_ready
        if on_initial_load is not None:
            self.on_initial_load = on_initial_load
        if on_vendor_open is not None:
            self.on_vendor_open = on_vendor_open
        if on_vendor_close is not None:
            self.on_vendor_close = on_vendor_close
        if on_equipped_armour_saved is not None:
            self.on_equipped_armour_saved = on_equipped_armour_saved
        if on_bonus_weapon_pickup is not None:
            self.on_bonus_weapon_pickup = on_bonus_weapon_pickup
        if on_scripted_gadget_pickup is not None:
            self.on_scripted_gadget_pickup = on_scripted_gadget_pickup

    @property
    def vendor_active(self) -> bool:
        return self.weapon_vendor.active or self.mod_vendor.active

    # -- AP inventory application ---------------------------------------------

    def apply_inventory(
        self,
        *,
        weapons:         dict[str, bool],
        gadgets:         dict[str, bool],
        weapon_levels:   dict[str, int],
        weapon_mods:     dict[str, set[str]],
        armour_unlocked: dict[str, int],
        infobot_planets: set[str],
    ) -> None:
        """Write a fully-rebuilt AP inventory snapshot into game memory every tick.
        Skips memory a vendor session or death/pickup animation currently owns,
        to avoid fighting those windows' own zero/restore cycles."""
        self.planet_unlock.set_unlocked_planets(infobot_planets)
        # Read later by check_collected_armour()'s restore and _handle_respawn(),
        # so keep it current even if the memory write below is skipped.
        self.armour.set_ap_armour(armour_unlocked)
        if (not self.vendor_active and not self.planet.player.is_dead
                and not self.planet.player.is_picking_up and not self.planet.giant_clank_active):
            self.armour.apply_full()

        # Kept current even while writes below are gated, since
        # _suppress_forced_starter_items() needs an up-to-date answer every tick.
        self._ap_owned_weapons = dict(weapons)
        self._ap_owned_gadgets = dict(gadgets)
        # Pure bookkeeping; apply_progressive_leveling() turns this into level/xp writes.
        self.planet.weapons.level_caps = dict(weapon_levels)

        if not self.planet.is_ready or self.vendor_active:
            return

        wi = self.planet.weapons
        for name, owned in weapons.items():
            if owned:
                wi.set(name, True)
        for name, owned in gadgets.items():
            if owned:
                wi.set(name, True)
        for name, slots in weapon_mods.items():
            for slot in slots:
                wi.set_mod(name, slot, True)

        # Re-baseline so check_weapons() doesn't mistake this resync's 0->1
        # transitions for a fresh vendor purchase or scripted kiosk pickup.
        wi.sync_slots()
        # sync_slots() mirrors raw memory including any game force-write, so
        # anything baselined "owned" without real AP ownership must be corrected
        # back out this same tick or check() would mask a later genuine purchase.
        self._sync_weapon_gadget_ownership()

        self._apply_mod_unlock_flags()

    def _is_titan_pending(self, name: str) -> bool:
        """True once a Titan-eligible weapon's base purchase is done but its Titan
        variant hasn't; _sync_weapon_gadget_ownership() must not revert that."""
        wi = self.planet.weapons
        if wi.challenge_mode < 1 or name not in TITAN_ELIGIBLE_WEAPONS or wi.titan_purchased.get(name, False):
            return False
        loc = WEAPON_INTERNAL_TO_LOCATION.get(name)
        return bool(loc and wi.vendor_locations.get(loc, False))

    def _sync_weapon_gadget_ownership(self) -> None:
        """Forces every weapon/gadget's unlocked bit back to true AP ownership.
        Fires a gadget's scripted-pickup location here too, since this may be
        the only place that ever sees an un-owned forced unlock before it's corrected away."""
        wi = self.planet.weapons
        for name in wi._weapon_addrs:
            if self._is_titan_pending(name):
                continue
            owned = self._ap_owned_weapons.get(name, False)
            if wi.weapons.get(name, False) != owned:
                wi.set(name, owned)
                wi.weapons[name] = owned
        for name in wi._gadget_addrs:
            owned = self._ap_owned_gadgets.get(name, False)
            if wi.gadgets.get(name, False) != owned:
                if not owned:
                    loc = _SCRIPTED_GADGET_LOCATIONS.get(name)
                    if loc:
                        self.send_location(loc)
                wi.set(name, owned)
                wi.gadgets[name] = owned

    def _apply_mod_unlock_flags(self) -> None:
        """TODO: rebuild on top of the new vendor.py — used to write
        mod_unlock_N per weapon mod slot, removed with the old vendor-unlock machinery."""
        pass

    # -- Crash-recovery restores ----------------------------------------------
    #
    # Seed bolt/skill-point/armour state from already-checked locations for
    # reconnects where memory may be stale relative to the server.

    def restore_world_states(self, checked_locations: set[str]) -> None:
        self.bolts.sync_from_ap(checked_locations)
        self.bolts.sync()
        self.skill_points.sync_from_ap(checked_locations)
        self.skill_points.sync()
        for address in AUTO_UNLOCK_ADDRESSES:
            self.pine.write_int8(address, INFOBOT_UNLOCK_VALUE)

    def restore_armour_from_locations(self, checked_locations: set[str]) -> None:
        """Seed armour.game_armour from already-checked AP locations so a reconnect
        doesn't re-detect a pickup. Deliberately does not write game memory."""
        loc_to_flag = {v: k for k, v in ARMOUR_FLAG_TO_LOCATION.items()}
        pieces: dict[str, ArmourPiece] = {}
        for loc_name in checked_locations:
            flag = loc_to_flag.get(loc_name)
            if flag:
                set_key, piece = flag
                pieces[set_key] = pieces.get(set_key, ArmourPiece.NONE) | piece
        if pieces:
            self.armour.record_pickup(pieces)

    # -- AP sync ----------------------------------------------------------------

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        """Fold already-checked AP locations into every completion-tracking Inventory
        so a reconnect doesn't re-report anything the server already knows."""
        self.clank.sync_from_ap(checked_locations)
        self.skyboard.sync_from_ap(checked_locations)
        self.shrink_ray.sync_from_ap(checked_locations)
        self.planet.weapons.sync_from_ap(checked_locations)
        self.skill_points.sync_from_ap(checked_locations)
        self.missions.sync_from_ap(checked_locations)
        self.restore_armour_from_locations(checked_locations)

    def spawn_ghost_ratchet(self) -> bool:
        """Manually triggered via /spawn_ghost. Only works on planets present
        in GHOST_RATCHET_ADDRESSES — returns False on any other planet."""
        planet_id = self.planet.planet_id
        if planet_id is None:
            return False
        return self.ghost_ratchet.spawn(planet_id)

    # -- Notifications ---------------------------------------------------------

    def notify(self, text: bytes | str) -> None:
        """Show a small text-box notification, unless a menu is open (planet
        transitions are already handled by PlanetInventory.show_text())."""
        if self.planet.menu.get() not in (None, MenuStateValue.CLOSED):
            return
        self.planet.show_text(text)

    def tick(self) -> None:
        """One poll cycle, called once per tick by the client's poll loop. Doesn't
        manage its own timing or swallow errors, so connection problems surface to the caller."""
        became_ready = self.planet.check_transition()
        # Planet-unlock addresses are fixed/global, so safe (and necessary)
        # to enforce every tick even mid-transition, unlike everything gated below.
        self.planet_unlock.check()

        # Watched unconditionally so a redirect lands as soon as possible, even mid-transition.
        for name in self.planet.check_giant_clank():
            self.send_location(name)

        if self.planet.giant_clank_active:
            # Self-contained vanilla sequence; check_giant_clank() above is all the tracking it needs.
            return

        if self.planet.planet_id == _KALIDON_RACE_ID:
            # Has no addresses of its own, so skip every normal per-planet check
            # and just poll the skyboard completion bits at their fixed addresses.
            if self.planet.is_ready and self.skyboard_enabled:
                for name in self.skyboard.check():
                    self.send_location(name)
            return

        self.planet.check_controller()
        self.planet.check_death()
        self.planet.check_equipped_armour()

        if not self.planet.is_ready:
            return

        if became_ready:
            if not self._initial_load_done:
                # Wipe the save's weapon/gadget/mod/level state before anything
                # diffs against it, so stale-session progress doesn't look like new pickups.
                self.planet.weapons.wipe()
                self.planet.weapon_cycler.initialize(self._first_owned_weapon_id)
            self.skin.setup()
            self.challenge_mode.setup()
            if self.clank_enabled:
                # Unlocks every Clank Challenge section on every tracked planet; idempotent.
                self.clank.setup(self.clank_all_challenges)
            self.on_planet_ready()
            if not self._initial_load_done:
                self._initial_load_done = True
                self.on_initial_load()

        self.quick_select.check()

        for name in self.bolts.check():
            self.send_location(name)
        if self.skill_points_enabled:
            for name in self.skill_points.check():
                self.send_location(name)
        for name in self.missions.check(self.planet.planet_id):
            # Goal/gadget-handoff signals must fire even when the location
            # itself isn't sent below — they aren't gated by all_missions/all_cutscenes.
            gadget_loc = _MISSION_GADGET_LOCATION.get(name)
            if gadget_loc:
                self.send_location(gadget_loc)
            if name == Rac5CutsceneLocations.QUODRONA_GOAL:
                self.on_goal()

            reload_planet = _MISSION_FORCE_RELOAD.get(name)
            if reload_planet is not None:
                self.pine.write_int32(NEW_PLANET_START_LOAD_ADDR, reload_planet)

            if name in _CUTSCENE_LOCATIONS and not self.all_cutscenes_enabled:
                continue
            if name in _STORY_MISSION_LOCATIONS and not self.all_missions_enabled:
                continue
            self.send_location(name)
        if self.clank_enabled:
            for name in self.clank.check(all_challenges=self.clank_all_challenges):
                self.send_location(name)
        if self.skyboard_enabled:
            for name in self.skyboard.check():
                self.send_location(name)
        self.shrink_ray.force_outpost_omega_open()
        if self.shrink_ray_skips_enabled and self._ap_owned_gadgets.get(Rac5GadgetKeys.SHRINK_RAY, False):
            self.shrink_ray.skip_all()
        if self.shrink_ray_locations_enabled:
            for name in self.shrink_ray.check():
                self.send_location(name)

        # No-op unless a ghost has actually been spawned; self-deactivates on planet change.
        if self.planet.planet_id is not None:
            self.ghost_ratchet.keep_alive(self.planet.planet_id)

        self.planet.weapons.apply_experience_boost()
        # Skipped while the weapons vendor is open, since it zeroes every
        # weapon's level so the displayed price doesn't depend on level.
        if not self.weapon_vendor.active:
            self.planet.weapons.apply_progressive_leveling()
        self.player_bolts.apply_boost()
        self.player_health_exp.apply_boost()
        if self.nanotech_level_checks_enabled:
            for name in self.player_health_exp.check_level(self.planet.player.max_health):
                self.send_location(name)
        self._check_armour_pickups()
        self._check_vendor_purchases()
        self.planet.check_weapon_cycler(
            is_ap_owned=self._is_weapon_id_ap_owned, vendor_active=self.vendor_active,
            fallback_weapon_id=self._first_owned_weapon_id,
        )

    def _is_weapon_id_ap_owned(self, weapon_id: int) -> bool:
        """WEAPON_VENDOR_IDS-scheme id -> AP ownership, shared by
        WeaponCyclerInventory and QuickSelectState."""
        name = _CYCLER_ID_TO_WEAPON_NAME.get(weapon_id)
        if name is None:
            # Unknown id — fail closed rather than let it slip through unchallenged.
            return False
        return self._ap_owned_weapons.get(name, False) or self._ap_owned_gadgets.get(name, False)

    def _first_owned_weapon_id(self) -> int | None:
        """Lowest WEAPON_VENDOR_IDS id among AP-owned weapons (gadgets excluded),
        or None if AP hasn't granted any weapon yet; fills an empty current_weapon."""
        owned_ids = [
            WEAPON_VENDOR_IDS[name] for name, owned in self._ap_owned_weapons.items()
            if owned and name in WEAPON_VENDOR_IDS
        ]
        return min(owned_ids) if owned_ids else None

    def _check_armour_pickups(self) -> None:
        """Diff armour.game_armour before/after check_collected_armour() and send a
        location per newly-owned piece; record_pickup() rebinds rather than mutates,
        so `prev` safely captures the old state."""
        prev = self.armour.game_armour
        self.planet.check_collected_armour()
        current = self.armour.game_armour
        for set_key in ArmourStruct.SET_FIELDS:
            new_bits = int(getattr(current, set_key) or 0) & ~int(getattr(prev, set_key) or 0)
            if not new_bits:
                continue
            for piece in _ARMOUR_PIECES:
                if new_bits & int(piece):
                    loc = ARMOUR_FLAG_TO_LOCATION.get((set_key, piece))
                    if loc:
                        self.send_location(loc)

    def _suppress_forced_starter_items(self, changed: dict[str, list], is_vendor: bool) -> None:
        """Strip game-forced weapons/gadgets out of check_weapons()'s "changed" lists
        when not AP-owned, and zero them back in memory. Must react to the same read
        check_weapons() just did, or a later read could race the game's re-forcing."""
        if is_vendor:
            return
        wi = self.planet.weapons
        kept_weapons = []
        forced_this_tick: set[str] = set()
        for name in changed["weapons"]:
            if name in _GAME_FORCED_WEAPONS and not self._ap_owned_weapons.get(name, False):
                wi.set(name, False)
                wi.weapons[name] = False
                forced_this_tick.add(name)
                continue
            kept_weapons.append(name)
        changed["weapons"] = kept_weapons

        # A queued "reached level" for a forced-unlock weapon is equally spurious;
        # also drop the raw-level baseline so a future unlock starts fresh.
        if forced_this_tick:
            changed["levels"] = [
                (name, level) for name, level in changed["levels"] if name not in forced_this_tick
            ]
            for name in forced_this_tick:
                wi._raw_level.pop(name, None)

        kept_gadgets = []
        for name in changed["gadgets"]:
            if name in _GAME_FORCED_GADGETS and not self._ap_owned_gadgets.get(name, False):
                wi.set(name, False)
                wi.gadgets[name] = False
                continue
            kept_gadgets.append(name)
        changed["gadgets"] = kept_gadgets

    def _check_vendor_purchases(self) -> None:
        """Track weapons/mod-vendor open+close, calling weapon_vendor()/mod_vendor()
        every tick while open. check_weapons() is only read once per tick — VendorInventory
        calls it itself while open, so Core calls it here only for non-vendor bookkeeping."""
        current    = self.planet.menu.get()
        is_vendor  = current in (MenuStateValue.WEAPONS_VENDOR, MenuStateValue.MOD_VENDOR)
        was_vendor = self._prev_vendor in (MenuStateValue.WEAPONS_VENDOR, MenuStateValue.MOD_VENDOR)
        self._prev_vendor = current

        if is_vendor and not was_vendor:
            # Snapshot the wheel before the vendor menu takes over, then stop
            # polling — same freeze pattern PlanetInventory uses for transitions.
            self.quick_select.sync()
            self.quick_select.freeze()
            if current == MenuStateValue.WEAPONS_VENDOR:
                self.weapon_vendor.activate()
            else:
                self.mod_vendor.activate()
            self.on_vendor_open()
        elif was_vendor and not is_vendor:
            self.weapon_vendor.deactivate()
            self.mod_vendor.deactivate()
            self.vendor.close()
            # Write the pre-vendor snapshot back so any wheel slot the game
            # auto-assigned during the visit is reverted, not adopted.
            self.quick_select.restore()
            self.quick_select.unfreeze()
            self.on_vendor_close()

        if current == MenuStateValue.WEAPONS_VENDOR:
            self.vendor.weapon_vendor()
            return
        if current == MenuStateValue.MOD_VENDOR:
            self.vendor.mod_vendor()
            return

        changed = self.planet.check_weapons()

        # Must fire before _suppress_forced_starter_items() below, which
        # would otherwise discard this same transition as forced-unlock noise.
        for name in changed["gadgets"]:
            loc = _SCRIPTED_GADGET_LOCATIONS.get(name)
            if loc:
                self.send_location(loc)

        self._suppress_forced_starter_items(changed, is_vendor)

        # A newly-changed bonus-trigger weapon/gadget is a scripted world pickup,
        # not a purchase; gated to Pokitaru (the intro kiosk).
        if self.planet.planet_id == _POKITARU_ID:
            for name in changed["weapons"]:
                if name in _BONUS_TRIGGER_WEAPONS:
                    self.on_bonus_weapon_pickup(name)
            for name in changed["gadgets"]:
                if name in _SCRIPTED_PICKUP_GADGETS:
                    self.on_scripted_gadget_pickup(name)

        # Gated on the option directly rather than relying on send_location()'s
        # no-op, to skip the pointless check_locations() call entirely.
        if self.weapon_level_checks_enabled:
            for name, level in changed["levels"]:
                loc = WEAPON_LEVEL_LOOKUP.get((name, level))
                if loc:
                    self.send_location(loc)

        # Catches the level 4->5 Titan jump even when it happens organically
        # (Progressive Weapons) without ever opening the vendor to claim it.
        for name in changed["titans"]:
            titan_loc = TITAN_INTERNAL_TO_LOCATION.get(name)
            if titan_loc:
                self.planet.weapons.titan_purchased[name] = True
                self.send_location(titan_loc)

    def _handle_death(self) -> None:
        # The death sequence must see only physically-picked-up pieces, not AP-granted
        # ones never found; _handle_respawn() reverts to the full union afterward.
        self.armour.apply_collected_only()

        if not self.death_link_enabled():
            return
        self._death_count += 1
        if self._death_count > self.death_amnesty():
            cause = int(self.planet.player.movement_state)
            self.send_deathlink(cause)

    def _handle_respawn(self) -> None:
        self._death_count = 0
        self.armour.apply_full()

    def __repr__(self) -> str:
        return f"Core(planet_id={self.planet.planet_id}, is_ready={self.planet.is_ready})"
