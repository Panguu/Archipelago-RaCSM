"""Publish reversible AP permissions to the v1.30 native inventory filters."""
import struct
from .patch_hooks import code, HOOKS
from .game_versions import identify
from .inventory_policy_hooks import BUFFER, MAGIC, CAPACITY


class InventoryPolicy:
    def __init__(self, pine, inventory):
        self.pine, self.inventory = pine, inventory
        self.verified = False
        self.current = None

    def validate(self):
        if self.verified:
            return
        if identify(self.pine)[1]['version'] != '01.30':
            raise RuntimeError('AP inventory filtering requires the v1.30 patch')
        wanted = {name: code(name) for name in ('inventory_policy', 'random_candidate')}
        # RPCS3 may redirect compiled execution without updating PINE-visible text.
        for address in range(0x10000, 0x2000000, 0x10000):
            try:
                prefix = self.pine.read(address, 32)
            except ValueError:
                continue
            for name, binary in list(wanted.items()):
                if prefix == binary[:32] and self.pine.read(address, len(binary)) == binary:
                    del wanted[name]
            if not wanted:
                self.verified = True
                return
        raise RuntimeError('Inventory ownership patch missing or outdated; restart RPCS3 with the updated patch')

    def word(self, address, value):
        if not BUFFER <= address < BUFFER+0x10000:
            raise ValueError('Policy writes must stay inside their mailbox')
        self.pine.request(struct.pack('<BII', 6, address, value))

    def refresh(self, profile):
        base, count, capacity = struct.unpack('>III', self.pine.read(profile[1]+0xc0, 12))
        if not 0 <= count <= capacity <= 256:
            raise RuntimeError('Inventory views changed; retry policy publication')
        views = struct.unpack(f'>{count}I', self.pine.read(base,count*4)) if count else ()
        if self.inventory.profile() != profile:
            raise RuntimeError('Profile changed while refreshing inventory views')
        for view in views:
            if view:
                self.pine.request(struct.pack('<BIB',4,view+0x38,1))

    def publish(self, plans):
        plans = tuple(sorted(set(plans)))
        if len(plans)>CAPACITY or any(type(p) is not int or not 0<p<0x80000000 for p in plans):
            raise ValueError('Invalid AP inventory allowlist')
        self.validate()
        profile = self.inventory.profile()
        identity = (profile, plans)
        if identity == self.current:
            return True
        self.word(BUFFER, MAGIC)
        self.word(BUFFER+8, 2)
        self.word(BUFFER+4, 1)
        self.word(BUFFER+12, profile[0])
        self.word(BUFFER+16, len(plans))
        commands = b''.join(struct.pack('<BII',6,BUFFER+0x100+4*i,p) for i,p in enumerate(plans))
        if commands:
            self.pine.request(commands)
        expected = struct.pack(f'>{len(plans)}I',*plans)
        if self.pine.read(BUFFER+0x100,len(expected)) != expected or self.inventory.profile()!=profile:
            raise RuntimeError('Inventory allowlist publication changed; access remains blocked')
        self.word(BUFFER+8, 1)
        self.refresh(profile)
        self.current = identity
        return True

    def disable(self):
        if self.verified:
            self.word(BUFFER+8, 0)
            self.refresh(self.inventory.profile())
            self.current = None
