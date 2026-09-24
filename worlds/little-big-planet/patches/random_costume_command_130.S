# Inserted after the solo/profile guards in inventory_delivery.
# +0xd0 opcode (0 grant, 1 randomise), +0xd4 verified Popit pointer.
    lwz 0,0xd0(31)
    cmpwi 0,1
    bne normal_inventory
    lwz 3,0xd4(31)
    cmpwi 3,0
    beq profile_error
    lwz 9,0xf90(3)
    lis 10,0x0085
    ori 10,10,0x9430
    cmpw 9,10
    bne profile_error
    lwz 9,0x17a0(3)
    cmpwi 9,0
    bne done
    lis 12,0x002d
    ori 12,12,0xb780
    mtctr 12
    bctrl
    li 0,1
    stw 0,32(31)
    li 0,0
    stw 0,36(31)
    stw 0,40(31)
    li 0,3
    sync
    stw 0,12(31)
    b done
normal_inventory:
