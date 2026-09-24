"""Read actual v1.30 sticker activation, never inventory ownership or object removal."""
import struct


def active_switches(reader, progress, guid, locations):
    if reader.build['version'] != '01.30':
        return []
    wanted = {loc['uid']:loc for loc in locations.values()
              if loc['level_guid']==guid and loc['kind']=='sticker_switch'}
    if not wanted: return []
    pine=reader.pine
    world=progress['world_address']
    address=world+0x44+25*12
    header=pine.read(address,12)
    pointer,count,capacity=struct.unpack('>III',header)
    if not 0<=count<=capacity<=100000 or (count and not pointer):
        raise RuntimeError('Invalid switch vector')
    checks=[]
    for part, in struct.iter_unpack('>I',pine.read(pointer,count*4)):
        if not part: continue
        thing=reader.word(part+8)
        if not thing or reader.word(thing+0x70)!=part: continue
        loc=wanted.get(reader.word(thing+0xb8))
        if not loc or reader.word(part+0x160)!=5: continue
        if reader.word(part+0x4c)!=int(loc['sticker_plan'][1:]): continue
        # Native PSwitch::Refresh uses this manual-activation value for STICKER.
        # Tested 0 -> 1 on Get a Grip's Tea Pot switch, UID 824392.
        if pine.read(part+0x168,4)==b'\x3f\x80\x00\x00':
            checks.append(loc['id'])
    after=reader.progress()
    if pine.read(address,12)!=header or any(after[k]!=progress[k]
            for k in ('slot_type','slot_number','world_address','active_user','inventory_address')):
        raise RuntimeError('Level/profile changed while reading switches')
    return checks
