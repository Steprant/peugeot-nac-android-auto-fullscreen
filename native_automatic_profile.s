/* Native automatic video configuration, after the file override check.
   Preserve the chosen frame, screen type, frame rate and common DPI path.
   r8 remains the requested height until the width margin has been selected. */
ldr r2, [sp, #0x54]
mov r3, #0
ldr sl, [sp, #0x50]
ldr lr, [r4, #8]
ldr r1, [r4, #0xc]
str r2, [r4, #0x20]
str sl, [r4, #0x1c]
str lr, [r4, #0x18]
str r1, [r4, #0x30]
str r3, [r4, #0x24]
str r3, [r4, #0x28]
str r3, [r4, #0x2c]
str r3, [r4, #0x34]
str r3, [r4, #0x38]
str r3, [r4, #0x3c]
str r3, [r4, #0x40]

/* Same even, absolute vertical margin, retaining the original height. */
subs ip, r8, r2
rsbmi ip, ip, #0
add ip, ip, #1
bic ip, ip, #1
str ip, [r4, #0x2c]

/* Only the exact 1920x720 request with a selected 1920x1080 frame
   uses the ordinary computed horizontal margin on 10-inch types. */
cmp r8, #720
ldreq r0, [sp, #0x28]
cmpeq r0, #1920
cmpeq sl, #1920
movw ip, #1080
cmpeq r2, ip
beq computed_margin

/* The getter returns the cached screen enum. Types 4 and 5 keep
   the original special margin block for every other geometry. */
ldr r0, [r4, #0x50]
bl 0x37e273ec
bic r0, r0, #1
cmp r0, #4
beq 0x37ebdbf4

computed_margin:
ldr r0, [sp, #0x28]
subs ip, r0, sl
rsbmi ip, ip, #0
str ip, [r4, #0x28]

/* Fall through to the original resolution and DPI lookup. */
