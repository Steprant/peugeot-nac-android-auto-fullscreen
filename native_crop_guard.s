/* Keep all factory cases unless the complete laboratory geometry matches.
   Fix the factory two-pixel offset only for the 1920x1080 / 1920x720 case.
   sb points at AAutoHMIUIFwkAdaptor. Original frame/canary are preserved. */
ldr r0, [sb, #0x24]
cmp r0, #0
bne done
ldr r0, [sb, #0x28]
cmp r0, #0
bne done
ldr r0, [sb, #0x2c]
cmp r0, #1920
bne done
ldr r0, [sb, #0x30]
cmp r0, #720
bne done
ldr r0, [sb, #0x34]
cmp r0, #0
bne done
ldr r0, [sb, #0x3c]
cmp r0, #1920
bne done
ldr r0, [sb, #0x40]
movw r1, #1080
cmp r0, r1
bne done
ldr r0, [sp, #0x3c]
cmp r0, #360
bne done
mov r0, #180
rsb r0, r0, #0
str r0, [sb, #0x38]
done:
b 0x37d8f240
