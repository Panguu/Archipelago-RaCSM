"""Research barrier between DLL relocation and starting the level thread."""
import struct


class LoaderGate:
    SITE = 0x103BCC
    ORIGINAL = 0x24030005
    HELD = 0x10000069  # beq zero, zero, 0x103D74; existing delay slot is safe
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
        self.armed = False

    def validate(self, *, patched=False):
        if self.pine.get_game_id() != "SCUS-97623":
            raise RuntimeError("Loader barrier supports only SCUS-97623")
        expected = list(self.SIGNATURE)
        if patched:
            expected[5] = self.HELD
        actual = self.pine.read_bytes(self.SIGNATURE_START, len(expected) * 4)
        if actual != struct.pack("<11I", *expected):
            raise RuntimeError("Resident loader signature changed")

    def arm(self):
        if self.armed:
            raise RuntimeError("Loader barrier already armed")
        self.validate()
        # Mark before the write so finally can recover a failed readback.
        self.armed = True
        self.pine.write_int32(self.SITE, self.HELD)
        self.validate(patched=True)

    def held_module(self):
        if not self.armed:
            return None
        self.validate(patched=True)
        p = self.pine
        before = (p.read_int32(self.STATE), p.read_int32(self.STATUS))
        target, handle = p.read_int32(self.TARGET), p.read_int32(self.HANDLE)
        after = (p.read_int32(self.STATE), p.read_int32(self.STATUS))
        # State 4 + completed relocation. State 5 can still display a loading
        # screen but the level thread is already running and is NOT safe.
        if before == after == (4, 1) and 0 <= target < 33 and handle:
            return target
        return None

    def release(self):
        if not self.armed:
            return
        if self.pine.get_game_id() != "SCUS-97623":
            raise RuntimeError("Game changed; refusing resident code restoration")
        word = self.pine.read_int32(self.SITE)
        if word == self.HELD:
            self.validate(patched=True)
            self.pine.write_int32(self.SITE, self.ORIGINAL)
        elif word != self.ORIGINAL:
            raise RuntimeError("Barrier was replaced; refusing to overwrite unknown code")
        self.validate()
        self.armed = False
