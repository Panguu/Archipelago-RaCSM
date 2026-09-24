"""Read-only executable-locked NPEA00241 v1.27/v1.30 level reader over PINE."""
import struct

from .game_versions import identify


def u32(data, offset=0):
    return struct.unpack_from('>I', data, offset)[0]


def parse_rewards(data, stride=44):
    if len(data) % stride:
        raise ValueError('Truncated reward array')
    result = []
    for offset in range(0, len(data), stride):
        record = data[offset:offset + stride]
        source = u32(record, stride - 4)
        if source not in range(4):
            raise ValueError(f'Unexpected reward source {source}')
        result.append({'plan_guid': u32(record, 8 if stride == 44 else 4), 'source': source,
                       'descriptor_hex': record[:stride-4].hex()})
    return result


class LevelReader:
    # Resolved from the actual GetNumCollectablesInLevel implementation.
    ROOT_TOC_SLOT = 0x86B3C8
    SIGNATURES = {
        0x85D48: bytes.fromhex('81229f30806900004e800020'),
        0x85F74: bytes.fromhex('8523007c800300047d2b4b78'),
    }

    def __init__(self, pine, catalogue):
        self.pine = pine
        self.catalogue = catalogue

    def word(self, address):
        return u32(self.pine.read(address, 4))

    def validate(self):
        info = self.pine.info()
        self.executable, self.build = identify(self.pine, info)
        self.ROOT_TOC_SLOT = self.build['root']
        if info['status'] not in ('running', 'paused'):
            raise RuntimeError('Game is not running')
        for address, expected_hex in self.build['signatures'].items():
            expected = bytes.fromhex(expected_hex)
            if self.pine.read(address, len(expected)) != expected:
                raise RuntimeError(f'Executable signature mismatch at {address:#x}')
        return info

    def snapshot(self):
        """Diagnostic snapshot for the dev CLI; not used by the live client."""
        info = self.validate()
        global_address = self.word(self.ROOT_TOC_SLOT)
        if not global_address:
            raise RuntimeError('Game context unavailable')
        context = self.word(global_address)
        if not context:
            raise RuntimeError('No active game context')
        header = self.pine.read(context + 0x7c, 12)
        address, count, capacity = struct.unpack('>III', header)
        if not 0 <= count <= capacity <= 100000 or (count and not address):
            raise RuntimeError('Invalid reward array; level may be loading')
        records = parse_rewards(self.pine.read(address, count * self.build['reward_size']), self.build['reward_size']) if count else []
        if self.word(global_address) != context or self.pine.read(context + 0x7c, 12) != header:
            raise RuntimeError('Level changed during read; retry')
        prizes = [r for r in records if r['source'] == 0]
        # Match the complete reward multiset, not a single GUID or a guessed level pointer.
        plans = sorted(r['plan_guid'] for r in prizes)
        matches = []
        if plans:
            for level in self.catalogue['levels']:
                authored = [b for b in level['bubbles'] if b['kind'] == 'prize']
                if any(not str(b['prize_plan']).startswith('g') for b in authored):
                    continue
                if sorted(int(b['prize_plan'][1:]) for b in authored) == plans:
                    matches.append(level)
        result = {
            'game': info, 'level_match_method': 'exact prize-plan multiset; not a live level-ID field',
            'matching_level_guids': [l['guid'] for l in matches],
            'live_prize_total': len(prizes), 'live_reward_total_including_awards': len(records),
            'collected_prizes': None, 'collected_score_bubbles': None,
            'collection_status': 'unknown: reward array lists available rewards, not pickups',
            'rewards': records,
        }
        if len(matches) == 1:
            level = matches[0]
            result['level'] = {k:v for k,v in level.items() if k != 'bubbles'}
            result['prize_locations'] = [b for b in level['bubbles'] if b['kind'] == 'prize']
        return result

    def completion_prizes(self, level, expected_slot=None):
        """Match the live prize multiset to the authored level before using its total."""
        context = self.word(self.word(self.ROOT_TOC_SLOT))
        if not context:
            raise RuntimeError('No active level context')
        slot = self.pine.read(context+self.build['slot'], 8)
        if expected_slot is not None and struct.unpack('>II', slot) != expected_slot:
            raise RuntimeError('Level changed before reading completion rewards')
        header = self.pine.read(context+0x7c, 12)
        pointer, count, capacity = struct.unpack('>III', header)
        if not 0 <= count <= capacity <= 10000 or (count and not pointer):
            raise RuntimeError('Invalid live reward array')
        size = count*self.build['reward_size']
        data = b''.join(self.pine.read(pointer+offset, min(256, size-offset))
                        for offset in range(0, size, 256))
        records = parse_rewards(data, self.build['reward_size'])
        collected = self.word(context+0x88)
        if (self.word(self.word(self.ROOT_TOC_SLOT)) != context
                or self.pine.read(context+self.build['slot'], 8) != slot
                or self.pine.read(context+0x7c, 12) != header):
            raise RuntimeError('Level changed while reading completion rewards')
        expected = [loc.get('plan') for loc in level['locations'] if loc['kind'] == 'prize']
        actual = sorted(f'g{r["plan_guid"]}' for r in records if r['source'] == 0)
        if not expected or any(not p or not p.startswith('g') for p in expected):
            return None, None
        if sorted(expected) != actual:
            return None, None
        return collected, len(actual)

    def progress(self):
        """Observed LBP1 profile counters. No writes and no inferred physical pickups."""
        self.validate()
        global_address = self.word(self.ROOT_TOC_SLOT)
        context = self.word(global_address)
        if not context: raise RuntimeError('No active context')
        slot_type, slot_number = struct.unpack('>II',self.pine.read(context+self.build['slot'],8))
        # World death count implements GetDeathCount; this can include multiple players.
        level = self.word(context+0x78)
        thing = self.word(level+0x50) if level else 0
        world = self.word(thing+0x14) if thing else 0
        death_count = self.word(world+0x520) if world else None
        active_user = self.word(self.word(self.build['user']))
        table = self.word(self.build['table'])
        players = self.pine.read(table,7*16)
        inventories = [u32(players,i+12) for i in range(0,len(players),16)
                       if players[i] and u32(players,i+4)==active_user and u32(players,i+12)]
        if len(inventories)!=1: raise RuntimeError('Active player inventory is ambiguous')
        inventory = inventories[0]
        header = self.pine.read(inventory+0x14c,12)
        pointer,count,capacity = struct.unpack('>III',header)
        if not 0 <= count <= capacity <= 10000: raise RuntimeError('Invalid played-level array')
        records = self.pine.read(pointer,count*0x58) if count else b''
        progress = []
        for offset in range(0,len(records),0x58):
            record = records[offset:offset+0x58]
            typ,number = struct.unpack_from('>II',record)
            plays,completions,aces = struct.unpack_from('>HHH',record,0x22)
            progress.append({'slot_type':typ,'slot_number':number,'play_count':plays,
                             'completion_count':completions,'ace_count':aces})
        if (self.word(global_address)!=context or
            self.pine.read(context+self.build['slot'],8)!=struct.pack('>II',slot_type,slot_number) or
            self.pine.read(inventory+0x14c,12)!=header):
            raise RuntimeError('Game changed while reading progress')
        return {'slot_type':slot_type,'slot_number':slot_number,'world_address':world,
                'world_death_count':death_count,'active_user':active_user,
                'inventory_address':inventory,
                'prizes_at_last_completion':self.word(context+0x88),
                'played_levels':progress,
                'validation':'Death/completion tested in First Steps; ace positive case and other levels untested'}
