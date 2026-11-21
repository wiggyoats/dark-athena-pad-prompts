# Dark Athena gamepad prompts (v1.0)

Makes the PC version of *The Chronicles of Riddick: Assault on Dark Athena* show controller buttons instead of
keyboard keys. Made for the Steam Deck; works with any Xbox-style pad. The Butcher Bay remake included with
Dark Athena gets the same prompts.

The PC build has no gamepad prompts at all: menus say "Esc BACK", hints say "press E", the title says
"PRESS ENTER", even when you play with a controller. With this mod:

- menus and in-game prompts use the game's own Xbox 360 button icons (A, B, X, Y, LB, RB, LT, RT, Back, Start,
  sticks, d-pad), for example the red B next to BACK;
- tutorial text names the pad button ("Walk up to a character and press Y to initiate Dialog-mode");
- the title screen says PRESS A.

Buttons follow the game's default controller layout: Use Y, Jump A, Reload B, Crouch X, Journal Back,
Pause Start, Shoot RT, Block LT, Lean LB, Cycle weapon RB, Sprint L3, Melee R3, Eyeshine d-pad up,
Flashlight d-pad down.

## Requirements

- The **GOG** release (build GMC-1.161). The installer checks this and changes nothing on any other version.
- Python 3 (included in SteamOS and most Linux systems; on Windows install it from python.org).

## Install

```
python3 install.py "/path/to/The Chronicles of Riddick - Assault on Dark Athena"
```

On the Steam Deck the game folder is wherever you installed it, for example `~/Games/DarkAthena`.

## Uninstall

```
python3 install.py "/path/to/game" --uninstall
```

Every file the mod changes is backed up next to the original as `*.orig`; uninstall puts them back.

## What it changes

| File | Change |
|---|---|
| `Content/GameClasses_Win32_x86.dll`, `Content/GameWorld_Win32_x86.dll` | A few bytes in the prompt code plus a small added code section (`.prompts`). Source: `cave/prompts.s`, patcher: `patch_prompts.py`. |
| `Content*/Registry/Stringtables/*.txt` | Tutorial tokens such as `§LCONTROLLER_USE_B` become literal text ("press Y"), in all five languages. |
| `Content/Registry/Stringtables/Frontend_Eng.txt` | "PRESS ENTER" becomes "PRESS A". |

No game files are included; the mod only modifies your own copy.

## How it works (for the curious)

- The menu code fills the prompt labels with "Esc"/"Enter" on PC; the patch points them at "B"/"A"/"X"/"Y".
- `CRC_Util2D`'s prompt drawer draws a keyboard keycap for text labels and a single icon for mouse
  buttons. A small hook sends labels that name a pad button down the icon path with the matching
  `GUI_Button_*` texture, which ships unused in the PC build's `GUI.xtc`.
- In-game action prompts get their key name from `CScanKey::GetLocalizedKeyName`; at those call sites a
  replacement maps the default PC key to the default pad button (E to Y, Space to A, and so on).
- The tutorial text is expanded by code inside the encrypted `DarkAthena.exe`, so those strings are changed
  in the string tables instead.

## Known limits

- The prompts assume the default controller layout. If you remap the pad in the game's options, they don't follow.
- The in-game "HELP" hint still shows the F1 key: the pad's Back button opens the Journal, and no pad
  button for Help was found, so it is left as is rather than show a wrong button.
- Keyboard players should not install this: prompts will show pad buttons.

## License

MIT (the mod code only; the game and its files belong to their owners).
