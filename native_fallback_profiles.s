/* Preserve the original 32-byte property copy and mode dispatch. */
ldm sl!, {r0, r1, r2, r3}
mov fp, r5
cmp r0, #2
stm fp!, {r0, r1, r2, r3}
mov ip, r0
ldm sl, {r0, r1, r2, r3}
stm fp, {r0, r1, r2, r3}
beq 0x37ebc9e8
cmp ip, #3
bne common

/* Only a 1080p primary profile with 360 vertical pixels gets the
   proportional 720p fallback margin: 360 * 720 / 1080 = 240. */
ldr r3, [sp, #0x14]
mov sb, #1
mov sl, #2
str sb, [sp, #0x20]
str sl, [sp, #0xc]
cmp r3, #360
moveq r3, #240
streq r3, [sp, #0x14]
ldr r0, [r4, #0x50]
bl 0x37e273ec
mov fp, r0
ldr r2, [sp, #0x14]
mov r1, sl
mov r3, fp
mov r0, r4
bl 0x37e26eb8
mov r1, r5
mov r2, #0
str r2, [sp, #0x28]
str r0, [sp, #0x24]
mov r0, r6
bl 0x37e2552c

/* The 480p record remains unresolved and inherits the new margin. */
mov r1, sb
mov r0, r4
str sl, [sp, #0x20]
str sb, [sp, #0xc]
bl 0x37e260d8
ldr sl, [sp, #0x14]
str r0, [sp, #0x1c]
mov r1, sb
mov r2, sl
mov r3, fp
mov r0, r4
bl 0x37e26eb8
mov r1, r5
str r0, [sp, #0x24]
mov r0, r6
bl 0x37e2552c

common:
mov r1, r6
mov r0, r8
bl 0x37e26b40
mov r0, r8
ldr r8, [sp, #0x2c]
ldr r6, [r7]
cmp r8, r6
bne 0x37ebcab0
add sp, sp, #0x34
pop {r4, r5, r6, r7, r8, sb, sl, fp, pc}
nop
