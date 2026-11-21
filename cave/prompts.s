# Dark Athena (GOG GMC-1.161) gamepad prompts. Assembled into a new PE section (.prompts) of each patched DLL.
# Entry 0x000: keyname  - replacement for CScanKey::GetLocalizedKeyName(CStr* ret, int scancode) at hint call sites.
# Entry 0x100: icon_hook - jumped to from CRC_Util2D's prompt drawer where it picks keycap (types 0-2) vs icon (3-5).
# Position independent (DLLs are relocated); external addresses are rel32 jumps/calls (no relocations needed).
        .intel_syntax noprefix
        .code32
        .text
        .globl _start
_start:
keyname:
        push esi
        push edi
        mov eax, [esp+0x10]          # scancode
        call k_next
k_next: pop esi
        lea edi, [esi + keytable - k_next]
k_scan: mov edx, [edi]
        cmp edx, -1
        je k_orig
        cmp edx, eax
        je k_found
        add edi, 8
        jmp k_scan
k_found:
        mov edx, [edi+4]
        add edx, esi                 # char* label (relative to k_next)
        mov ecx, [esp+0xc]           # ret CStr*
        push edx
        call CSTR_CTOR               # CStr::CStr(const char*), callee pops 4
        mov eax, [esp+0xc]
        pop edi
        pop esi
        ret
k_orig: pop edi
        pop esi
        jmp KEYNAME_ORIG

        .org 0x100
icon_hook:                           # eax = prompt type, label CStr* = 5th argument at [esp+0xec], one value on the FPU stack
        test eax, eax
        jnz i_not0
        mov edx, [esp+0xec]             # 5th argument of the drawer (its return address is at esp+0xd8)
        test edx, edx
        jz i_keycap
        mov edx, [edx+4]
        test edx, edx
        jz i_keycap
        add edx, 2                   # label text (CStr data has a 2-byte header)
        push esi
        push edi
        push ebx
        call i_next
i_next: pop ebx
        lea esi, [ebx + icontable - i_next]
i_loop: mov edi, [esi]
        cmp edi, -1
        je i_nomatch
        add edi, ebx
        push edx
i_cmp:  mov al, [edx]
        cmp al, [edi]
        jne i_ne
        test al, al
        je i_eq
        inc edx
        inc edi
        jmp i_cmp
i_ne:   pop edx
        add esi, 8
        jmp i_loop
i_eq:   pop edx
        mov eax, [esi+4]
        add eax, ebx                 # texture name
        pop ebx
        pop edi
        pop esi
        fstp st(0)                   # same as the type 3-5 branch
        push eax
        jmp ICON_DRAW                # draws the pushed texture as an icon
i_nomatch:
        pop ebx
        pop edi
        pop esi
        xor eax, eax
i_keycap:
        jmp KEYCAP
i_not0: cmp eax, 1
        je KEYCAP
        cmp eax, 2
        je KEYCAP
        jmp OTHER

        .align 4
keytable:                            # default PC key -> default Xbox 360 pad button (offsets from k_next)
        .long 0x12, s_Y - k_next     # E      Use
        .long 0x39, s_A - k_next     # Space  Jump
        .long 0x13, s_B - k_next     # R      Reload
        .long 0x2e, s_X - k_next     # C      Crouch / stealth
        .long 0x24, s_Back - k_next  # J      Journal
        .long 0x01, s_Start - k_next # Esc    Pause
        .long 0x2f, s_LB - k_next    # V      Lean
        .long 0x2c, s_RB - k_next    # Z      Cycle weapon
        .long 0x1d, s_L3 - k_next    # Ctrl   Sprint
        .long 0x21, s_R3 - k_next    # F      Melee
        .long 0x10, s_DUp - k_next   # Q      Eyeshine
        .long 0x22, s_DDown - k_next # G      Flashlight
        .long 0xf0, s_RT - k_next    # Mouse1 Shoot / punch
        .long 0xf1, s_LT - k_next    # Mouse2 Block
        .long -1, 0
icontable:                           # prompt label -> texture in GUI.xtc (offsets from i_next)
        .long s_A - i_next,     t_A - i_next
        .long s_B - i_next,     t_B - i_next
        .long s_X - i_next,     t_X - i_next
        .long s_Y - i_next,     t_Y - i_next
        .long s_LB - i_next,    t_LB - i_next
        .long s_RB - i_next,    t_RB - i_next
        .long s_LT - i_next,    t_LT - i_next
        .long s_RT - i_next,    t_RT - i_next
        .long s_Back - i_next,  t_Back - i_next
        .long s_Start - i_next, t_Start - i_next
        .long s_L3 - i_next,    t_LC - i_next
        .long s_R3 - i_next,    t_RC - i_next
        .long s_DUp - i_next,   t_DUp - i_next
        .long s_DDown - i_next, t_DDown - i_next
        .long s_Left - i_next,  t_DLeft - i_next
        .long s_Right - i_next, t_DRight - i_next
        .long -1, 0
s_Y:     .asciz "Y"
s_A:     .asciz "A"
s_B:     .asciz "B"
s_X:     .asciz "X"
s_Back:  .asciz "Back"
s_Start: .asciz "Start"
s_LB:    .asciz "LB"
s_RB:    .asciz "RB"
s_L3:    .asciz "L3"
s_R3:    .asciz "R3"
s_DUp:   .asciz "D-pad Up"
s_DDown: .asciz "D-pad Down"
s_RT:    .asciz "RT"
s_LT:    .asciz "LT"
s_Left:  .asciz "Left"
s_Right: .asciz "Right"
t_A:     .asciz "GUI_Button_A"
t_B:     .asciz "GUI_Button_B"
t_X:     .asciz "GUI_Button_X"
t_Y:     .asciz "GUI_Button_Y"
t_LB:    .asciz "GUI_Button_LB"
t_RB:    .asciz "GUI_Button_RB"
t_LT:    .asciz "GUI_Button_LT"
t_RT:    .asciz "GUI_Button_RT"
t_Back:  .asciz "GUI_Button_Back"
t_Start: .asciz "GUI_Button_Start"
t_LC:    .asciz "GUI_Button_LC"
t_RC:    .asciz "GUI_Button_RC"
t_DUp:   .asciz "GUI_Button_DUp"
t_DDown: .asciz "GUI_Button_DDown"
t_DLeft: .asciz "GUI_Button_DLeft"
t_DRight: .asciz "GUI_Button_DRight"
