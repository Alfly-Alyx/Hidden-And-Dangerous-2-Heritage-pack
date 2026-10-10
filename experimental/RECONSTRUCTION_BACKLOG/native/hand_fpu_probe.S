/* Caller-owned buffers and host x87 state only; no game code. */
.text
.globl Hd2FpuRoundtrip
Hd2FpuRoundtrip:
    push %ebp
    mov %esp, %ebp
    sub $112, %esp
    push %esi
    push %edi
    fnsave -108(%ebp)
    push $0x27f
    fldcw (%esp)
    add $4, %esp
    fld1
    fldpi
    fldz
    mov 8(%ebp), %esi
    mov 12(%ebp), %edi
    fnsave (%esi)
    fldcw (%esi)
    fldln2
    fld1
    frstor (%esi)
    fnsave (%edi)
    frstor -108(%ebp)
    pop %edi
    pop %esi
    mov %ebp, %esp
    pop %ebp
    ret
