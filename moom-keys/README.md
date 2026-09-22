# moom-keys

A keyboard-driven window-region strategy for [Moom](https://manytricks.com/moom/)
on a very wide display, generated from one table.

Every region has a name, a fixed place on the screen, and a key whose physical
position mirrors that place. One file — `regions.py` — is the source of truth,
and both Moom and a QMK/VIA keyboard (Keychron K3 Max) are generated from it,
so they cannot drift apart.

## How the parts fit together

Two generated artefacts, each imported into a different place. Neither
generator talks to the other; they agree because they read the same table.

```
                ┌─ moom-gen.py ──────▶ a plist you import into Moom:
                │                      the regions, and which chord fires each
  regions.py ───┤
                └─ launcher-patch.py ▶ a keymap you import into the keyboard:
                                       which key sends which chord
```

At press time none of that is involved — the keyboard and Moom meet at the
chord and nowhere else:

```
  hold Caps, press D  ──▶  keyboard sends ⌃⌥⇧⌘D  ──▶  Moom moves the window
                                                       to the centre half
```

Which means the two halves are independent. Import only the plist and every
region still works through Moom's own **⌥`** overlay, pressing the same letter
without the chord. Import only the keymap and the chords fire into nothing.
Both together is the point, but either half alone is harmless — and when
something misbehaves, that is how you tell which half to look at.

A third route exists for later: every region is titled, so
`tell application "Moom" to run "Camera stage"` works once Moom's AppleScript
support is switched on. That is the hook for composite multi-window layouts.

## Quick start

Everything runs from this directory, and nothing has dependencies beyond the
standard library — the Python 3 that ships with macOS is enough.

**1. Moom.** Quit it first: it holds its preferences in memory and writes them
back on quit, which would clobber the import.

```sh
osascript -e 'quit app "Moom"'
defaults export com.manytricks.Moom ~/Desktop/Moom-backup.plist   # keep: rollback
./moom-gen.py ~/Desktop/Moom-backup.plist -o ~/Desktop/Moom-new.plist -c CHEATSHEET.md
defaults import com.manytricks.Moom ~/Desktop/Moom-new.plist
open -a Moom
```

Check it worked: **⌥`** then **D** should move the window to the centre half.

**2. The keyboard.** Plug it in — Launcher only talks over USB, from a
Chromium-based browser — and put the Mac/Win switch on **Mac**. Open
<https://launcher.keychron.com>, authorize the device, and **Export** the
current keymap; keep that file, it is the rollback.

```sh
./launcher-patch.py ~/Downloads/Keymap-K3_Max_RGB.json --layer 3 -o ~/Downloads/Keymap-windows.json
```

Import the result in Launcher. Check it worked: hold **Caps**, press **D** —
same jump as before. The keymap lives in the keyboard, so it keeps working
over Bluetooth and 2.4GHz afterwards.

That is the whole install. [`INSTALL.md`](INSTALL.md) has the same thing at
walking pace, plus a verification ladder whose failures each point at what to
fix, and rollback for each half.

## What you get

21 regions, each reachable with one keystroke from either hand. Hold **Caps**
(tapped, it is still Escape) or **left Option**, then:

```
  left hand                        right hand

  1  2  3  4  5                    6  7  8  9  0     width variants
  Q  W  E  R  T                    Y  U  I  O  P     top-anchored
  A  S  D  F  G                    H  J  K  L  ;     full height
  Z  X  C  V  B                    N  M  ,  .  /     bottom-anchored
  Tab  full screen                 '                 full screen

     ⅓L ½L ½C ½R ⅓R                   ⅓L ½L ½C ½R ⅓R
```

Row picks the vertical anchor, column picks the horizontal position. `D`/`K`
is the centred half, `E`/`I` the camera stage above it, `C`/`,` the working
window below it. `CHEATSHEET.md` is generated alongside the plist and has
every region with its grid cells and pixel size.

## Changing the layout

Edit `regions.py` — it is the only file meant to be edited by hand — then
regenerate **both** halves and import both. The chord a region uses can
change when the table changes, so a new plist with an old keymap will not
line up.

```sh
osascript -e 'quit app "Moom"'
defaults export com.manytricks.Moom ~/Desktop/Moom-current.plist
./moom-gen.py ~/Desktop/Moom-current.plist -o ~/Desktop/Moom-new.plist -c CHEATSHEET.md
defaults import com.manytricks.Moom ~/Desktop/Moom-new.plist
open -a Moom
./launcher-patch.py ~/Downloads/Keymap-K3_Max_RGB.json --layer 3 -o ~/Downloads/Keymap-windows.json
```

**Export fresh every time rather than regenerating from the first backup.**
Generated actions carry deterministic identifiers derived from their region
id, so generating from an already-generated plist replaces them in place
rather than duplicating them — while anything you have added since is kept.
Saved layouts are the case that matters: record one in Moom, generate from a
stale backup, and it is gone. The original backup is for rollback, not for
regenerating from.

Useful flags: `--keep-existing` keeps hand-drawn actions instead of replacing
them, `--no-chord-keys` and `--no-controller-keys` drop either half of each
pair, `--chord meh` moves every chord to ⌃⌥⇧ if something claims a Hyper one.

## Files

* `regions.py` — the region table. Edit by hand.
* `actions.yaml` — the actions table: apps to focus, modes to enter. Edit by
  hand; no YAML library needed to read it.
* `actions.py` — load and validate that file, with PyYAML or without it.
* `miniyaml.py` — the fallback parser, for machines with no YAML library.
* `actions-gen.py` — generate the AppleScripts and cheat sheet for the actions
  layer.
* `moom-gen.py` — generate Moom actions, the palette and a cheat sheet.
* `moom-inspect.py` — decode an exported plist: grid, hotkeys, every action
  as grid cells and an ASCII map, flagging duplicates and off-grid frames.
* `launcher-patch.py` — write the window layer into a Launcher export.
* `launcher-inspect.py` — decode a Launcher export: every layer, and which
  layers are reachable from which.
* `qmk.py` — the QMK keycode numbers and encodings both Launcher tools need.
* `scripts/` — generated AppleScripts, committed so they travel with the repo.
* `CHEATSHEET.md`, `ACTIONS.md` — generated; the printable references.
* `INSTALL.md` — the runbook, with verification and rollback.

## The actions layer

A second layer, held by **Tab** (tapped, it is still Tab), on layer 2 — the
Windows base, which is the last layer Launcher offers. Where the window layer
is spatial, this one is mnemonic: `C` focuses Chrome, `T` iTerm2, `O` Obsidian.
Position carries no meaning, so there is no mirror and one key per action.

It uses **Meh** chords (⌃⌥⇧) because the window layer has already claimed
Hyper on most letters. Alfred listens for them and runs a generated
AppleScript:

```sh
./actions-gen.py -c ACTIONS.md
./launcher-patch.py ~/Downloads/Keymap-K3_Max_RGB.json \
    --layer 3 --actions-layer 2 -o ~/Downloads/Keymap-windows.json
```

The scripts land in `scripts/` and are committed, so `git pull` delivers them
to any machine and Alfred can point straight at the checkout — nothing to copy
anywhere. Each runs standalone, so an action can be proven before any hotkey
exists:

```sh
osascript scripts/mode-meeting.applescript
```

Then one Alfred hotkey each, bound once.

Apps are addressed by **bundle identifier**, not name: it survives renames,
and it is the only way to reach a Chrome PWA, which is a real application
bundle rather than a window of Chrome. Calendar and Chat are both PWAs.

Modes compose steps, and `actions.yaml` is the file to edit:

```yaml
modes:
  Meeting:
    key: "1"
    steps:
      - layout: Meeting        # a saved Moom layout, by name
      - focus: Obsidian        # ends focused here, ready to type
  Notes:
    key: "3"
    steps:
      - place: Chrome          # an app from the list above
        region: Left third     # a region title from regions.py
      - place: Obsidian
        region: Right two-thirds
```

Also `shortcut:` to run something from Shortcuts.app — that is how Focus modes
get in — and `url:` to open a link. Steps run in order and the last one
decides where focus ends up.

`layout:` is the right choice when a mode has to place several windows of one
app: `place` only ever reaches the frontmost window, so a layout recorded in
Moom is the only way to express "both terminals".

Region titles are checked against `regions.py` at generation time, app names
against the list above, so a typo fails with the line rather than producing a
script that quietly does nothing. Scripts for actions you have removed are
deleted on regeneration, so nothing stale stays bound in Alfred.

The file is read by **PyYAML if it is installed**, and by `miniyaml.py` — a
parser for the subset these files use — if it is not, because macOS ships a
Python without it and a corporate machine may not be one you can `pip
install` on. The generator prints which parser ran.

Two things keep the paths honest. Scalars are normalised to strings, so
PyYAML reading `key: 1` as an integer and `no` as a boolean cannot change
what the file means. And when PyYAML is present the fallback parser is run
too: if it disagrees, or cannot read the file at all, the generator says so
rather than letting the difference surface on the machine that lacks PyYAML.

## The design

**Regions are a grammar, not a list of rectangles.** Every region is a column
band crossed with a row band, both whole cells of the 12 × 10 grid, so nothing
is ever off-grid and the set can be reasoned about rather than remembered:

| Column bands (427px per cell) | Cells | Row bands (216px per cell) | Cells |
| --- | --- | --- | --- |
| `third-l` / `third-c` / `third-r` | 0–4 / 4–8 / 8–12 | `full` | 0–10 |
| `half-l` / `half-c` / `half-r` | 0–6 / 3–9 / 6–12 | `cam` (top 60%) | 0–6 |
| `two3-l` / `two3-r` | 0–8 / 4–12 | `stage` (bottom 50%) | 5–10 |
| `side-l` / `side-r` | 0–3 / 9–12 | `upper` / `lower` (70%) | 0–7 / 3–10 |

Vertical thirds are 30/70 rather than 33/67: a 10-row grid cannot express
thirds, and 72px on a 2160px screen is not worth an off-grid frame forever.

**The keyboard is a map of the screen, under either hand.** The same map is
mirrored on both hands so it can be driven one-handed while the other hand is
on the mouse. Mirrored keys send the same chord, so Moom sees one action
either way and the mirror costs nothing.

The layer key has to be reachable by the hand that is *not* pressing a region
key, which for the left-hand block means the thumb: `LM(3, MOD_LALT)` on left
Option holds the layer with Option active, and since the chord already
contains Option that changes nothing, while every unmapped key stays
transparent so ⌥←, ⌥⌫ and ⌥-click keep working. Caps Lock as
`LT(3, KC_ESC)` is the same layer under the left pinky for when the right
hand is doing the pressing, and tapped it is still Escape.

**The chord is chosen separately from the keys that send it**, and is always
a letter or a digit. Punctuation under Hyper is where macOS keeps system
shortcuts — ⌃⌥⌘, and ⌃⌥⌘. adjust contrast, ⇧⌘/ opens Help search — and
chords on `,` `.` `/` never reached Moom at all, while letter ones worked
first time. So the bottom row's keys send `⌃⌥⇧⌘C`, `V` and `B`, the chords of
the letters under the left hand. Full screen is the same trick for a
different reason: Tab sends Return's chord, because ⌘Tab is the app switcher
and Hyper contains Command.

Two other keys are deliberately left alone. Alfred owns ⌃⌥⇧⌘Space, so no
region uses Space. And `` ` `` is unmapped on the layer, so held left Option
it still sends ⌥` — Moom's own keyboard controller, which the layer is meant
to complement rather than swallow.

**Two bindings per region, because Moom allows one hotkey per action.** Each
region generates a pair: a controller-restricted single key, which keeps the
⌥` overlay working as the cheat sheet, and the same key under a global chord
for one-keystroke invocation from the window layer. QMK emits the chord
natively as `HYPR(KC_D)` — no macro, no inter-stroke delay, nothing to leak
into the focused app if Moom is slow.

## Reference: how Moom is driven

Three transports, which differ mainly in what they cost the global shortcut
namespace and how they fail.

**Controller-restricted single keys.** A hotkey whose modifier flags carry no
real modifier only fires while the keyboard controller overlay is up. Zero
global footprint; costs two keystrokes (⌥` then the key) and the overlay's
cheat sheet doubles as documentation.

**Global chords.** Any hotkey with a real modifier is global. `Hyper`
(⌃⌥⇧⌘) is the safe corner of the namespace: effectively nothing ships
bindings there, and QMK emits it natively with no macro, no delay and no
leaked keystroke.

**AppleScript.** `tell application "Moom" to run "<action title>"` runs a
named custom action; Moom also scripts saved layouts and centring. It needs
AppleScript support enabled in Moom's settings and something to bind a key
to the script, so it is the wrong tool for per-window nudges and the right
one for composite layouts that place several windows at once.

## Reference: Moom's plist

Moom 4 keeps its actions in `Custom Controls (4001)` in `com.manytricks.Moom`;
a legacy Moom 3 `Custom Controls` array may also be present and is ignored.
Each entry is a dictionary:

* `Identifier` — a UUID string, also repeated inside the `Hot Key` dictionary.
* `Action` — `19` move & zoom, `1001` saved layout (carries a `Snapshot` array
  of per-window frames), `-101` section header (uses `Title`), `0` separator.
* `Relative Frame` — `{{x, y}, {w, h}}` as fractions of the screen, **origin
  bottom-left**, AppKit style: `{{0.25, 0}, {0.5, 0.6}}` is the *bottom*-centre
  half-width region. The saved layouts settle it — a snapshot records a screen
  1692px tall whose available frame is 1667px tall at origin y 0, so the menu
  bar comes off the top while the origin stays at the bottom. `regions.py`
  writes row bands top-down, the way people describe them, and flips them in
  `frame()`.
* `Configuration Grid` — optional per-action override recording the grid the
  action was *authored* on. It is editor metadata; the relative frame is the
  truth, so generated frames need not respect the global grid.
* `Hot Key` — `Key Code` is a macOS virtual key code, `Modifier Flags` is an
  NSEvent mask with a constant `0x100` bit set. No bit above `0x10000` means a
  controller-restricted single key; `Option` is `0x80000`, `Command` `0x100000`,
  `Control` `0x40000`, `Shift` `0x20000`, so Hyper is `0x1E0100`.
* `Title` — optional, and required for AppleScript addressing.

## Reference: Launcher's export

Launcher's export is not VIA's. It is `{"id", "keymap", "version", "MD5"}`,
where `keymap` is one array per layer of `{"col", "row", "val"}` objects —
98 per layer on a K3 Max — and `val` is a raw numeric QMK keycode:

* basic keycodes are HID usage IDs: `KC_A` is 4, `KC_ESC` 41, `KC_CAPS` 57;
* `0x0100`–`0x1FFF` is a basic keycode with modifiers, `mods << 8 | keycode`,
  so `HYPR(KC_D)` is `0x0F00 | 7` = 3847;
* `LT(layer, kc)` is `0x4000 | layer << 8 | kc`, `LM(layer, mod)` is
  `0x5000 | layer << 5 | mod`, `MO(layer)` is `0x5220 | layer`;
* `0x7800`+ is lighting, `0x7E00`+ is Keychron's own — including the Mac
  modifiers, where left Option is `KB0` rather than `KC_LALT`.

**`MD5` is over the `keymap` array serialised as compact JSON**
(`json.dumps(keymap, separators=(",", ":"))`), so a patched file has to be
re-signed or Launcher will reject it.

The K3 Max has four layers and the Mac/Win switch chooses the base: 0 and 1
are macOS base and Fn, 2 and 3 Windows base and Fn. Layer 3 is reachable only
via `MO(3)` on layer 2, so on macOS it is free — which is why the window layer
goes there. The cost is that flipping the switch to Windows turns Fn into the
window layer.

Keys are located by what they type on the base layer rather than by matrix
position, so the patch needs no keyboard definition and does not care about
ANSI or ISO.

## Reference: what this replaced

The original hand-built config was 13 actions on a 12 × 10 grid, all
controller-restricted single keys behind ⌥`, which was the only global
shortcut in it. Four things were worth fixing:

* `6` and `7` were byte-identical duplicates of `3` and `2`, authored later
  against a 12 × 6 grid and landing on the same frames.
* The vertical thirds were **off-grid** — authored on a 6-row grid, so on a
  10-row configuration grid they sat at rows 3.33 and 6.67, unreproducible by
  the mouse grid and rounded by the editor if ever touched.
* Nothing was titled, so nothing could be scripted.
* `Z` (centre half, top half) and `X` (centre half, bottom 60%) overlapped by
  10% of the height — the deliberate webcam arrangement that `cam` and
  `stage` now express.

## Next

The AppleScript layer for composite window arrangements: one key that places
several windows at once, for meeting mode and deep-work mode.
