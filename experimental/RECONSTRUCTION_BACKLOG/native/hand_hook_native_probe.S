/* Standalone host-CPU test wrapper. No original game routine is executed. */
.text
.globl Hd2ProbeHandAdapter
Hd2ProbeHandAdapter:
    push %ebp
    mov %esp, %ebp
    sub $112, %esp
    push %esi
    fnsave -108(%ebp)
    fldcw Hd2NativeControl
    fld1
    fldpi
    fldz
    fnsave Hd2NativeBefore
    frstor Hd2NativeBefore
    mov 8(%ebp), %esi
    call Hd2AfterHandPose
    fnsave Hd2NativeAfter
    frstor -108(%ebp)
    pop %esi
    mov %ebp, %esp
    pop %ebp
    ret

.globl Hd2ProbeHandRefresh
Hd2ProbeHandRefresh:
    fnsave Hd2NativeRefreshState
    frstor Hd2NativeRefreshState
    incl Hd2NativeRefreshCount
    mov 4(%esp), %eax
    mov %eax, Hd2NativeRefreshModel
    ret $4
