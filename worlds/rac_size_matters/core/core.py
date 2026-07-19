from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

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
from .vendor import ModVendorMenu, VendorInventory, WeaponVendorMenu

if TYPE_CHECKING:
    from ..pypine import Pine

logger = logging.getLogger("CommonClient")

_ARMOUR_PIECES = (ArmourPiece.CHESTPLATE, ArmourPiece.HELMET, ArmourPiece.GLOVES, ArmourPiece.BOOTS)

# Bonus/scripted pickups still detected outside vendor context (via
# check_weapons()'s newly-changed lists, same mechanism a vendor purchase
# uses). lacerator/acid_bomb_glove/hypershot are deliberately NOT included
# here — despite living at Pokitaru's kiosk, they're sold by Pokitaru's
# actual vendor too (see WEAPON_VENDOR_LOCATIONS/GADGET_VENDOR_LOCATIONS)
# and are meant to be checked only through that normal purchase flow; the
# game's own forced auto-unlock of them is suppressed entirely by
# _enforce_no_forced_starter_items() below instead of being treated as a
# pickup.
_BONUS_TRIGGER_WEAPONS: frozenset[str] = frozenset({"concussion_gun"})
_SCRIPTED_PICKUP_GADGETS: frozenset[str] = frozenset()
# apply_inventory() re-applies every owned weapon/gadget onto whichever
# planet's array is currently active, every time that planet loads — so a
# bonus-trigger weapon's unlocked bit can legitimately flip 0->1 on any
# planet the very first time this session it's re-synced, not just at
# Pokitaru's kiosk. Without this gate that resync gets misread as the
# scripted kiosk pickup itself and fires its location check the moment the
# player merely visits (or even just apply-inventory-resyncs on) an
# unrelated planet.
_POKITARU_ID: int = 0x01

# Scripted gadget handoffs that have their OWN dedicated AP location,
# distinct from the mission/cutscene location that coincides with them
# (e.g. Sprout-o-Matic is handed over during Ryllus's "Buzzing Cameras"
# cutscene, but "Ryllus: Receive Spout-O-Matic" and "Ryllus: Buzzing
# Cameras" are two separate locations that must both fire independently;
# same for Shrink Ray during Kalidon's "Explore the planet" cutscene).
# Internal gadget name -> its own location name. Kept as a secondary signal
# alongside _MISSION_GADGET_LOCATION below — harmless if it never fires
# (e.g. if the game doesn't actually force the gadget's unlock bit at that
# moment), and _append_location_by_name() dedupes either way.
_SCRIPTED_GADGET_LOCATIONS: dict[str, str] = {
    "sprout_o_matic": Rac5Locations.RYLLUS_SPROUT,
    "shrink_ray":     Rac5Locations.KALIDON_SHRINK,
}

# Mission/cutscene location -> the gadget-pickup location that coincides
# with it in-game. The primary signal for these: missions.check() fires on
# the mission struct's own bit regardless of whether all_cutscenes is
# enabled (that option only controls whether the mission location has a
# meaningful AP rule / is in this seed's pool — send_location() for a
# location not in the pool is already a safe no-op) — so it reliably fires
# even when _SCRIPTED_GADGET_LOCATIONS's gadget-unlock-bit signal above
# doesn't. Ryllus: Buzzing Cameras (mission) doubles as Ryllus: Receive
# Spout-O-Matic (gadget); Kalidon: Explore the planet doubles as Kalidon:
# Receive Shrink Ray.
_MISSION_GADGET_LOCATION: dict[str, str] = {
    Rac5CutsceneLocations.RYLLUS_BUZZING: Rac5Locations.RYLLUS_SPROUT,
    Rac5CutsceneLocations.KALIDON_EXPLORE: Rac5Locations.KALIDON_SHRINK,
}

# The game's own tutorial/cutscene logic keeps force-writing these items'
# unlocked bit to 1 on its own, regardless of AP ownership — completely
# independent of apply_inventory()'s resync. Left unchecked, that forced
# write (a) looks identical to a genuine kiosk pickup/vendor purchase the
# first time it happens, and (b) once check()/sync_slots() baseline it as
# "owned" (bool dicts never regress True->False), permanently prevents ever
# detecting a *real* purchase/pickup of the same item afterwards. Enforced
# back to actual AP-ownership truth every tick, before check_weapons() ever
# sees it — except sprout_o_matic/shrink_ray's own locations (above) still
# need to fire first, since the forced write is the only signal that event
# happened. shrink_ray is also force-granted client-side on Outpost Omega 1
# (see client/vendor.py's _parse_inventory — its facility puzzle needs it
# regardless of AP ownership); that flows through _ap_owned_gadgets too
# (set directly in the same "gadgets" dict apply_inventory() receives), so
# this correction correctly leaves it alone there.
_GAME_FORCED_WEAPONS: frozenset[str] = frozenset({"lacerator", "acid_bomb_glove"})
# map_o_matic/box_breaker: sold at a vendor (see core/vendor.py's
# _GADGET_TO_PLANET_KEY) same as lacerator/acid_bomb_glove above, but the
# game also force-grants them on its own at some point outside that
# purchase flow — same forced-unlock class as hypershot, just discovered
# later; without this they permanently latch "owned" the first time that
# happens, regardless of whether AP ever actually granted them.
_GAME_FORCED_GADGETS: frozenset[str] = frozenset({
    "hypershot", "sprout_o_matic", "shrink_ray", "map_o_matic", "box_breaker",
})


class Core:
    """Initial setup + per-tick orchestration for the whole client.

    Most of what the old GameOrchestrator did by hand — per-planet BaseState
    juggling, hotkey/vendor-toggle/debug-button polling, enter/exit lifecycle
    — now lives inside PlanetInventory and the other *Inventory classes. This
    class constructs them once, then each tick() pulls whatever changed from
    every check() and turns it into a send_location() call. It never pokes
    memory or reimplements that detection logic itself.

    Also replaces the old client-side InventoryMixin's memory-writing half:
    apply_inventory() takes a parsed AP snapshot (plain internal-name dicts —
    parsing items_received itself stays a client concern, it needs
    NetworkItem/item_names) and writes it via the same Inventory get/set
    methods everything else here uses. restore_world_states()/
    restore_armour_from_locations() cover the crash-recovery seed-from-
    checked-locations path.

    NOT YET PORTED from GameOrchestrator/client vendor.py: the hybrid
    armour-set-combo check (old ArmourSetCollectedState), the pickup-animation
    freeze/clear/rescan window (armour tracking here is purely pull-based via
    check_collected_armour() instead), and debug-button logging. Wrong-game-id
    detection is intentionally excluded — that's a client-layer concern now,
    checked before any of this runs.
    """

    def __init__(self, pine: Pine, log: Callable[[str], None] | None = None) -> None:
        self.pine = pine
        self._log = log or logger.info

        self.armour        = ArmourInventory(pine)
        self.quick_select  = QuickSelectState(pine)
        self.planet_unlock = PlanetUnlockState(pine)

        self.clank        = ChallengeInventory(pine)
        self.skyboard     = SkyboardInventory(pine)
        self.bolts        = TitaniumBoltInventory(pine)
        self.player_bolts = PlayerBoltInventory(pine)
        self.skill_points = SkillPointInventory(pine)
        self.missions     = MissionInventory(pine)
        self.skin         = SkinInventory(pine)

        # PlanetInventory is planet-agnostic — one instance rebinds itself to
        # whichever planet is loaded via check_transition(), instead of the
        # old dict of one PlanetState per planet.
        self.planet = PlanetInventory(pine, self.armour, self.quick_select)
        self.planet.on_death             = self._handle_death
        self.planet.on_respawn           = self._handle_respawn
        self.planet.on_equipped_armour_saved = lambda data: self.on_equipped_armour_saved(data)
        self.planet.on_pause_close       = self.quick_select.push_save

        # Slot-option gating — set directly by the client from slot_data (no
        # BaseState set_mode()/set_enabled() anymore; check() just isn't
        # called for a disabled system, and "all challenges" is passed
        # straight into clank.check() each tick instead of being stored on
        # ChallengeInventory itself).
        self.clank_enabled:              bool = True
        self.clank_all_challenges:       bool = False
        self.skyboard_enabled:           bool = False
        self.skill_points_enabled:       bool = False
        self.weapon_level_checks_enabled: bool = False

        # Vendor purchase flow.
        # send_location is a forwarding lambda, not self.send_location itself
        # — wire() replaces that attribute after __init__ runs, and vendor
        # must always call whatever it currently points to, not the no-op
        # default captured here at construction time.
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

        # True AP ownership, as of the last apply_inventory() call — kept
        # separate from WeaponInventory.weapons/gadgets (which just mirrors
        # whatever's currently in memory, including the game's own forced
        # writes) so _enforce_no_forced_starter_items() has an authoritative
        # answer to "does the player actually own this" independent of what
        # the game itself has written.
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
        # doesn't own items_received here, so it re-applies AP ownership
        # itself (apply_inventory() again) in response instead of this file
        # trying to do it without that data. on_initial_load fires only the
        # very first time (main_menu True -> False edge); on_planet_ready
        # fires on every transition after that too.
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
    # the existing Inventory get/set/(set_mod/set_level/set_mod_unlock)
    # methods — never raw pine pokes. The client parses items_received into
    # these plain internal-name structures (it owns NetworkItem/item_names,
    # not this file) and calls apply_inventory() with the result.

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

        Called every tick during normal gameplay (see PineMixin._poll_game())
        so memory is continuously kept in sync with AP truth rather than only
        at specific event boundaries — but never while some other window
        owns this same memory for its own temporary purpose: a vendor
        session (weapons/gadgets/mods — existing is_ready/vendor_active
        guard below), or the death sequence / an armour-pickup animation
        (armour — its own guard just below). Re-applying mid-window would
        fight those windows' own zero/restore cycles (see _handle_death()
        and PlanetInventory.check_collected_armour()).

        Planet/infobot unlock and armour are global addresses, safe to write
        any time otherwise. Weapons/gadgets/mods live on a per-planet array,
        so those are skipped while a planet transition is in flight or the
        vendor menu owns the weapon-display state — same guards the old
        writes_blocked/vendor_active checks provided.
        """
        self.planet_unlock.set_unlocked_planets(infobot_planets)
        # Bookkeeping dict always kept current regardless of whether the
        # memory write below is skipped — check_collected_armour()'s
        # pickup-exit restore and _handle_respawn() both read this later.
        self.planet.sync_unlock_armour(armour_unlocked)
        if (not self.vendor_active and not self.planet.player.is_dead
                and not self.planet.player.is_picking_up):
            self.armour.sync_unlocked(armour_unlocked)

        # Always kept current, even while the writes below are skipped —
        # _enforce_no_forced_starter_items() needs an up-to-date answer to
        # "does AP actually own this" on every tick regardless of whether a
        # planet happens to be mid-transition or the vendor is open.
        self._ap_owned_weapons = dict(weapons)
        self._ap_owned_gadgets = dict(gadgets)
        # Level caps are pure bookkeeping (no memory write), so keep them
        # current the same way as _ap_owned_weapons above, regardless of
        # whether writes are gated below — apply_progressive_leveling()
        # (called every tick from tick()) is what actually turns this into
        # level/experience writes, gated on progressive_mode.
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
        # was just written, so the next check_weapons() doesn't see this
        # re-sync's own 0->1 transitions and mistake already-owned items for
        # a fresh vendor purchase or scripted kiosk pickup. This resync runs
        # on every planet load (any owned item gets re-applied onto whatever
        # planet's array is now active) — without this, e.g. starting
        # weapons look identical to a genuine first-time pickup the moment
        # the very first planet finishes loading.
        wi.sync_slots()
        # sync_slots() just mirrored whatever's currently in memory — the
        # game can force-write any weapon/gadget's unlocked bit on its own
        # (not just the known lacerator/acid_bomb_glove/hypershot handful),
        # so anything that got baselined as "owned" here without AP actually
        # granting it needs to be corrected back out the same tick, or
        # check() would treat it as permanently owned (never regresses
        # owned->not-owned) and mask any later genuine purchase.
        self._sync_weapon_gadget_ownership()

        self._apply_mod_unlock_flags()

    def _sync_weapon_gadget_ownership(self) -> None:
        """Force every weapon/gadget's unlocked bit (memory + tracking dict)
        to match true AP ownership: zero out anything AP doesn't own that's
        currently reading as unlocked (the game force-writing it, a stale
        vendor-display leftover, etc.), and unlock anything AP does own that
        isn't. Runs after sync_slots() re-baselines from raw memory, since a
        forced write can race back in during that exact read gap — the
        correction has to look at the freshest snapshot, not values written
        moments earlier.

        A gadget with its own dedicated scripted-pickup location (see
        _SCRIPTED_GADGET_LOCATIONS) still needs that location fired when
        caught here losing an un-owned forced unlock — sync_slots() runs
        independently of check_weapons()'s tick-by-tick diffing, so if
        apply_inventory() happens to run between the cutscene completing and
        the next tick, this is the only place left that ever sees the
        transition before it gets corrected away."""
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
    # Seed + write bolt/skill-point/armour state from already-checked
    # locations — for reconnects where memory may be stale/reset relative to
    # what the server already knows was collected.

    def restore_world_states(self, checked_locations: set[str]) -> None:
        self.bolts.sync_from_ap(checked_locations)
        self.bolts.sync()
        self.skill_points.sync_from_ap(checked_locations)
        self.skill_points.sync()
        for address in AUTO_UNLOCK_ADDRESSES:
            self.pine.write_int8(address, INFOBOT_UNLOCK_VALUE)

    def restore_armour_from_locations(self, checked_locations: set[str]) -> None:
        """Seed collected_armour bookkeeping from already-checked AP
        locations so a reconnect doesn't re-detect (and re-report) an armour
        pickup that's already been sent. Deliberately does NOT write game
        memory here — a checked location only proves that spot was visited,
        not that this player owns the item that was there. Memory is only
        ever written from unlock_armour (via apply_inventory/
        check_collected_armour), which reflects actual AP ownership."""
        loc_to_flag = {v: k for k, v in ARMOUR_FLAG_TO_LOCATION.items()}
        for loc_name in checked_locations:
            flag = loc_to_flag.get(loc_name)
            if flag:
                set_key, piece = flag
                self.planet.collected_armour[set_key] |= int(piece)

    # -- AP sync ----------------------------------------------------------------

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        """Fold already-checked AP locations into every completion-tracking
        Inventory, so a reconnect or late-joining sync doesn't re-report
        anything the server already knows about. Covers both the "Connected"
        and "ReceivedItems" sync points — armour_sets (hybrid combo checks)
        isn't ported yet, so it's not included here."""
        self.clank.sync_from_ap(checked_locations)
        self.skyboard.sync_from_ap(checked_locations)
        self.planet.weapons.sync_from_ap(checked_locations)
        self.skill_points.sync_from_ap(checked_locations)
        self.missions.sync_from_ap(checked_locations)
        self.restore_armour_from_locations(checked_locations)

    # -- Notifications ---------------------------------------------------------

    def notify(self, text: bytes | str) -> None:
        """Show a small text-box notification, unless a menu is open or a
        planet transition is in flight (PlanetInventory.show_text() already
        no-ops on the latter)."""
        if self.planet.menu.get() not in (None, MenuStateValue.CLOSED):
            return
        self.planet.show_text(text)

    def tick(self) -> None:
        """One poll cycle. Called by the client's own poll loop (PineMixin)
        once per tick, after it's already verified the connection/game — this
        never manages its own timing or swallows its own errors, so a
        connection problem always surfaces to the caller instead of being
        silently absorbed here.

        check_transition() gates everything else — every check_*/show_text
        call on PlanetInventory already no-ops while a planet transition is
        in flight (is_ready False), so nothing here needs to check that
        itself except the collections below that aren't part of
        PlanetInventory.
        """
        became_ready = self.planet.check_transition()
        self.planet.check_controller()
        self.planet.check_death()
        self.planet.check_equipped_armour()

        if not self.planet.is_ready:
            return

        if became_ready:
            if not self._initial_load_done:
                # Very first planet-ready this process — the save's weapon/
                # gadget/mod/level state has never been touched by AP yet,
                # so wipe it clean before anything below ever diffs against
                # it. Without this, whatever the save already had (vanilla
                # progress, a stale prior session) looks identical to a
                # batch of brand-new pickups/level-ups the instant
                # check_weapons() first runs, since every raw baseline
                # starts blank/-1. apply_inventory() (fired moments later
                # via on_planet_ready, below) then writes true AP ownership
                # onto this now-clean array.
                self.planet.weapons.wipe()
            self.skin.setup()
            if self.clank_enabled:
                # Unlocks every Clank Challenge section (Derby/Gadgetbot Toss/
                # Gadgetbot) on every tracked planet — fixed per-planet
                # addresses, safe to call regardless of which planet is
                # currently loaded (see CLANK_SECTION_UNLOCK_ADDRESSES).
                # Never wired in before this, so challenge sections stayed
                # locked behind whatever vanilla story progress unlocks them,
                # independent of AP's own reachability logic. Idempotent, so
                # re-running it on every transition is harmless.
                self.clank.setup(self.clank_all_challenges)
            self.on_planet_ready()
            if not self._initial_load_done:
                self._initial_load_done = True
                self.on_initial_load()

        self.planet_unlock.check()
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
            for name in self.clank.check(all_challenges=self.clank_all_challenges):
                self.send_location(name)
        if self.skyboard_enabled:
            for name in self.skyboard.check():
                self.send_location(name)

        self.planet.weapons.apply_experience_boost()
        # Skipped while the weapons vendor is open — it zeroes every
        # weapon's level for the duration of the visit (see
        # VendorInventory.weapon_vendor()) to stop the displayed price from
        # depending on level; this would otherwise fight that back to the
        # real level every tick.
        if not self.weapon_vendor.active:
            self.planet.weapons.apply_progressive_leveling()
        self.player_bolts.apply_boost()
        self._check_armour_pickups()
        self._check_vendor_purchases()

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
        """Strip lacerator/acid_bomb_glove/hypershot out of check_weapons()'s
        freshly-detected "changed" lists whenever they're not AP-owned and
        we're not at a vendor, and immediately zero them back out in memory
        — the game keeps force-writing their unlocked bit on its own,
        regardless of AP ownership, and they're meant to be checked only via
        a genuine vendor purchase.

        Must react to the *same* read check_weapons() just did, not a
        separate later read: PINE round-trips take real wall-clock time, so
        a second independent read/write pair racing the game's own
        continuous re-forcing could see it flip back to 1 again in the gap,
        corrupting the "was this a genuine purchase" baseline check_weapons()
        relies on for detecting the real thing once the player actually buys
        it. Skipped entirely while genuinely at a vendor so it can never
        suppress (or interfere with the baseline for) a real purchase.
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

        # check()'s level diffing only gates on is_unlocked, so it has no way
        # to know the game's forced unlock above isn't real AP ownership —
        # any "reached level" it already queued for one of these weapons
        # this same tick is just as spurious as the "newly unlocked" entry
        # was, and must be stripped too. Also drop the raw-level baseline
        # check() just wrote so a genuine future unlock (real AP ownership,
        # or a vendor purchase) starts from "never observed" again instead
        # of silently comparing against this suppressed reading and seeing
        # no change.
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
        mod_vendor() every tick while that menu stays open (not just once on
        open) so VendorInventory can poll the D-pad toggle without blocking.

        check_weapons() is only ever read once per tick — VendorInventory
        calls it itself while a vendor is open (it owns the purchase -> AP-
        location mapping now), so Core only calls it here for the non-vendor
        bookkeeping below, and only while no vendor is open.
        """
        current    = self.planet.menu.get()
        is_vendor  = current in (MenuStateValue.WEAPONS_VENDOR, MenuStateValue.MOD_VENDOR)
        was_vendor = self._prev_vendor in (MenuStateValue.WEAPONS_VENDOR, MenuStateValue.MOD_VENDOR)
        self._prev_vendor = current

        if is_vendor and not was_vendor:
            # Snapshot the wheel as it stood right before the vendor menu
            # took over, then stop polling — same freeze pattern
            # PlanetInventory uses for transitions, just triggered by the
            # vendor menu instead of a planet change.
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
            # Write the pre-vendor snapshot back before resuming polling, so
            # any wheel slot the game auto-assigned during the vendor visit
            # (e.g. a newly bought weapon) is reverted rather than adopted
            # as the player's own choice.
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
        # before _suppress_forced_starter_items() below — that call would
        # otherwise discard this exact same transition as forced-unlock
        # noise before anything else gets a chance to see it.
        for name in changed["gadgets"]:
            loc = _SCRIPTED_GADGET_LOCATIONS.get(name)
            if loc:
                self.send_location(loc)

        self._suppress_forced_starter_items(changed, is_vendor)

        # Any newly-changed bonus-trigger weapon or scripted-pickup gadget is
        # a scripted world pickup, not a purchase (we're not at a vendor —
        # already returned above otherwise). Only genuine on Pokitaru (where
        # the intro kiosk lives) — apply_inventory() re-syncs every owned
        # weapon/gadget onto whichever planet's array is currently active, so
        # this same 0->1 transition happens the first time it's re-applied on
        # ANY planet without the gate, misfiring the kiosk-pickup hook every
        # time the player merely visits an unrelated planet.
        if self.planet.planet_id == _POKITARU_ID:
            for name in changed["weapons"]:
                if name in _BONUS_TRIGGER_WEAPONS:
                    self.on_bonus_weapon_pickup(name)
            for name in changed["gadgets"]:
                if name in _SCRIPTED_PICKUP_GADGETS:
                    self.on_scripted_gadget_pickup(name)

        # Weapon Level Checks — gated on the option directly rather than
        # relying on send_location() being a no-op for an unpooled location:
        # that no-op still logs a "not in server locations" warning every
        # time (see _append_location_by_name), which fired constantly with
        # the option off whenever check_weapons() saw a level change (e.g.
        # during the death sequence, which doesn't gate this call).
        if self.weapon_level_checks_enabled:
            for name, level in changed["levels"]:
                loc = WEAPON_LEVEL_LOOKUP.get((name, level))
                if loc:
                    self.send_location(loc)

    def _handle_death(self) -> None:
        # The game's own death sequence needs to see every piece the player
        # has physically picked up this session (collected_armour), not just
        # what AP has actually granted (unlock_armour). Memory going into
        # this is normal-gameplay state (unlock_armour, which can include
        # pieces AP granted but the player never physically found), so this
        # is a real downgrade, not a no-op write — zero first (same
        # defensive pattern as check_collected_armour()'s pickup window) so
        # no unlock_armour-only bit can linger, then write collected_armour.
        # _handle_respawn() below reverts it back to AP truth once the death
        # sequence is over.
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
