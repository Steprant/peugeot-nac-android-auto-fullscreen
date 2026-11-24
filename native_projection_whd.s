/* Inside CGraphic::onSetVideoParams, after the default format's verbose log
   prefix. Its two sequences of four coordinate writes share one loop here.
   Entry at whd is reached only from the format switch after its 480p/720p
   tests. r9/r8 still hold the ORIGINAL total horizontal/vertical margins. */
b log_rectangles
whd:
    cmp r10, #3
    cmpeq r9, #0
    cmpeq r8, #360
    bne 0x77040
    mov r0, #0
    mov r1, #180
    mov r2, #1920
    mov r3, #900
    add r12, sp, #0x39c
    stmia r12!, {r0-r3}
    stmia r12, {r0-r3}
    b 0x76ff0

log_rectangles:
    add r6, sp, #0x39c
    mov r7, #8
next_coordinate:
    ldr r1, [r6], #4
    mov r0, r10
    bl 0x1c464
    subs r7, r7, #1
    beq finish_log
    cmp r7, #4
    bne next_coordinate
    ldr r1, target_offset
target_pc:
    add r1, pc, r1
    mov r0, r10
    bl 0x1cac4
    b next_coordinate
finish_log:
    mov r0, r10
    bl 0x1c47c
    b 0x76ff0
target_offset:
    /* target ltrb, relative to the PC seen by the ADD at target_pc. */
    .word 0x909d8 - 0x7719c
