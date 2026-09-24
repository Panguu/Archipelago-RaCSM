"""Assembled v1.30 hook identities, shared by the live client and the standalone
RPCS3 patch builder (dev-tools/little-big-planet/build_patches_130.py)."""
from pathlib import Path

from .ppc_assembler import assemble
from .inventory_policy_hooks import source as policy_source, random_source

ROOT = Path(__file__).resolve().parents[1]

CHANGES = [
    (0x115d8, 0x419dff20, 0x4bffff20, 'Skip mandatory intro'),
    (0x36b8f0, 0xf821ff81, 0x38600001, 'Intro completion UI query'),
    (0x36b8f4, 0x7c0802a6, 0x4e800020, 'Return'),
    (0x2d10f8, 0xf821ff91, 0x38600004, 'Progression UI query'),
    (0x2d10fc, 0x7c0802a6, 0x4e800020, 'Return'),
    (0x2696a0, 0x80090204, 0x38000004, 'Planet action progression'),
    (0x26e730, 0x80090204, 0x38000004, 'Planet display progression'),
    (0x18d54, 0x80630000, 0x38600001, 'Expose installed GOTY bonus content'),
    (0x18d58, 0x38000001, 0x4e800020, 'GOTY query return'),
]
HOOKS = {'prize_probe': (0x3afeb4, 0x824293a8),
         'score_pickup': (0x72a080, 0xf821ff61),
         'key_pickup': (0x3afc44, 0x38040008),
         'inventory_delivery': (0x68cac, 0xf821ff71),
         'level_access': (0xb744c, 0xf821ff31),
         'inventory_policy': (0x28aba4, 0xf821ff81),
         'random_candidate': (0x920cc, 0x552006b4)}


def source(name):
    if name in ('inventory_policy', 'random_candidate'):
        return random_source() if name == 'random_candidate' else policy_source()
    s = (ROOT / 'patches' / f'{name}.S').read_text(encoding='utf-8')
    s = s.replace('01.27', '01.30').replace('0xb3c8', '0xb3d8')
    if name in ('prize_probe', 'score_pickup'):
        s = s.replace('0x128(9)', '0x120(9)').replace('0x12c(9)', '0x124(9)')
        s = s.replace('-0x6c54(2)', '-0x6c58(2)')
    if name == 'inventory_delivery':
        for before, after in [('0x1498', '0x14a0'), ('0x9f84', '0x9f90'),
                              ('0x892c', '0x8db4'), ('0x353c', '0x2358'),
                              ('0x43c4', '0x83cc'), ('0x05f4', '0x10dc'),
                              ('lis 12,0x0056\n    ori 12,12,0x1648',
                               'lis 12,0x0055\n    ori 12,12,0x0d58'),
                              ('0x9a(3)', '0x92(3)')]:
            s = s.replace(before, after)
        start = s.index('    li 0,-1\n    stw 0,0x80(31)')
        end = s.index('    # Obtain a retained RPlan handle', start)
        s = s[:start] + '''    li 0,-1
    stw 0,0x80(31)
    lwz 4,20(31)
    stw 4,0x84(31)
    li 0,0
    stw 0,0x88(31)
    stw 0,0x8c(31)
    stw 0,0x90(31)
    stw 0,0x94(31)
    stw 0,0x98(31)
    stw 0,40(31)
    stw 0,44(31)
    stw 0,32(31)
    stw 0,36(31)
    lis 0,0x8000
    ori 0,0,0x26
    stw 0,0x9c(31)
''' + s[end:]
        marker = '    lwz 0,12(31)\n    cmpwi 0,2\n    beq loading'
        s = s.replace(marker, (ROOT/'patches/random_costume_command_130.S').read_text() + '\n' + marker)
        s = s.replace('    lwz 0,0xd0(31)', (ROOT/'patches/gameplay_commands_130.S').read_text() + '\n    lwz 0,0xd0(31)', 1)
        s = s.replace('    lwz 0,0x100(31)', (ROOT/'patches/bomb_command_130.S').read_text() + '\n    lwz 0,0x100(31)', 1)
        # Timed native effects continue even after their delivery is acknowledged.
        s = s.replace('    lwz 0,12(31)\n    cmpwi 0,1',
                      '    lwz 0,0x200(31)\n    cmpwi 0,0\n    bne active\n    lwz 0,0x100(31)\n    cmpwi 0,0\n    bne active\n    lwz 0,12(31)\n    cmpwi 0,1', 1)
        s = s.replace('    lwz 9,0x78(9)', '    stw 9,0xe4(31)\n    lwz 9,0x78(9)', 1)
        s = s.replace('    lwz 10,0x90(9)', '    stw 9,0xe0(31)\n    lwz 10,0x90(9)', 1)

    if name == 'level_access':
        s = s.replace('    lis 11,0x0304\n', '''    lis 11,0x0304
    lwz 0,0(11)
    cmpwi 0,0
    bne initialized
    li 0,1
    stw 0,4(11)
    lis 0,0x4150
    ori 0,0,0x4c56
    sync
    stw 0,0(11)
initialized:
''')
    return s


def code(name):
    return assemble(source(name))
