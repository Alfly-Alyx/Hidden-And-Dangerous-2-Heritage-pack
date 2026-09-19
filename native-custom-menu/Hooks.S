/* x86 adapters for the stock client's calling conventions. */
.text

#define jump(address) push $address; ret

.globl GameCount
GameCount:
    push 4(%esp)
    mov 0x8aea10, %ecx
    mov $0x6b9350, %eax
    call *%eax
    ret

.globl GameReload
GameReload:
    mov 4(%esp), %ecx
    mov $0x63ab60, %eax
    call *%eax
    ret

.globl GameFindNode
GameFindNode:
    mov 4(%esp), %eax
    mov 8(%esp), %ecx
    mov (%eax), %edx
    push $1
    push %ecx
    push %eax
    call *0x48(%edx)
    ret

.globl GameSetNodeVisible
GameSetNodeVisible:
    mov 4(%esp), %eax
    mov 8(%esp), %ecx
    test %eax, %eax
    jz 1f
    mov (%eax), %edx
    push %ecx
    push %eax
    call *0x30(%edx)
1:  ret

.globl HookBuild
HookBuild:
    pushfl
    pusha
    mov %esi, %ecx
    push $MenuControlName
    push $0x14
    mov $0x615360, %eax
    call *%eax
    mov %eax, %ebx
    push $20402
    push $0xd
    push $0x1000015
    push $0
    push %ebx
    mov $0x614f10, %eax
    call *%eax
    push $HookCustomCallback
    push %edi
    push $0x4003000
    push $0x1000007
    push $0
    push %ebx
    mov $0x61e100, %eax
    call *%eax
    push $HookCustomCallback
    push %edi
    push $0x4001000
    push $0x1000007
    push $0
    push %ebx
    mov $0x61e100, %eax
    call *%eax
    add $0x44, %esp
    popa
    popfl
    mov %esi, %ecx
    push $0x83ebc0
    jump(0x625c88)

.globl HookCustomCallback
HookCustomCallback:
    mov 8(%esp), %eax
    test %eax, %eax
    jz 1f
    movl $0x0cd00000, 0x60(%eax)
1:  jump(0x63b9a0)

.globl HookPlayerCallback
HookPlayerCallback:
    mov 8(%esp), %eax
    test %eax, %eax
    jz 1f
    movl $0x0cd10000, 0x60(%eax)
1:
    jump(0x63b9a0)

.globl HookMultiCallback
HookMultiCallback:
    mov 8(%esp), %eax
    test %eax, %eax
    jz 1f
    movl $0x0cd20000, 0x60(%eax)
1:
    jump(0x63b9a0)

.globl HookExploreCallback
HookExploreCallback:
    mov 8(%esp), %eax
    test %eax, %eax
    jz 1f
    movl $0x0cd30000, 0x60(%eax)
1:
    jump(0x63b9a0)

.globl HookBackCallback
HookBackCallback:
    mov 8(%esp), %eax
    test %eax, %eax
    jz 1f
    movl $0x0cd40000, 0x60(%eax)
1:
    jump(0x63b9a0)

/* The stock Back control normally posts 0x01000004 to its parent screen.
 * Detail lists need a screen-local event so the mission browser can return
 * to our category selector first. The category selector keeps the native
 * parent event and therefore still returns to Single Player normally. */
.globl HookNativeBackEvent
HookNativeBackEvent:
    push $0
    push $0x02000003
    jump(0x639af6)

.globl HookMissionBuild
HookMissionBuild:
    add $0x24, %esp
    pushfl
    pusha

    mov 4(%esp), %ebx
    mov %ebx, MenuBackControl

    movl $0, MenuCategoryControls
    movl $0, MenuCategoryControls+4
    movl $0, MenuCategoryControls+8
    mov %ebx, MenuCategoryControls+12

    mov 8(%ebp), %ecx
    push $MenuPlayerControlName
    push $0x14
    mov $0x615360, %eax
    call *%eax
    mov %eax, %ebx
    mov %ebx, MenuCategoryControls
    push $20411
    push $0xd
    push $0x1000015
    push $0
    push %ebx
    mov $0x614f10, %eax
    call *%eax
    push $HookPlayerCallback
    push 8(%ebp)
    push $0x4003000
    push $0x1000007
    push $0
    push %ebx
    mov $0x61e100, %eax
    call *%eax
    push $HookPlayerCallback
    push 8(%ebp)
    push $0x4001000
    push $0x1000007
    push $0
    push %ebx
    mov $0x61e100, %eax
    call *%eax
    add $0x44, %esp

    mov 8(%ebp), %ecx
    push $MenuMultiControlName
    push $0x14
    mov $0x615360, %eax
    call *%eax
    mov %eax, %ebx
    mov %ebx, MenuCategoryControls+4
    push $20410
    push $0xd
    push $0x1000015
    push $0
    push %ebx
    mov $0x614f10, %eax
    call *%eax
    push $HookMultiCallback
    push 8(%ebp)
    push $0x4003000
    push $0x1000007
    push $0
    push %ebx
    mov $0x61e100, %eax
    call *%eax
    push $HookMultiCallback
    push 8(%ebp)
    push $0x4001000
    push $0x1000007
    push $0
    push %ebx
    mov $0x61e100, %eax
    call *%eax
    add $0x44, %esp

    mov 8(%ebp), %ecx
    push $MenuExploreControlName
    push $0x14
    mov $0x615360, %eax
    call *%eax
    mov %eax, %ebx
    mov %ebx, MenuCategoryControls+8
    push $20412
    push $0xd
    push $0x1000015
    push $0
    push %ebx
    mov $0x614f10, %eax
    call *%eax
    push $HookExploreCallback
    push 8(%ebp)
    push $0x4003000
    push $0x1000007
    push $0
    push %ebx
    mov $0x61e100, %eax
    call *%eax
    push $HookExploreCallback
    push 8(%ebp)
    push $0x4001000
    push $0x1000007
    push $0
    push %ebx
    mov $0x61e100, %eax
    call *%eax
    add $0x44, %esp

    push 12(%ebp)
    push 8(%ebp)
    call MenuMissionReady
    add $8, %esp
    popa
    popfl
    mov $1, %eax
    jump(0x639b06)

.globl HookStartLabel
HookStartLabel:
    push %eax
    mov 0x14(%esp), %eax
    mov %eax, MenuStartControl
    pop %eax
    cmpl $2, MenuView
    jne 1f
    push $20499
    jump(0x639703)
1:  push $0x935
    jump(0x639703)

.globl HookListCaption
HookListCaption:
    push %eax
    mov 0x28(%esp), %eax
    mov %eax, MenuCaptionControl
    pop %eax
    cmpl $2, MenuView
    jne 1f
    push $20499
    jump(0x639a1c)
1:  push $0x8d2
    jump(0x639a1c)

.globl HookResumeLabel
HookResumeLabel:
    mov %eax, MenuResumeControl
    cmpl $2, MenuView
    jne 1f
    push $20499
    jump(0x639a99)
1:  push $0x839
    jump(0x639a99)

.globl HookAction
HookAction:
    test %edi, %edi
    jz 9f
    cmp MenuCategoryControls+12, %edi
    jne 8f
    mov $0x0cd40000, %eax
    jmp 1f
8:  cmpl $2, MenuView
    jne 9f
    cmp MenuCategoryControls, %edi
    jne 7f
    mov $0x0cd10000, %eax
    jmp 1f
7:  cmp MenuCategoryControls+4, %edi
    jne 6f
    mov $0x0cd20000, %eax
    jmp 1f
6:  cmp MenuCategoryControls+8, %edi
    jne 9f
    mov $0x0cd30000, %eax
    jmp 1f
9:
    cmp $0x0cd00000, %eax
    je 1f
    cmp $0x0cd10000, %eax
    je 1f
    cmp $0x0cd20000, %eax
    je 1f
    cmp $0x0cd30000, %eax
    je 1f
    cmp $0x0cd40000, %eax
    je 1f
    cmp $0x0cc00000, %eax
    jne 0f
    cmpl $3, MenuView
    jb 0f
    mov $0x0cd40000, %eax
    jmp 1f
0:
    cmpl $2, MenuView
    jne 4f
    cmp $0x0cc00000, %eax
    jne 3f
    push %ecx
    push %edx
    call MenuLeave
    pop %edx
    pop %ecx
    jmp 4f
1:  push %ecx
    push %edx
    push %eax
    call MenuActivateAction
    add $4, %esp
    pop %edx
    pop %ecx
    cmp $1, %eax
    je 3f
    cmp $2, %eax
    je 2f
    mov 0x8aea34, %eax
    jump(0x63be31)
2:  mov $0x0cc00000, %eax
4:  cmp $0x0cc00000, %eax
    jump(0x63c095)
3:  jump(0x63c270)

.globl HookEventDispatch
HookEventDispatch:
    mov 4(%ecx), %eax
    mov %eax, %edx
    and $0x03000fff, %edx
    cmp $0x02000003, %edx
    jne 1f
    cmpl $3, MenuView
    jae 3f
    cmpl $2, MenuView
    jne 4f
    pushfl
    pusha
    call MenuLeave
    popa
    popfl
4:  movl $0x01000004, 4(%ecx)
    jump(0x6391ea)
3:
    mov %eax, MenuLastEvent
    mov %edx, MenuLastMaskedEvent
    push $0x0cd40000
    call MenuActivateAction
    add $4, %esp
    push %esi
    call GameReload
    add $4, %esp
    jump(0x6391d4)
1:
    and $0x03000fff, %eax
    jump(0x638e29)

.globl HookListBegin
HookListBegin:
    mov 0x8aea10, %esi
    xor %edi, %edi
    cmpl $2, MenuView
    jb 2f
    mov MenuView, %edi
    cmpl $0, MenuCustomVisibility
    jne 3f
    mov 0x20c(%ebp), %eax
    mov %eax, MenuSavedVisibility
    movl $1, MenuCustomVisibility
3:
    movl $100, 0x20c(%ebp)
    cmpl $2, MenuView
    je 4f
    jmp 1f
2:
    cmpl $0, MenuCustomVisibility
    je 1f
    mov MenuSavedVisibility, %eax
    mov %eax, 0x20c(%ebp)
    movl $0, MenuCustomVisibility
1:  jump(0x63ae08)
4:  jump(0x63af06)

.globl HookListOffset
HookListOffset:
    push 0x10(%esp)
    call MenuOffset
    add $4, %esp
    jump(0x63ae6b)

.globl HookListNext
.globl HookOfficialGroups
HookOfficialGroups:
    cmp $2, %eax
    jbe 1f
    mov $2, %eax
1:  cmp %eax, %ebp
    jge 2f
    jump(0x639d70)
2:  jump(0x63a166)

.globl HookLabelOffset
HookLabelOffset:
    push %ebx
    call MenuOffset
    add $4, %esp
    jump(0x63a3e7)

HookListNext:
    cmpl $2, MenuView
    jae 1f
    inc %eax
    mov %eax, 0x10(%esp)
    cmp $2, %eax
    jae 1f
    jump(0x63aeff)
1:  jump(0x63af06)

.globl HookRowClick
HookRowClick:
    pushfl
    pusha
    push 44(%esp)
    push %ecx
    call MenuRow
    add $8, %esp
    test %eax, %eax
    jnz 1f
    popa
    popfl
    mov %fs:0, %eax
    jump(0x63b316)
1:  popa
    popfl
    mov $1, %al
    ret $16

.globl HookRowDecode
HookRowDecode:
    push %esi
    call MenuDecode
    add $4, %esp
    mov %eax, 0x14(%esp)
    mov %edx, 0x48(%esp)
    jump(0x63b378)

.globl HookSelect
HookSelect:
    cmpl $2, MenuView
    je 2f
    jb 1f
    push MenuView
    call MenuOffset
    add $4, %esp
    mov 0x8aea10, %ecx
    mov MenuView, %edx
1:  mov %edx, 0xe8(%ecx)
    jump(0x6390cf)
2:  jump(0x6391d4)

.globl HookNativeSingle
HookNativeSingle:
    pushfl
    pusha
    call MenuLeave
    popa
    popfl
    mov 0x8aea34, %eax
    jump(0x63be31)

.globl HookNativeCarnage
HookNativeCarnage:
    pushfl
    pusha
    call MenuLeave
    popa
    popfl
    mov 0x8aea34, %eax
    jump(0x63be78)

.globl HookCatalogueReset
HookCatalogueReset:
    pushfl
    cmpl $2, MenuView
    jae 1f
    movl $1, 0xe8(%eax)
1:  popfl
    jump(0x6b691c)

.globl HookTitle
HookTitle:
    pushfl
    cmpl $2, MenuView
    jb 1f
    mov $20402, %ecx
    cmpl $2, MenuView
    je 1f
    mov MenuView, %ecx
    add $20407, %ecx
1:  popfl
    mov %ebx, 0x30(%esp)
    movl $0x14100000, 0x1c(%esp)
    jump(0x63abf8)

/* The stock screen rebuild turns scene nodes back on after the menu action.
 * Reapply the current view once that rebuild is completely finished. */
.globl HookRefreshDone
HookRefreshDone:
    pushfl
    pusha
    push MenuView
    call MenuApplyLayout
    add $4, %esp
    popa
    popfl
    mov 0x34(%esp), %ecx
    pop %edi
    jump(0x63af0b)
