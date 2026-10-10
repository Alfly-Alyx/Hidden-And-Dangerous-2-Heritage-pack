/* Original diagnostic interception of native SetParent. Integer-only guard.
 * Six complete entry bytes are replaced in the private emulator image only.
 */
.text
.globl Hd2BeforeNativeParentChange
Hd2BeforeNativeParentChange:
    pushfl
    pusha
    cld
    mov 44(%esp), %eax
    mov 48(%esp), %edx
    push %edx
    push %eax
    call Hd2BeforeParentEvent
    add $8, %esp
    cmp $2, %eax
    jb hd2_parent_ready
    .byte 0x0f, 0x0b
hd2_parent_ready:
    popa
    popfl
    lea 4(%esp), %esp
    /* Checkpoint for full pre-prologue CPU state in the diagnostic oracle. */
.globl Hd2ParentReplay
Hd2ParentReplay:
    push %ebp
    mov %esp, %ebp
    and $-16, %esp
    push $0x1001d686
    ret
