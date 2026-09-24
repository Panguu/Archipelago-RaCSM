# GetLockState(inventory, &SlotID). AP table is enabled by one atomic pointer.
# Unknown slots and an unconfigured client follow the original game function.
# No native profile writes; r3 returns 0 locked, 1 unlocked, 2 played, 3 complete.
.text
.globl level_access
level_access:
    stdu 1,-96(1)
    std 0,16(1)
    std 9,24(1)
    std 10,32(1)
    std 11,40(1)
    std 12,48(1)
    mfcr 0
    std 0,56(1)
    lis 11,0x0304
    lwz 11,8(11)
    cmpwi 11,0
    beq original
    sync
    lwz 9,0(11)
    cmplwi 9,256
    bgt original
    addi 11,11,4
loop:
    cmpwi 9,0
    beq original
    lwz 10,0(4)
    lwz 12,0(11)
    cmpw 10,12
    bne next
    lwz 10,4(4)
    lwz 12,4(11)
    cmpw 10,12
    bne next
    lwz 3,8(11)
    ld 0,56(1)
    mtcr 0
    ld 12,48(1)
    ld 11,40(1)
    ld 10,32(1)
    ld 9,24(1)
    ld 0,16(1)
    addi 1,1,96
    blr
next:
    addi 9,9,-1
    addi 11,11,12
    b loop
original:
    ld 0,56(1)
    mtcr 0
    ld 12,48(1)
    ld 11,40(1)
    ld 10,32(1)
    ld 9,24(1)
    ld 0,16(1)
    addi 1,1,96
    stdu 1,-208(1)
