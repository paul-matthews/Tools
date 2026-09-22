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

Each script needs one Alfred hotkey, once. In a workflow, add a **Hotkey** trigger, record the chord, and connect it to a **Run Script** action set to `/usr/bin/osascript` with the script's path in this checkout. Powerpack required.

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
