# Installing

One pass, start to finish. Each step has a check; if a check fails, the table
at the end says what it means. Everything runs from this directory:

```sh
git pull
cd moom-keys
```

No dependencies — the Python that ships with macOS is enough.

## 1. Generate everything

```sh
osascript -e 'quit app "Moom"'
defaults export com.manytricks.Moom ~/Desktop/Moom-rollback.plist   # keep, untouched
defaults export com.manytricks.Moom ~/Desktop/Moom-current.plist    # working copy

./moom-gen.py ~/Desktop/Moom-current.plist -o ~/Desktop/Moom-new.plist -c CHEATSHEET.md
./actions-gen.py -c ACTIONS.md
./alfred-gen.py -o ~/Desktop/moom-keys.alfredworkflow
./launcher-patch.py ~/Downloads/Keymap-K3_Max_RGB.json -o ~/Downloads/Keymap-new.json
```

Two Moom exports on purpose: the rollback is written once and never again,
the working copy is re-exported every time. One file for both means the first
regeneration overwrites what you meant to be able to return to.

`moom-gen.py` reports what it preserved, saved layouts by name. Anything it
did not write itself, it keeps.

## 2. Load Moom

```sh
defaults import com.manytricks.Moom ~/Desktop/Moom-new.plist
open -a Moom
```

**Check:** **⌥`** then **D** moves the front window to the centred half.

## 3. Load the keyboard

Plug the K3 Max in — Launcher only talks over USB, from a Chromium browser —
with the Mac/Win switch on **Mac**. Open <https://launcher.keychron.com>,
click **Authorize device**, then **Export** the current keymap and keep that
file as your keyboard rollback. Now **Import** `~/Downloads/Keymap-new.json`.

**Check:** hold **Caps Lock**, press **D** — the same jump. Then tap Caps on
its own: it should type Escape.

This writes two layers. Layer 3 is windows, held by Caps Lock or left Option.
Layer 2 is actions, held by **right Command**, which stops being Command —
left Command still does every shortcut you type.

## 4. Record a layout

Layouts are the one thing that cannot be generated: Moom records them from
windows you have arranged, which is also the only way to place two windows of
the same app.

Arrange the windows you want for a meeting, then Moom's menu bar icon →
**Save Window Layout Snapshot**, and name it exactly `Meeting`.

**Check:**

```sh
osascript -e 'tell application "Moom" to run "Meeting"'
```

Move a window, run it again, and everything should snap back.

## 5. Run a mode

```sh
osascript scripts/mode-meeting.applescript
```

This runs the `Meeting` layout and then brings Obsidian forward, which is
what `config.yaml` says the mode does. macOS will ask for permission to
control Moom and Obsidian the first time — allow each.

**Check:** the windows arrange and Obsidian ends up focused.

## 6. Install the Alfred workflow

Double-click `~/Desktop/moom-keys.alfredworkflow`. Alfred will ask to install
it and to approve the hotkeys.

It contains one hotkey per action, each wired to run the matching script from
this checkout. That means editing `config.yaml` and re-running
`actions-gen.py` changes what the hotkeys do without touching Alfred again;
only adding or moving a key needs the workflow rebuilt.

**Check:** hold **right Command** and press **1** — the meeting layout runs.
Then right Command and **C** — Chrome comes forward.

**If the hotkeys arrive blank**, the encoding Alfred wants is not what was
generated — but nothing is wasted. Every object is built, named and wired, so
open the workflow and double-click each Hotkey object: its canvas note says
which chord to record (`⌃⌥⇧C  Chrome`). Fourteen chords, no typing, no
wiring.

## When a check fails

| Check | Means |
| --- | --- |
| ⌥` then `D` does nothing | Moom was running during the import. Quit it and import again. |
| ⌃⌥⇧⌘`D` typed by hand does nothing | The modifier flags are wrong. Regenerate with `--no-device-bits` and reimport. |
| Caps types nothing, or types Caps | The keymap did not take. Re-run `launcher-inspect.py` on the patched file and check layer 0 shows `LT(3,Esc)`. |
| Caps + `D` does nothing but ⌥` + `D` works | Layer 3 is wrong or missing — check the inspector's layer 3. |
| left Option + `D` does nothing | `LM` did not take. The Caps route still works meanwhile. |
| ⌥← stops jumping a word | `LM` is not passing Option through. Tell me — the fallback is a plain `MO(3)`. |
| left Option + `` ` `` does not open Moom's overlay | `` ` `` got mapped on the layer; it must stay transparent. |
| Caps + `I` puts the window at the bottom | Row bands are inverted; `frame()` flips them for Moom's bottom-left origin. |
| `run "Meeting"` errors | The layout is not saved under exactly that name, or Moom's AppleScript support is off. |
| right Command + `1` does nothing | The workflow is not installed, or its hotkeys were not approved. Check Alfred → Workflows. |
| right Command still types Command | The keymap did not take — layer 0 column 10 should read `MO(2)`. |

## Rolling back

Moom:

```sh
osascript -e 'quit app "Moom"'
defaults import com.manytricks.Moom ~/Desktop/Moom-rollback.plist
open -a Moom
```

The keyboard: import the export you kept in step 3. Alfred: delete the
workflow from Alfred → Workflows.
