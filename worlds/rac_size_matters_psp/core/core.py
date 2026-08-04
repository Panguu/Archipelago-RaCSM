from __future__ import annotations

import logging
from collections.abc import Callable

from ..constants import Rac5CutsceneLocations, Rac5Locations
from ..locations import WEAPON_LEVEL_LOOKUP
from .armour import ARMOUR_FLAG_TO_LOCATION, ArmourInventory, ArmourPiece, ArmourUnlocks
from .challenges import ChallengeInventory, SkyboardInventory
from .menu import MenuStateValue
from .missions import MissionInventory
from .planets import AUTO_UNLOCK_ADDRESSES, INFOBOT_UNLOCK_VALUE, PlanetInventory, PlanetUnlockState
from .player_bolts import PlayerBoltInventory
from .quick_select import QuickSelectState
from .skill_points import SkillPointInventory
from .skins import SkinInventory
from .titanium_bolts import TitaniumBoltInventory
from .vendor import WEAPON_VENDOR_IDS, ModVendorMenu, VendorInventory, WeaponVendorMenu
from ..pypsp import Psp

logger = logging.getLogger("CommonClient")

_ARMOUR_PIECES = (ArmourPiece.CHESTPLATE, ArmourPiece.HELMET, ArmourPiece.GLOVES, ArmourPiece.BOOTS)

# Bonus/scripted pickups detected via check_weapons()'s newly-changed lists.
# lacerator/acid_bomb_glove/hypershot are NOT included here — though they
# live at Pokitaru's kiosk, they're sold by Pokitaru's real vendor too and
# are meant to be checked only through that purchase flow; the game's forced
# auto-unlock of them is suppressed by _enforce_no_forced_starter_items()
# instead of being treated as a pickup.
_BONUS_TRIGGER_WEAPONS: frozenset[str] = frozenset({"concussion_gun"})
_SCRIPTED_PICKUP_GADGETS: frozenset[str] = frozenset()
# Gated to Pokitaru only: apply_inventory() re-applies every owned
# weapon/gadget onto whichever planet is active on load, so a bonus-trigger
# weapon's unlocked bit can flip 0->1 on ANY planet the first time it's
# re-synced this session, not just at the kiosk. Without this gate that
# resync would misfire as a kiosk pickup on an unrelated planet.
_POKITARU_ID: int = 0x01

# Scripted gadget handoffs with their OWN dedicated AP location, distinct
# from the mission/cutscene location that coincides with them (e.g.
# Sprout-o-Matic is handed over during Ryllus's "Buzzing Cameras" cutscene,
# but the two locations must fire independently; same for Shrink Ray during
# Kalidon's "Explore the planet"). Secondary signal alongside
# _MISSION_GADGET_LOCATION below — harmless if it never fires.
_SCRIPTED_GADGET_LOCATIONS: dict[str, str] = {
    "sprout_o_matic": Rac5Locations.RYLLUS_SPROUT,
    "shrink_ray":     Rac5Locations.KALIDON_SHRINK,
}

# Mission/cutscene location -> the gadget-pickup location that coincides
# with it in-game. Primary signal: missions.check() fires on the mission's
# own bit regardless of all_cutscenes, so it reliably fires even when
# _SCRIPTED_GADGET_LOCATIONS's gadget-unlock-bit signal above doesn't.
_MISSION_GADGET_LOCATION: dict[str, str] = {
    Rac5CutsceneLocations.RYLLUS_BUZZING: Rac5Locations.RYLLUS_SPROUT,
    Rac5CutsceneLocations.KALIDON_EXPLORE: Rac5Locations.KALIDON_SHRINK,
}

# The game's own tutorial/cutscene logic force-writes these items' unlocked
# bit to 1 regardless of AP ownership, independent of apply_inventory()'s
# resync. Unchecked, that forced write looks like a genuine pickup/purchase
# and — since ownership bools never regress True->False — permanently masks
# ever detecting a *real* purchase of the same item afterwards. Corrected
# back to AP truth every tick, before check_weapons() sees it — except
# sprout_o_matic/shrink_ray's own locations (above) must fire first, since
# the forced write is the only signal that event happened. shrink_ray is
# also force-granted client-side on Outpost Omega 1 (its facility puzzle
# needs it regardless of AP ownership), which flows through
# _ap_owned_gadgets already, so this correction leaves it alone there.
_GAME_FORCED_WEAPONS: frozenset[str] = frozenset({"lacerator", "acid_bomb_glove"})
# map_o_matic/box_breaker: sold at a vendor like lacerator/acid_bomb_glove
# above, but the game also force-grants them on its own — same forced-unlock
# class as hypershot, discovered later.
_GAME_FORCED_GADGETS: frozenset[str] = frozenset({
    "hypershot", "sprout_o_matic", "shrink_ray", "map_o_matic", "box_breaker",
})

# Weapon-cycler/quick-select id -> internal weapon/gadget name, reused from
# WEAPON_VENDOR_IDS's id scheme (array-slot index + 2). Ported from PS2,
# where this was confirmed accurate — UNVERIFIED on PSP specifically.
_CYCLER_ID_TO_WEAPON_NAME: dict[int, str] = {wid: name for name, wid in WEAPON_VENDOR_IDS.items()}


class Core:
    """Initial setup + per-tick orchestration for the whole client.

    Per-planet state juggling lives in PlanetInventory and the other
    *Inventory classes; this class constructs them once, then tick() pulls
    whatever changed from each check() and turns it into a send_location()
    call. It never pokes memory or reimplements detection logic itself.

    apply_inventory() takes a parsed AP snapshot (plain internal-name dicts;
    parsing items_received itself stays a client concern) and writes it via
    the Inventory get/set methods. restore_world_states()/
    restore_armour_from_locations() cover crash-recovery seed-from-checked-
    locations.

    NOT YET PORTED: the hybrid armour-set-combo check, the pickup-animation
    freeze/clear/rescan window (armour tracking here is pull-based via
    check_collected_armour() instead), and debug-button logging. Wrong-game-id
    detection is a client-layer concern, checked before any of this runs.
    """

    def __init__(self, pine: Psp, log: Callable[[str], None] | None = None) -> None:
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
        self.skill_points = SkillPointInventory(pine)
        self.missions     = MissionInventory(pine)
        self.skin         = SkinInventory(pine)

        # PlanetInventory is planet-agnostic — one instance rebinds itself to
        # whichever planet is loaded via check_transition().
        self.planet = PlanetInventory(pine, self.armour, self.quick_select)
        self.planet.on_death             = self._handle_death
        self.planet.on_respawn           = self._handle_respawn
        self.planet.on_equipped_armour_saved = lambda data: self.on_equipped_armour_saved(data)
        self.planet.on_pause_close       = self.quick_select.push_save

        # Slot-option gating — set directly by the client from slot_data;
        # check() just isn't called for a disabled system.
        self.clank_enabled:              bool = True
        self.clank_all_challenges:       bool = False
        self.skyboard_enabled:           bool = False
        self.skill_points_enabled:       bool = False
        self.weapon_level_checks_enabled: bool = False

        # Vendor purchase flow. send_location is a forwarding lambda, not
        # self.send_location itself — wire() replaces that attribute after
        # __init__ runs, and vendor must always call whatever it currently
        # points to, not the no-op default captured here.
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

        # True AP ownership as of the last apply_inventory() call — kept
        # separate from WeaponInventory.weapons/gadgets (which mirrors
        # whatever's in memory, including the game's own forced writes) so
        # _enforce_no_forced_starter_items() has an authoritative answer.
        self._ap_owned_weapons: dict[str, bool] = {}
        self._ap_owned_gadgets: dict[str, bool] = {}

        # Deathlink / goal
        self.send_location:      Callable[[str], None] = lambda _: None
        self.send_deathlink:     Callable[[int], None]  = lambda _: None
        self.death_amnesty:      Callable[[], int]      = lambda: 1
        self.death_link_enabled: Callable[[], bool]     = lambda: False
        self.on_goal:            Callable[[], None]     = lambda: None
        self._death_count: int = 0

        # Fired once, the tick a planet transition completes — the client
        # re-applies AP ownership itself in response, since it owns
        # items_received. on_initial_load fires only the very first time
        # (main_menu True -> False edge); on_planet_ready fires every time.
        self.on_planet_ready:  Callable[[], None] = lambda: None
        self.on_initial_load:  Callable[[], None] = lambda: None
        self._initial_load_done: bool = False

        # Vendor menu open/close — for hint-sending and armour-set-check
        # rescanning, neither of which this file owns.
        self.on_vendor_open:  Callable[[], None] = lambda: None
        self.on_vendor_close: Callable[[], None] = lambda: None

        # Fired by PlanetInventory.on_equipped_armour_saved, only on pause-menu-close.
        self.on_equipped_armour_saved: Callable[[dict[str, int]], None] = lambda _: None

        # Scripted (non-vendor) weapon/gadget pickups.
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
    #
    # Turns a fully-rebuilt AP inventory snapshot into game-memory writes via
    # the existing Inventory get/set methods — never raw pine pokes. The
    # client parses items_received into these plain internal-name structures
    # and calls apply_inventory() with the result.

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
        """Write a fully-rebuilt AP inventory snapshot into game memory.

        Called every tick (see PspMixin._poll_game()) to keep memory
        continuously synced with AP truth — but never while another window
        owns this memory for its own temporary purpose: a vendor session
        (weapons/gadgets/mods) or the death sequence / an armour-pickup
        animation (armour). Re-applying mid-window would fight those
        windows' own zero/restore cycles (see _handle_death() and
        PlanetInventory.check_collected_armour()).

        Planet/infobot unlock and armour are global addresses, safe to write
        any time. Weapons/gadgets/mods live on a per-planet array, so those
        are skipped while a planet transition is in flight or the vendor
        menu owns the weapon-display state.
        """
        self.planet_unlock.set_unlocked_planets(infobot_planets)
        # Kept current regardless of whether the memory write below is
        # skipped — check_collected_armour()'s pickup-exit restore and
        # _handle_respawn() both read this later.
        self.planet.sync_unlock_armour(armour_unlocked)
        if (not self.vendor_active and not self.planet.player.is_dead
                and not self.planet.player.is_picking_up):
            self.armour.sync_unlocked(armour_unlocked)

        # Always kept current even while the writes below are gated —
        # _enforce_no_forced_starter_items() needs an up-to-date answer to
        # "does AP actually own this" on every tick.
        self._ap_owned_weapons = dict(weapons)
        self._ap_owned_gadgets = dict(gadgets)
        # Pure bookkeeping (no memory write); apply_progressive_leveling()
        # (called every tick from tick()) turns this into level/experience
        # writes, gated on progressive_mode.
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

        # Re-baseline the weapons/gadgets/mods ownership dicts to match what
        # was just written, so the next check_weapons() doesn't mistake this
        # resync's own 0->1 transitions for a fresh purchase/pickup — this
        # runs on every planet load, so e.g. starting weapons would
        # otherwise look identical to a genuine first-time pickup.
        wi.sync_slots()
        # sync_slots() just mirrored whatever's in memory — the game can
        # force-write any weapon/gadget's unlocked bit on its own, so
        # anything baselined "owned" without AP granting it must be
        # corrected back out this same tick, or check() would treat it as
        # permanently owned and mask a later genuine purchase.
        self._sync_weapon_gadget_ownership()

        self._apply_mod_unlock_flags()

    def _sync_weapon_gadget_ownership(self) -> None:
        """Force every weapon/gadget's unlocked bit (memory + tracking dict)
        to match true AP ownership. Runs after sync_slots() re-baselines
        from raw memory, since a forced write can race back in during that
        exact read gap.

        A gadget with its own dedicated scripted-pickup location (see
        _SCRIPTED_GADGET_LOCATIONS) still needs that location fired when
        caught here losing an un-owned forced unlock — if apply_inventory()
        runs between the cutscene completing and the next tick, this is the
        only place left that sees the transition before it's corrected away."""
        wi = self.planet.weapons
        for name in wi._weapon_addrs:
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
        mod_unlock_N (the mod vendor's "purchasable" byte) per weapon mod
        slot based on vendor-region accessibility, which was removed along
        with the rest of the old vendor-unlock machinery."""
        pass

    # -- Crash-recovery restores ----------------------------------------------
    #
    # Seed bolt/skill-point/armour state from already-checked locations, for
    # reconnects where memory may be stale relative to the server.

    def restore_world_states(self, checked_locations: set[str]) -> None:
        self.bolts.sync_from_ap(checked_locations)
        self.bolts.sync()
        self.skill_points.sync_from_ap(checked_locations)
        self.skill_points.sync()
        for address in AUTO_UNLOCK_ADDRESSES:
            self.pine.write_int8(address, INFOBOT_UNLOCK_VALUE)

    def restore_armour_from_locations(self, checked_locations: set[str]) -> None:
        """Seed collected_armour bookkeeping from already-checked AP
        locations so a reconnect doesn't re-report an armour pickup already
        sent. Deliberately does NOT write game memory — a checked location
        only proves that spot was visited, not that this player owns the
        item. Memory is only ever written from unlock_armour, which
        reflects actual AP ownership."""
        loc_to_flag = {v: k for k, v in ARMOUR_FLAG_TO_LOCATION.items()}
        for loc_name in checked_locations:
            flag = loc_to_flag.get(loc_name)
            if flag:
                set_key, piece = flag
                self.planet.collected_armour[set_key] |= int(piece)

    # -- AP sync ----------------------------------------------------------------

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        """Fold already-checked AP locations into every completion-tracking
        Inventory, so a reconnect doesn't re-report anything the server
        already knows. armour_sets (hybrid combo checks) isn't ported yet,
        so it's not included here."""
        self.clank.sync_from_ap(checked_locations)
        self.skyboard.sync_from_ap(checked_locations)
        self.planet.weapons.sync_from_ap(checked_locations)
        self.skill_points.sync_from_ap(checked_locations)
        self.missions.sync_from_ap(checked_locations)
        self.restore_armour_from_locations(checked_locations)

    # -- Notifications ---------------------------------------------------------

    def notify(self, text: bytes | str) -> None:
        """In-game text-box notifications aren't supported on PSP. Log-only
        stand-in so every existing caller keeps working unchanged. Callers
        often still build messages with display_text.colored_text(), which
        embeds raw 0x90-prefixed colour-marker byte pairs and a trailing
        NUL — strip those out so the log line reads as plain text."""
        if isinstance(text, bytes):
            text = text.rstrip(b"\x00")
            parts = text.split(b"\x90")
            text = parts[0].decode("ascii", errors="replace")
            for part in parts[1:]:
                text += part[1:].decode("ascii", errors="replace")  # drop the colour-id byte after 0x90
        logger.info(f"[RAC] {text}")

    def tick(self) -> None:
        """One poll cycle, called once per tick by PspMixin's poll loop.
        Never manages its own timing or swallows errors, so a connection
        problem always surfaces to the caller.

        check_transition() gates everything else — every check_*/show_text
        call on PlanetInventory already no-ops while a planet transition is
        in flight, so nothing here needs to check that itself except the
        collections below that aren't part of PlanetInventory.
        """
        became_ready = self.planet.check_transition()
        self.planet.check_controller()
        self.planet.check_death()
        self.planet.check_equipped_armour()
        # Planet-unlock addresses are fixed/global, not per-planet-relative
        # like weapons/menu/player — safe (and necessary) to keep enforcing
        # every tick even while a transition is in flight, unlike everything
        # gated below on is_ready.
        self.planet_unlock.check()

        if not self.planet.is_ready:
            return

        if became_ready:
            if not self._initial_load_done:
                # First planet-ready this process — the save's weapon state
                # has never been touched by AP yet, so wipe it clean before
                # anything diffs against it. Otherwise whatever the save
                # already had (vanilla progress, a stale session) looks like
                # a batch of brand-new pickups the instant check_weapons()
                # first runs. apply_inventory() then writes true AP
                # ownership onto this clean array.
                self.planet.weapons.wipe()
                self.planet.weapon_cycler.initialize(self._first_owned_weapon_id)
            else:
                # Every later transition needs its level baseline reset, or
                # a mismatch between this planet's saved level and the last
                # one's _raw_level floods a location send per weapon per
                # level. See WeaponInventory.rebaseline_levels()'s docstring.
                self.planet.weapons.rebaseline_levels()
            self.skin.setup()
            if self.clank_enabled:
                # Unlocks every Clank Challenge section on every tracked
                # planet, independent of vanilla story-progress gating.
                # Idempotent, so re-running it every transition is harmless.
                # Addresses are CONFIRMED live on PSP, but keep the guard so
                # a future regression doesn't take the whole client down —
                # disable for the rest of the session on first failure
                # instead of retrying every transition.
                try:
                    self.clank.setup(self.clank_all_challenges)
                except Psp.RequestError as exc:
                    logger.warning(
                        f"[RAC] Clank Challenge addresses aren't verified yet on PSP ({exc}) — "
                        "disabling Clank Challenges for this session."
                    )
                    self.clank_enabled = False
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
        for name in self.missions.check():
            self.send_location(name)
            gadget_loc = _MISSION_GADGET_LOCATION.get(name)
            if gadget_loc:
                self.send_location(gadget_loc)
            if name == Rac5CutsceneLocations.QUODRONA_GOAL:
                self.on_goal()
        if self.clank_enabled:
            try:
                for name in self.clank.check(all_challenges=self.clank_all_challenges):
                    self.send_location(name)
            except Psp.RequestError as exc:
                logger.warning(
                    f"[RAC] Clank Challenge addresses aren't verified yet on PSP ({exc}) — "
                    "disabling Clank Challenges for this session."
                )
                self.clank_enabled = False
        if self.skyboard_enabled:
            try:
                for name in self.skyboard.check():
                    self.send_location(name)
            except Psp.RequestError as exc:
                logger.warning(
                    f"[RAC] Skyboard Challenge addresses aren't verified yet on PSP ({exc}) — "
                    "disabling Skyboard Challenges for this session."
                )
                self.skyboard_enabled = False

        self.planet.weapons.apply_experience_boost()
        # Skipped while the weapons vendor is open — it zeroes every
        # weapon's level for the duration of the visit (see
        # VendorInventory.weapon_vendor()), and this would fight that back
        # to the real level every tick.
        if not self.weapon_vendor.active:
            self.planet.weapons.apply_progressive_leveling()
        self.player_bolts.apply_boost()
        self._check_armour_pickups()
        self._check_vendor_purchases()
        self.planet.check_weapon_cycler(
            is_ap_owned=self._is_weapon_id_ap_owned, vendor_active=self.vendor_active,
            fallback_weapon_id=self._first_owned_weapon_id,
        )

    def _is_weapon_id_ap_owned(self, weapon_id: int) -> bool:
        """WEAPON_VENDOR_IDS-scheme id -> AP ownership, shared by
        WeaponCyclerInventory (current_weapon/stored_weapon) and
        QuickSelectState (wheel slots) — both reference weapons the same way
        the vendor's item list does (see _CYCLER_ID_TO_WEAPON_NAME)."""
        name = _CYCLER_ID_TO_WEAPON_NAME.get(weapon_id)
        if name is None:
            # Unknown id — fail closed rather than let it slip through unchallenged.
            return False
        return self._ap_owned_weapons.get(name, False) or self._ap_owned_gadgets.get(name, False)

    def _first_owned_weapon_id(self) -> int | None:
        """Lowest WEAPON_VENDOR_IDS id among AP-owned weapons (gadgets
        excluded — this fills the weapon cycler, not the gadget slot), or
        None if AP hasn't granted any weapon yet. Used by
        WeaponCyclerInventory.check() to fill an empty current_weapon."""
        owned_ids = [
            WEAPON_VENDOR_IDS[name] for name, owned in self._ap_owned_weapons.items()
            if owned and name in WEAPON_VENDOR_IDS
        ]
        return min(owned_ids) if owned_ids else None

    def _check_armour_pickups(self) -> None:
        """Diff collected_armour before/after check_collected_armour() and
        send a location for every newly-owned piece."""
        prev = dict(self.planet.collected_armour)
        self.planet.check_collected_armour()
        for set_key, mask in self.planet.collected_armour.items():
            new_bits = mask & ~prev.get(set_key, 0)
            if not new_bits:
                continue
            for piece in _ARMOUR_PIECES:
                if new_bits & int(piece):
                    loc = ARMOUR_FLAG_TO_LOCATION.get((set_key, piece))
                    if loc:
                        self.send_location(loc)

    def _suppress_forced_starter_items(self, changed: dict[str, list], is_vendor: bool) -> None:
        """Strip game-forced weapons/gadgets out of check_weapons()'s
        freshly-detected "changed" lists whenever they're not AP-owned and
        we're not at a vendor, and zero them back out in memory — the game
        keeps force-writing their unlocked bit on its own, and they're meant
        to be checked only via a genuine vendor purchase.

        Must react to the *same* read check_weapons() just did, not a
        separate later read: a second independent read/write pair racing
        the game's own continuous re-forcing could see it flip back to 1 in
        the gap, corrupting the purchase-detection baseline. Skipped
        entirely while genuinely at a vendor so it can never suppress a
        real purchase.
        """
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

        # check()'s level diffing only gates on is_unlocked, so any "reached
        # level" already queued for one of these weapons this tick is just
        # as spurious and must be stripped too. Also drop the raw-level
        # baseline check() just wrote so a genuine future unlock starts from
        # "never observed" again.
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
        """Track weapons/mod-vendor open+close, calling weapon_vendor()/
        mod_vendor() every tick while that menu stays open so VendorInventory
        can poll the D-pad toggle without blocking.

        check_weapons() is only ever read once per tick — VendorInventory
        calls it itself while a vendor is open, so Core only calls it here
        for the non-vendor bookkeeping below, while no vendor is open.
        """
        current    = self.planet.menu.get()
        is_vendor  = current in (MenuStateValue.WEAPONS_VENDOR, MenuStateValue.MOD_VENDOR)
        was_vendor = self._prev_vendor in (MenuStateValue.WEAPONS_VENDOR, MenuStateValue.MOD_VENDOR)
        self._prev_vendor = current

        if is_vendor and not was_vendor:
            # Snapshot the wheel as it stood right before the vendor menu
            # took over, then stop polling — same freeze pattern
            # PlanetInventory uses for planet transitions.
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
            # Revert any wheel slot the game auto-assigned during the vendor
            # visit (e.g. a newly bought weapon) rather than adopting it as
            # the player's own choice.
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

        # Gadgets with their own dedicated (non-vendor) location must fire
        # before _suppress_forced_starter_items() below, which would
        # otherwise discard this exact transition as forced-unlock noise.
        for name in changed["gadgets"]:
            loc = _SCRIPTED_GADGET_LOCATIONS.get(name)
            if loc:
                self.send_location(loc)

        self._suppress_forced_starter_items(changed, is_vendor)

        # A newly-changed bonus-trigger weapon or scripted-pickup gadget is a
        # scripted world pickup, not a purchase (we already returned above if
        # at a vendor). Gated to Pokitaru (where the intro kiosk lives) —
        # see _POKITARU_ID's comment for why.
        if self.planet.planet_id == _POKITARU_ID:
            for name in changed["weapons"]:
                if name in _BONUS_TRIGGER_WEAPONS:
                    self.on_bonus_weapon_pickup(name)
            for name in changed["gadgets"]:
                if name in _SCRIPTED_PICKUP_GADGETS:
                    self.on_scripted_gadget_pickup(name)

        # Gated on the option directly rather than relying on send_location()
        # being a silent no-op for an unpooled location — it still logs a
        # warning every time, which fired constantly with the option off.
        if self.weapon_level_checks_enabled:
            for name, level in changed["levels"]:
                loc = WEAPON_LEVEL_LOOKUP.get((name, level))
                if loc:
                    self.send_location(loc)

    def _handle_death(self) -> None:
        # The game's death sequence needs to see every piece the player has
        # physically picked up this session (collected_armour), not just
        # what AP granted (unlock_armour, which can include pieces the
        # player never physically found) — so this is a real downgrade, not
        # a no-op. Zero first so no unlock_armour-only bit can linger.
        # _handle_respawn() reverts back to AP truth once death is over.
        self.armour.sync_unlocked(dict.fromkeys(ArmourUnlocks._OFFSETS, 0))
        self.armour.sync_unlocked(self.planet.collected_armour)

        if not self.death_link_enabled():
            return
        self._death_count += 1
        if self._death_count > self.death_amnesty():
            cause = int(self.planet.player.movement_state)
            self.send_deathlink(cause)

    def _handle_respawn(self) -> None:
        self._death_count = 0
        self.armour.sync_unlocked(self.planet.unlock_armour)

    def __repr__(self) -> str:
        return f"Core(planet_id={self.planet.planet_id}, is_ready={self.planet.is_ready})"
