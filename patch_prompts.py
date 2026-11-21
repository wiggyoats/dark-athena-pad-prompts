#!/usr/bin/env python3
"""patch_prompts.py GAME_DIR [--undo]   (DLL part only; normally run install.py instead)

Gamepad button prompts for The Chronicles of Riddick: Assault on Dark Athena (PC, GOG build GMC-1.161).
The PC build only knows keyboard prompts. This patches GameClasses_Win32_x86.dll and GameWorld_Win32_x86.dll:
  1. Menu prompt labels "Esc"/"Enter" become "B"/"A" (X/Y too), by repointing four string addresses per DLL.
  2. A new code section (.prompts) holds two small routines (cave/prompts.s):
     - keyname: maps the default PC key of an in-game hint to its default Xbox 360 button (E->Y, Space->A ...),
       used at the CScanKey::GetLocalizedKeyName call sites of the hint code;
     - icon_hook: in CRC_Util2D's prompt drawer, a keycap whose label is a pad button ("A", "LB", "Back" ...)
       is drawn with the game's own Xbox 360 button texture (GUI_Button_A ...) instead of a keyboard key.
Backs up each DLL to *.orig first; --undo restores them. Refuses to touch any other game version.
"""
import os, shutil, struct, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
B = 0x10000000  # preferred image base of both DLLs; file offset = VA - B for .text/.rdata

DLLS = {
    "Content/GameClasses_Win32_x86.dll": dict(
        labels={0x453f68: (0x1076be38, 0x1076759f),   # B label: "Esc"   -> "B"
                0x453f80: (0x1076be30, 0x107675af),   # A label: "Enter" -> "A"
                0x453f96: (0x1076be38, 0x1076758f),   # X label: "Esc"   -> "X"
                0x453f9d: (0x1076be38, 0x1076757f)},  # Y label: "Esc"   -> "Y"
        keyname=0x106e678e, cstr_ctor=0x100162e0,
        calls=[0x103f727f, 0x103f7978, 0x103f89b8],
        mouse=[0x103f7943, 0x103f7952, 0x103f7960, 0x103f8983, 0x103f8992, 0x103f89a0],
        hook=0x103f7c89, icon_draw=0x103f864e, other=0x103f8189,
        bin="cave/prompts_gc.bin"),
    "Content/GameWorld_Win32_x86.dll": dict(
        labels={0x25f3b8: (0x10406d14, 0x104050a7),
                0x25f3d0: (0x10406d0c, 0x104050b7),
                0x25f3e6: (0x10406d14, 0x10405097),
                0x25f3ed: (0x10406d14, 0x10405087)},
        keyname=0x10320fd0, cstr_ctor=0x100162e0,
        calls=[0x100d014b, 0x100d029d, 0x100d03d1, 0x100e337a, 0x10139d9c, 0x10139e93, 0x10139f94,
               0x10154e25, 0x1024972f, 0x10249e28, 0x1024ae68],
        mouse=[0x10249df3, 0x10249e02, 0x10249e10, 0x1024ae33, 0x1024ae42, 0x1024ae50],
        hook=0x1024a139, icon_draw=0x1024aafe, other=0x1024a639,
        bin="cave/prompts_gw.bin"),
}
HOOK_ORIG = bytes.fromhex("740e83f801740983f8020f85")  # je; cmp eax,1; je; cmp eax,2; jne rel32 (opcode part)
SEC_SIZE = 0x1000
align = lambda x, a: (x + a - 1) // a * a


def pe_info(d):
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    nsec = struct.unpack_from("<H", d, pe + 6)[0]
    opt = pe + 24
    optsz = struct.unpack_from("<H", d, pe + 20)[0]
    salign, falign = struct.unpack_from("<II", d, opt + 32)
    return pe, nsec, opt, opt + optsz, salign, falign


def new_section_place(d):
    pe, nsec, opt, st, salign, falign = pe_info(d)
    vs, va, rs, ra = struct.unpack_from("<IIII", d, st + (nsec - 1) * 40 + 8)
    return B + align(va + vs, salign), align(len(d), falign)


def add_section(d, va, raw, code):
    pe, nsec, opt, st, salign, falign = pe_info(d)
    hdr = st + nsec * 40
    soh = struct.unpack_from("<I", d, opt + 60)[0]
    assert hdr + 40 <= soh and d[hdr:hdr + 40] == bytes(40), "no room for another section header"
    struct.pack_into("<8sIIIIIIHHI", d, hdr, b".prompts", SEC_SIZE, va - B, SEC_SIZE, raw, 0, 0, 0, 0, 0x60000020)
    struct.pack_into("<H", d, pe + 6, nsec + 1)
    struct.pack_into("<I", d, opt + 56, va - B + SEC_SIZE)          # SizeOfImage
    d.extend(bytes(raw - len(d)))
    d.extend(code + bytes(SEC_SIZE - len(code)))


def build(cfg, va):
    """Assemble cave/prompts.s for this DLL (GNU as/ld). Prebuilt cave/*.bin are used when present (e.g. on the Deck)."""
    out = os.path.join(HERE, cfg["bin"])
    if os.path.exists(out) and not os.environ.get("REBUILD"):
        return open(out, "rb").read()
    o = out[:-4]
    syms = dict(CSTR_CTOR=cfg["cstr_ctor"], KEYNAME_ORIG=cfg["keyname"], ICON_DRAW=cfg["icon_draw"],
                KEYCAP=(cfg["hook"] or 0x10000000) + 16, OTHER=cfg["other"])
    args = ["as", "--32", "-o", o + ".o", os.path.join(HERE, "cave", "prompts.s")]
    for k, v in syms.items():
        args += ["--defsym", f"{k}={v:#x}"]
    subprocess.check_call(args)
    subprocess.check_call(["ld", "-m", "elf_i386", f"-Ttext={va:#x}", "-e", "_start", "-o", o + ".elf", o + ".o"])
    subprocess.check_call(["objcopy", "-O", "binary", "-j", ".text", o + ".elf", out])
    return open(out, "rb").read()


def patch(d, cfg):
    va, raw = new_section_place(d)
    code = build(cfg, va)
    assert len(code) <= SEC_SIZE
    keyname_va, hook_va = va, va + 0x100
    for o, (old, new) in cfg["labels"].items():
        assert struct.unpack_from("<I", d, o)[0] == old, f"{o:#x}: unexpected bytes (different game version?)"
        assert d[new - B:new - B + 2] in (b"A\0", b"B\0", b"X\0", b"Y\0")
        struct.pack_into("<I", d, o, new)
    for c in cfg["calls"]:
        o = c - B
        assert d[o] == 0xE8 and c + 5 + struct.unpack_from("<i", d, o + 1)[0] == cfg["keyname"], hex(c)
        struct.pack_into("<i", d, o + 1, keyname_va - (c + 5))
    for c in cfg["mouse"]:
        o = c - B
        assert d[o] == 0x3D and struct.unpack_from("<I", d, o + 1)[0] in (0xF0, 0xF1, 0xF2), hex(c)
        struct.pack_into("<I", d, o + 1, 0x7FFF0000)                # never matches: mouse buttons use the table
    if not cfg["hook"]:
        add_section(d, va, raw, code)
        return va
    o = cfg["hook"] - B
    assert d[o:o + 12] == HOOK_ORIG and cfg["hook"] + 16 + struct.unpack_from("<i", d, o + 12)[0] == cfg["other"]
    d[o:o + 16] = b"\xE9" + struct.pack("<i", hook_va - (cfg["hook"] + 5)) + b"\x90" * 11
    add_section(d, va, raw, code)
    return va


def main():
    game, undo = sys.argv[1], "--undo" in sys.argv
    for rel, cfg in DLLS.items():
        p = os.path.join(game, rel)
        if undo:
            shutil.copy2(p + ".orig", p); print("restored", rel); continue
        if not os.path.exists(p + ".orig"):
            shutil.copy2(p, p + ".orig")
        d = bytearray(open(p + ".orig", "rb").read())
        va = patch(d, cfg)
        open(p, "wb").write(d)
        print(f"patched {rel} (.prompts at {va:#x})")


if __name__ == "__main__":
    main()
