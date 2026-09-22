#!/usr/bin/env python3
"""Generate Moom's custom actions from config.yaml.

Reads an exported Moom plist, replaces its custom actions with ones built
from the config, and writes a new plist to import. Saved layouts are carried
across untouched — they are recorded by hand and cannot be generated.

    osascript -e 'quit app "Moom"'
    defaults export com.manytricks.Moom ~/Desktop/Moom-current.plist
    ./moom-gen.py ~/Desktop/Moom-current.plist -o ~/Desktop/Moom-new.plist -c CHEATSHEET.md
    defaults import com.manytricks.Moom ~/Desktop/Moom-new.plist
    open -a Moom

Every region gets a global chord. Regions marked `overlay: true` also get a
bare single key, which only fires while Moom's ⌥` controller is on screen.
Identifiers are derived from the region id, so regenerating updates actions
in place rather than piling up duplicates.
"""

from __future__ import annotations

import argparse
import plistlib
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config as config_module  # noqa: E402

# Namespace for deterministic action identifiers. Constant forever: change it
# and every generated action becomes a new action to Moom.
NAMESPACE = uuid.UUID("6f9b1d4e-6d1e-5a2f-9c3b-4a7e0d21c8f5")

MOVE_AND_ZOOM = 19
SECTION_HEADER = -101
SAVED_LAYOUT = 1001

# NSEvent modifier bits: device-independent, the device-dependent left-side
# bit (what Moom records from a real keypress, and what QMK sends), and glyph.
BASE_FLAG = 0x100
MODIFIERS = {
    "control": (0x40000, 0x1, "⌃"),
    "option": (0x80000, 0x20, "⌥"),
    "shift": (0x20000, 0x2, "⇧"),
    "command": (0x100000, 0x8, "⌘"),
}
CHORDS = {
    "hyper": ["control", "option", "shift", "command"],
    "meh": ["control", "option", "shift"],
}
GLYPH_ORDER = ("control", "option", "shift", "command")

COLUMN_SHORT = {
    "full": "FULL", "third-l": "⅓L", "third-c": "⅓C", "third-r": "⅓R",
    "half-l": "½L", "half-c": "½C", "half-r": "½R",
    "two3-l": "⅔L", "two3-c": "⅔C", "two3-r": "⅔R",
    "side-l": "▏L", "side-r": "R▕",
}
ROW_SHORT = {"full": "", "cam": "▀", "stage": "▄", "upper": "▀", "lower": "▄"}

# The window layer, one block per hand, for the cheat sheet.
LAYOUTS = {
    "Left hand": [["1", "2", "3", "4", "5"], ["Q", "W", "E", "R", "T"],
                  ["A", "S", "D", "F", "G"], ["Z", "X", "C", "V", "B"], ["Tab"]],
    "Right hand": [["6", "7", "8", "9", "0"], ["Y", "U", "I", "O", "P"],
                   ["H", "J", "K", "L", ";"], ["N", "M", ",", ".", "/"], ["'"]],
}


def identifier(name, variant):
    return str(uuid.uuid5(NAMESPACE, f"moom-keys:{name}:{variant}")).upper()


def glyphs(chord):
    return "".join(MODIFIERS[name][2] for name in GLYPH_ORDER
                   if name in CHORDS[chord])


def hot_key(cfg, key, control_id, chord, device_bits):
    """A Moom hot key. `chord` is None for a controller-only single key."""
    code, _ = cfg.KEYS[key]
    label, flags = key, BASE_FLAG
    if chord:
        for name in CHORDS[chord]:
            independent, device, _ = MODIFIERS[name]
            flags |= independent | (device if device_bits else 0)
        label = glyphs(chord) + label
    return {"Visual Representation": label, "Identifier": control_id,
            "Key Code": code, "Modifier Flags": flags}


def action(cfg, region, variant, chord, device_bits):
    control_id = identifier(region["id"], variant)
    x, y, w, h = cfg.frame(region)
    return {
        "Identifier": control_id,
        # The chord action keeps the clean title: it is the one AppleScript
        # addresses, and the one a mode's `place` step names.
        "Title": region["title"] if variant == "chord" else f'{region["title"]} (⌥`)',
        "Action": MOVE_AND_ZOOM,
        "Relative Frame": "{{%.17g, %.17g}, {%.17g, %.17g}}" % (x, y, w, h),
        "Configuration Grid": {"Configuration Grid: Columns": cfg.columns,
                               "Configuration Grid: Rows": cfg.rows},
        "Hot Key": hot_key(cfg, region["chord"] if variant == "chord" else region["chord"],
                           control_id, chord if variant == "chord" else None,
                           device_bits),
    }


def build(cfg, chord, device_bits):
    controls, index_of, group = [], {}, None
    for region in cfg.regions:
        if region["group"] != group:
            group = region["group"]
            controls.append({"Identifier": identifier(group, "header"),
                             "Title": group, "Action": SECTION_HEADER})
        index_of[region["id"]] = len(controls)
        controls.append(action(cfg, region, "chord", chord, device_bits))
        if region["overlay"]:
            controls.append(action(cfg, region, "overlay", chord, device_bits))
    return controls, index_of


def cheat_sheet(cfg, chord):
    by_key = {}
    for region in cfg.regions:
        by_key[region["left"]] = region
        by_key[region["right"]] = region

    lines = [
        "# Window regions", "",
        f"Generated from `config.yaml`. Screen {cfg.width} x {cfg.height}.", "",
        "Hold **Caps Lock** or **left Option**, then the key below. The map is "
        "mirrored, so either hand can drive it alone while the other stays on "
        "the mouse.", "",
    ]
    for hand, rows in LAYOUTS.items():
        lines += [f"**{hand}**", "", "```"]
        for row in rows:
            keys, labels = [], []
            for key in row:
                region = by_key[key]
                short = (COLUMN_SHORT[region["column_band"]]
                         + ROW_SHORT[region["row_band"]])
                cell = max(6, len(short) + 2, len(key) + 2)
                keys.append(key.center(cell))
                labels.append(short.center(cell))
            lines += ["".join(keys).rstrip(), "".join(labels).rstrip(), ""]
        lines += ["```", ""]

    lines += [
        "| Keys | Region | Chord | Columns (of 12) | Rows (of 10, from the top) | Pixels |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for region in cfg.regions:
        left, right = region["columns"]
        top, bottom = region["rows"]
        x, y, w, h = cfg.pixels(region)
        lines.append(
            f'| `{region["left"]}` / `{region["right"]}` | {region["title"]} | '
            f'{glyphs(chord)}`{region["chord"]}` | {left}–{right} | {top}–{bottom} | '
            f"{w}×{h} at {x},{y} |")

    overlay = [region for region in cfg.regions if region["overlay"]]
    if overlay:
        lines += ["", "## Inside the ⌥` overlay", "",
                  "These regions also answer to a bare key while Moom's "
                  "keyboard controller is on screen:", ""]
        for region in overlay:
            lines.append(f'* `{region["chord"]}` — {region["title"]}')

    lines += ["", "## Keyboard layer", "",
              "Both keys of a pair send the same chord, so Moom sees one action "
              "either way. Chords are always a letter or a digit — never "
              "punctuation, which is where macOS keeps its own shortcuts.", "",
              "## Scripting", "",
              "Every region is addressable by title:", "",
              "```applescript", 'tell application "Moom" to run "Camera stage"',
              "```", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plist", help="exported com.manytricks.Moom plist")
    parser.add_argument("-o", "--output", required=True, help="plist to write")
    parser.add_argument("-c", "--cheatsheet", help="also write a markdown cheat sheet")
    parser.add_argument("--keep-existing", action="store_true",
                        help="keep hand-drawn actions instead of replacing them")
    parser.add_argument("--no-device-bits", action="store_true",
                        help="omit the left-modifier device bits from chords")
    parser.add_argument("--binary", action="store_true", help="write a binary plist")
    args = parser.parse_args()

    cfg = config_module.load()
    cfg.KEYS = config_module.KEYS
    print(f"read {config_module.CONFIG.name} with {cfg.parser}\n")

    chord = cfg.layer("window_layer").get("chord", "hyper")
    if chord not in CHORDS:
        raise SystemExit(f"window_layer: unknown chord {chord!r}")

    with open(args.plist, "rb") as handle:
        prefs = plistlib.load(handle)

    generated, index_of = build(cfg, chord, not args.no_device_bits)
    generated_ids = {control["Identifier"] for control in generated}
    existing = prefs.get("Custom Controls (4001)") or []
    kept = [control for control in existing
            if control.get("Identifier") not in generated_ids
            and (args.keep_existing or control.get("Action") == SAVED_LAYOUT)]

    prefs["Custom Controls (4001)"] = generated + kept
    prefs["Configuration Grid: Columns"] = cfg.columns
    prefs["Configuration Grid: Rows"] = cfg.rows
    prefs["Palette"] = {f"{index + 3}-3": index_of[name]
                        for index, name in enumerate(cfg.palette)
                        if name in index_of}

    with open(args.output, "wb") as handle:
        plistlib.dump(prefs, handle,
                      fmt=plistlib.FMT_BINARY if args.binary else plistlib.FMT_XML,
                      sort_keys=True)

    overlay = sum(region["overlay"] for region in cfg.regions)
    print(f"{len(cfg.regions)} regions -> {len(generated)} actions "
          f"({overlay} also on the ⌥` overlay, {len(kept)} existing kept, "
          f"{len(existing) - len(kept)} replaced)")
    print(f"wrote {args.output}")
    if args.cheatsheet:
        Path(args.cheatsheet).write_text(cheat_sheet(cfg, chord))
        print(f"wrote {args.cheatsheet}")
    print("\nTo apply:")
    print("  osascript -e 'quit app \"Moom\"'")
    print(f"  defaults import com.manytricks.Moom {args.output}")
    print("  open -a Moom")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # piping into head and friends
        sys.exit(0)
