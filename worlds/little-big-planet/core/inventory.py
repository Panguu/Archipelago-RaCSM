"""Verified, idempotent inventory deliveries via a native-game PINE mailbox.

PINE writes only the dedicated command buffer. The boot hook owns allocation,
resource loading, inventory insertion, dirty marking and resource cleanup.
"""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import struct
import time

from .inventory_delivery_hooks import BUFFER, HASH, HOOK
from .reader import LevelReader
from .game_versions import identify
from .ppc_assembler import assemble
from .patch_hooks import HOOKS, code
from ..items import PRIZE_PLAN_TO_ITEM_ID

ROOT = Path(__file__).resolve().parents[1]
MAGIC = 0x41504947
ERRORS = {1: 'active profile changed or game is not solo', 2: 'resource loading failed',
          3: 'resource loading timed out', 4: 'native inventory lookup did not verify the grant'}


@contextmanager
def delivery_lock(path):
    """Serialize local clients sharing the mailbox; never wait on another client."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as stream:
        if stream.tell() == 0:
            stream.write(b'0'); stream.flush()
        stream.seek(0)
        if os.name == 'nt':
            import msvcrt
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                yield False
                return
            try:
                yield True
            finally:
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                yield False
                return
            try:
                yield True
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)


class InventoryDelivery:
    def __init__(self, pine, save_directory=None, output=None):
        self.pine = pine
        self.reader = LevelReader(pine, {})
        self.output = Path(output or ROOT / 'output/inventory_delivery')
        self.save_directory = Path(save_directory) if save_directory else None
        self.backed_up = set()
        self.status = 'inventory delivery patch not checked'
        self.last_result = None
        self.verified_code = False
        self.blocked_request = None
        self.known_plans = set(PRIZE_PLAN_TO_ITEM_ID)

    def mailbox(self):
        raw = self.pine.read(BUFFER, 48)
        values = struct.unpack('>12I', raw)
        names = ('magic', 'version', 'heartbeat', 'state', 'sequence', 'plan',
                 'inventory', 'user', 'result', 'error', 'resource', 'loading_ticks')
        data = dict(zip(names, values))
        if data['magic'] != MAGIC or data['version'] != 1 or data['state'] not in range(5):
            raise RuntimeError('Inventory hook is not initialized; enter a solo level after restarting RPCS3')
        return data

    def validate_patch(self):
        info = self.reader.validate()
        if info['status'] != 'running':
            raise RuntimeError('Resume RPCS3 before inventory delivery')
        if not self.verified_code:
            executable, build = identify(self.pine)
            hook = HOOK
            if build['version'] == '01.30':
                hook = HOOKS['inventory_delivery'][0]
                expected = code('inventory_delivery')
            else:
                expected = assemble((ROOT / 'patches/inventory_delivery.S').read_text())
            self.verify_hook(hook, expected)
            self.verified_code = True
        return self.mailbox()

    def verify_hook(self, hook, expected):
        instruction = int.from_bytes(self.pine.read(hook, 4), 'big')
        if instruction & 0xfc000003 == 0x48000000:
            delta = instruction & 0x03fffffc
            if delta & 0x02000000:
                delta -= 0x04000000
            candidates = [(hook + delta) & 0xffffffff]
        elif instruction == int.from_bytes(expected[-4:], 'big'):
            # RPCS3 can redirect execution without changing PINE-visible text.
            # calloc allocations are 64 KiB aligned. Search only the bounded
            # low code-allocation range used by this executable, read-only.
            self.mailbox()
            candidates = []
            for address in range(0x10000, 0x2000000, 0x10000):
                try:
                    if self.pine.read(address, 32) == expected[:32]:
                        candidates.append(address)
                except ValueError:
                    continue
        else:
            candidates = []
        if len(candidates) != 1 or self.pine.read(candidates[0], len(expected)) != expected:
            raise RuntimeError('Inventory delivery hook bytes do not match this client')

    def available(self):
        try:
            header = self.validate_patch()
            self.status = f'inventory delivery active (queue state {header["state"]})'
            return True
        except (ValueError, RuntimeError) as exc:
            self.status = str(exc)
            return False

    def profile(self):
        word = self.reader.word
        user = word(word(self.reader.build['user']))
        table = self.pine.read(word(self.reader.build['table']), 112)
        matches = [int.from_bytes(table[i+12:i+16], 'big') for i in range(0,112,16)
                   if table[i] and int.from_bytes(table[i+4:i+8], 'big') == user]
        if len(matches) != 1 or not matches[0]:
            raise RuntimeError('Active inventory is ambiguous')
        inventory = matches[0]
        if word(inventory) != 0x8548b0:
            raise RuntimeError('Unsupported inventory implementation')
        return user, inventory

    def owned_entry(self, plan, profile):
        """Native local-inventory ordering: resource type, GUID, then SHA1."""
        user, inventory = profile
        header = self.pine.read(inventory + 0x8c, 12)
        pointer, count, capacity = struct.unpack('>III', header)
        if not 0 <= count <= capacity <= 20000 or (count and not pointer):
            raise RuntimeError('Invalid inventory array')
        pointers = struct.unpack(f'>{count}I', self.pine.read(pointer, count * 4)) if count else ()
        target = (0x26, plan, bytes(20))
        lo, hi = 0, count
        found = None
        while lo < hi:
            mid = (lo + hi) // 2
            entry = pointers[mid]
            raw = self.pine.read(entry, 40)
            modern = self.reader.build['version'] == '01.30'
            key = ((int.from_bytes(raw[28:32], 'big') & 0x7fffffff), int.from_bytes(raw[4:8], 'big'), raw[8:28]) if modern else (int.from_bytes(raw[32:36], 'big'), int.from_bytes(raw[8:12], 'big'), raw[12:32])
            if key < target:
                lo = mid + 1
            elif key > target:
                hi = mid
            else:
                flag = self.pine.read(entry + (0x92 if modern else 0x9a), 1)[0]
                if flag not in (0, 1):
                    raise RuntimeError('Invalid inventory collected flag')
                if flag == 0:
                    found = entry
                break
        if self.pine.read(inventory + 0x8c, 12) != header or self.profile() != (user, inventory):
            raise RuntimeError('Inventory changed during lookup; retry')
        return found

    def solo_ready(self):
        word = self.reader.word
        context = word(word(self.reader.ROOT_TOC_SLOT))
        if not context:
            return False
        level = word(context + 0x78)
        thing = word(level + 0x50) if level else 0
        world = word(thing + 0x14) if thing else 0
        return bool(world and word(world + 0x90) == 1)

    def backup(self, profile):
        if profile in self.backed_up:
            return
        save = self.save_directory
        if save is None:
            installation = self.output / 'installation.json'
            if self.reader.build['version'] == '01.30':
                installation = ROOT / 'output/port_130/installation.json'
            if installation.exists():
                save = Path(json.loads(installation.read_text())['save'])
        if save is None or not save.is_dir():
            raise RuntimeError('Set --save-dir to the active LBP USRDIR save folder before delivering items')
        directory = self.output / 'delivery_backups' / str(time.time_ns())
        directory.mkdir(parents=True)
        shutil.copytree(save, directory / 'save')
        user, inventory = profile
        header = self.pine.read(inventory + 0x8c, 12)
        pointer, count, _ = struct.unpack('>III', header)
        if count > 20000:
            raise RuntimeError('Invalid inventory backup size')
        (directory / 'inventory_pointer_array.bin').write_bytes(self.pine.read(pointer, count * 4))
        (directory / 'profile.json').write_text(json.dumps(dict(user=user, inventory=inventory, header=header.hex())))
        self.backed_up.add(profile)

    def audit(self, event):
        self.output.mkdir(parents=True, exist_ok=True)
        with (self.output / 'deliveries.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(dict(time=time.time(), **event)) + '\n')
            stream.flush()
            os.fsync(stream.fileno())

    def write(self, address, data):
        if not BUFFER <= address <= address + len(data) <= BUFFER + 0x100:
            raise ValueError('Inventory commands may only write the dedicated mailbox')
        commands = b''.join(struct.pack('<BIB', 4, address+i, value) for i,value in enumerate(data))
        if self.pine.request(commands):
            raise RuntimeError('Unexpected PINE write reply')

    def grant(self, plan):
        """Return True only for verified ownership. Pending requests return False."""
        if type(plan) is not int or plan not in self.known_plans:
            raise ValueError('Unknown inventory plan')
        with delivery_lock(ROOT / 'output/inventory_delivery/mailbox.lock') as locked:
            if not locked:
                return False
            header = self.validate_patch()
            if self.reader.build['version'] == '01.30' and int.from_bytes(self.pine.read(BUFFER+0xd0,4),'big'):
                return False  # The costume command owns this mailbox until acknowledged.
            profile = self.profile()
            identity = (header['sequence'], header['plan'], header['inventory'], header['user'])
            if header['state'] in (1, 2):
                self.status = f'Inventory loading plan {header["plan"]}; delivery pending'
                return False
            if header['state'] == 4:
                self.blocked_request = identity
                raise RuntimeError(f'Inventory request {header["sequence"]} failed: {ERRORS.get(header["error"], "unknown error")}; item remains pending')
            if header['state'] == 3:
                if (header['user'], header['inventory']) != profile:
                    raise RuntimeError('Completed inventory command belongs to another profile')
                owned = self.owned_entry(header['plan'], profile)
                if not owned or owned != header['result'] or header['error'] or header['resource']:
                    raise RuntimeError('Inventory command acknowledgement failed readback verification')
                self.last_result = dict(plan=header['plan'], sequence=header['sequence'], entry=owned, verified=True)
                self.audit(dict(event='verified', **self.last_result))
                self.write(BUFFER + 12, struct.pack('>I', 0))
                if header['plan'] == plan:
                    return True
            if self.owned_entry(plan, profile):
                self.last_result = dict(plan=plan, verified=True, already_owned=True)
                return True
            if not self.solo_ready():
                self.status = 'Inventory delivery waiting for solo gameplay'
                return False
            self.backup(profile)
            # Re-resolve immediately before publishing; payload first, state last.
            if self.profile() != profile or self.mailbox()['state'] != 0:
                return False
            sequence = (header['sequence'] + 1) & 0xffffffff or 1
            self.audit(dict(event='submit', sequence=sequence, plan=plan, user=profile[0], inventory=profile[1]))
            self.write(BUFFER + 16, struct.pack('>8I', sequence, plan, profile[1], profile[0], 0, 0, 0, 0))
            self.write(BUFFER + 0xd0, struct.pack('>I', 0))
            self.write(BUFFER + 12, struct.pack('>I', 1))
            self.status = f'Inventory submitted plan {plan}; awaiting native grant'
            return False

    def random_costume(self):
        """Invoke native Popit randomisation once; wait for its mailbox receipt."""
        with delivery_lock(ROOT / 'output/inventory_delivery/mailbox.lock') as locked:
            if not locked:
                return False
            header = self.validate_patch()
            if self.reader.build['version'] != '01.30':
                raise RuntimeError('Random Costume Trap requires the v1.30 patch')
            opcode = int.from_bytes(self.pine.read(BUFFER+0xd0,4),'big')
            if opcode == 1:
                if header['state'] == 3 and header['result'] == 1 and not header['error']:
                    if (header['user'],header['inventory']) != self.profile() or header['resource']:
                        raise RuntimeError('Costume acknowledgement belongs to a different profile')
                    self.write(BUFFER+12, struct.pack('>I',0))
                    self.write(BUFFER+0xd0, struct.pack('>I',0))
                    return True
                if header['state'] == 4:
                    raise RuntimeError('Native costume trap rejected the active profile')
                return False
            if header['state'] != 0 or not self.solo_ready():
                return False
            word = self.reader.word
            # Solo Popit tree has exactly one node; never choose another player's UI.
            tree = word(0x8766b4)
            if word(tree+8) != 1:
                return False
            head = word(tree+4)
            node = word(head+4)
            popit = word(node+16)
            if not popit or word(popit+0xf90) != 0x859430 or word(popit+0x17a0):
                return False
            profile = self.profile()
            self.backup(profile)
            sequence = (header['sequence']+1)&0xffffffff or 1
            self.write(BUFFER+16, struct.pack('>8I',sequence,0,profile[1],profile[0],0,0,0,0))
            self.write(BUFFER+0xd0,struct.pack('>II',1,popit))
            self.write(BUFFER+12,struct.pack('>I',1))
            return False

    def gameplay_effect(self, kind):
        """Submit one consumable effect and acknowledge only its native receipt."""
        effects = self.effect_definitions()
        opcode = effects[kind][3]
        with delivery_lock(ROOT / 'output/inventory_delivery/mailbox.lock') as locked:
            if not locked:
                return False
            header = self.validate_patch()
            if self.reader.build['version'] != '01.30':
                raise RuntimeError('Gameplay effects require the v1.30 patch')
            active = int.from_bytes(self.pine.read(BUFFER+0xd0, 4), 'big')
            if header['state'] and active == opcode:
                if header['state'] == 3 and header['result'] == 1 and not header['error']:
                    if (header['user'], header['inventory']) != self.profile():
                        raise RuntimeError('Gameplay receipt belongs to another profile')
                    self.write(BUFFER+12, struct.pack('>I', 0))
                    self.write(BUFFER+0xd0, struct.pack('>I', 0))
                    return True
                if header['state'] == 4:
                    raise RuntimeError('Gameplay command rejected: return to the same solo profile')
                return False
            if header['state'] != 0 or not self.solo_ready():
                return False
            context = self.reader.word(self.reader.word(self.reader.ROOT_TOC_SLOT))
            if self.reader.word(context+self.reader.build['slot']) == 5:
                return False  # Never restart the pod or grant equipment there.
            profile = self.profile()
            sequence = (header['sequence']+1) & 0xffffffff or 1
            self.write(BUFFER+16, struct.pack('>8I', sequence, 0, profile[1], profile[0], 0, 0, 0, 0))
            self.write(BUFFER+0xd0, struct.pack('>I', opcode))
            self.write(BUFFER+12, struct.pack('>I', 1))
            return False

    @staticmethod
    def effect_definitions():
        from ..constants.traps import GAMEPLAY_EFFECTS
        return GAMEPLAY_EFFECTS

    def active_command_kind(self):
        if self.reader.build['version'] != '01.30':
            return 'inventory_plan'
        opcode = int.from_bytes(self.pine.read(BUFFER+0xd0, 4), 'big')
        if opcode == 1:
            return 'random_costume_trap'
        return next((kind for kind, data in self.effect_definitions().items() if data[3] == opcode),
                    'inventory_plan')
