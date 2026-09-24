# Game-thread colour command, inserted at inventory_delivery's done label.
# Validates world, slot, Thing UID and both sides of mesh ownership before writing.
# Mailbox 03060000: magic/version/state/sequence/world/count/applied/skipped/slot.
    lis 11,0x0306
    lwz 0,0(11)
    lis 10,0x4150
    ori 10,10,0x4248
    cmpw 0,10
    bne highlight_done
    lwz 0,8(11)
    cmpwi 0,1
    bne highlight_done
    sync
    li 0,0
    stw 0,24(11)
    stw 0,28(11)
    lis 9,0x0086
    ori 9,9,0xb3d8
    lwz 9,0(9)
    cmpwi 9,0
    beq highlight_reject
    lwz 9,0(9)
    cmpwi 9,0
    beq highlight_reject
    lwz 0,0x120(9)
    lwz 10,32(11)
    cmpw 0,10
    bne highlight_reject
    lwz 0,0x124(9)
    lwz 10,36(11)
    cmpw 0,10
    bne highlight_reject
    lwz 9,0x78(9)
    cmpwi 9,0
    beq highlight_reject
    lwz 9,0x50(9)
    cmpwi 9,0
    beq highlight_reject
    lwz 9,0x14(9)
    lwz 10,16(11)
    cmpw 9,10
    bne highlight_reject
    lwz 10,20(11)
    cmplwi 10,256
    bgt highlight_reject
    addi 12,11,0x100
highlight_loop:
    cmpwi 10,0
    beq highlight_publish
    lwz 3,0(12)
    lwz 4,4(12)
    cmpwi 3,0
    beq highlight_skip
    cmpwi 4,0
    beq highlight_skip
    lwz 5,8(12)
    lwz 0,0xb8(3)
    cmpw 0,5
    bne highlight_skip
    lwz 0,0x18(3)
    cmpw 0,4
    bne highlight_skip
    lwz 0,8(4)
    cmpw 0,3
    bne highlight_skip
    lwz 0,12(12)
    stw 0,0x10(4)
    lwz 0,16(12)
    stw 0,0x14(4)
    lwz 0,20(12)
    stw 0,0x18(4)
    lwz 0,24(12)
    stw 0,0x1c(4)
    lwz 0,24(11)
    addi 0,0,1
    stw 0,24(11)
    b highlight_next
highlight_skip:
    lwz 0,28(11)
    addi 0,0,1
    stw 0,28(11)
highlight_next:
    addi 12,12,32
    addi 10,10,-1
    b highlight_loop
highlight_reject:
    li 0,3
    b highlight_finish
highlight_publish:
    li 0,2
highlight_finish:
    sync
    stw 0,8(11)
highlight_done:
