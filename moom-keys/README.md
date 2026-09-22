# moom-keys

Keyboard-driven window management and app switching for a very wide display,
generated from one file.

`config.yaml` is the source of truth. Everything else is derived from it:
[Moom](https://manytricks.com/moom/)'s actions, a Keychron K3 Max's layers,
the AppleScripts Alfred runs, and the cheat sheets. Nothing is kept in sync by
hand.

## How the parts fit together

Three generators, each writing into a different place. They never talk to each
other; they agree because they read the same file.

```
                  ┌─ moom-gen.py ───────▶ a plist   ─▶ Moom
  config.yaml ────┼─ launcher-patch.py ─▶ a keymap  ─▶ the keyboard
                  └─ actions-gen.py ────▶ scripts/  ─▶ Alfred
```

At press time none of that is involved. The keyboard and everything else meet
at a **chord** and nowhere else:

```
  hold Caps, press D  ─▶  ⌃⌥⇧⌘D  ─▶  Moom moves the window to the centre half
  hold Tab,  press C  ─▶  ⌃⌥⇧C   ─▶  Alfred runs scripts/app-chrome.applescript
  press ⌥`, then D    ─▶           ─▶  Moom, via its own on-screen controller
```

Which means the pieces are independent, and that is how you tell which one is
broken. Import only the plist and the ⌥` overlay still drives the busiest
regions. Import only the keymap and the chords fire into nothing. Bind nothing
in Alfred and the scripts still run from a terminal.

## Quick start

Nothing here has dependencies: it uses PyYAML if you have it and its own
parser if you do not, and the Python that ships with macOS is enough.

**1. Moom.** Quit it first — it holds preferences in memory and writes them
back on quit, which would clobber the import.

```sh
osascript -e 'quit app "Moom"'
defaults export com.manytricks.Moom ~/Desktop/Moom-rollback.plist   # keep this, untouched
defaults export com.manytricks.Moom ~/Desktop/Moom-current.plist    # the working copy
./moom-gen.py ~/Desktop/Moom-current.plist -o ~/Desktop/Moom-new.plist -c CHEATSHEET.md
defaults import com.manytricks.Moom ~/Desktop/Moom-new.plist
open -a Moom
```

Two exports, deliberately: the rollback is written once and never again, while
the working copy is re-exported every time. Reusing one file for both means
the first regeneration overwrites the state you meant to be able to go back to.

Check: **⌥`** then **D** moves the window to the centre half.

**2. The keyboard.** Plug it in — Launcher only talks over USB, from a
Chromium browser — with the Mac/Win switch on **Mac**. Open
<https://launcher.keychron.com>, authorize the device, **Export** the current
keymap and keep that file as the rollback.

```sh
./launcher-patch.py ~/Downloads/Keymap-K3_Max_RGB.json -o ~/Downloads/Keymap-new.json
```

Import the result. Check: hold **Caps**, press **D** — same jump. The keymap
lives in the keyboard, so it keeps working over Bluetooth and 2.4GHz.

**3. Actions.** Optional, and independent of the rest.

```sh
./actions-gen.py -c ACTIONS.md
osascript scripts/mode-meeting.applescript          # runs it, here and now
./alfred-gen.py --install
```

Restart Alfred and the chords are live: one hotkey per action, each wired to
run its script from this checkout. Editing `config.yaml` and regenerating then
changes what the hotkeys do without touching Alfred again.

It installs rather than imports because **Alfred strips hotkeys out of an
imported workflow** — confirmed by exporting one back and finding every
hotkey it was given blanked, while hotkeys assigned by hand match what this
generates exactly. Writing into Alfred's workflows folder skips that.

[`INSTALL.md`](INSTALL.md) has all of this at walking pace, with a
verification ladder whose failures each point at what to fix, and rollback for
each part.

## What you get

21 regions, either hand, one keystroke. Hold **Caps** (tapped, still Escape)
or **left Option**:

```
  left hand                        right hand

  1  2  3  4  5                    6  7  8  9  0     widths
  Q  W  E  R  T                    Y  U  I  O  P     top-anchored
  A  S  D  F  G                    H  J  K  L  ;     full height
  Z  X  C  V  B                    N  M  ,  .  /     bottom-anchored
  Tab  whole screen                '                 whole screen

     ⅓L ½L ½C ½R ⅓R                   ⅓L ½L ½C ½R ⅓R
```

Row picks the vertical anchor, column picks the horizontal position. `D`/`K`
is the centred half, `E`/`I` the camera stage above it, `C`/`,` the working
window below it. The digit row is one width slid across the screen —
`2` `3` `4` are the left, centre and right two-thirds — flanked by the two
narrow sides on `1` and `5`.

Holding **right Command** gives the actions layer instead: `C` for Chrome, `T` for
iTerm2, `1` for meeting mode. `ACTIONS.md` lists them.

## Changing anything

Edit `config.yaml`, then regenerate. **Export Moom fresh first.** The
generator keeps everything it did not write, but it can only keep what is in
the file you give it — generate from last week's export and anything recorded
since is simply not there to keep.

```sh
osascript -e 'quit app "Moom"'
defaults export com.manytricks.Moom ~/Desktop/Moom-current.plist
./moom-gen.py ~/Desktop/Moom-current.plist -o ~/Desktop/Moom-new.plist -c CHEATSHEET.md
defaults import com.manytricks.Moom ~/Desktop/Moom-new.plist
open -a Moom
./launcher-patch.py ~/Downloads/Keymap-K3_Max_RGB.json -o ~/Downloads/Keymap-new.json
./actions-gen.py -c ACTIONS.md
```

It reports what it preserved, layouts by name:

```
kept 17 action(s) this tool did not write, including the saved layout(s): Meeting
```

Change a chord and both the plist and the keymap have to be reimported; they
agree on the chord or nothing fires.

Mistakes in the config fail loudly and name what is wrong — an unknown band, a
duplicate key, a region title a mode refers to that does not exist, a title
used twice (Moom addresses actions by title, so they must be unique).

## Files

* `config.yaml` — the source of truth. The only file meant to be edited.
* `config.py` — load and validate it; holds the key-code table and the
  geometry helpers.
* `miniyaml.py` — the fallback YAML parser, for machines without PyYAML.
* `qmk.py` — QMK keycode numbers and encodings.
* `moom-gen.py` / `moom-inspect.py` — write and read Moom's preferences.
* `launcher-patch.py` / `launcher-inspect.py` — write and read the keymap.
* `actions-gen.py` — write the AppleScripts and `ACTIONS.md`.
* `alfred-gen.py` — build an Alfred workflow binding every chord to its script.
* `scripts/` — generated AppleScripts, committed so they travel with the repo.
* `CHEATSHEET.md`, `ACTIONS.md` — generated references.
* `INSTALL.md` — the runbook, with verification and rollback.

## The design

**Regions are a grammar, not a list of rectangles.** Each is a column band
crossed with a row band, both whole cells of the 12 × 10 grid, so nothing is
ever off-grid and the set can be reasoned about rather than remembered. Both
vocabularies live under `bands:` in the config.

Vertical thirds are 30/70 rather than 33/67: a 10-row grid cannot express
thirds, and 72px on a 2160px screen is not worth an off-grid frame forever.

**The keyboard is a map of the screen, under either hand.** Mirroring costs
nothing because mirrored keys send the same chord, so Moom sees one action
either way.

The actions layer is held by **right Command**, which gives up being Command.
A tap-hold on Tab was the first choice and the wrong one: hold Tab a shade too
long and QMK reads it as a hold, sending no Tab at all, so ⌘Tab silently fails
to open the switcher. Tab is far too busy a key to gamble on a timing
threshold; right Command is one almost nobody uses, with shortcuts typed on
the left.

The window layer key must be reachable by the hand that is *not* pressing a
region key, which for the left-hand block means the thumb: `LM(3, MOD_LALT)` on left
Option holds the layer with Option live, and since the chord already contains
Option that changes nothing, while every unmapped key stays transparent so
⌥←, ⌥⌫ and ⌥-click keep working. Caps Lock as `LT(3, KC_ESC)` is the same
layer under the left pinky for when the right hand is pressing.

**The chord is chosen separately from the keys that send it**, and is always a
letter or a digit. Punctuation under Hyper is where macOS keeps system
shortcuts — ⌃⌥⌘, and ⌃⌥⌘. adjust contrast, ⇧⌘/ opens Help — and chords on
`,` `.` `/` never reached Moom at all, while letter ones worked first time. So
the bottom row's keys send `⌃⌥⇧⌘C`, `V` and `B`, the chords of the letters
under the left hand. Whole screen is the same trick for a different reason:
Tab sends Return's chord, because ⌘Tab is the app switcher and Hyper contains
Command.

Two keys are deliberately left alone. Alfred owns ⌃⌥⇧⌘Space, so no region
uses Space. And `` ` `` is unmapped on the layer, so held under left Option it
still sends ⌥` — Moom's own controller, which the layer complements rather
than swallows.

**Most regions have one binding; a few have two.** Moom allows one hotkey per
action, so a region that should answer both to a chord and to a bare key
inside the ⌥` overlay needs two actions. Only the regions marked
`overlay: true` get the second — the busiest three — which keeps the action
list at 29 rather than 42.

**Actions are mnemonic, not spatial.** The window layer is mirrored because
position means something; `C` for Chrome means nothing in the mirror position,
so the actions layer has one key per action and no mirror. It uses Meh
(⌃⌥⇧) because the window layer has claimed Hyper on most letters.

Apps are addressed by **bundle identifier**: it survives renames, and it is
the only way to reach a Chrome PWA, which is a real application bundle rather
than a window of Chrome.

Modes compose steps. `layout:` runs a saved Moom layout and is the right
choice when several windows of one app must be placed — `place:` only ever
reaches the frontmost window. `shortcut:` reaches anything Shortcuts.app can
do. Steps run in order and the last decides where focus ends up.

## Reference: the config file

Read by **PyYAML if installed**, by `miniyaml.py` if not, because macOS ships
a Python without one and a corporate machine may not be one you can `pip
install` on. The generators print which parser ran.

Two things keep the paths honest. Scalars are normalised to strings, so
PyYAML reading `key: 1` as an integer and `no` as a boolean cannot change what
the file means. And when PyYAML is present the fallback runs too: if it
disagrees or cannot read the file, the generator says so rather than letting
the difference surface on the machine that lacks PyYAML.

## Reference: Moom's plist

Moom 4 keeps its actions in `Custom Controls (4001)`; a legacy Moom 3
`Custom Controls` array may also be present and is ignored. Each entry:

* `Identifier` — a UUID, repeated inside the `Hot Key` dictionary.
* `Action` — `19` move & zoom, `1001` saved layout (carries a `Snapshot` of
  per-window frames), `-101` section header, `0` separator.
* `Relative Frame` — `{{x, y}, {w, h}}` as fractions, **origin bottom-left**,
  AppKit style: `{{0.25, 0}, {0.5, 0.6}}` is the *bottom*-centre half-width
  region. The saved layouts settle it — a snapshot records a screen 1692px
  tall whose available frame is 1667px at origin y 0, so the menu bar comes
  off the top while the origin stays at the bottom.
* `Configuration Grid` — editor metadata recording the grid an action was
  authored on; the relative frame is the truth.
* `Hot Key` — `Key Code` is a macOS virtual key code, `Modifier Flags` an
  NSEvent mask with a constant `0x100` bit. No bit above `0x10000` means a
  controller-only single key; Hyper is `0x1E0100`.
* `Title` — required for AppleScript addressing, and unique.

Saved layouts are recorded by hand and cannot be generated, so they must
survive every regeneration. `moom-gen.py` records the identifiers it writes
under its own key in the plist, and on the next run replaces exactly those,
keeping everything else — layouts, actions made by hand, anything a future
Moom adds. Deciding what is "mine" by an action's *type* is what deleted a
recorded layout once; identity is the only safe test. `--replace-all` drops
everything for a genuine clean slate, and says so.

## Reference: Launcher's export

Not VIA's format. `{"id", "keymap", "version", "MD5"}`, where `keymap` is one
array per layer of `{"col", "row", "val"}` — 98 per layer on a K3 Max — and
`val` is a raw numeric QMK keycode:

* basic keycodes are HID usage IDs: `KC_A` is 4, `KC_ESC` 41, `KC_CAPS` 57;
* `0x0100`–`0x1FFF` is a keycode with modifiers, `mods << 8 | keycode`, so
  `HYPR(KC_D)` is `0x0F00 | 7` = 3847;
* `LT(layer, kc)` is `0x4000 | layer << 8 | kc`, `LM(layer, mod)` is
  `0x5000 | layer << 5 | mod`, `MO(layer)` is `0x5220 | layer`;
* `0x7800`+ is lighting, `0x7E00`+ is Keychron's own — including the Mac
  modifiers, where left Option is `KB0`, not `KC_LALT`.

**`MD5` is over the `keymap` array as compact JSON**
(`json.dumps(keymap, separators=(",", ":"))`), so a patched file must be
re-signed or Launcher rejects it.

Four layers, and the Mac/Win switch chooses the base: 0 and 1 are macOS base
and Fn, 2 and 3 Windows base and Fn. Both Windows layers are taken — 3 for
windows, 2 for actions — which costs nothing on macOS, but flipping the switch
afterwards lands on those rather than a Windows keymap.

Keys are located by what they type on the base layer rather than by matrix
position, so the patch needs no keyboard definition and does not care about
ANSI or ISO.
