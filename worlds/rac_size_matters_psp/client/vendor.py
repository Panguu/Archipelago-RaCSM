from __future__ import annotations

import random

from ..core import (
    ALL_TRAPS,
    INFOBOT_ITEM_TO_PLANET,
    WEAPON_MAX_LEVELS,
    TextColour,
    activate_trap,
    colored_text,
)
from ..core.address_maps import PLAYER_BOLT_COUNT
from ..core.player_bolts import MAX_PLAYER_BOLTS
from ..items import (
    ARMOUR_DISPLAY_TO_INTERNAL,
    ARMOUR_PIECE_BITMASKS,
    ARMOUR_SET_DISPLAY_TO_INTERNAL,
    GADGET_DISPLAY_TO_INTERNAL,
    PROGRESSIVE_ARMOUR_NAME,
    PROGRESSIVE_MOD_NAME,
    PROGRESSIVE_WEAPON_NAME,
    WEAPON_DISPLAY_TO_INTERNAL,
    WEAPON_MOD_NAME_TO_SLOT,
)
from ..locations import GADGET_INTERNAL_TO_LOCATION, WEAPON_INTERNAL_TO_LOCATION

# Mirrors _OUTPOST_OMEGA_1_ID in core/orchestration/_planet_lifecycle.py.
_OUTPOST_OMEGA_1_PLANET_ID = 0x06

PROGRESSIVE_WEAPON_NAME_REVERSE = {v: k for k, v in PROGRESSIVE_WEAPON_NAME.items()}
PROGRESSIVE_ARMOUR_NAME_REVERSE = {v: k for k, v in PROGRESSIVE_ARMOUR_NAME.items()}
PROGRESSIVE_MOD_NAME_REVERSE = {v: k for k, v in PROGRESSIVE_MOD_NAME.items()}

# WEAPON_MOD_NAME_TO_SLOT / progressive-mod counts give 1-indexed slot
# numbers — WeaponInventory.set_mod() wants the struct field name.
_SLOT_ATTR: dict[int, str] = {1: "mod_slot_one", 2: "mod_slot_two", 3: "mod_slot_three"}


class VendorHandlerMixin:
    async def _send_vendor_hints(self) -> None:
        """Send AP location hints for all currently purchasable vendor items.

        Called each time the vendor menu opens. Skips locations that have already
        been hinted or checked this session.

        Whichever vendor menu is open at this instant (weapon_vendor/mod_vendor
        activate() before Core fires on_vendor_open — see
        Core._check_vendor_purchases()) decides which of VendorInventory's two
        location lists to hint; neither being active means this fired from some
        other event entirely, so there's nothing to hint.
        """
        if self.slot is None or not self.psp_connected:
            return
        vendor = self._wiring.vendor
        if self._wiring.weapon_vendor.active:
            loc_names = vendor.purchasable_locations()
        elif self._wiring.mod_vendor.active:
            loc_names = vendor.mod_locations()
        else:
            return
        checked   = self.checked_locations | self._locally_checked_locations
        server_locations = getattr(self, "server_locations", None)
        new_ids: list[int] = []
        for name in loc_names:
            loc_id = self._location_name_to_id.get(name)
            if loc_id is None or loc_id in self._already_hinted or loc_id in checked:
                continue
            # Not every location in the static table exists in this seed —
            # e.g. mods/armour-set/skyboard checks disabled by slot options
            # remove them from the world entirely. Don't hint a location the
            # server doesn't know about for this slot.
            if server_locations is not None and loc_id not in server_locations:
                continue
            new_ids.append(loc_id)
        if not new_ids:
            return
        await self.send_msgs([
            {"cmd": "LocationScouts", "locations": new_ids, "create_as_hint": 2}
        ])
        self._already_hinted.update(new_ids)


# Inventory application
#
# Parses items_received into plain internal-name structures (this needs
# NetworkItem/item_names, a client concern) and hands them to
# Core.apply_inventory(), which writes them into game memory via the same
# Inventory get/set methods everything else uses — nothing here pokes pine
# directly except the bolt/trap filler grants below, which aren't tied to any
# Inventory class.

class InventoryMixin:
    def _parse_inventory(self) -> dict:
        """Rebuild the full AP inventory snapshot from items_received."""
        weapon_prog_counts:     dict[str, int] = {}
        weapon_mod_prog_counts: dict[str, int] = {}
        armour_prog_counts:     dict[str, int] = {}
        weapon_unlocked:  dict[str, bool]     = {}
        gadget_unlocked:  dict[str, bool]     = {}
        weapon_mod_slots: dict[str, set[str]] = {}
        armour_unlocked:  dict[str, int]      = {}
        infobot_planets:  set[str]            = set()

        for network_item in self.items_received:
            item_name = self.item_names[self.game].get(network_item.item, "")

            if item_name in PROGRESSIVE_WEAPON_NAME_REVERSE:
                display = PROGRESSIVE_WEAPON_NAME_REVERSE[item_name]
                weapon_prog_counts[display] = weapon_prog_counts.get(display, 0) + 1
                continue
            if item_name in PROGRESSIVE_MOD_NAME_REVERSE:
                display = PROGRESSIVE_MOD_NAME_REVERSE[item_name]
                weapon_mod_prog_counts[display] = weapon_mod_prog_counts.get(display, 0) + 1
                continue
            if item_name in WEAPON_MOD_NAME_TO_SLOT:
                mod_display, slot = WEAPON_MOD_NAME_TO_SLOT[item_name]
                mod_internal = WEAPON_DISPLAY_TO_INTERNAL.get(mod_display)
                if mod_internal:
                    weapon_mod_slots.setdefault(mod_internal, set()).add(_SLOT_ATTR[slot])
                continue
            if item_name in PROGRESSIVE_ARMOUR_NAME_REVERSE:
                display = PROGRESSIVE_ARMOUR_NAME_REVERSE[item_name]
                armour_prog_counts[display] = armour_prog_counts.get(display, 0) + 1
                continue

            if item_name in INFOBOT_ITEM_TO_PLANET:
                infobot_planets.add(INFOBOT_ITEM_TO_PLANET[item_name].upper())
            elif item_name in WEAPON_DISPLAY_TO_INTERNAL:
                weapon_unlocked[WEAPON_DISPLAY_TO_INTERNAL[item_name]] = True
            elif item_name in GADGET_DISPLAY_TO_INTERNAL:
                gadget_unlocked[GADGET_DISPLAY_TO_INTERNAL[item_name]] = True
            elif item_name in ARMOUR_DISPLAY_TO_INTERNAL:
                set_key, piece = ARMOUR_DISPLAY_TO_INTERNAL[item_name]
                armour_unlocked[set_key] = armour_unlocked.get(set_key, 0) | int(piece)

        for display, count in armour_prog_counts.items():
            internal = ARMOUR_SET_DISPLAY_TO_INTERNAL.get(display)
            if not internal:
                continue
            bitmask = 0
            for i, bit in enumerate(ARMOUR_PIECE_BITMASKS):
                if i < count:
                    bitmask |= bit
            armour_unlocked[internal] = armour_unlocked.get(internal, 0) | bitmask

        # Progressive weapons: first copy unlocks, each further copy levels up
        weapon_levels: dict[str, int] = {}
        for display, count in weapon_prog_counts.items():
            internal = WEAPON_DISPLAY_TO_INTERNAL.get(display)
            if not internal:
                continue
            if count >= 1:
                weapon_unlocked[internal] = True
            weapon_levels[internal] = min(max(0, count - 1), WEAPON_MAX_LEVELS.get(internal, 1) - 1)

        # Progressive mods: each copy unlocks the next mod slot in sequence
        for display, count in weapon_mod_prog_counts.items():
            internal = WEAPON_DISPLAY_TO_INTERNAL.get(display)
            if not internal:
                continue
            slots = {_SLOT_ATTR[i] for i in range(1, count + 1) if i in _SLOT_ATTR}
            weapon_mod_slots.setdefault(internal, set()).update(slots)

        # Outpost Omega 1's facility puzzle requires the Shrink Ray regardless
        # of AP ownership — force it on here (not recorded as owned) so every
        # re-apply on this planet keeps it unlocked without granting the item.
        if self._wiring.planet.planet_id == _OUTPOST_OMEGA_1_PLANET_ID:
            gadget_unlocked["shrink_ray"] = True

        return {
            "weapons":         weapon_unlocked,
            "gadgets":         gadget_unlocked,
            "weapon_levels":   weapon_levels,
            "weapon_mods":     weapon_mod_slots,
            "armour_unlocked": armour_unlocked,
            "infobot_planets": infobot_planets,
        }

    async def force_sync(self) -> None:
        """Force the player's in-game state to match what was received from AP,
        regardless of what's already been applied.

        Wipes the current planet's weapon/gadget/mod array first (see
        WeaponInventory.wipe()) so any leftover non-AP state — vanilla
        progress, a stale prior session — is fully replaced by AP truth
        instead of merely topped up on top of it, same reasoning as the
        one-time wipe Core.tick() does on the very first planet-ready.
        Skipped if the planet isn't ready yet (nothing to wipe) or a
        vendor menu owns the display right now (that window has its own
        zero/restore cycle already; wiping here would just get clobbered
        by it) — apply_inventory() below already no-ops its own writes in
        both cases, so wiping here would otherwise leave the array blank
        with nothing to immediately rewrite it.
        """
        if not self.psp_connected:
            return
        inventory = self._parse_inventory()
        checked   = self._checked_location_names()
        async with self._psp_lock:
            wiring = self._wiring
            if wiring.planet.is_ready and not wiring.vendor_active:
                wiring.planet.weapons.wipe()
            wiring.apply_inventory(**inventory)
            wiring.restore_world_states(checked)
            wiring.restore_armour_from_locations(checked)
        self._pending_item_apply = False

    async def _apply_received_items(self) -> None:
        if not self.psp_connected:
            self._pending_item_apply = True
            return
        if not self.items_received:
            return
        inventory = self._parse_inventory()
        async with self._psp_lock:
            self._wiring.apply_inventory(**inventory)
            # Bolts/traps are simple filler grants, unrelated to any
            # Inventory class — apply immediately regardless of planet
            # readiness (their addresses are global).
            if self._filler_checkpoint_synced:
                self._grant_new_bolt_items()
                self._grant_new_trap_items()
                await self._persist_filler_checkpoint()
        self._show_new_item_notifications()
        self._pending_item_apply = False

    async def _persist_filler_checkpoint(self) -> None:
        """Persist how far into items_received bolts/traps have been granted,
        so a client restart can resume from here instead of re-granting
        everything or losing track of what's actually been applied (see
        _filler_applied_key/_filler_checkpoint_synced in context.py).

        "max" rather than "replace" guards against this client racing a
        slightly-behind stale read of its own previous checkpoint.
        """
        checkpoint = max(self._processed_item_count, self._processed_trap_count)
        await self.send_msgs([{
            "cmd": "Set",
            "key": self._filler_applied_key(),
            "default": 0,
            "want_reply": False,
            "operations": [{"operation": "max", "value": checkpoint}],
        }])

    async def _restore_world_states(self) -> None:
        """Seed and apply bolt/skill-point/armour state from already-checked
        locations. Called only on connection events (crash recovery)."""
        if not self.psp_connected:
            return
        checked = self._checked_location_names()
        async with self._psp_lock:
            self._wiring.restore_world_states(checked)
            self._wiring.restore_armour_from_locations(checked)

    # Bonus weapon pickup / intro-scripted vendor locations

    def _grant_random_bonus_item(self, trigger_name: str) -> None:
        """Called whenever lacerator/acid_bomb_glove/concussion_gun's unlocked
        bit transitions 0->1 in memory — both when the player picks one at
        Pokitaru's intro kiosk (a scripted event, not a normal vendor menu
        purchase) and when we ourselves re-write that same bit while
        re-applying an already-AP-owned weapon.

        Guarding on "is trigger_name already AP-owned" is wrong when
        trigger_name was precollected/received before the player ever visits
        the kiosk: our own resync write flips the bit first, so the real
        in-game pickup never shows up as a 0->1 transition, and the location
        never gets checked. Guard on whether the *location* was already
        checked instead — _append_location_by_name() already dedupes against
        that, so this only needs to skip the redundant bonus-item roll.
        """
        if not self.psp_connected or not self._wiring.planet.is_ready:
            return
        wi = self._wiring.planet.weapons
        loc = WEAPON_INTERNAL_TO_LOCATION.get(trigger_name)
        already_checked = loc is not None and loc in self._checked_location_names()
        if already_checked:
            return
        if loc:
            self._log(f"[RAC] Intro weapon picked: {trigger_name!r} -> loc={loc!r}")
            self._append_location_by_name(loc)
        candidates = [name for name in wi.weapons if wi.weapons[name] and name != trigger_name]
        candidates += [name for name in wi.gadgets if wi.gadgets[name]]
        if not candidates:
            return
        wi.set(random.choice(candidates), True)

    def _handle_scripted_gadget_pickup(self, trigger_name: str) -> None:
        """Called whenever hypershot's unlocked bit transitions 0->1.

        Hypershot is handed to the player during Pokitaru's tutorial as a
        scripted event, not a normal gadget-vendor purchase. Same
        already-checked-location guard as _grant_random_bonus_item, for the
        same reason — this also fires on our own re-apply writes.
        """
        if not self.psp_connected or not self._wiring.planet.is_ready:
            return
        loc = GADGET_INTERNAL_TO_LOCATION.get(trigger_name)
        if loc is not None and loc in self._checked_location_names():
            return
        if loc:
            self._log(f"[RAC] Intro gadget picked: {trigger_name!r} -> loc={loc!r}")
            self._append_location_by_name(loc)

    def _write_notification_text(self, msg: bytes) -> None:
        if not self.psp_connected:
            return
        self._wiring.notify(msg)

    def _show_new_item_notifications(self) -> None:
        new_items = self.items_received[self._notification_item_index:]
        self._notification_item_index = len(self.items_received)
        if not new_items or not self.psp_connected:
            return
        net_item = new_items[-1]
        item_name   = self.item_names[self.game].get(net_item.item, "???")
        player_name = self.player_names.get(net_item.player, f"Player {net_item.player}")
        msg = colored_text(
            "Received ", TextColour.PURPLE, item_name,
            TextColour.WHITE, " from ", TextColour.ORANGE, player_name, TextColour.WHITE,
        )
        self._write_notification_text(msg)

    def _grant_new_bolt_items(self) -> None:
        # PLAYER_BOLT_COUNT is a global address — safe to write during a transition.
        # Starting bolts (the precollected "Bolts" item, if starting_bolts>0)
        # are granted separately by _grant_starting_items(), fired from
        # on_planet_ready and gated on a flag persisted to AP data storage —
        # not here, since that grant needs to happen once a planet has
        # actually loaded, not merely once this filler scan runs. This scan
        # only needs to skip counting that one precollected item as generic
        # filler, which it can determine purely from checkpoint position:
        # precollected items are always the earliest entries in
        # items_received, so the precollected Bolts item (if any) only ever
        # appears in a scan starting from checkpoint 0 — a later scan
        # (checkpoint already > 0) never sees it again regardless of
        # _grant_starting_items()'s own timing, avoiding any race between
        # the two.
        starting_bolts = int(self.slot_data.get("starting_bolts", 0))
        skipped_precollected = self._processed_item_count != 0
        new_items = self.items_received[self._processed_item_count:]
        self._processed_item_count = len(self.items_received)

        bolt_items_to_grant = 0
        for network_item in new_items:
            item_name = self.item_names[self.game].get(network_item.item, "")
            if item_name != "Bolts":
                continue
            if starting_bolts and not skipped_precollected:
                skipped_precollected = True
                continue
            bolt_items_to_grant += 1

        if bolt_items_to_grant <= 0 or not self.psp_connected:
            return
        try:
            current = self.pine.read_int32(PLAYER_BOLT_COUNT)
            for _ in range(bolt_items_to_grant):
                grant = min(200000, max(75000, int(current * 0.2)))
                current = min(current + grant, MAX_PLAYER_BOLTS)
            self.pine.write_int32(PLAYER_BOLT_COUNT, current)
            # One-shot AP filler grant, not organic gameplay gain —
            # rebaseline so Core's per-tick apply_boost() doesn't multiply it.
            self._wiring.player_bolts.rebaseline(current)
        except Exception as exc:
            self._log(f"[RAC] Could not grant bolts: {exc}", "warning")

    def _grant_new_trap_items(self) -> None:
        # Trap addresses (DREAMTIME_EFFECT, BRIGHTNESS_ADDRESS, CHEATS) are all
        # global — safe to write during a transition.
        new_items = self.items_received[self._processed_trap_count:]
        self._processed_trap_count = len(self.items_received)

        if not self.psp_connected:
            return
        for network_item in new_items:
            item_name = self.item_names[self.game].get(network_item.item, "")
            if item_name not in ALL_TRAPS:
                continue
            try:
                activate_trap(self.pine, item_name)
            except Exception as exc:
                self._log(f"[RAC] Could not activate trap {item_name!r}: {exc}", "warning")
