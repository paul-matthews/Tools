# moom-keys

A keyboard-driven window-region strategy for [Moom](https://manytricks.com/moom/)
on a very wide display, plus the tooling to keep Moom's preferences and a
QMK/VIA keyboard (Keychron K3 Max) generated from one region table.

The goal: every region I use has a name, a fixed place on the screen, a key
whose *physical position mirrors that place*, and a single source of truth that
emits both the Moom actions and the keyboard layer.

## Current state, decoded

`moom-inspect.py` reads an exported Moom plist and prints what is actually
configured. From my export (September 2026):

| Key | Region | Columns (of 12) | Rows (of 10) |
| --- | --- | --- | --- |
| `1` | Centre half | 3–9 | full |
| `2` | Left third | 0–4 | full |
| `3` | Right third | 8–12 | full |
| `4` | Left two-thirds | 0–8 | full |
| `5` | Right two-thirds | 4–12 | full |
| `6` | Right third (duplicate of `3`) | 8–12 | full |
| `7` | Left third (duplicate of `2`) | 0–4 | full |
| `X` | VC window — centre half, top 60% | 3–9 | 0–6 |
| `Z` | Lower centre — centre half, bottom half | 3–9 | 5–10 |
| `A` | Left third, lower two-thirds | 0–4 | 3.33–10 |
| `B` | Right third, lower two-thirds | 8–12 | 3.33–10 |
| `C` | Left third, upper two-thirds | 0–4 | 0–6.67 |
| `D` | Right third, upper two-thirds | 8–12 | 0–6.67 |

Settings that matter: configuration grid **12 × 10**, grid spacing on with a
1px gap, snapping on, dismiss-after-move on, and the keyboard controller on
**⌥`** — the only global shortcut in the whole config.

Four things fall out of that:

* **`6` and `7` are dead weight** — byte-identical to `3` and `2`. They were
  authored later against a 12 × 6 grid and land on the same frame.
* **The vertical thirds are off-grid.** `A`–`D` use 1/3 and 2/3 of the height,
  authored on a 6-row grid. On a 10-row configuration grid those are rows 3.33
  and 6.67, so the mouse grid can never reproduce them and the visual editor
  rounds them if they are ever touched.
* **Nothing is named.** Moom's AppleScript entry point addresses actions by
  title (`tell application "Moom" to run "VC Top"`), so untitled actions cannot
  be scripted at all.
* **`X` and `Z` overlap by 10% of the height** (rows 5–6), which is the
  deliberate webcam/stage arrangement: video window high near the camera,
  working window below it.

## How Moom can be driven

Three transports, which differ mainly in what they cost the global shortcut
namespace and how they fail.

**Controller-restricted single keys** (what my config uses today). A hotkey
whose modifier flags carry no real modifier only fires while the keyboard
controller overlay is up. Zero global footprint; costs two keystrokes (⌥`
then the key) and the overlay's cheat sheet doubles as documentation. A
keyboard macro can collapse the two into one physical key — at the price of a
timing delay between the strokes, and a stray character typed into whatever
has focus if the overlay is slow to appear.

**Global chords.** Any hotkey with a real modifier is global. `Hyper`
(⌃⌥⇧⌘) is the safe corner of the namespace: effectively nothing ships
bindings there, and QMK emits it natively as `HYPR(KC_x)` with no macro, no
delay and no leaked keystroke. One entry per region in the global namespace is
the cost; the benefit is a single keystroke that is repeatable, holdable and
immune to overlay timing.

**AppleScript.** `tell application "Moom" to run "<action title>"` runs a named
custom action; Moom also scripts saved layouts and centring. It needs
AppleScript support enabled in Moom's settings, needs the action titled, and
still needs *something* to bind a key to the script (Shortcuts, Raycast, a
launcher). Too slow and too indirect for per-window nudges; the right tool for
composite "workspace" layouts that place several windows at once.

The strategy here is to use all three for what each is good at: global Hyper
chords for direct jumps, the same regions also bound to controller-restricted
single keys so ⌥` remains a discoverable fallback, and AppleScript reserved
for multi-window layouts.

## Plist notes (for the generator)

Moom 4 keeps its actions in `Custom Controls (4001)` in
`com.manytricks.Moom`; a legacy Moom 3 `Custom Controls` array may also be
present and is ignored by Moom 4. Export and import round-trip through
`defaults`:

```sh
defaults export com.manytricks.Moom ~/Desktop/Moom.plist
# ...edit...
osascript -e 'quit app "Moom"'
defaults import com.manytricks.Moom ~/Desktop/Moom.plist
open -a Moom
```

Each entry in the array is a dictionary:

* `Identifier` — a UUID string, also repeated inside the `Hot Key` dictionary.
* `Action` — `19` move & zoom, `1001` saved layout (carries a `Snapshot` array
  of per-window frames), `-101` section header (uses `Title`), `0` separator.
* `Relative Frame` — `{{x, y}, {w, h}}` as fractions of the screen, **origin
  top-left**: `{{0.25, 0}, {0.5, 0.6}}` is the top-centre half-width region.
* `Configuration Grid` — optional per-action override recording the grid the
  action was *authored* on. It is editor metadata; the relative frame is the
  truth, so generated frames need not respect the global grid.
* `Hot Key` — `Key Code` is a macOS virtual key code, `Modifier Flags` is an
  NSEvent mask with a constant `0x100` bit set. No bit above `0x10000` means a
  controller-restricted single key; `Option` is `0x80000`, `Command` `0x100000`,
  `Control` `0x40000`, `Shift` `0x20000`, so Hyper is `0x1E0100`.
* `Title` — optional, and required for AppleScript addressing.

## Files

* `moom-inspect.py` — decode an exported plist: grid, hotkeys, every action as
  grid cells and an ASCII map, flagging duplicates and off-grid frames.

## Still to build

A `regions` table as the single source of truth, generating: the
`Custom Controls (4001)` array (both hotkey kinds per region), a Keychron
Launcher keymap patch for the window layer, and a printable cheat sheet laid
out like the keys themselves.
