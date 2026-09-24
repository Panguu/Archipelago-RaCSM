# v1.30 CollectKey, after validation of Thing and key-link pointer.
# Exact authored UID plus source/target SlotIDs; no native behavior changes.
.text
.globl key_pickup
key_pickup:
    stdu 1,-96(1)
    std 0,16(1)
    std 9,24(1)
    std 10,32(1)
    std 11,40(1)
    std 12,48(1)
    mfcr 0
    std 0,56(1)
    lis 11,0x0300
    lwz 0,0(11)
    cmpwi 0,0
    bne initialized
    lis 0,0x4c42
    ori 0,0,0x5032
    stw 0,0(11)
initialized:
    lwz 10,4(11)
    lwz 9,8(11)
    subf 0,9,10
    cmplwi 0,256
    bge overflow
    andi. 12,10,255
    mulli 12,12,160
    add 12,11,12
    addi 12,12,256
    stw 10,0(12)
    li 0,3
    stw 0,4(12)
    lis 9,0x0086
    ori 9,9,0xb3d8
    lwz 9,0(9)
    lwz 9,0(9)
    lwz 0,0x120(9)
    stw 0,8(12)
    lwz 0,0x124(9)
    stw 0,12(12)
    # r4 is the validated key-link object; SlotID starts at +8.
    lwz 0,12(4)
    stw 0,16(12)
    stw 27,20(12)
    li 0,0
    stw 0,24(12)
    lwz 0,0xb8(27)
    stw 0,28(12)
    li 0,0
    .set offset,0
    .rept 32
    stw 0,offset+32(12)
    .set offset,offset+4
    .endr
    lwz 0,8(4)
    stw 0,32(12)
publish:
    sync
    addi 10,10,1
    stw 10,4(11)
    b done
overflow:
    lwz 9,12(11)
    addi 9,9,1
    stw 9,12(11)
done:
    ld 0,56(1)
    mtcr 0
    ld 12,48(1)
    ld 11,40(1)
    ld 10,32(1)
    ld 9,24(1)
    ld 0,16(1)
    addi 1,1,96
    addi 0,4,8
