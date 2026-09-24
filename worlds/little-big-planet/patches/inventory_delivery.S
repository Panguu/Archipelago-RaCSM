# NPEA00241 01.27 only. Hook entry of PYellowHead suicide-button update.
# Original routine takes only r3; preserve it, LR, TOC and all nonvolatile regs used.
# Mailbox 0x03030000: magic/version/heartbeat/state/seq/plan/inventory/user/
# result/error/resource/loading_ticks. Descriptor at +0x80. Slot at +0xc0.
# States: 0 idle, 1 submitted, 2 loading, 3 verified, 4 failed.
# Calls use the native main TOC and absolute CTR branches (calloc relocates code).
.text
.globl inventory_delivery
inventory_delivery:
    stdu 1,-0xb0(1)
    mflr 0
    std 0,0xa0(1)
    std 2,0x90(1)
    std 3,0x88(1)
    std 30,0x78(1)
    std 31,0x80(1)
    lis 31,0x0303
    lwz 0,0(31)
    cmpwi 0,0
    bne initialized
    li 0,1
    stw 0,4(31)
    lis 0,0x4150
    ori 0,0,0x4947
    sync
    stw 0,0(31)
initialized:
    lwz 9,8(31)
    addi 9,9,1
    stw 9,8(31)
    lwz 0,12(31)
    cmpwi 0,1
    beq active
    cmpwi 0,2
    bne done
active:
    sync
    # Child Sackboy Things have no world pointer; follow the active level root.
    lis 9,0x0086
    ori 9,9,0xb3c8
    lwz 9,0(9)
    cmpwi 9,0
    beq profile_error
    lwz 9,0(9)
    cmpwi 9,0
    beq profile_error
    lwz 9,0x78(9)
    cmpwi 9,0
    beq profile_error
    lwz 9,0x50(9)
    cmpwi 9,0
    beq profile_error
    lwz 9,0x14(9)
    cmpwi 9,0
    beq profile_error
    lwz 10,0x90(9)
    cmpwi 10,1
    bne profile_error
    lwz 9,0x8c(9)
    lwz 9,0(9)
    cmpw 9,3
    bne profile_error
    lis 2,0x0087
    ori 2,2,0x1498
    lis 9,0x0087
    ori 9,9,0x9f84
    lwz 9,0(9)
    lwz 9,0(9)
    lwz 10,28(31)
    cmpw 9,10
    bne profile_error
    lis 12,0x001d
    ori 12,12,0x892c
    mtctr 12
    bctrl
    lwz 30,0(3)
    lwz 9,24(31)
    cmpw 30,9
    bne profile_error
    cmpwi 30,0
    beq profile_error
    lwz 9,0(30)
    lis 10,0x0085
    ori 10,10,0x48b0
    cmpw 9,10
    bne profile_error
    lwz 0,12(31)
    cmpwi 0,2
    beq loading
    # Local GUID descriptor, same shape constructed by native RPlan loader.
    li 0,-1
    stw 0,0x80(31)
    stw 0,0x84(31)
    lwz 4,20(31)
    stw 4,0x88(31)
    li 0,0
    stw 0,0x8c(31)
    stw 0,0x90(31)
    stw 0,0x94(31)
    stw 0,0x98(31)
    stw 0,0x9c(31)
    stw 0,40(31)
    stw 0,44(31)
    stw 0,32(31)
    stw 0,36(31)
    li 0,0x26
    stw 0,0xa0(31)
    li 0,1
    stb 0,0xa4(31)
    # Obtain a retained RPlan handle; loading completes asynchronously.
    addi 3,31,40
    li 5,0
    li 6,2
    lis 12,0x0057
    ori 12,12,0x353c
    mtctr 12
    bctrl
    lwz 9,40(31)
    cmpwi 9,0
    beq load_error
    li 0,2
    stw 0,12(31)
loading:
    lwz 9,40(31)
    cmpwi 9,0
    beq load_error
    lwz 0,0x1c(9)
    cmpwi 0,3
    beq loaded
    cmplwi 0,3
    bgt load_error
    lwz 9,44(31)
    addi 9,9,1
    stw 9,44(31)
    cmplwi 9,1800
    bge timeout_error
    b done
loaded:
    lwz 0,0x34(9)
    lwz 10,20(31)
    cmpw 0,10
    bne load_error
    # Use native AddPlan with collect=true, including its duplicate handling.
    addi 3,30,0
    addi 4,31,40
    li 5,0
    li 6,0
    li 7,1
    li 8,0
    addi 9,31,0xc0
    lis 12,0x000b
    ori 12,12,0x43c4
    mtctr 12
    bctrl
    # A return flag alone is insufficient: find the exact GUID in this profile.
    addi 3,30,0
    addi 4,31,0x80
    lis 12,0x000a
    ori 12,12,0x05f4
    mtctr 12
    bctrl
    cmpwi 3,0
    beq verify_error
    stw 3,32(31)
    lbz 0,0x9a(3)
    cmpwi 0,0
    bne verify_error
    # Native AddPlan marks the profile dirty. Release our retained resource.
    li 0,0
    stw 0,36(31)
    b finish
profile_error:
    li 0,1
    stw 0,36(31)
    b finish
load_error:
    li 0,2
    stw 0,36(31)
    b finish
timeout_error:
    li 0,3
    stw 0,36(31)
    b finish
verify_error:
    li 0,4
    stw 0,36(31)
finish:
    # Profile errors can occur before the native TOC is installed.
    lis 2,0x0087
    ori 2,2,0x1498
    lwz 0,40(31)
    cmpwi 0,0
    beq released
    addi 3,31,40
    lis 12,0x0056
    ori 12,12,0x1648
    mtctr 12
    bctrl
    li 0,0
    stw 0,40(31)
released:
    lwz 0,36(31)
    cmpwi 0,0
    li 9,3
    beq publish
    li 9,4
publish:
    sync
    stw 9,12(31)
done:
    ld 0,0xa0(1)
    mtlr 0
    ld 2,0x90(1)
    ld 3,0x88(1)
    ld 30,0x78(1)
    ld 31,0x80(1)
    addi 1,1,0xb0
    stdu 1,-0x90(1)
