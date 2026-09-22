# Installing

Two halves that have to agree: Moom learns the regions and their hotkeys, the
keyboard learns which chord each key sends. Either half works without the
other — Moom's ⌥` overlay drives the regions with no keyboard changes, and
the keyboard's chords do nothing until Moom knows them — so they can be done
in either order and verified separately.

Everything below runs from this directory:

```sh
git fetch origin claude/keychron-moom-window-strategy-k63ayg
git checkout claude/keychron-moom-window-strategy-k63ayg
cd moom-keys
```

No dependencies; the Python 3 that ships with macOS runs all of it. If a
script will not execute directly, put `python3` in front of it.

## Part 1 — Moom

Moom holds its preferences in memory and writes them back when it quits, so
it has to be quit before both the export and the import.

```sh
osascript -e 'quit app "Moom"'

# Two exports: the rollback is written once and never touched again, the
# working copy is re-exported every time you regenerate.
defaults export com.manytricks.Moom ~/Desktop/Moom-rollback.plist
defaults export com.manytricks.Moom ~/Desktop/Moom-current.plist

./moom-gen.py ~/Desktop/Moom-current.plist -o ~/Desktop/Moom-new.plist -c CHEATSHEET.md

# Optional: read back what was generated before committing to it.
./moom-inspect.py ~/Desktop/Moom-new.plist --no-map | less

defaults import com.manytricks.Moom ~/Desktop/Moom-new.plist
open -a Moom
```

Expect 46 actions: 21 regions twice, plus four group headers.

## Part 2 — the keyboard

Launcher only talks to the keyboard over USB, and only from a Chromium-based
browser (WebHID). The Mac/Win switch must be on **Mac**, because the patch
rebinds Caps Lock and left Option on layer 0, which is the macOS base layer.

1. Plug the K3 Max in with its cable and open <https://launcher.keychron.com>.
   Click **Authorize device** and pick the keyboard.
2. **Export** the current keymap — even if you exported one before, work from
   a fresh file so nothing configured since is lost. Keep it as the rollback.
3. Patch it:

   ```sh
   ./launcher-inspect.py ~/Downloads/Keymap-K3_Max_RGB.json
   ./launcher-patch.py ~/Downloads/Keymap-K3_Max_RGB.json -o ~/Downloads/Keymap-new.json
   ./launcher-inspect.py ~/Downloads/Keymap-new.json --layer 0 --layer 2 --layer 3
   ```

   The first reports which layers are reachable from which. The third reads
   the patched file back: 42 chords on layer 3 and 14 on layer 2, with
   `LT(3,Esc)` on Caps, `LM(3,0x04)` on left Option and `LT(2,Tab)` on Tab.
4. **Import** the patched file in Launcher and let it write to the keyboard.
   The checksum is recomputed by the patcher, so Launcher accepts it.

The keymap lives in the keyboard, so it works over Bluetooth and 2.4GHz
afterwards; the cable is only needed for programming.

## Part 3 — the actions layer (optional)

Independent of the window layer, and safe to leave until later.

```sh
./actions-gen.py -c ACTIONS.md
osascript scripts/mode-meeting.applescript
```

The second line runs the mode there and then — no editor, no hotkey, nothing
to paste. If the windows land where you expect, the whole chain is proven:
AppleScript reaching Moom, region titles resolving, bundle identifiers
resolving, and the delay being long enough.

Then bind each script to its Meh chord in Alfred: a **Hotkey** trigger
connected to a **Run Script** action with **Language** set to `/bin/bash`,
running `osascript "<path to the script>"`. `ACTIONS.md` lists the exact line
for each. Powerpack required.

Not `/usr/bin/osascript` as the language: Alfred passes the box's contents to
the interpreter, so it would read the path as AppleScript source and fail.

The keymap patch in Part 2 already put these chords on layer 2, held by Tab —
both layers are written in one pass. That spends layer 2, the Windows base:
nothing on macOS reaches it, but flipping the Mac/Win switch afterwards lands
on the actions layer rather than a Windows keymap.

## Part 4 — verifying

Four checks, in this order. They fail differently, and which one fails says
what to fix.

| # | Do this | Expect | If it fails |
| --- | --- | --- | --- |
| 1 | **⌥`** then **D** | Window jumps to the centred half | Moom was running during the import — quit it and import again |
| 2 | **⌃⌥⇧⌘D** by hand | Same jump | Regenerate with `--no-device-bits` and re-import |
| 3 | Tap **Caps** | Escape | The keymap did not take; re-run `launcher-inspect.py` on the patched file |
| 4 | Hold **Caps**, press **K** | Same jump (K sends D's chord) | As 3 — check layer 3 in the inspector output |
| 5 | Hold **left Option**, press **D** | Same jump | `LM` did not take; as a fallback the Caps route still works |
| 6 | **⌥←** in any text field | Jumps a word left | `LM` is not passing Option through; report it, the fallback is `MO(3)` |
| 7 | Hold **left Option**, press **`** | Moom's overlay opens | `` ` `` got mapped on the layer; it must stay transparent |
| 8 | Hold **Caps**, press **I** | Window goes to the **top** centre | Row bands are inverted — `frame()` flips them for Moom's bottom-left origin |
| 9 | Hold **Caps**, press **,** | Window goes to the **bottom** centre | The chord is `⌃⌥⇧⌘C`, not `⌃⌥⇧⌘,` — re-patch the keymap and re-import the plist together |
| 10 | Tap **Tab** | A tab character | Tab also holds the actions layer; a tap must still type |
| 11 | Hold **Tab**, press **C** | Chrome comes forward | Only once Alfred is bound — until then the chord fires into nothing |

Checks 1–2 are the Moom half, 3–9 the keyboard half. If 1 works and 2 does
not, the modifier flags are wrong and nothing on the keyboard will fire; fix
that before touching the keymap.

The overlay in check 1 takes the **chord key** — the left-hand letter — and
only for regions marked `overlay: true` in the config, which is Left third,
Centre half and Right third. The keyboard checks press whichever physical key
you like, since both keys of a pair send the same chord. `CHEATSHEET.md`
lists all three columns.

## Saved layouts

Moom's own saved layouts (arrange windows, then save) survive every
regeneration: `moom-gen.py` records the identifiers it writes and replaces
only those, keeping everything else. But it can only keep what is in the file
you hand it, so **export fresh before regenerating**. Every run says what it
kept, layouts by name, and `moom-inspect.py` reports them at the top of its
output — so a missing layout shows up immediately rather than the next time
you need it.

They are worth having alongside the generated regions: a layout can place
several windows of the same app, which a scripted sequence of region moves
cannot. What they cannot do is survive a change of display — a snapshot stores
absolute pixel frames and the screen set it was recorded on.

## Rolling back

Each half independently:

```sh
osascript -e 'quit app "Moom"'
defaults import com.manytricks.Moom ~/Desktop/Moom-rollback.plist
open -a Moom
```

For the keyboard, import the export from step 2 in Launcher. Launcher's own
factory reset also works, at the cost of anything else configured.
