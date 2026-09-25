"""PINE physical pickup checks, progress counters and verified inventory delivery.

Full randomizer readiness also requires vanilla reward suppression. Individual
pickup checks use exact captured identities; unmatched evidence stays in the journal.
"""
import asyncio
import time

from .core.pine import Pine
from .core.reader import LevelReader
from .core.death import PineDeathAdapter
from .core.inventory import InventoryDelivery
from .core.pickups import PickupReader
from .core.level_access import LevelAccess, access_rows
from .core.inventory_policy import InventoryPolicy
from .core.switches import active_switches
from .levels import LEVELS, SLOT_LEVELS
from .locations import LOCATIONS_BY_LEVEL, Kind
from .tracker import CheckTracker


class PineGameAdapter:
    ready = False  # Vanilla reward suppression is still pending.
    can_detect_checks = True

    def __init__(self, port=28011, save_directory=None, rpcs3_directory=None):
        from .dlc_validation import ContentPackValidator
        self.content_validator = ContentPackValidator(rpcs3_directory, save_directory)
        self.port = port
        self.pine = self.reader = self.death = None
        self.inventory = None
        self.policy = None
        self.policy_ready = False
        self.pickups = None
        self.access = None
        self.applied_kits = set()
        self.applied_chapters = set()
        self.last_progress = None
        self.pending_checks = set()
        self.save_directory = save_directory
        self.can_deliver_items = False
        self.last_profile = None
        self.next_connect = 0
        self.status = f'PINE: waiting for RPCS3 on 127.0.0.1:{port}'
        self.probe_status = 'prize diagnostic not loaded'
        self.tracker = CheckTracker()
        self.progress_profile = None
        self.seed_identity = None
        self.tracked_seed = None

    def set_seed(self, identity):
        # Applied by the serialized poller, never in the middle of a PINE read.
        self.seed_identity = identity

    async def validate_content_packs(self, slot_data):
        await asyncio.to_thread(self.content_validator.validate, slot_data)

    @property
    def can_apply_death(self):
        return self.death is not None and self.death.can_apply_death

    def can_die_now(self):
        return self.death is not None and self.death.can_die_now()

    async def apply_death(self):
        return await self.death.apply_death() if self.death else False

    async def grant(self, state):
        from .constants.traps import GAMEPLAY_EFFECTS
        if state['kind'] in GAMEPLAY_EFFECTS:
            return bool(self.policy_ready and self.inventory and
                        await asyncio.to_thread(self.inventory.gameplay_effect, state['kind']))
        if state['kind'] == 'random_costume_trap':
            return bool(self.policy_ready and self.inventory and
                        await asyncio.to_thread(self.inventory.random_costume))
        if state['kind'] == 'content_pack_unlock':
            return bool(self.access and self.access.verified and
                        await asyncio.to_thread(self.access.granted,
                            [dict(slot_type=9,slot_number=state['slot_number'])]))
        if state['kind'] == 'progressive_chapter':
            return bool(self.access and self.access.verified and state['chapter'] in self.applied_chapters)
        if state['kind'] == 'dlc_unlock':
            return bool(self.access and self.access.verified and state['kit'] in self.applied_kits)
        if state['kind'] == 'level_unlock':
            if self.access and self.access.verified:
                return await asyncio.to_thread(self.access.granted, state['slots'])
            return False
        if state['kind'] == 'inventory_plan' and self.inventory and self.can_deliver_items:
            return await asyncio.to_thread(self.inventory.grant, state['plan_guid'])
        return False

    async def sync_inventory(self, slot_data, received_items):
        if not self.policy:
            return False
        from .inventory_policy import allowed_plans
        self.policy_ready = False
        self.policy_ready = await asyncio.to_thread(self.policy.publish, allowed_plans(slot_data, received_items))
        return self.policy_ready

    async def active_command_kind(self):
        return await asyncio.to_thread(self.inventory.active_command_kind) if self.inventory else None

    async def sync_level_access(self, slot_data, received_items):
        if not self.access or not self.last_progress:
            return False
        from .items import ITEM_ID_TO_DATA
        from .dlc import accessible_levels, owned_kit_keys
        received = {ITEM_ID_TO_DATA[item.item]['level_guid'] for item in received_items
                    if item.item in ITEM_ID_TO_DATA and ITEM_ID_TO_DATA[item.item]['state']['kind']=='level_unlock'}
        item_ids = [item.item for item in received_items]
        from collections import Counter
        counts = Counter(ITEM_ID_TO_DATA[i]['state']['chapter'] for i in item_ids
                         if i in ITEM_ID_TO_DATA and ITEM_ID_TO_DATA[i]['state']['kind']=='progressive_chapter')
        for chapter,members in slot_data.get('progressive_chapters',{}).items():
            received.update(members[:counts[chapter]])
        accessible = accessible_levels(slot_data['levels'], received, slot_data['starting_level'],
                                       item_ids, slot_data.get('level_kits', {}))
        rows = access_rows(LEVELS, slot_data['levels'], received,
                           slot_data['starting_level'], self.last_progress['played_levels'], accessible)
        if 'costume_packs' in slot_data:
            from .content_packs import access_rows as content_rows
            packs = {ITEM_ID_TO_DATA[i]['state']['slot_number'] for i in item_ids
                     if i in ITEM_ID_TO_DATA and ITEM_ID_TO_DATA[i]['state']['kind']=='content_pack_unlock'}
            rows += content_rows(slot_data['costume_packs'],packs)
        applied = await asyncio.to_thread(self.access.publish, rows)
        if applied:
            self.applied_kits = owned_kit_keys(item_ids)
            self.applied_chapters = {c for c,n in counts.items() if n and c in slot_data.get('progressive_chapters',{})}
        return applied

    def close(self):
        if self.pine:
            self.pine.close()
        self.pine = self.reader = self.death = None
        self.inventory = None
        self.policy = None
        self.policy_ready = False
        self.pickups = None
        self.access = None
        self.applied_kits = set()
        self.applied_chapters = set()
        self.last_progress = None
        self.can_deliver_items = False
        self.last_profile = None
        self.tracker.observe_run(None, None, None)

    def _poll(self):
        empty = {'location_ids':[], 'local_death':False}
        if not self.pine and time.monotonic() < self.next_connect:
            return empty
        try:
            if self.tracked_seed != self.seed_identity:
                self.tracker = CheckTracker()
                self.pending_checks.clear()
                self.progress_profile = None
                self.tracked_seed = self.seed_identity
            if not self.pine:
                self.pine = Pine(self.port)
                self.reader = LevelReader(self.pine)
                self.death = PineDeathAdapter(self.pine)
                self.inventory = InventoryDelivery(self.pine, self.save_directory)
                self.policy = InventoryPolicy(self.pine, self.inventory)
                self.pickups = PickupReader(self.pine)
                self.access = LevelAccess(self.pine)
            q = self.reader.progress()
            self.last_progress = q
            profile = (q['active_user'], q['inventory_address'])
            inventory_changed = profile != self.last_profile
            self.last_profile = profile
            if self.progress_profile != profile:
                self.tracker = CheckTracker()
                self.progress_profile = profile
            slot = (q['slot_type'], q['slot_number'])
            candidates = SLOT_LEVELS.get(slot, set())
            guid = next(iter(candidates)) if len(candidates) == 1 else None
            old_run = self.tracker.run
            collected = total = None
            if guid and self.tracker.progress_initialized:
                completions = sum(r['completion_count'] for r in q['played_levels']
                                  if guid in SLOT_LEVELS.get((r['slot_type'], r['slot_number']), set()))
                old_count = self.tracker.counters.get(guid, (0, 0))[0]
                if completions > old_count or guid in self.tracker.awaiting_collection:
                    try:
                        prize_plans = [loc.plan for loc in LOCATIONS_BY_LEVEL[guid] if loc.kind == Kind.PRIZE]
                        collected, total = self.reader.completion_prizes(prize_plans, slot)
                    except (ValueError, RuntimeError):
                        pass  # Keep completion/ace checks; retry collection evidence next poll.
            events = self.tracker.update_progress(q['played_levels'], SLOT_LEVELS, guid,
                                                 q['world_address'], q['world_death_count'],
                                                 collected, total)
            self.pending_checks.update(events['location_ids'])
            self.can_deliver_items = self.inventory.available()
            access_ready = self.access.available()
            self.can_deliver_items = self.can_deliver_items or access_ready
            pickups = {'location_ids': [], 'pickup_events': [], 'pickup_cursor': None}
            try:
                pickups = self.pickups.read()
                self.probe_status = pickups['pickup_status']
            except (ValueError, RuntimeError) as exc:
                self.probe_status = f'pickup checks paused: {exc}'
            self.pending_checks.update(pickups['location_ids'])
            if len(candidates) != 1:
                self.status = f"PINE connected: NPEA00241 {self.reader.build['version']}; pod/loading or unmapped slot {slot}; {self.probe_status}; {self.inventory.status}; {self.access.status}"
                return dict(pickups, location_ids=sorted(self.pending_checks),
                            local_death=False, level_changed=True, inventory_changed=inventory_changed)
            guid = next(iter(candidates))
            try:
                self.pending_checks.update(active_switches(self.reader, q, guid))
            except (ValueError,RuntimeError):
                pass  # Unstable loads must never become checks; retry next poll.
            rec = next((r for r in q['played_levels'] if (r['slot_type'],r['slot_number'])==slot),None)
            if rec is None:
                raise RuntimeError('Waiting for level progress record')
            players = self.reader.word(q['world_address']+0x90) if q['world_address'] else 0
            self.status = (f'PINE connected: {LEVELS[guid]["name"]}; deaths {q["world_death_count"]}; '
                           f'completions {rec["completion_count"]}; {self.probe_status}; {self.inventory.status}; {self.access.status}; reward suppression pending')
            return {**pickups, 'location_ids':sorted(self.pending_checks),
                    'local_death':events['local_death'] and players==1,
                    'inventory_changed':inventory_changed,
                    'level_changed':old_run != self.tracker.run}
        except (OSError, ValueError, RuntimeError) as exc:
            self.status = f'PINE waiting: {exc} (127.0.0.1:{self.port})'
            self.close()
            self.next_connect = time.monotonic()+2
            return dict(empty,level_changed=True)

    async def poll(self):
        return await asyncio.to_thread(self._poll)

    async def acknowledge_events(self, events):
        # The client commits checks AND raw pickup evidence before calling this.
        if self.pickups:
            await asyncio.to_thread(self.pickups.acknowledge, events.get('pickup_cursor'))
        self.pending_checks.difference_update(events['location_ids'])
