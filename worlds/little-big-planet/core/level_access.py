"""Seed-specific level access in a private RPCS3 patch allocation, never the save."""
from pathlib import Path
import re
import struct

from .level_access_hooks import BUFFER, MAGIC, HASH, CHANGES
from .ppc_assembler import assemble
from .game_versions import identify
from .patch_hooks import CHANGES as HOOK_CHANGES, code
from .inventory import delivery_lock

ROOT = Path(__file__).resolve().parents[1]
BANKS = (BUFFER+0x100, BUFFER+0x1100)


def access_rows(levels, enabled, received, starting_level, progress, accessible=None):
    """Keep real played/completed badge states only for AP-owned levels."""
    enabled = set(enabled)
    received = set(received) | {starting_level}
    if starting_level not in enabled or enabled-set(levels) or received-set(levels):
        raise ValueError('Invalid seed level access configuration')
    played = {(r['slot_type'],r['slot_number']):r for r in progress}
    rows = {}
    for guid, level in levels.items():
        for slot in level['slots']:
            match = re.fullmatch(r'SlotID\{(DEVELOPER|DLC_LEVEL), (\d+)\}',slot['slot'])
            if not match: continue
            key = (0 if match[1]=='DEVELOPER' else 8),int(match[2])
            status = 0
            if guid in enabled and guid in received and (accessible is None or guid in accessible):
                record = played.get(key,{})
                status = 3 if record.get('completion_count',0) else 2 if record.get('play_count',0) else 1
            if key in rows and rows[key] != status:
                raise ValueError('Ambiguous slot access')
            rows[key] = status
    if len(rows)>256: raise ValueError('Too many level slots for patch protocol')
    return [(typ,number,status) for (typ,number),status in sorted(rows.items())]


class LevelAccess:
    def __init__(self, pine):
        self.pine = pine
        self.verified = False
        self.status = 'level access patch pending'
        self.last_payload = None
        self.rows = {}

    def available(self):
        try:
            header = self.pine.read(BUFFER,12)
            magic, version, active = struct.unpack('>3I',header)
            blank = header == bytes(12)
            if not blank and ((magic,version)!=(MAGIC,1) or active not in (0,*BANKS)):
                raise RuntimeError('restart RPCS3 with the level access patch enabled')
            if not self.verified:
                executable, build = identify(self.pine)
                changes = CHANGES
                expected = assemble((ROOT/'patches/level_access.S').read_text())
                if build['version'] == '01.30':
                    changes = HOOK_CHANGES
                    expected = code('level_access')
                elif executable != HASH: raise RuntimeError('unsupported game executable')
                for address,original,replacement,_ in changes:
                    if int.from_bytes(self.pine.read(address,4),'big') != replacement:
                        raise RuntimeError(f'access bypass is not loaded at {address:#x}')
                matches = []
                for address in range(0x10000,0x2000000,0x10000):
                    try:
                        if self.pine.read(address,32)==expected[:32] and self.pine.read(address,len(expected))==expected:
                            matches.append(address)
                    except ValueError: continue
                if len(matches)!=1: raise RuntimeError('level access hook byte verification failed')
                self.verified = True
            if blank:
                # A zeroed mailbox may be initialized only after executable and
                # hook verification; allocation must be writable data memory.
                self.pine.request(struct.pack('<BII',6,BUFFER+4,1)+struct.pack('<BII',6,BUFFER,MAGIC))
                if self.pine.read(BUFFER,12) != struct.pack('>3I',MAGIC,1,0):
                    raise RuntimeError('access header initialization failed')
            self.status = 'AP level access active' if active else 'level access patch ready; waiting for AP seed'
            return True
        except (ValueError,RuntimeError) as exc:
            self.status = f'level access unavailable: {exc}'
            return False

    def publish(self, rows):
        if not self.available(): return False
        rows = list(rows)
        if len(rows)>256 or len({tuple(r[:2]) for r in rows})!=len(rows):
            raise ValueError('Invalid level access rows')
        if any(typ not in (0,8,9) or status not in (0,1,2,3) for typ,number,status in rows):
            raise ValueError('Invalid level access value')
        payload = struct.pack('>I',len(rows))+b''.join(struct.pack('>3I',*r) for r in rows)
        with delivery_lock(ROOT/'output/level_access/writer.lock') as locked:
            if not locked: return False
            active = int.from_bytes(self.pine.read(BUFFER+8,4),'big')
            if active not in (0,*BANKS): raise RuntimeError('Invalid active access table')
            if active and self.pine.read(active,len(payload)) == payload:
                self.rows = {(typ,number):state for typ,number,state in rows}
                return True
            target = BANKS[1] if active==BANKS[0] else BANKS[0]
            words = struct.unpack(f'>{len(payload)//4}I',payload)
            self.pine.request(b''.join(struct.pack('<BII',6,target+i*4,word) for i,word in enumerate(words)))
            if self.pine.read(target,len(payload)) != payload:
                raise RuntimeError('Level access table readback failed; old table remains active')
            # Publish only the fully populated inactive bank with one aligned Write32.
            self.pine.request(struct.pack('<BII',6,BUFFER+8,target))
            if int.from_bytes(self.pine.read(BUFFER+8,4),'big') != target:
                raise RuntimeError('Level access publication failed')
            self.rows = {(typ,number):state for typ,number,state in rows}
            self.status = f'AP level access active ({sum(state>0 for state in self.rows.values())} unlocked slots)'
            return True

    def granted(self, states):
        if not states: return False
        active = int.from_bytes(self.pine.read(BUFFER+8,4),'big')
        if active not in BANKS: return False
        count = int.from_bytes(self.pine.read(active,4),'big')
        if count>256: return False
        raw = self.pine.read(active+4,count*12)
        rows = {(typ,number):value for typ,number,value in struct.iter_unpack('>3I',raw)}
        return all(rows.get((s['slot_type'],s['slot_number']),0)>0 for s in states)
