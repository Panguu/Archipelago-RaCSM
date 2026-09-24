# Script-native OnCollectFluff entry. The argument contains the recipient UID;
# At this entry the current frame's cached Thing is the collecting bubble;
# resolving the recipient argument replaces that cache. Capture before resolution.
# Only exact authored SCORE UIDs are mapped by the client, never score amounts.
# Same committed ring as prize_probe.S; no calls or floating-point changes.
.text
.globl score_pickup
score_pickup:
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
    li 0,2
    stw 0,4(12)
    lis 9,0x0086
    ori 9,9,0xb3c8
    lwz 9,0(9)
    lwz 9,0(9)
    lwz 0,0x128(9)
    stw 0,8(12)
    lwz 0,0x12c(9)
    stw 0,12(12)
    li 0,0
    stw 0,16(12)
    stw 0,20(12)
    lwz 0,0(5)
    stw 0,24(12)
    li 0,0
    stw 0,28(12)
    # Keep argument and VM provenance for validating the hook, not inference.
    li 0,0
    .set offset,0
    .rept 32
    stw 0,offset+32(12)
    .set offset,offset+4
    .endr
    .set offset,0
    .rept 10
    lwz 0,offset(3)
    stw 0,offset+32(12)
    .set offset,offset+4
    .endr
    lwz 0,4(5)
    stw 0,72(12)
    # Snapshot the two calling frames: callback's current UID is the recipient.
    # Frame provenance is needed to recover the originating bubble safely.
    lwz 9,0x1c(3)
    cmplwi 9,2
    bge frames
    b publish
frames:
    addi 9,9,-2
    mulli 9,9,40
    lwz 0,0x18(3)
    add 9,0,9
    .set offset,0
    .rept 20
    lwz 0,offset(9)
    stw 0,offset+76(12)
    .set offset,offset+4
    .endr
    # The last frame's valid cached Thing has not yet been replaced by recipient.
    lbz 0,76(9)
    cmpwi 0,1
    bne publish
    lwz 9,64(9)
    cmpwi 9,0
    beq publish
    stw 9,20(12)
    lwz 0,0xb8(9)
    stw 0,28(12)
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
    stdu 1,-160(1)
