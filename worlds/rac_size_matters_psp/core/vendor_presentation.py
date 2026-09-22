"""Checked PSP T4 vendor icons. Addresses verified live on UCUS98633 Pokitaru."""
import logging
import struct
from importlib.resources import files

from .address_maps import CURRENT_PLANET_ADDRESS, WEAPON_VENDOR_ITEMS, WEAPON_VENDOR_SLOTS, WEAPON_ARRAY_BASE_BY_PLANET
from .patches import Patch, Plan
from .structs.game import TransitionGateStruct, TRANSITION_GATE_IDLE


class VendorPresentation:
    # row array, HUD resource map, texture descriptors, weapon vendor menu
    PROFILES = {1: (0x093FEE8C, 0x093F7CAC, 0x094420C0, 0x09597B24)}

    def __init__(self, memory):
        self.memory = memory
        root = files(__package__.rsplit('.', 1)[0]).joinpath('images', 'icons')
        self.pixels = root.joinpath('archipelago-psp.t4').read_bytes()
        self.palette = root.joinpath('archipelago-psp.rgba').read_bytes()
        if (len(self.pixels), len(self.palette)) != (512, 64):
            raise ValueError('Invalid PSP AP texture assets')
        self.plan = None
        self.failed = False
        self.reward_for_id = lambda identity: None

    def _original(self, address, size):
        data = bytearray(self.memory.read_bytes(address, size))
        for edit in self.plan.edits if self.plan else ():
            left, right = max(address, edit.address), min(address + size, edit.address + len(edit.original))
            if left < right:
                data[left-address:right-address] = edit.original[left-edit.address:right-edit.address]
        return bytes(data)

    def _text_edits(self, spec, reward):
        # Live-verified localization state: pointer, flags, count, TDEF tag flag.
        state = self.memory.read_bytes(0x094A0EC0, 24)
        pointer, count = struct.unpack_from('<I', state)[0], struct.unpack_from('<I', state, 16)[0]
        if state[8] != 1 or state[20:22] != b'\x01\x00' or not 0 < count < 20000:
            return []
        raw = self.memory.read_bytes(pointer, count * 12)
        entries = {}
        for offset in range(0, len(raw), 12):
            if raw[offset:offset+4] != b'TDEF':
                return []
            entries[struct.unpack_from('<I', raw, offset+4)[0]] = pointer+offset+8
        title_id, desc_id = struct.unpack('<II', self.memory.read_bytes(spec+16, 8))
        if title_id not in entries or desc_id not in entries or title_id == desc_id:
            return []
        title_entry, desc_entry = entries[title_id], entries[desc_id]
        desc = struct.unpack('<I', self._original(desc_entry, 4))[0]
        original = self._original(desc, 1024)
        end = original.find(b'\0')
        if end < 32:
            return []
        capacity = end + 1
        clean = lambda value: ''.join(c if 32 <= ord(c) < 127 else '?' for c in value).encode('ascii')
        name = clean(reward[0])[:min(96, capacity-25)]
        title = b'\x90\x02' + name + b'\x90\x01\0'
        recipient = (b'For ' + clean(reward[1]))[:capacity-len(title)-1] + b'\0'
        return [Patch(desc, original[:capacity], (title+recipient).ljust(capacity, b'\0')),
                Patch(title_entry, self._original(title_entry, 4), struct.pack('<I', desc)),
                Patch(desc_entry, self._original(desc_entry, 4), struct.pack('<I', desc+len(title)))]

    def abandon(self):
        """A loader owns this RAM now; never write an old overlay snapshot."""
        self.plan = None
        self.failed = False

    def restore(self):
        if self.plan is None:
            return
        with self.memory.paused():
            if (self.memory.read_int32(CURRENT_PLANET_ADDRESS) != self.plan.planet_id
                    or self.memory.read_int32(TransitionGateStruct.BASE_ADDRESS) != TRANSITION_GATE_IDLE):
                self.abandon()
                return
            self.plan.restore()
        self.plan = None

    def _edits(self, planet_id):
        rows, icons, textures, menu = self.PROFILES[planet_id]
        if self.memory.read_int32(menu) != 9:
            return None
        count = self.memory.read_int32(WEAPON_VENDOR_SLOTS)
        if not 1 <= count <= 21:
            return None
        ids = struct.unpack(f'<{count}I', self.memory.read_bytes(WEAPON_VENDOR_ITEMS, count * 4))
        edits = {}
        icon_ids = set()
        for index, identity in enumerate(ids):
            row = struct.unpack('<7I', self.memory.read_bytes(rows + index * 28, 28))
            # Native rows rebuild one frame after the client changes its list.
            if row[0] != identity:
                return None
            if row[2] == 0 and row[3] == 0:
                continue  # Native placeholder for an unavailable/hidden row.
            if not 0 < row[3] <= 108:
                return None
            icon_ids.add(row[3])
            if 2 <= identity <= 24:
                # Level-zero vendor specification: title, description, preview icon.
                spec = self.memory.read_int32(WEAPON_ARRAY_BASE_BY_PLANET[planet_id] + 1 + (identity-2)*88)
                if 0x08000000 <= spec <= 0x09FFFFB0:
                    preview = self.memory.read_int32(spec+24)
                    if 0 < preview <= 108:
                        icon_ids.add(preview)
                    reward = self.reward_for_id(identity)
                    if reward is not None:
                        for edit in self._text_edits(spec, reward):
                            edits[edit.address] = edit
        for icon_id in icon_ids:
            resource = self.memory.read_int32(icons + icon_id * 4)
            if not 0 < resource < 1024:
                return None
            image, clut = struct.unpack('<II', self.memory.read_bytes(textures + resource * 44 + 12, 8))
            ih, ph = self.memory.read_bytes(image, 64), self.memory.read_bytes(clut, 64)
            if (struct.unpack_from('<4H', ih, 4) != (4, 1, 32, 32)
                    or struct.unpack_from('<3H', ph, 4) != (3, 0, 16)):
                return None
            for header, payload in ((ih, self.pixels), (ph, self.palette)):
                address = struct.unpack_from('<I', header, 48)[0]
                edits[address] = Patch(address, self.memory.read_bytes(address, len(payload)), payload)
        return edits

    def update(self, planet_id, ready, enabled):
        if not ready:
            self.abandon()
            return
        try:
            if not enabled or planet_id not in self.PROFILES:
                self.restore()
                self.failed = False
                return
            if self.failed:
                return
            edits = self._edits(planet_id)
            if edits is None:
                return
            if not edits:
                self.restore()
                return
            previous = {e.address: e for e in self.plan.edits} if self.plan else {}
            if previous.keys() == edits.keys() and all(previous[a].replacement == e.replacement for a, e in edits.items()):
                self.plan.validate()
                return
            # Preserve genuine originals for textures shared with the last list.
            self.restore()
            edits = [Patch(addr, previous[addr].original if addr in previous else edit.original, edit.replacement)
                     for addr, edit in edits.items()]
            plan = Plan(self.memory, edits, name='AP vendor icons', planet_id=planet_id)
            with self.memory.paused():
                if (self.memory.read_int32(CURRENT_PLANET_ADDRESS) != planet_id
                        or self.memory.read_int32(TransitionGateStruct.BASE_ADDRESS) != TRANSITION_GATE_IDLE):
                    return
                plan.install()
            self.plan = plan
        except Exception:
            self.failed = True
            logging.getLogger('CommonClient').warning('AP vendor icon update failed; gameplay remains connected', exc_info=True)
