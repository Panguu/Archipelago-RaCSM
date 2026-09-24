"""Executable-locked NPEA00241 solo DeathLink action using the game's RequestedSuicide flag."""
import asyncio
import struct
import time

from .reader import LevelReader


class PineDeathAdapter:
    can_apply_death = True
    SIGNATURES = {
        0x1caa8: bytes.fromhex('380000003920000190030070992300744e800020'),
        0x6cc3c: bytes.fromhex('88030074'),
        0x6cd40: bytes.fromhex('4bfffeb938000000981f0074'),
    }

    def __init__(self, pine):
        self.pine = pine
        self.reader = LevelReader(pine, {})
        self.last_result = None

    def snapshot(self):
        info = self.reader.validate()
        if info['status'] != 'running':
            raise RuntimeError('Game must be running')
        for address, expected_hex in self.reader.build['death'].items():
            expected = bytes.fromhex(expected_hex)
            if self.pine.read(address, len(expected)) != expected:
                raise RuntimeError(f'Death action signature mismatch at {address:#x}')
        q = self.reader.progress()
        if q['slot_type'] not in (0,8):
            raise RuntimeError('DeathLink requires a playable story/DLC level')
        world = q['world_address']
        header = self.pine.read(world+0x8c,12)
        pointer, count, capacity = struct.unpack('>III',header)
        if count != 1 or not 1 <= capacity <= 32:
            raise RuntimeError('DeathLink currently requires exactly one player')
        yellow = self.reader.word(pointer)
        thing = self.reader.word(yellow+8)
        if not yellow or not thing or self.reader.word(thing+0x24) != yellow:
            raise RuntimeError('Player part backlink mismatch')
        creature = self.reader.word(thing+0x40)
        if not creature:
            raise RuntimeError('No player creature')
        state = self.pine.read(creature+0x937,1)[0]
        request = self.pine.read(yellow+0x70,5)
        if self.pine.read(world+0x8c,12) != header:
            raise RuntimeError('Player list changed during read')
        return {'world':world, 'yellowhead':yellow, 'thing':thing, 'creature':creature,
                'state':state, 'request_hex':request.hex(), 'deaths':q['world_death_count'],
                'slot':[q['slot_type'],q['slot_number']]}

    def can_die_now(self):
        if not self.can_apply_death:
            return False
        try:
            state = self.snapshot()
            return state['state']==0 and state['request_hex']=='0000000000'
        except (RuntimeError, ValueError, OSError):
            return False

    async def apply_death(self):
        if not self.can_apply_death:
            return False
        before = self.snapshot()
        if before['state'] != 0 or before['request_hex'] != '0000000000':
            return False
        fresh = self.snapshot()
        if fresh != before:
            return False
        # Equivalent to the traced request setter; the game's update performs death.
        # Timer is already zero by guard, so only the one request byte changes.
        reply = self.pine.request(struct.pack('<BIB',4,before['yellowhead']+0x74,1))
        if reply:
            self.can_apply_death = False
            raise RuntimeError('Unexpected suicide request response; action disabled')
        start = time.monotonic()
        while time.monotonic()-start < 5:
            await asyncio.sleep(.05)
            after = self.snapshot()
            if after['world'] != before['world'] or after['thing'] != before['thing']:
                break
            if after['deaths'] > before['deaths']:
                self.last_result = {'before':before, 'after':after, 'acknowledged':True}
                return True
        # Do not keep injecting requests when acknowledgement is uncertain.
        self.can_apply_death = False
        raise RuntimeError('Death request acknowledgement uncertain; further requests disabled')
