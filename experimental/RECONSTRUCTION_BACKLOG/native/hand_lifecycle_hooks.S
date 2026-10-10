/* Original private-emulator entry interceptors for pinned LS3DF 1.12.
 * CALL replaces complete entry instructions, then the saved instructions are
 * replayed and execution resumes at their exact end. No installer is included.
 * The callback and registry use integer instructions only; no x87/SSE state
 * is touched. A rejected notification stops the diagnostic CPU before ANY
 * original entry instruction or native mutation. Not a production hook.
 */
.text
.globl Hd2BeforeNativeModelAdd
Hd2BeforeNativeModelAdd:
    pushfl
    pusha
    cld
    mov 44(%esp), %eax
    mov 48(%esp), %edx
    push $1
    push %edx
    push %eax
    call Hd2BeforeLifecycleEvent
    add $12, %esp
    cmp $2, %eax
    jb hd2_add_ready
    .byte 0x0f, 0x0b
hd2_add_ready:
    popa
    popfl
    lea 4(%esp), %esp
    push %ebx
    mov 12(%esp), %ebx
    push $0x100341c5
    ret

.globl Hd2BeforeNativeModelRemove
Hd2BeforeNativeModelRemove:
    pushfl
    pusha
    cld
    mov 44(%esp), %eax
    mov 48(%esp), %edx
    push $2
    push %edx
    push %eax
    call Hd2BeforeLifecycleEvent
    add $12, %esp
    cmp $2, %eax
    jb hd2_remove_ready
    .byte 0x0f, 0x0b
hd2_remove_ready:
    popa
    popfl
    lea 4(%esp), %esp
    push %ebx
    push %esi
    push %edi
    mov 16(%esp), %edi
    push $0x10034267
    ret

.globl Hd2BeforeNativeObjectRelease
Hd2BeforeNativeObjectRelease:
    pushfl
    pusha
    cld
    mov 44(%esp), %eax
    push $3
    push $0
    push %eax
    call Hd2BeforeLifecycleEvent
    add $12, %esp
    cmp $2, %eax
    jb hd2_release_ready
    .byte 0x0f, 0x0b
hd2_release_ready:
    popa
    popfl
    lea 4(%esp), %esp
    push %esi
    mov 8(%esp), %esi
    push $0x1001c375
    ret
