"""Executable-locked v1.27 intro/menu bypass and level-access hook identity."""
HASH = 'PPU-53fe207e75d7dfa26f83416f0f587bebe7005a0b'
NAME = 'Archipelago intro skip and level access v1'
BUFFER = 0x03040000
MAGIC = 0x41504c56
HOOK = 0xb3428
# Each replacement has been traced independently: no completion counter stores.
CHANGES = [
    (0x115f4, 0x419dff20, 0x4bffff20, 'Boot into saved/default pod, not mandatory intro'),
    (0x36b580, 0xf821ff81, 0x38600001, 'IntroLevelHasBeenCompleted query returns true'),
    (0x36b584, 0x7c0802a6, 0x4e800020, 'Return without editing intro completion data'),
    (0x2d0b3c, 0xf821ff91, 0x38600004, 'GetGameProgression UI query returns first-group-complete'),
    (0x2d0b40, 0x7c0802a6, 0x4e800020, 'Return without editing saved progression'),
    (0x269220, 0x80090204, 0x38000004, 'Native planet action selection progression gate'),
    (0x26e2c0, 0x80090204, 0x38000004, 'Native planet menu rendering progression gate'),
]
