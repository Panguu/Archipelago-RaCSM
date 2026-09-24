# Development opcode 8: native Timed Explosive emitter. Not in the item pool yet.
# Input +140 count, +144 up to nine tick offsets. Runtime +200 countdown,
# +204 owner Thing, +208 world, +20c emitter, +210 elapsed, +214 next index.
    lwz 9,0x200(31)
    cmpwi 9,0
    beq bomb_command
    ld 10,0x88(1)
    lwz 10,8(10)
    lwz 11,0x204(31)
    cmpw 10,11
    bne bomb_cancel
    lwz 10,0xe0(31)
    lwz 11,0x208(31)
    cmpw 10,11
    bne bomb_cancel
    lwz 10,0x204(31)
    lwz 10,0x5c(10)
    lwz 11,0x20c(31)
    cmpw 10,11
    bne bomb_cancel
    addi 9,9,-1
    stw 9,0x200(31)
    cmpwi 9,0
    beq bomb_remove
    lwz 9,0x210(31)
    addi 9,9,1
    stw 9,0x210(31)
    cmpwi 9,900
    bge bomb_command
    lwz 10,0x214(31)
    lwz 11,0x140(31)
    cmpw 10,11
    bge bomb_command
    mulli 11,10,4
    add 11,31,11
    lwz 11,0x144(11)
    cmpw 9,11
    bge bomb_due
    b bomb_command
bomb_due:
    addi 10,10,1
    stw 10,0x214(31)
    # Missed drops while dead are skipped, never accumulated.
    lwz 11,0x204(31)
    lwz 11,0x40(11)
    lwz 11,0x934(11)
    cmpwi 11,3
    bge bomb_command
    lwz 11,0x20c(31)
    lwz 9,0x4c(11)
    addi 9,9,1
    stw 9,0x48(11)
    b bomb_command
bomb_remove:
    lwz 3,0x204(31)
    li 4,20
    lis 2,0x0088
    ori 2,2,0x1314
    lis 12,0x0038
    ori 12,12,0xf380
    mtctr 12
    bctrl
    lis 2,0x0087
    ori 2,2,0x14a0
bomb_cancel:
    li 9,0
    stw 9,0x200(31)
bomb_command:
    lwz 0,12(31)
    cmpwi 0,1
    bne bomb_end
    lwz 0,0xd0(31)
    cmpwi 0,8
    bne bomb_end
    lwz 0,0x200(31)
    cmpwi 0,0
    bne done
    lwz 9,0xe4(31)
    lwz 9,0x120(9)
    cmpwi 9,5
    beq done
    lwz 0,0x140(31)
    cmpwi 0,0
    beq profile_error
    cmplwi 0,9
    bgt profile_error
    # Reject malformed schedules before allocating or touching a native part.
    li 9,0
    li 10,0
bomb_validate_tick:
    mulli 11,9,4
    add 11,31,11
    lwz 12,0x144(11)
    cmplwi 12,899
    bgt profile_error
    subf 11,10,12
    cmplwi 11,300
    bgt profile_error
    cmplwi 11,90
    bge bomb_valid_gap
    b profile_error
bomb_valid_gap:
    addi 10,12,0
    addi 9,9,1
    cmpw 9,0
    bne bomb_validate_tick
    ld 9,0x88(1)
    lwz 3,8(9)
    lwz 9,0x5c(3)
    cmpwi 9,0
    bne done
    stw 3,0x204(31)
    lwz 9,0xe0(31)
    stw 9,0x208(31)
    # Native AddPart owns allocation and world registration.
    li 4,20
    lis 12,0x0054
    ori 12,12,0x8b58
    mtctr 12
    bctrl
    ld 2,0x28(1)
    lwz 9,0x204(31)
    lwz 9,0x5c(9)
    cmpwi 9,0
    beq profile_error
    stw 9,0x20c(31)
    # Capture current player position through the game's PPos getter.
    lwz 4,0x204(31)
    lwz 4,0x1c(4)
    addi 3,31,0x240
    lis 12,0x0004
    ori 12,12,0xa164
    mtctr 12
    bctrl
    li 0,-1
    stw 0,0x280(31)
    li 0,0
    ori 0,0,0xd9fc
    stw 0,0x284(31)
    li 0,0
    stw 0,0x288(31)
    stw 0,0x28c(31)
    stw 0,0x290(31)
    stw 0,0x294(31)
    stw 0,0x298(31)
    stw 0,0x260(31)
    lis 0,0x3f80
    stw 0,0x264(31)
    lis 0,0x8000
    ori 0,0,0x26
    stw 0,0x29c(31)
    lwz 3,0x20c(31)
    addi 4,31,0x280
    li 9,0x240
    lvx 2,31,9
    li 9,0
    lfs 1,0x260(31)
    lfs 2,0x264(31)
    lfs 3,0x260(31)
    lfs 4,0x260(31)
    lis 12,0x0005
    ori 12,12,0xfdd4
    mtctr 12
    bctrl
    lwz 9,0x20c(31)
    # Spawn above the owner's centre: local Y +200 world units.
    # Native GetWorldEmitPos follows the owner's position on subsequent drops.
    lis 0,0x4348
    stw 0,0xa4(9)
    li 0,1
    stw 0,0x38(9)
    li 0,0
    stw 0,0x3c(9)
    stw 0,0x40(9)
    stw 0,0x210(31)
    stw 0,0x214(31)
    # Native max=0 means unlimited. Equal nonzero total/limit blocks emission.
    li 0,1
    stw 0,0x48(9)
    stw 0,0x4c(9)
    li 0,10
    stw 0,0x50(9)
    # Allow the prefab's final fuse to finish before native emitter cleanup.
    li 0,1200
    stw 0,0x200(31)
    b effect_success
bomb_end:
