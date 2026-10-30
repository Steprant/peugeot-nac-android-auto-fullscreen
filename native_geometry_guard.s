/* Research candidate for the hash-pinned 44.07.33.32 AA library.
   Runs after the unchanged ScreenManager::getVisibleArea call.
   r5 points at the QRect result. Original frame and canary stay intact. */
ldr r0, [r5]
cmp r0, #320
bne done
ldr r0, [r5, #4]
cmp r0, #0
bne done
ldr r0, [r5, #8]
movw r1, #1599
cmp r0, r1
bne done
ldr r0, [r5, #12]
movw r1, #719
cmp r0, r1
bne done
mov r0, #0
str r0, [r5]
movw r0, #1919
str r0, [r5, #8]
done:
b 0x37da6e14
