"""Archipelago network client with PINE pickup checks and native item delivery.

Run using the Archipelago checkout's Python: python Client.py --connect host:port --name slot
"""
import asyncio
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
from .delivery_state import DeliveryState
from .deathlink import DeathLinkBridge, UnverifiedPineDeathAdapter
from .items import ITEM_ID_TO_DATA
from .dlc_validation import ContentOptionsError
tracker_loaded = False
try:
    from worlds.tracker.TrackerClient import TrackerGameContext as SuperContext
    tracker_loaded = True
except ModuleNotFoundError:
    from CommonClient import CommonContext as SuperContext
from CommonClient import ClientCommandProcessor, get_base_parser, handle_url_arg, gui_enabled, server_loop, mark_raw
from NetUtils import ClientStatus

logger = logging.getLogger('Client')
FILLER_ID = 1_249_999_999


class LBPCommandProcessor(ClientCommandProcessor):
    def _cmd_connect(self, address: str = ''):
        """Connect to an Archipelago server; RPCS3 PINE connects automatically."""
        port = getattr(self.ctx.game_adapter, 'port', 28011)
        if address.removeprefix('ws://').rstrip('/') in (f'127.0.0.1:{port}', f'localhost:{port}'):
            self.output(f'Port {port} is the RPCS3 PINE connection. Use /pine to see it; enter your AP server address here.')
            return False
        return super()._cmd_connect(address)

    def _cmd_patch(self):
        """Verify the running Union-patched LBP and export its personal AP RPCS3 patch."""
        if getattr(self, '_patch_task', None) and not self._patch_task.done():
            self.output('Patch verification is already running.')
            return False
        self._patch_task = asyncio.create_task(self._export_patch())
        return True

    async def _export_patch(self):
        from .core.patch_export import export_patch
        self.output('Checking AP code compatibility in the running game...')
        try:
            async with self.ctx.game_lock:
                path = await asyncio.to_thread(export_patch, self.ctx.state_dir / 'patches',
                                              getattr(self.ctx.game_adapter, 'port', 28011),
                                              getattr(self.ctx.game_adapter, 'pine', None))
        except (OSError, RuntimeError, ValueError) as exc:
            self.output(f'Patch export failed: {exc}')
            return
        self.output(f'AP patch exported: {path.resolve()}')
        self.output('Import this file in RPCS3 Manage > Game Patches, enable '
                    'Archipelago LittleBigPlanet v1.30, then restart the game. '
                    'Keep your Union-patched EBOOT. Run /patch again after repatching online settings.')

    @mark_raw
    def _cmd_reset_progress(self, arguments: str = ''):
        """Preview saved level counters; use /reset_progress apply [save USRDIR] to clear them."""
        if getattr(self, '_reset_task', None) and not self._reset_task.done():
            self.output('A progress reset is already running.')
            return False
        action, _, directory = arguments.strip().partition(' ')
        if action not in ('', 'apply'):
            self.output('Usage: /reset_progress or /reset_progress apply [active save USRDIR]')
            return False
        self._reset_task = asyncio.create_task(self._reset_progress(action == 'apply', directory.strip().strip('"')))
        return True

    async def _reset_progress(self, apply, directory):
        from .core.progress_reset import ProgressReset
        if not self.ctx.slot_data:
            self.output('Connect to your AP seed first; only its enabled levels will be reset.')
            return
        adapter = self.ctx.game_adapter
        try:
            async with self.ctx.game_lock:
                if not getattr(adapter, 'pine', None):
                    self.output('Connect RPCS3 first, return to the pod, then pause emulation.')
                    return
                enabled = set(self.ctx.slot_data['levels'])
                slots = {slot for slot, guids in adapter.slots.items()
                         if len(guids) == 1 and next(iter(guids)) in enabled}
                reset = ProgressReset(adapter.pine, slots)
                if not apply:
                    state = await asyncio.to_thread(reset.snapshot)
                    changed = sum(any(r['counts']) for r in state['records'])
                    self.output(f'{changed} seed levels have saved play/completion/ace counters. '
                                'To clear these counters, use /reset_progress apply [active save USRDIR]. '
                                'This can persist when LBP saves. Inventory and AP checks are preserved.')
                    return
                save = directory or getattr(adapter, 'save_directory', None)
                if not save:
                    self.output('Supply the active LBP save folder: /reset_progress apply "C:\\path\\to\\USRDIR"')
                    return
                result = await asyncio.to_thread(reset.apply, save, self.ctx.state_dir/'progress_backups')
                # Rebaseline after intentional counter decreases, without touching the AP journal.
                adapter.tracker.counters.clear()
                adapter.tracker.progress_initialized = False
                adapter.tracker.observe_run(None, None, None)
                adapter.last_progress = None
                self.output(f'Reset play/completion/ace counters for {result["levels"]} seed levels. '
                            f'Backup: {result["backup"] or "not needed"}. '
                            'Resume RPCS3 and reopen the level menu. Existing AP checks remain checked.')
        except (OSError, RuntimeError, ValueError) as exc:
            self.output(f'Progress reset stopped: {exc}')

    def _cmd_pine(self):
        """Show the local RPCS3 PINE connection status."""
        self.output(getattr(self.ctx.game_adapter, 'status', 'No PINE adapter configured'))
        self.output('AP uses /connect host:port; RPCS3 connects automatically on PINE port 28011.')
        return True


class PendingGameAdapter(UnverifiedPineDeathAdapter):
    """Explicitly unimplemented operations never acknowledge a delivery."""
    ready = False

    async def grant(self, state):
        return False

    async def poll(self):
        return {'location_ids': [], 'local_death': False}


class LBPContext(SuperContext):
    game = 'LittleBigPlanet'
    items_handling = 0b111  # Receive local, remote and starting inventory through one path.
    want_slot_data = True
    command_processor = LBPCommandProcessor
    tags = {'AP'}  # This is a full playing client, not UT's tracker-only mode.

    def __init__(self, server_address=None, password=None, state_dir=ROOT/'output/client', adapter=None):
        super().__init__(server_address, password)
        self.state_dir = Path(state_dir)
        self.game_lock = asyncio.Lock()
        self.journal = None
        self.slot_data = None
        self.game_adapter = adapter or PendingGameAdapter()
        self.death_bridge = DeathLinkBridge(self, self.game_adapter)
        self.remote_deaths = []
        self.protocol_error = None

    async def server_auth(self, password_requested=False):
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    def on_package(self, cmd, args):
        super().on_package(cmd, args)
        if cmd == 'RoomInfo':
            # CommonContext validates an existing seed identity before authenticating.
            if self.seed_name is None:
                self.seed_name = args['seed_name']
        elif cmd == 'Connected':
            self.slot_data = None
            if self.journal:
                self.journal.close()
                self.journal = None
            data = dict(args['slot_data'])
            # Earlier schema-1 seeds stored the single goal as a scalar.
            if 'goal_locations' not in data and isinstance(data.get('goal_location'), int):
                data['goal_locations'] = [data['goal_location']]
            if data.get('schema') != 1 or data.get('game_id') != 'NPEA00241' or data.get('game_version') not in ('01.27', '01.30'):
                self.protocol_error = 'Unsupported LittleBigPlanet slot data'
                logger.error(self.protocol_error)
                return
            self.protocol_error = None
            self.slot_data = data
            if hasattr(self.game_adapter, 'set_seed'):
                self.game_adapter.set_seed((self.seed_name, self.team, self.slot))
            self.journal = DeliveryState(self.state_dir, self.seed_name, self.team, self.slot)
            self.journal.confirm_checks(self.checked_locations)
            self.journal.reconcile_game()
            self.remote_deaths.clear()
            self.death_bridge.level_changed()
            logger.info('AP connected. PINE checks and inventory delivery use independent capabilities; vanilla reward suppression is pending.')
        elif cmd == 'ReceivedItems' and self.journal:
            # CommonContext assembles valid contiguous packets and requests Sync on gaps.
            # Use its assembled history rather than accepting a packet with an invalid index.
            self.journal.receive(0, self.items_received)
        elif cmd == 'RoomUpdate' and self.journal:
            self.journal.confirm_checks(self.checked_locations)

    def make_gui(self):
        ui = super().make_gui()
        ui.base_title = 'LittleBigPlanet Client'
        if tracker_loaded:
            from worlds.tracker.TrackerClient import UT_VERSION
            ui.base_title += f' | Universal Tracker {UT_VERSION}'
        return ui

    def on_deathlink(self, data):
        super().on_deathlink(data)
        if self.death_bridge.enabled:
            key = (data['source'], data['time'])
            if key not in self.death_bridge.seen and not any(
                    (d['source'], d['time']) == key for d in self.remote_deaths):
                self.remote_deaths.append(data)

    async def tick(self):
        async with self.game_lock:
            await self._tick()

    async def _tick(self):
        # Check local installation before publishing policies, checks or deliveries.
        if (self.slot_data and self.server and self.server.socket
                and hasattr(self.game_adapter, 'validate_content_packs')):
            await self.game_adapter.validate_content_packs(self.slot_data)
        events = await self.game_adapter.poll()
        if not self.journal or not self.slot_data or not self.server or not self.server.socket:
            return
        if events.get('inventory_changed'):
            self.journal.reconcile_game()
        if hasattr(self.game_adapter, 'sync_inventory'):
            await self.game_adapter.sync_inventory(self.slot_data, self.items_received)
        if hasattr(self.game_adapter, 'sync_level_access'):
            await self.game_adapter.sync_level_access(self.slot_data, self.items_received)
        enabled = set(self.slot_data['enabled_locations'])
        pending = set(self.journal.pending_checks()) & enabled
        if pending:
            await self.check_locations(pending)
        wants_death = bool(self.slot_data.get('death_link')) and self.game_adapter.can_apply_death
        if wants_death != self.death_bridge.enabled:
            await self.death_bridge.enable(wants_death)
        if events.get('level_changed'):
            self.death_bridge.level_changed()
            self.remote_deaths.clear()
        if events.get('local_death'):
            await self.death_bridge.local_death()
        if self.remote_deaths and not self.death_bridge.remote_pending:
            if await self.death_bridge.receive(self.remote_deaths[0]):
                self.remote_deaths.pop(0)
        # Check detection, item delivery and reward suppression are independent.
        if getattr(self.game_adapter, 'can_detect_checks', self.game_adapter.ready):
            # A real pickup in an excluded level (or with score checks disabled)
            # is valid game activity, but is not a location in this AP seed.
            checks = set(events['location_ids']) & enabled
            self.journal.queue_checks(checks, events.get('pickup_events', ()))
            if hasattr(self.game_adapter, 'acknowledge_events'):
                await self.game_adapter.acknowledge_events(events)
        # Delivery capability is independent of pickup/suppression readiness.
        from .constants.traps import ONE_SHOT_KINDS, RETIRED_EFFECT_IDS
        can_deliver = getattr(self.game_adapter, 'can_deliver_items', self.game_adapter.ready)
        deliveries = self.journal.pending_items() if can_deliver else []
        if deliveries and hasattr(self.game_adapter, 'active_command_kind'):
            active_kind = await self.game_adapter.active_command_kind()
            if active_kind and active_kind != 'inventory_plan':
                # Finish an in-flight trap before replaying ownership grants on reconnect.
                deliveries.sort(key=lambda row: ITEM_ID_TO_DATA.get(row[1],{}).get('state',{}).get('kind') != active_kind)
        for index, item_id in deliveries:
            if item_id in RETIRED_EFFECT_IDS:
                self.journal.applied(index, one_shot=True)
                continue
            if item_id == FILLER_ID:
                self.journal.applied(index)
                continue
            if item_id not in ITEM_ID_TO_DATA:
                raise ValueError(f'Unknown received LittleBigPlanet item {item_id}')
            # True must mean a verified, idempotent grant; False keeps this item pending.
            if await self.game_adapter.grant(ITEM_ID_TO_DATA[item_id]['state']):
                state = ITEM_ID_TO_DATA[item_id]['state']
                if state['kind'] == 'content_pack_unlock':
                    from .content_packs import PACK_LOCATIONS
                    location = PACK_LOCATIONS[state['slot_number']]['id']
                    self.journal.queue_checks({location} & enabled)
                self.journal.applied(index, one_shot=state['kind'] in ONE_SHOT_KINDS)
            elif ITEM_ID_TO_DATA[item_id]['state']['kind'] in ONE_SHOT_KINDS | {'inventory_plan'}:
                # One native mailbox command at a time; do not hammer PINE for
                # every remaining inventory item while the first is loading.
                break
        pending = set(self.journal.pending_checks()) & enabled
        if pending:
            await self.check_locations(pending)
        if set(self.slot_data['goal_locations']) <= self.journal.checked() and not self.finished_game:
            await self.send_msgs([{'cmd': 'StatusUpdate', 'status': ClientStatus.CLIENT_GOAL}])
            self.finished_game = True


async def game_loop(ctx):
    last_error = None
    last_status = None
    while not ctx.exit_event.is_set():
        try:
            await ctx.tick()
            status = getattr(ctx.game_adapter, 'status', None)
            if status and status != last_status:
                logger.info(status)
                last_status = status
            last_error = None
        except ContentOptionsError as exc:
            if str(exc) != last_error:
                logger.error('%s', exc)
                last_error = str(exc)
        except (ConnectionError, OSError, RuntimeError, ValueError) as exc:
            if str(exc) != last_error:
                logger.error('Game integration paused: %s', exc)
                last_error = str(exc)
        await asyncio.sleep(0.25)


async def main(args):
    from .pine_game import PineGameAdapter
    ctx = LBPContext(args.connect, args.password, args.state_dir,
                     PineGameAdapter(args.pine_port, args.save_dir, getattr(args, 'rpcs3_dir', None)))
    ctx.auth = args.name
    ctx.server_task = asyncio.create_task(server_loop(ctx), name='AP server')
    watcher = asyncio.create_task(game_loop(ctx), name='LBP game')
    if tracker_loaded:
        ctx.run_generator()
    if gui_enabled and not getattr(args, 'nogui', False):
        ctx.run_gui()
    ctx.run_cli()
    try:
        await ctx.exit_event.wait()
    finally:
        watcher.cancel()
        await asyncio.gather(watcher, return_exceptions=True)
        await ctx.shutdown()
        ctx.game_adapter.close()
        if ctx.journal:
            ctx.journal.close()


def launch(*argv):
    parser = get_base_parser(description=__doc__)
    parser.add_argument('--name', help='Archipelago slot name')
    parser.add_argument('--pine-port', type=int, default=28011, help='Local RPCS3 PINE port')
    parser.add_argument('url', nargs='?', help='Archipelago connection URL')
    parser.add_argument('--state-dir', type=Path, default=ROOT/'output/client')
    parser.add_argument('--save-dir', type=Path, help='Active LBP USRDIR save folder for pre-delivery backups; defaults to installed hook configuration')
    parser.add_argument('--rpcs3-dir', type=Path, help='Active RPCS3 folder for checking required DLC installation')
    logging.basicConfig(level=logging.INFO)
    logging.getLogger().setLevel(logging.INFO)
    # websockets logs every PING/PONG frame at DEBUG; keep only warnings and above.
    logging.getLogger('websockets').setLevel(logging.WARNING)
    args = handle_url_arg(parser.parse_args(argv), parser=parser)
    asyncio.run(main(args))


if __name__ == '__main__':
    launch(*sys.argv[1:])
