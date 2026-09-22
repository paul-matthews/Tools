# Actions

Generated from `config.yaml`. Hold **Tab** for the actions layer, then the key. Each key sends ⌃⌥⇧ and itself, which Alfred turns into the script.

| Key | Chord | Does |
| --- | --- | --- |
| `C` | ⌃⌥⇧`C` | Focus Chrome |
| `T` | ⌃⌥⇧`T` | Focus iTerm2 |
| `V` | ⌃⌥⇧`V` | Focus VSCodium |
| `O` | ⌃⌥⇧`O` | Focus Obsidian |
| `A` | ⌃⌥⇧`A` | Focus Calendar |
| `W` | ⌃⌥⇧`W` | Focus Chat |
| `G` | ⌃⌥⇧`G` | Focus Gemini |
| `D` | ⌃⌥⇧`D` | Focus Drive |
| `F` | ⌃⌥⇧`F` | Focus Finder |
| `P` | ⌃⌥⇧`P` | Focus 1Password |
| `1` | ⌃⌥⇧`1` | Meeting — 2 steps |
| `2` | ⌃⌥⇧`2` | Presenting — 1 steps |
| `3` | ⌃⌥⇧`3` | Notes — 2 steps |
| `4` | ⌃⌥⇧`4` | Terminals — 1 steps |

## Binding them in Alfred

Each chord needs one Alfred hotkey, bound once. Powerpack required.

1. Alfred Preferences → **Workflows** → **+** → **Blank Workflow**. Name it something like `moom-keys`.
2. Right-click the canvas → **Inputs** → **Hotkey**. Record the chord.
3. Right-click → **Actions** → **Run Script**. Set **Language** to `/bin/bash` and paste the line for that action from below.
4. Drag from the hotkey's right edge to the script action to connect them.

**Language must be `/bin/bash`, not `/usr/bin/osascript`.** Alfred's Run Script passes the box's *contents* to the interpreter, so osascript would read the path as AppleScript source and fail. Bash runs the file, which keeps this checkout the only copy.

The paths below are this checkout's, as it stands on the machine that last ran `actions-gen.py` — run it yourself and they will be yours.

```sh
osascript "/home/user/Tools/moom-keys/scripts/app-chrome.applescript"       # ⌃⌥⇧C  Chrome
osascript "/home/user/Tools/moom-keys/scripts/app-iterm2.applescript"       # ⌃⌥⇧T  iTerm2
osascript "/home/user/Tools/moom-keys/scripts/app-vscodium.applescript"     # ⌃⌥⇧V  VSCodium
osascript "/home/user/Tools/moom-keys/scripts/app-obsidian.applescript"     # ⌃⌥⇧O  Obsidian
osascript "/home/user/Tools/moom-keys/scripts/app-calendar.applescript"     # ⌃⌥⇧A  Calendar
osascript "/home/user/Tools/moom-keys/scripts/app-chat.applescript"         # ⌃⌥⇧W  Chat
osascript "/home/user/Tools/moom-keys/scripts/app-gemini.applescript"       # ⌃⌥⇧G  Gemini
osascript "/home/user/Tools/moom-keys/scripts/app-drive.applescript"        # ⌃⌥⇧D  Drive
osascript "/home/user/Tools/moom-keys/scripts/app-finder.applescript"       # ⌃⌥⇧F  Finder
osascript "/home/user/Tools/moom-keys/scripts/app-1password.applescript"    # ⌃⌥⇧P  1Password
osascript "/home/user/Tools/moom-keys/scripts/mode-meeting.applescript"     # ⌃⌥⇧1  Meeting
osascript "/home/user/Tools/moom-keys/scripts/mode-presenting.applescript"  # ⌃⌥⇧2  Presenting
osascript "/home/user/Tools/moom-keys/scripts/mode-notes.applescript"       # ⌃⌥⇧3  Notes
osascript "/home/user/Tools/moom-keys/scripts/mode-terminals.applescript"   # ⌃⌥⇧4  Terminals
```

## Modes

### Meeting (`1`)

* `layout` — Meeting
* `focus` — md.obsidian

### Presenting (`2`)

* `layout` — Presenting

### Notes (`3`)

* `place` — com.google.chrome, Left third
* `place` — md.obsidian, Right two-thirds

### Terminals (`4`)

* `layout` — Terminals
