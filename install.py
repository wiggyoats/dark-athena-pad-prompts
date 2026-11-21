#!/usr/bin/env python3
"""install.py GAME_DIR [--uninstall]

Gamepad button prompts for The Chronicles of Riddick: Assault on Dark Athena (PC, GOG release, build GMC-1.161).
Made for the Steam Deck, works with any Xbox-style pad.

What it changes (every original is kept next to it as *.orig; --uninstall puts them back):
  * Content/GameClasses_Win32_x86.dll, Content/GameWorld_Win32_x86.dll  -> see patch_prompts.py
    Menu and in-game prompts draw the game's own Xbox 360 button icons instead of keyboard keys.
  * Content*/Registry/Stringtables/*.txt   tutorial tokens like "§LCONTROLLER_USE_B" become literal text
    ("press Y"), because the PC build fills them with keyboard keys (code that lives in the encrypted exe).
  * Content/Registry/Stringtables/Frontend_Eng.txt   title screen "PRESS ENTER" -> "PRESS A".
Button mapping = the game's default Xbox 360 controller layout.
"""
import glob, hashlib, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import patch_prompts  # noqa: E402

ORIG_MD5 = {
    "Content/GameClasses_Win32_x86.dll": "0e2d0dcd2428a90db136e7e73e06a57e",
    "Content/GameWorld_Win32_x86.dll": "7d40cbe42a42f1b627f90542468f3c1e",
}
# action in CONTROLLER_<ACTION>_<suffix> tokens -> default Xbox 360 button
PAD = dict(USE="Y", JUMP="A", RELOAD="B", CROUCH="X", CROUCHTOGGLE="X", JOURNAL="Back", PRIMARYFIRE="RT",
           SECONDARYFIRE="LT", LEANMODE="LB", WEAPONSELECT="RB", SPRINT2="L3", WEAPONMELEE="R3",
           EYESHINE="D-pad Up", DPAD_UP="D-pad Up", WEAPONFLASHLIGHT="D-pad Down", DPAD_DOWN="D-pad Down",
           DPAD_LEFT="D-pad Left", DPAD_RIGHT="D-pad Right")
TOKEN = re.compile("\xa7LCONTROLLER_([A-Z0-9_]+_(?:A2|B2|C2|C3|D2|A|B|C|D))(?![A-Z0-9_])")


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def backup(p):
    if not os.path.exists(p + ".orig"):
        shutil.copy2(p, p + ".orig")


def load_text(p):
    d = open(p, "rb").read()
    enc = "utf-16" if d[:2] in (b"\xff\xfe", b"\xfe\xff") else "latin1"
    return d.decode(enc), enc


def strings(game):
    changed = 0
    for tdir in sorted(glob.glob(os.path.join(game, "Content*", "Registry", "Stringtables"))):
        prefix = {}
        for p in glob.glob(os.path.join(tdir, "Misc_*.txt")):
            src = p + ".orig" if os.path.exists(p + ".orig") else p
            prefix.update(re.findall(r'\*BUTTON_PREFIX_(\w+)\s+"([^"]*)"', load_text(src)[0]))

        def rep(m):
            act, suf = m.group(1).rsplit("_", 1)
            return (prefix.get(suf, "") + " " + PAD[act]).strip() if act in PAD else m.group(0)

        for p in sorted(glob.glob(os.path.join(tdir, "*.txt"))):
            src = p + ".orig" if os.path.exists(p + ".orig") else p
            t, enc = load_text(src)
            new, n = TOKEN.subn(rep, t)
            if os.path.basename(p) == "Frontend_Eng.txt":
                new, k = re.subn(r'(\*MENU_PRESSSTART_PC\s+)"PRESS ENTER"', r'\1"PRESS A"', new)
                n += k
            if n:
                backup(p)
                open(p, "wb").write(new.encode(enc))
                changed += 1
                print(f"  {os.path.relpath(p, game)}: {n} prompts")
    return changed


def uninstall(game):
    for p in glob.glob(os.path.join(game, "Content*", "**", "*.orig"), recursive=True):
        shutil.copy2(p, p[:-5])
        os.remove(p)
        print("  restored", os.path.relpath(p[:-5], game))


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    game = os.path.abspath(sys.argv[1])
    if "--uninstall" in sys.argv:
        uninstall(game); print("Uninstalled."); return
    for rel, want in ORIG_MD5.items():
        p = os.path.join(game, rel)
        src = p + ".orig" if os.path.exists(p + ".orig") else p
        if md5(src) != want:
            sys.exit(f"{rel} is not the GOG 1.161 version this mod was made for (md5 {md5(src)}). Nothing changed.")
    print("DLLs:")
    for rel, cfg in patch_prompts.DLLS.items():
        p = os.path.join(game, rel)
        backup(p)
        d = bytearray(open(p + ".orig", "rb").read())
        va = patch_prompts.patch(d, cfg)
        open(p, "wb").write(d)
        print(f"  {rel}: patched (.prompts section at {va:#x})")
    print("String tables:")
    strings(game)
    print("Done. Run with --uninstall to restore the original files.")


if __name__ == "__main__":
    main()
