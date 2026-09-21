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
| `X` | Lower centre — centre half, bottom 60% | 3–9 | 4–10 |
| `Z` | VC window — centre half, top half | 3–9 | 0–5 |
| `A` | Left third, upper two-thirds | 0–4 | 0–6.67 |
| `B` | Right third, upper two-thirds | 8–12 | 0–6.67 |
| `C` | Left third, lower two-thirds | 0–4 | 3.33–10 |
| `D` | Right third, lower two-thirds | 8–12 | 3.33–10 |

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
* **`Z` and `X` overlap by 10% of the height** (rows 4–5), which is the
  deliberate webcam/stage arrangement: `Z` high near the camera, `X` below it.

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

Vertical thirds became 30/70. A 10-row grid cannot express 33/67, and 72px on
a 2160px screen is not worth carrying an off-grid frame forever.

**The keyboard is a map of the screen, under either hand.** On the window
layer the alpha block *is* the monitor — row chooses the vertical anchor,
column chooses the horizontal position — and the same map is mirrored on both
hands so it can be driven one-handed while the other hand is on the mouse.
`K`/`D` is the centred half, `I`/`E` the camera stage above it, `,`/`C` the
working window below it. Mirrored keys send the same chord, so Moom sees one
action either way and the mirror costs nothing.

The layer key has to be reachable by the hand that is *not* pressing a region
key, which for the left-hand block means the thumb: `LM(<layer>, MOD_LALT)` on
left Option holds the layer with Option active, and since the chord already
contains Option that changes nothing, while every unmapped key stays
transparent so ⌥←, ⌥⌫ and ⌥-click keep working. Caps Lock as
`LT(<layer>, KC_ESC)` is the same layer under the left pinky for when the
right hand is doing the pressing, and tapped it is still Escape.

**The chord is chosen separately from the keys that send it.** A region's
chord is always a letter or a digit; the two physical keys that send it can
be anything. That matters because punctuation under Hyper is where macOS
keeps system shortcuts — ⌃⌥⌘, and ⌃⌥⌘. adjust contrast, ⇧⌘/ opens Help
search — and chords on `,` `.` `/` never reached Moom at all, while the
letter ones worked first time. So the bottom row's keys send `⌃⌥⇧⌘C`, `V`
and `B`, the chords of the letters under the left hand, and nothing is bound
to a punctuation chord anywhere. Full screen is the same trick for a
different reason: Tab sends Return's chord, because ⌘Tab is the app
switcher and Hyper contains Command.

**Two bindings per region, because Moom allows one hotkey per action.** Each
region generates a pair: a controller-restricted single key, which keeps the
⌥` overlay working as the cheat sheet, and the same key under a global chord
for one-keystroke invocation from the window layer. QMK emits the chord
natively as `HYPR(KC_D)` — no macro, no inter-stroke delay, nothing to leak
into the focused app if Moom is slow. Titles make every region AppleScript-
addressable for composite layouts later.

Alfred owns ⌃⌥⇧⌘Space, so full screen is on `Tab` / `'` instead. `` ` ``
is deliberately left unmapped on the layer: held left Option it still sends
⌥`, which is Moom's own keyboard controller — mapping it there would have
swallowed the overlay the layer is meant to complement. If
anything else turns out to hold a Hyper chord, `--chord meh` regenerates the
whole set on ⌃⌥⇧ (no Command) rather than picking at individual keys.

## Files

* `regions.py` — the region table. The only file to edit by hand.
* `moom-gen.py` — generate Moom actions, the palette and a cheat sheet from it.
* `launcher-inspect.py` — decode a Keychron Launcher export: every layer, and
  which layers are reachable from which.
* `launcher-patch.py` — write the window layer into a Launcher export.
* `qmk.py` — the QMK keycode numbers and encodings both of those need.
* `moom-inspect.py` — decode an exported plist: grid, hotkeys, every action as
  grid cells and an ASCII map, flagging duplicates and off-grid frames.
* `CHEATSHEET.md` — generated; the printable reference.
* `INSTALL.md` — the end-to-end runbook for both halves, and how to verify
  and roll back each of them.

## Using it

`INSTALL.md` is the full runbook, both halves. In short, for Moom:

Quit Moom first: it holds its preferences in memory and writes them back on
quit, which would clobber the import.

```sh
osascript -e 'quit app "Moom"'
defaults export com.manytricks.Moom ~/Desktop/Moom-backup.plist   # keep this
./moom-gen.py ~/Desktop/Moom-backup.plist -o ~/Desktop/Moom-new.plist -c CHEATSHEET.md
./moom-inspect.py ~/Desktop/Moom-new.plist --no-map | less        # optional look
defaults import com.manytricks.Moom ~/Desktop/Moom-new.plist
open -a Moom
```

To roll back, quit Moom and import the backup again:

```sh
osascript -e 'quit app "Moom"'
defaults import com.manytricks.Moom ~/Desktop/Moom-backup.plist
open -a Moom
```

macOS ships a Python 3 that runs all of this; nothing here has dependencies
beyond the standard library.

Generated actions carry deterministic identifiers derived from their region
id, so regenerating updates them in place instead of piling up duplicates.
Saved layouts are carried across; the hand-drawn move & zoom actions are
replaced. `--keep-existing` keeps them instead, `--no-chord-keys` and
`--no-controller-keys` drop either half of each pair.

Two things to verify on first import, both one-line fixes if wrong:

* **Hyper chords firing.** The generated flags include the device-dependent
  left-modifier bits, matching what Moom records when you press a chord by
  hand and what `HYPR()` sends. If a chord does not fire, regenerate with
  `--no-device-bits`.
* **Single-key collisions.** `Space` and the punctuation keys are assumed free
  inside the ⌥` overlay; if one is claimed by Moom's built-in controls,
  change that region's key in `regions.py`.

## Launcher notes (for the patcher)

Launcher's export is not VIA's. It is `{"id", "keymap", "version", "MD5"}`,
where `keymap` is one array per layer of `{"col", "row", "val"}` objects —
98 per layer on a K3 Max — and `val` is a raw numeric QMK keycode. So both
reading and writing it means knowing the quantum ranges:

* basic keycodes are HID usage IDs: `KC_A` is 4, `KC_ESC` 41, `KC_CAPS` 57;
* `0x0100`–`0x1FFF` is a basic keycode with modifiers, `mods << 8 | keycode`,
  so `HYPR(KC_K)` is `0x0F00 | 40` = 3854;
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
ANSI or ISO:

```sh
./launcher-inspect.py Keymap-K3_Max_RGB.json          # which layers are free?
./launcher-patch.py Keymap-K3_Max_RGB.json --layer 3 -o Keymap-windows.json
./launcher-inspect.py Keymap-windows.json --layer 3   # read it back
```

Then import the result in Launcher over USB.

## Next

Confirm on hardware that Launcher imports a re-signed file and that
`LM(3, MOD_LALT)` behaves — Option held, layer active, unmapped keys still
typing. Then the AppleScript layer for composite window arrangements.
