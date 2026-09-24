"""v1.30 AP ownership gates; preserve inventory metadata and save contents."""
BUFFER = 0x03050000
MAGIC = 0x41504950
CAPACITY = 16000


def source(random_candidate=False):
    # The randomiser hook is mid-function, so preserve its live volatile regs/CR.
    entry = 27 if random_candidate else 4
    save = '\n'.join(f'    std {r},{offset}(1)' for r, offset in
                     ((0,112),(9,120),(10,128),(11,136),(12,144)))
    restore = '\n'.join(f'    ld {r},{offset}(1)' for r, offset in
                        ((0,112),(9,120),(10,128),(11,136),(12,144)))
    deny = ('    li 0,0\n    std 0,120(1)\n    b allowed' if random_candidate else
            f'{restore}\n    ld 0,152(1)\n    mtcr 0\n    ld 0,112(1)\n'
            '    addi 1,1,0xa0\n    li 3,0\n    blr')
    original = '    lwz 9,0x40(28)' if random_candidate else '    stdu 1,-0x80(1)'
    return f'''# Generated ownership predicate. Header: magic/version/mode/user/count.
.text
    stdu 1,-0xa0(1)
{save}
    mfcr 0
    std 0,152(1)
    lis 12,0x0305
    lwz 0,0(12)
    lis 10,0x4150
    ori 10,10,0x4950
    cmpw 0,10
    bne allowed
    lwz 0,8(12)
    cmpwi 0,0
    beq allowed
    # Mode 2 is an atomic publication barrier: deny until the table is complete.
    cmpwi 0,1
    bne denied
    lis 9,0x0087
    ori 9,9,0x9f90
    lwz 9,0(9)
    cmpwi 9,0
    beq denied
    lwz 9,0(9)
    lwz 10,12(12)
    cmpw 9,10
    bne denied
    lwz 10,4({entry})
    cmpwi 10,0
    beq denied
    lwz 11,16(12)
    cmplwi 11,{CAPACITY}
    bgt denied
    addi 12,12,0x100
loop:
    cmpwi 11,0
    beq denied
    lwz 0,0(12)
    cmpw 0,10
    beq allowed
    addi 12,12,4
    addi 11,11,-1
    b loop
denied:
{deny}
allowed:
{restore}
    ld 0,152(1)
    mtcr 0
    ld 0,112(1)
    addi 1,1,0xa0
{original}
'''


def random_source():
    # At 0x920c8, replay the original load on allowed paths, skip it on denied
    # paths with r9=0; absolute continuation is needed because calloc relocates.
    s = source(True)
    s = s.replace('    li 0,0\n    std 0,120(1)\n    b allowed',
                  '    li 0,0\n    std 0,120(1)\n    b random_denied')
    restore = s[s.index('allowed:\n') + len('allowed:\n'):]
    # Denied continuation preserves CTR by using a patched displaced category
    # test instead: move hook to 0x920cc, after the original load.
    s = s[:s.index('allowed:\n')] + 'random_denied:\nallowed:\n' + restore
    return s.replace('    lwz 9,0x40(28)', '    .word 0x552006b4')
