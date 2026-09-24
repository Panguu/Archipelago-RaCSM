"""Explicit, backed-up reset of native play/completion/ace counters for seed levels."""
import json
from pathlib import Path
import shutil
import struct
import time

from .reader import LevelReader


class ProgressReset:
    def __init__(self, pine, slots):
        self.pine = pine
        self.slots = set(slots)
        self.reader = LevelReader(pine, {})

    def snapshot(self):
        info = self.reader.validate()
        if self.reader.build['version'] != '01.30':
            raise RuntimeError('Progress reset currently supports v1.30 only')
        if info['status'] != 'paused':
            raise RuntimeError('Return to the pod, then pause emulation in RPCS3 before resetting progress')
        # Verified native completion/ace increment stores and profile dirty-bit update.
        for address, expected in {
            0xb70f4: '39290001b1230024',
            0xb7100: '881e005060000001981e0050',
            0xb71d4: 'a123002639290001b1230026',
        }.items():
            raw = bytes.fromhex(expected)
            if self.pine.read(address, len(raw)) != raw:
                raise RuntimeError(f'Progress reset signature mismatch at {address:#x}')
        progress = self.reader.progress()
        if (progress['slot_type'], progress['slot_number']) != (5, 0):
            raise RuntimeError('Return to the pod before resetting progress')
        inventory = progress['inventory_address']
        header = self.pine.read(inventory+0x14c, 12)
        pointer, count, capacity = struct.unpack('>III', header)
        if not 0 <= count <= capacity <= 10000 or (count and not pointer):
            raise RuntimeError('Invalid played-level array')
        records = []
        seen = set()
        for i in range(count):
            address = pointer+i*0x58
            raw = self.pine.read(address, 0x58)
            slot = struct.unpack_from('>II', raw)
            if slot not in self.slots:
                continue
            if slot in seen:
                raise RuntimeError('Duplicate played-level record')
            seen.add(slot)
            records.append(dict(slot=list(slot), address=address, raw=raw.hex(),
                                counts=list(struct.unpack_from('>HHH', raw, 0x22))))
        if self.pine.read(inventory+0x14c, 12) != header or self.reader.progress() != progress:
            raise RuntimeError('Profile changed while reading progress; retry')
        if self.reader.validate()['status'] != 'paused':
            raise RuntimeError('Keep RPCS3 paused until the progress reset finishes')
        return dict(user=progress['active_user'], inventory=inventory,
                    header=header.hex(), records=records)

    def apply(self, save_directory, backup_directory):
        before = self.snapshot()
        changed = [r for r in before['records'] if any(r['counts'])]
        if not changed:
            return dict(levels=0, backup=None)
        save = Path(save_directory).resolve(strict=True)
        backup = Path(backup_directory).resolve() / str(time.time_ns())
        if not save.is_dir() or not any(save.glob('littlefart*')):
            raise RuntimeError('Supply the active LBP USRDIR save directory containing littlefart')
        if backup.is_relative_to(save):
            raise RuntimeError('Progress backup must be outside the game save directory')
        backup.mkdir(parents=True, exist_ok=False)
        shutil.copytree(save, backup/'save')
        (backup/'memory_before.json').write_text(json.dumps(before, indent=2), encoding='utf-8')
        if self.snapshot() != before:
            raise RuntimeError('Profile changed before reset; no counters were written')
        # Paused game, fresh pointers, and six counter bytes only; never clear
        # inventory, lock flags, scores, reward metadata, or other players' profiles.
        commands = bytearray()
        for record in changed:
            for offset in range(0x22, 0x28):
                commands += struct.pack('<BIB', 4, record['address']+offset, 0)
        dirty = self.pine.read(before['inventory']+0x50, 1)[0]
        commands += struct.pack('<BIB', 4, before['inventory']+0x50, dirty | 1)
        if self.pine.request(commands):
            raise RuntimeError(f'Unexpected reset response; inspect backup: {backup}')
        after = self.snapshot()
        if not self.pine.read(before['inventory']+0x50, 1)[0] & 1:
            raise RuntimeError(f'Profile dirty flag readback failed; inspect backup: {backup}')
        if (after['user'], after['inventory'], after['header']) != (
                before['user'], before['inventory'], before['header']):
            raise RuntimeError(f'Profile changed during reset; inspect backup: {backup}')
        if len(after['records']) != len(before['records']):
            raise RuntimeError(f'Level records changed during reset; inspect backup: {backup}')
        for old, new in zip(before['records'], after['records']):
            expected = bytearray.fromhex(old['raw'])
            expected[0x22:0x28] = bytes(6)
            if old['slot'] != new['slot'] or bytes.fromhex(new['raw']) != expected:
                raise RuntimeError(f'Progress reset readback failed; inspect backup: {backup}')
        (backup/'memory_after.json').write_text(json.dumps(after, indent=2), encoding='utf-8')
        return dict(levels=len(changed), backup=str(backup))
