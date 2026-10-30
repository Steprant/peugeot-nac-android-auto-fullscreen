/* Preserve the factory allowed result r4 in all SD/HD and non-AA cases.
   Hide WHD sidebars only when the native zone monitor says AA owns focus.
   Unknown, absent or unfocused contexts retain the factory result.
   r5 is CStatusLineManager; its original prologue/epilogue remain intact.
   Enum 0 is taken from the AA registration at ELF 0x37da13ac, not from
   the human-readable label of a zone. */
ldrb r0, [r5, #0x60]
cmp r0, #0
beq done
ldr r7, [r5, #0x20]
cmp r7, #0
beq done
mov r0, r7
mov r1, #0
bl 0x378f8b74
mov r6, r0
mov r0, r7
bl 0x378fa41c
cmp r6, r0
bhs done
mov r0, r7
mov r1, r6
bl 0x378fa4e8
cmp r0, #0
beq done
add r0, sp, #8
mov r1, r7
mov r2, r6
bl 0x378f9c78
ldr r0, [sp, #8]
ldr r1, [r0, #4]
cmp r1, #13
cmpne r1, #17
cmpne r1, #22
bne destroy
ldr r2, [r0, #12]
add r2, r0, r2
adr r3, aa_name
again:
ldrh r0, [r2], #2
ldrb ip, [r3], #1
cmp r0, ip
bne destroy
subs r1, r1, #1
bne again
mov r4, #0
destroy:
add r0, sp, #8
bl 0x378f972c
done:
b 0x378fdfac
aa_name:
.ascii "INTERNET_0033SkinLogic"
.byte 0
