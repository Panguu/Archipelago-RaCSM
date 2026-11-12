"""The child process exclusively owns Core and the one PINE connection."""
import logging
import traceback

from rule_builder.rules import False_

from ..constants import CASE_ID_TO_CASE, GoalOptions, MissionsOptions, RingLinkBehaviorOptions
from ..core import Core
from ..locations import LOCATION_NAME_TO_ID
from ..options import Goal
from ..pypine import Pine
from ..rules import VENDOR_REQUIREMENTS
from ..patcher.release import load_runtime_build
from ..vendor_logic import VendorLogic
from .constants import EXPECTED_GAME_ID
from .vendor_scouts import VendorScouts


class GameRuntime:
    def __init__(self, emit, *, permanent_build=None):
        self.emit = emit
        self.identity = None
        self.connected = False
        self.allowed = set()
        self.data = {}
        self.pine = Pine()
        self.permanent_build = load_runtime_build() if permanent_build is None else permanent_build
        self._make_core()

    def _make_core(self):
        self.core = Core(self.pine, log=lambda message: self.event('log', message),
                         debug=lambda message: self.event('debug', message), permanent_build=self.permanent_build)
        self.scouts = VendorScouts(LOCATION_NAME_TO_ID)
        self.core.vendor_rewards.scouts = self.scouts
        self.core.native_runtime.configure_vendors(
            name for name, rule in VENDOR_REQUIREMENTS.items() if not isinstance(rule, False_))
        self.core.wire(
            send_location=self.location,
            send_deathlink=lambda cause: self.event('death', {'cause': cause, 'planet': self._planet_name()}),
            death_amnesty=lambda: int(self.data.get('death_amnesty', 0)),
            death_link_enabled=lambda: bool(self.data.get('death_link', False)),
            on_goal=lambda: self.event('goal', None),
            missions_all=lambda: self.data.get('all_missions', MissionsOptions.LEVEL_COMPLETION) == MissionsOptions.ALL,
            on_bolt_state_changed=lambda delivered, pending: self.event('bolts', (delivered, pending)),
        )
        self.core.stealth.on_count = lambda counts: self.event('stealth', counts)

    def event(self, kind, value):
        self.emit(kind, value, self.identity)

    def _planet_name(self):
        case = CASE_ID_TO_CASE.get(self.core.case.case_id)
        return case.planet if case else None

    def location(self, name):
        if name in self.allowed:
            self.event('location', name)
        return False

    def disconnect(self):
        try:
            if self.connected:
                self.core.native_runtime.verify()
                self.core.close()
        finally:
            self.pine.disconnect()
            self.connected = False
            self.core.case.is_ready = False

    def dispatch(self, command, payload):
        w = self.core
        if self.connected:
            try:
                identity = w.native_runtime.verify()
            except Exception:
                # Never restore session data or run commands on unverified RAM.
                w.native_runtime.close(disarm=False)
                w.case.is_ready = False
                self.pine.disconnect()
                self.connected = False
                raise
            if identity != w.native_runtime.bound or not w.native_runtime._gameplay_settled(require_current=False):
                w.case.is_ready = False
                if command in ('effect', 'reset_traps', 'death', 'ring_link'):
                    return False
        if command == 'configure':
            identity, data, allowed = payload
            if data.get('iso_patch_abi', 1) != self.permanent_build['abi']:
                raise RuntimeError('This seed requires a different SAC ISO patch ABI; update the world and client.')
            changed = identity != self.identity
            if changed and self.identity is not None:
                self.disconnect()
                self._make_core()
                w = self.core
            self.identity, self.data, self.allowed = identity, dict(data), set(allowed)
            if changed:
                w.notifications.queue.clear()
            w.stealth.configure(dict(data.get('stealth_cases', {})), reset=changed)
            w.bolt_rewards.enabled = False
            self.scouts.rewards.clear()
            w.native_runtime.ap_connected = True
            w.native_runtime.starting_case.configure(data)
            w.progression.configure(data)
            w.ring_link.configure(int(data.get('ring_link_behavior', RingLinkBehaviorOptions.ITEMS)),
                                  int(data.get('bolt_multiplier', 1)))
            w.vendor_logic = VendorLogic(data['vendor_rules']) if 'vendor_rules' in data else None
            w.native_runtime.available_vendor_locations = frozenset() if w.vendor_logic is not None else None
            w.keycards.hunt.enabled = bool(data.get("keycard_hunt", False))
            w.skins.configure(data)
            w.weapon_mods.configure(data)
            w.wrench.enabled = bool(data.get('progressive_wrench', False))
            w.planet_cases = data.get('planet_cases')
            w.traps.durations.update(data.get('trap_duration', {}))
            w.goal = int(data.get('goal', GoalOptions.DEFEAT_KLUNK))
            w.pick_and_mix_goals = (tuple(Goal.from_any(name).value for name in data.get('pick_and_mix_goals', ()))
                                    if w.goal == GoalOptions.PICK_AND_MIX else None)
            w._goal_sent = False
            w.native_runtime.vendor_locations = self.allowed
            w.skill_points.allowed_locations = self.allowed
            return {"connected": self.connected}
        elif command == 'connect':
            if self.connected:
                return self.pine.get_game_id()
            self.pine.set_slot(payload)
            try:
                self.pine.connect()
                game_id = self.pine.get_game_id()
                if game_id != EXPECTED_GAME_ID:
                    raise RuntimeError(f'Wrong game: {game_id!r}; expected {EXPECTED_GAME_ID}')
                w.native_runtime.verify()
                self.event('log', f"[SAC] Verified patched ISO {self.permanent_build['build_id']}. Native patches are installed on disc.")
                self.connected = True
                return game_id
            except Exception:
                self.pine.disconnect()
                raise
        elif command in ('disconnect', 'shutdown'):
            self.disconnect()
        elif command == 'tick':
            if not self.connected:
                raise ConnectionError('PINE is not connected')
            if self.pine.get_game_id() != EXPECTED_GAME_ID:
                self.disconnect()
                raise ConnectionError('PCSX2 changed games; reconnect after loading Secret Agent Clank')
            w.sync_from_ap(set(payload))
            w.tick()
            return {'vendor_active': w.vendor.active, 'vendor_cases': tuple(w.vendor_cases),
                    'vendor_locations': (tuple(w.native_runtime.available_vendor_locations)
                                         if w.native_runtime.available_vendor_locations is not None else None),
                    'case_id': w.case.case_id, 'ring_link': w.ring_link.poll(w.bolt_balance())}
        elif command == 'sync':
            w.sync_from_ap(set(payload))
        elif command == 'items':
            inventory, notifications = payload
            w.apply_inventory(**inventory)
            for notification in notifications:
                w.notifications.enqueue(*notification)
        elif command == 'sent':
            w.notifications.enqueue_sent(*payload)
        elif command == 'effect':
            return w.activate_effect(payload) if self.connected else False
        elif command == 'ring_link':
            return w.receive_ring_link(payload) if self.connected else False
        elif command == 'reset_traps':
            return w.reset_traps() if self.connected else False
        elif command == 'death':
            if not self.connected:
                return False
            w.notifications.enqueue_death(*payload)
            return w.case.receive_death()
        elif command == 'death_sent':
            w.notifications.enqueue_death_sent(payload)
        elif command == 'death_enabled':
            self.data['death_link'] = payload
        elif command == 'ap_connected':
            w.native_runtime.ap_connected = payload
        elif command == 'bolts':
            w.bolt_rewards.configure(**payload)
        elif command == 'stealth':
            w.stealth.load(payload)
            w.stealth.on_count(dict(w.stealth.counts))
        elif command == 'scouts':
            self.scouts.rewards = payload
        elif command == 'diagnostic':
            return self.diagnostic(*payload)
        else:
            raise ValueError(f'Unknown game-worker command: {command}')

    def diagnostic(self, command):
        w = self.core
        if command == 'sac_info':
            barrier = w.native_runtime.startup_barrier
            loader = None
            if self.connected:
                addresses = (barrier.SIGNATURE_START, barrier.STATE, barrier.STATUS, barrier.TARGET, barrier.HANDLE,
                             0x206324, 0x206328, 0x206338)
                loader = dict(zip(
                    ('barrier_instruction', 'state', 'status', 'target', 'handle',
                     'requested_module', 'current_module', 'game_state'),
                    (f'0x{value:08X}' for value in self.pine.batch_read_int32(addresses))))
            return {'case_id': w.case.case_id, 'inventory_initialized': w._inventory_initialized,
                    'hooks_installed': w.location_hooks.installed,
                    'loader': loader, 'startup_barrier_attached': barrier.attached,
                    'reload_requested': w.native_runtime.reload_requested,
                    'stealth_loaded': w.stealth.loaded,
                    'stealth_cases': len(w.stealth.cases),
                    'awaiting_start': w.native_runtime.awaiting_start,
                    'generation': w.native_runtime.generation,
                    'owned_equipment': sorted(name for name, owned in w._owned_equipment().items() if owned),
                    'missions': repr(w.missions)}
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
