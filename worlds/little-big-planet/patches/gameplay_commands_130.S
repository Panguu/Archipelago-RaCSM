# Opcodes 2 restart, 3 empty checkpoint, 4 refill checkpoint,
# 5 jetpack, 6 paintball gun. Opcode 7 is retired. Runs after solo/profile guards.
# Timer lease: +100 ticks, +104 creature, +108 world, +10c native state.
    lwz 0,0x100(31)
    cmpwi 0,0
    beq effect_command
    ld 9,0x88(1)
    lwz 9,8(9)
    lwz 3,0x40(9)
    lwz 10,0x104(31)
    cmpw 3,10
    bne effect_cancel
    lwz 9,0xe0(31)
    lwz 10,0x108(31)
    cmpw 9,10
    bne effect_cancel
    lwz 9,0x934(3)
    lwz 10,0x10c(31)
    cmpw 9,10
    bne effect_cancel
    lwz 9,0x100(31)
    addi 9,9,-1
    stw 9,0x100(31)
    cmpwi 9,0
    bne effect_command
    li 4,0
    lis 12,0x0006
    ori 12,12,0x79c4
    mtctr 12
    bctrl
effect_cancel:
    li 0,0
    stw 0,0x100(31)
effect_command:
    lwz 0,12(31)
    cmpwi 0,1
    bne effect_no_command
    lwz 0,0xd0(31)
    cmpwi 0,2
    bge effect_level_guard
    b effect_no_command
effect_level_guard:
    lwz 9,0xe4(31)
    lwz 9,0x120(9)
    cmpwi 9,5
    beq done
    lwz 0,0xd0(31)
    cmpwi 0,2
    beq effect_restart
    cmpwi 0,3
    beq effect_checkpoint
    cmpwi 0,4
    beq effect_checkpoint
    cmpwi 0,5
    beq effect_equipment
    cmpwi 0,6
    beq effect_equipment
    b effect_no_command
effect_restart:
    lwz 3,0xe4(31)
    li 4,0
    lis 12,0x000a
    ori 12,12,0xf898
    mtctr 12
    bctrl
    b effect_success
effect_checkpoint:
    li 3,0
    lis 12,0x0001
    ori 12,12,0xdddc
    mtctr 12
    bctrl
    cmpwi 3,0
    beq done
    lwz 0,0xd0(31)
    cmpwi 0,3
    beq effect_empty
    lwz 9,0x120(31)
    cmpw 9,3
    bne effect_refill
    lwz 9,0x12c(31)
    lwz 10,0xe0(31)
    cmpw 9,10
    bne effect_refill
    lwz 0,0x128(31)
    stb 0,0x1c(3)
effect_refill:
    lwz 0,0x18(3)
    cmpwi 0,0
    bge effect_checkpoint_write
    b done
effect_empty:
    lwz 9,0x120(31)
    cmpw 9,3
    bne effect_save_checkpoint
    lwz 9,0x12c(31)
    lwz 10,0xe0(31)
    cmpw 9,10
    beq effect_disable_checkpoint
effect_save_checkpoint:
    stw 3,0x120(31)
    lwz 9,0xe0(31)
    stw 9,0x12c(31)
    lbz 9,0x1c(3)
    stw 9,0x128(31)
effect_disable_checkpoint:
    li 0,0
    stb 0,0x1c(3)
effect_checkpoint_write:
    stw 0,0x14(3)
    b effect_success
effect_equipment:
    # Defer until alive and without an existing ability; never overwrite equipment.
    ld 9,0x88(1)
    lwz 9,8(9)
    lwz 3,0x40(9)
    cmpwi 3,0
    beq done
    lwz 9,0x934(3)
    cmpwi 9,0
    bne done
    stw 3,0x104(31)
    lwz 9,0xe0(31)
    stw 9,0x108(31)
    li 9,900
    stw 9,0x100(31)
    li 4,1
    cmpwi 0,5
    beq effect_state
    li 4,2
    b effect_gun
effect_state:
    stw 4,0x10c(31)
    lis 12,0x0006
    ori 12,12,0x79c4
    mtctr 12
    bctrl
    b effect_success
effect_gun:
    stw 4,0x10c(31)
    li 4,0
    lis 12,0x0006
    ori 12,12,0x96f0
    mtctr 12
    bctrl
effect_success:
    li 0,1
    stw 0,32(31)
    li 0,0
    stw 0,36(31)
    li 0,3
    sync
    stw 0,12(31)
    b done
effect_no_command:
    lwz 0,12(31)
    cmpwi 0,1
    beq effect_normal
    cmpwi 0,2
    bne done
effect_normal:
