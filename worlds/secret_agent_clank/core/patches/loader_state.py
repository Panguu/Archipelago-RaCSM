class StartupBarrierLost(RuntimeError):
    """The verified loader barrier no longer matches the running game."""


class LoaderStateReader:
    """Read loader state and identify stable loads; never write game memory."""
    ORIGINAL = 0x24030005
    STATE = 0x1AAE3C
    STATUS = 0x19EF04
    TARGET = 0x1AAE78
    HANDLE = 0x1AAE5C
    SIGNATURE_START = 0x103BB8
    SIGNATURE = (0x0C0400A6, 0, 0x2404FFFF, 0x1044006B, 0x3C020020,
                 ORIGINAL, 0x24426320, 0xAE43AE3C, 0xAC510018,
                 0x0C04107A, 0xAC440004)

    def __init__(self, pine):
        self.pine = pine
        self.attached = False
        self._held_candidate = None

    def validate(self, *, patched=False):
        """The concrete startup barrier must validate its resident code."""
        raise NotImplementedError("Use the verified ISO startup barrier")

    def held_module(self, *, settled=False):
        if not self.attached:
            self._held_candidate = None
            return None
        self.validate(patched=True)
        p = self.pine
        addresses = [self.STATE, self.STATUS, self.TARGET, self.HANDLE]
        before = tuple(p.batch_read_int32(addresses))
        after = tuple(p.batch_read_int32(addresses))
        state, status, target, handle = before
        # State 4 + completed relocation. State 5 can still display a loading
        # screen but the level thread is already running and is NOT safe.
        if before != after or (state, status) != (4, 1) or not 0 <= target < 33 or not handle:
            self._held_candidate = None
            return None
        if settled:
            # PermanentRuntime calls once per poll. Do not initialize the DLL
            # on the first observation of completed relocation; the entire
            # loader identity must remain held through the next poll.
            previous, self._held_candidate = self._held_candidate, before
            if previous != before:
                return None
        elif self._held_candidate is not None and self._held_candidate != before:
            self._held_candidate = None
            return None
        return target
