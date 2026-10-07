"""The child process exclusively owns Core and the one PINE connection."""
import logging
import traceback


class GameRuntime:
    def __init__(self, emit):
        from ..pypine import Pine
        self.emit = emit
        self.identity = None
        self.connected = False
        self.allowed = set()
        self.data = {}
        self.pine = Pine()  # Never constructed in the UI process.
        self._make_core()

    def _make_core(self):
        from ..core.core import Core
        from ..locations import LOCATION_NAME_TO_ID
        from ..rules.vendor_access import VENDOR_REQUIREMENTS
        from rule_builder.rules import False_
        from .vendor_scouts import VendorScouts
        self.core = Core(self.pine, log=lambda message: self.event('log', message))
        self.scouts = VendorScouts(LOCATION_NAME_TO_ID)
        self.core.vendor_rewards.scouts = self.scouts
        self.core.native_runtime.configure_vendors(
            name for name, rule in VENDOR_REQUIREMENTS.items() if not isinstance(rule, False_))
        self.core.wire(
            send_location=self.location,
            send_deathlink=lambda cause: self.event('death', cause),
            death_amnesty=lambda: int(self.data.get('death_amnesty', 1)),
            death_link_enabled=lambda: bool(self.data.get('death_link', False)),
            on_goal=lambda: self.event('goal', None),
            missions_all=lambda: self.data.get('all_missions', 0) == 1,
            on_bolt_state_changed=lambda delivered, pending: self.event('bolts', (delivered, pending)),
        )
        self.core.stealth.on_count = lambda count: self.event('stealth', count)

    def event(self, kind, value):
        self.emit(kind, value, self.identity)

    def location(self, name):
        if name in self.allowed:
            self.event('location', name)
        # Confirmation arrives in the next tick's checked-location snapshot.
        # A broken IPC connection must never silently confirm a check.
        return False

    def disconnect(self):
        try:
            if self.connected:
                self.core.close()
        finally:
            self.pine.disconnect()
            self.connected = False

    def dispatch(self, command, payload):
        w = self.core
        if command == 'configure':
            from ..options import Goal
            identity, data, allowed = payload
            changed = identity != self.identity
            if changed and self.identity is not None:
                self.disconnect()
                self._make_core()
                w = self.core
            self.identity, self.data, self.allowed = identity, dict(data), set(allowed)
            if changed:
                w.notifications.queue.clear()
            w.stealth.configure(int(data.get('stealth_takedown_checks', 0)), reset=changed)
            w.bolt_rewards.enabled = False
            self.scouts.rewards.clear()
            w.native_runtime.ap_connected = True
            w.native_runtime.starting_case.configure(data)
            w.progression.configure(data)
            w.skins.configure(data)
            w.weapon_mods.configure(data)
            w.wrench.enabled = bool(data.get('progressive_wrench', False))
            w.progressive_planets = data.get('progressive_planets')
            w.character_unlocks = int(data.get('infobots', 1)) == 3
            w.traps.durations.update(data.get('trap_duration', {}))
            w.goal = int(data.get('goal', 0))
            w.pick_and_mix_goals = (tuple(Goal.from_any(name).value for name in data.get('pick_and_mix_goals', ()))
                                    if w.goal == Goal.option_pick_and_mix or data.get('pick_and_mix', False) else None)
            w._goal_sent = False
            w.native_runtime.vendor_locations = self.allowed
            w.skill_points.allowed_locations = self.allowed
            return {"connected": self.connected}
        elif command == 'connect':
            from .constants import EXPECTED_GAME_ID
            if self.connected:
                return self.pine.get_game_id()
            self.pine.set_slot(payload)
            try:
                self.pine.connect()
                game_id = self.pine.get_game_id()
                if game_id != EXPECTED_GAME_ID:
                    raise RuntimeError(f'Wrong game: {game_id!r}; expected {EXPECTED_GAME_ID}')
                self.connected = True
                return game_id
            except Exception:
                self.pine.disconnect()
                raise
        elif command in ('disconnect', 'shutdown'):
            self.disconnect()
        elif command == 'tick':
            from .constants import EXPECTED_GAME_ID
            if not self.connected:
                raise ConnectionError('PINE is not connected')
            if self.pine.get_game_id() != EXPECTED_GAME_ID:
                self.disconnect()
                raise ConnectionError('PCSX2 changed games; reconnect after loading Secret Agent Clank')
            w.sync_from_ap(set(payload))
            w.tick()
            return {'vendor_active': w.vendor.active, 'owned_cases': tuple(w.owned_cases),
                    'case_id': w.case.case_id}
        elif command == 'sync':
            w.sync_from_ap(set(payload))
        elif command == 'items':
            inventory, notifications = payload
            w.apply_inventory(**inventory)
            for notification in notifications:
                w.notifications.enqueue(*notification)
        elif command == 'trap':
            return w.activate_trap(payload) if self.connected else False
        elif command == 'death':
            if self.connected and w.case.is_ready:
                w.case.ratchet.health = 0.0
        elif command == 'death_enabled':
            self.data['death_link'] = payload
        elif command == 'ap_connected':
            w.native_runtime.ap_connected = payload
        elif command == 'bolts':
            w.bolt_rewards.configure(**payload)
        elif command == 'stealth':
            w.stealth.load(payload)
            w.stealth.on_count(w.stealth.count)
        elif command == 'scouts':
            self.scouts.rewards = payload
        elif command == 'native_locations':
            w.set_native_locations(payload)
        elif command == 'diagnostic':
            return self.diagnostic(*payload)
        else:
            raise ValueError(f'Unknown game-worker command: {command}')

    def diagnostic(self, command, case_id=None):
        from ..core.ratchet_nanotech import read_ratchet_nanotech
        w = self.core
        if command == 'sac_info':
            return {'case_id': w.case.case_id, 'inventory_initialized': w._inventory_initialized,
                    'hooks_installed': w.location_hooks.installed,
                    'awaiting_start': w.native_runtime.awaiting_start,
                    'generation': w.native_runtime.generation,
                    'owned_equipment': sorted(name for name, owned in w._owned_equipment().items() if owned),
                    'missions': repr(w.missions)}
        if not self.connected or not w.case.is_ready:
            raise ValueError('Wait until gameplay is ready')
        if command == 'ratchet_nanotech':
            return read_ratchet_nanotech(self.pine, w.case.symbols)
        if command == 'mission_table':
            return [row._asdict() for row in w.missions.dump_chapter_table()]
        case_id = case_id if case_id is not None else w.case.case_id
        if command == 'case_states':
            return {name: state.name for name, state in w.case_unlocks.read_all(case_id).items()}
        if command == 'case_struct':
            return {slot: (value, w.case_struct.slot_case_name(slot))
                    for slot, value in w.case_struct.read_all(case_id).items()}
        raise ValueError(f'Unknown diagnostic: {command}')


def worker_main(connection, runtime_factory=GameRuntime):
    """One blocking command at a time, with events interleaved in the reply stream."""
    runtime = None
    def emit(kind, value, identity=None):
        connection.send(('event', kind, value, identity))

    class ForwardLog(logging.Handler):
        def emit(self, record):
            emit('log', self.format(record))

    handler = ForwardLog()
    logger = logging.getLogger('CommonClient')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        runtime = runtime_factory(emit)
        while True:
            command, payload = connection.recv()
            try:
                result = runtime.dispatch(command, payload)
                connection.send(('result', result))
            except Exception:
                connection.send(('error', traceback.format_exc()))
            if command == 'shutdown':
                break
    except (EOFError, BrokenPipeError, OSError):
        pass
    finally:
        try:
            if runtime is not None:
                runtime.disconnect()
        finally:
            logger.removeHandler(handler)
            connection.close()
