"""Queued AP messages rendered independently of native interaction prompts."""
from collections import deque
import logging

from .address_maps import CURRENT_PLANET_ADDRESS
from .structs.game import TransitionGateStruct, TRANSITION_GATE_IDLE
from .vendor_profiles import resolve
from .patches.kernel import KernelBridge
from .patches.storage import PatchStorage
from .patches.notification import NotificationHook


class HudNotifications:
    def __init__(self, memory):
        self.memory = memory
        self.pending = deque(maxlen=12)
        self.profile = self.planet = None
        self.kernel = self.storage = self.hook = None
        self.failed = False

    def enqueue(self, text):
        text = ''.join(c if 32 <= ord(c) < 127 else '?' for c in str(text))
        if text:
            self.pending.append(text[:60])

    def _ready(self, planet):
        return (self.memory.read_int8(CURRENT_PLANET_ADDRESS) == planet
                and self.memory.read_int32(TransitionGateStruct.BASE_ADDRESS) == TRANSITION_GATE_IDLE)

    def _release(self, planet):
        if self.storage is None:
            return
        if planet != self.planet:
            profile = resolve(self.memory, planet)
            if profile is None:
                raise RuntimeError('Cannot release notification storage on unknown overlay')
            self.kernel.profile = profile
        with self.kernel.frame():
            if self.hook is not None and self.hook.plan is not None:
                if planet == self.planet:
                    self.hook.restore()
                else:
                    # Do not restore instructions belonging to an unloaded overlay.
                    edit = self.hook.plan.edits[0]
                    if self.memory.read_bytes(edit.address, 8) == edit.replacement:
                        raise RuntimeError('Old notification hook is still reachable')
                    self.storage.release(self.hook)
            self.storage.close()
        self.storage = self.kernel = self.hook = None
        self.profile = self.planet = None

    def tick(self, planet, ready):
        if not ready or not self._ready(planet) or self.failed:
            return
        if not self.pending and self.storage is None:
            return
        try:
            if self.planet is not None and self.planet != planet:
                self._release(planet)
            if self.hook is not None:
                # Reads only here; all writes and allocation validation occur
                # at a verified boundary after the executable hook has returned.
                if self.memory.read_int32(self.hook.state.address):
                    return
            if not self.pending:
                return
            if self.profile is None:
                self.profile = resolve(self.memory, planet)
                if self.profile is None:
                    return
                self.planet = planet
                self.kernel = KernelBridge(self.memory, self.profile, interior=True)
            with self.kernel.frame():
                if self.storage is None:
                    self.storage = PatchStorage(self.memory, self.kernel, size=1024)
                    self.storage.open()
                    self.hook = NotificationHook(self.memory, self.storage, self.profile, planet)
                    self.hook.install()
                self.hook.show(self.pending[0])
                self.pending.popleft()
        except Exception:
            self.failed = True
            logging.getLogger('CommonClient').exception(
                'PSP notifications stopped after validation failure; messages remain in client log')

    def close(self):
        planet = self.memory.read_int8(CURRENT_PLANET_ADDRESS)
        if self.storage is not None and not self._ready(planet):
            raise RuntimeError('Cannot release notification storage during loading')
        self._release(planet)
        self.failed = False
