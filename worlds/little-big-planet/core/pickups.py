"""Read committed physical pickup events. Never infer a pickup from inventory/score."""
import re
import struct

BUFFER = 0x03000000
MAGIC = 0x4c425032
CAPACITY = 256
STRIDE = 160


class PickupReader:
    def __init__(self, pine, levels, interactions=()):
        self.pine = pine
        self.slots = {}
        self.locations = {}
        for guid, level in levels.items():
            for slot in level['slots']:
                match = re.fullmatch(r'SlotID\{(DEVELOPER|DLC_LEVEL), (\d+)\}', slot['slot'])
                if match:
                    self.slots.setdefault((0 if match[1] == 'DEVELOPER' else 8,
                                           int(match[2])), set()).add(guid)
            for location in level['locations']:
                if location['kind'] in ('prize', 'score'):
                    self.locations[(guid, location['kind'], location['uid'])] = location
        for location in interactions:
            if location['kind']=='key':
                self.locations[(location['level_guid'],'key',location['uid'])]=location

    def map_event(self, event):
        levels = self.slots.get((event['slot_type'], event['slot_number']), set())
        if len(levels) != 1:
            return None
        kind = {1: 'prize', 2: 'score', 3: 'key'}.get(event['type'])
        location = self.locations.get((next(iter(levels)), kind, event['uid']))
        if not location:
            return None
        if kind == 'prize' and location.get('plan') is not None and location['plan'] != f'g{event["plan_guid"]}':
            return None
        if kind == 'key':
            slot_type=event.get('target_slot_type')
            if slot_type not in (0,8): return None
            target='SlotID{%s, %d}' % ('DEVELOPER' if slot_type==0 else 'DLC_LEVEL',event['plan_guid'])
            if location['target_slot']!=target: return None
        return location['id']

    def read(self):
        magic, producer, consumer, dropped = struct.unpack('>4I', self.pine.read(BUFFER, 16))
        if magic == 0:
            return {'location_ids': [], 'pickup_events': [], 'pickup_cursor': None,
                    'pickup_status': 'pickup hook waiting for its first event'}
        if magic != MAGIC:
            raise RuntimeError('Pickup hook v2 requires a full RPCS3 restart')
        if dropped:
            raise RuntimeError(f'Pickup ring overflow: {dropped} events lost; replay affected level after restart')
        count = (producer - consumer) & 0xffffffff
        if count > CAPACITY:
            raise RuntimeError('Invalid pickup ring counters')
        events, checks = [], set()
        for offset in range(count):
            sequence = (consumer + offset) & 0xffffffff
            raw = self.pine.read(BUFFER + 256 + (sequence % CAPACITY) * STRIDE, STRIDE)
            seq, kind, typ, slot, plan, thing, collector, uid = struct.unpack('>8I', raw[:32])
            if seq != sequence or kind not in (1, 2, 3):
                raise RuntimeError('Incomplete pickup ring event')
            event = dict(sequence=seq, type=kind, slot_type=typ, slot_number=slot,
                         plan_guid=plan, thing_address=thing, collector_address=collector,
                         uid=uid, raw=raw.hex())
            if kind==3: event['target_slot_type']=struct.unpack_from('>I',raw,32)[0]
            location = self.map_event(event)
            event['location_id'] = location
            if location is not None:
                checks.add(location)
            events.append(event)
        unmatched = sum(e['location_id'] is None for e in events)
        return dict(location_ids=sorted(checks), pickup_events=events,
                    pickup_cursor=(consumer, producer),
                    pickup_status=f'pickup hook v2: {producer} captured, {unmatched} unmatched pending')

    def acknowledge(self, cursor):
        if cursor is None:
            return
        consumer, producer = cursor
        header = struct.unpack('>4I', self.pine.read(BUFFER, 16))
        if header[0] != MAGIC or header[2] != consumer or (header[1]-producer)&0xffffffff > CAPACITY:
            raise RuntimeError('Pickup ring changed before durable acknowledgement')
        # One aligned guest Write32: byte-wise writes can transiently expose an
        # invalid cursor to the producer when the low byte wraps at 256 events.
        self.pine.request(struct.pack('<BII', 6, BUFFER+8, producer))
