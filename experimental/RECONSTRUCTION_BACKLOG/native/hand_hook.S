/* Original adapter for the six reviewed bytes at LS3DF 1.12 0x10034bc3.
 * This source does NOT patch that address or install a DLL in the game.
 * Called via a diagnostic rel32 CALL replacing mov ecx,[esi]; push esi;
 * call [ecx+0x24]. It restores integer/flags/x87 state before replaying those
 * instructions. SSE is neither used nor modified by this compiled component.
 */
.text
.globl Hd2AfterHandPose
Hd2AfterHandPose:
    pushfl
    pusha
    sub $108, %esp
    fnsave (%esp)
    fldcw (%esp)
    cld
    movzwl (%esp), %eax
    push %eax
    push %esi
    call Hd2OnModelHandPose
    add $8, %esp
    frstor (%esp)
    add $108, %esp
    popa
    popfl
    mov (%esi), %ecx
    push %esi
    call *0x24(%ecx)
    ret
