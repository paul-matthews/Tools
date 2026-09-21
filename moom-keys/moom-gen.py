#!/usr/bin/env python3
"""Generate Moom custom actions and a cheat sheet from the region table.

Reads an exported Moom plist, replaces its custom actions with ones generated
from `regions.py`, and writes a new plist to import. Saved layouts (Moom's
window snapshots) are carried across untouched; the hand-drawn move & zoom
actions are the thing being replaced.

    defaults export com.manytricks.Moom ~/Desktop/Moom.plist
    ./moom-gen.py ~/Desktop/Moom.plist -o ~/Desktop/Moom-new.plist -c CHEATSHEET.md
    osascript -e 'quit app "Moom"'
    defaults import com.manytricks.Moom ~/Desktop/Moom-new.plist
    open -a Moom

Every region gets two actions: one bound to a controller-restricted single key
(visible in the ⌥` overlay) and one bound to the same key under Hyper
(⌃⌥⇧⌘) for direct invocation from the keyboard's window layer. Identifiers
are derived from the region id, so regenerating updates actions in place
rather than piling up duplicates.
"""

from __future__ import annotations

import argparse
import plistlib
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import regions as spec  # noqa: E402

# Namespace for deterministic action identifiers. Constant forever: change it
# and every generated action becomes a new action to Moom.
NAMESPACE = uuid.UUID("6f9b1d4e-6d1e-5a2f-9c3b-4a7e0d21c8f5")

MOVE_AND_ZOOM = 19
SECTION_HEADER = -101
SAVED_LAYOUT = 1001

# NSEvent modifier bits. Moom always sets 0x100; anything above 0x10000 makes
# the hotkey global, anything without it is restricted to the ⌥` overlay.
BASE_FLAG = 0x100
SHIFT, CONTROL, OPTION, COMMAND = 0x20000, 0x40000, 0x80000, 0x100000
# Device-dependent bits for the left-hand modifiers, which is what Moom itself
# records when you press a shortcut and what QMK's HYPR() sends.
LEFT_SIDE_BITS = 0x1 | 0x2 | 0x8 | 0x20
HYPER = SHIFT | CONTROL | OPTION | COMMAND

COLUMN_SHORT = {
    "full": "FULL", "third-l": "⅓L", "third-c": "⅓C", "third-r": "⅓R",
    "half-l": "½L", "half-c": "½C", "half-r": "½R",
    "two3-l": "⅔L", "two3-r": "⅔R", "side-l": "▏L", "side-r": "R▕",
}
ROW_SHORT = {"full": "", "cam": "▀", "stage": "▄", "upper": "▀", "lower": "▄"}


def identifier(region_id, variant):
    """Stable UUID for one generated action."""
    return str(uuid.uuid5(NAMESPACE, f"moom-keys:{region_id}:{variant}")).upper()


def frame_string(region):
    x, y, w, h = spec.frame(region)
    return "{{%.17g, %.17g}, {%.17g, %.17g}}" % (x, y, w, h)


def hot_key(key, control_id, hyper, device_bits):
    """Build a Moom hot key dictionary for a key label."""
    code, _ = spec.KEYS[key]
    label = "␣" if key == "Space" else key
    if hyper:
        flags = BASE_FLAG | HYPER | (LEFT_SIDE_BITS if device_bits else 0)
        label = "⌃⌥⇧⌘" + label
    else:
        flags = BASE_FLAG
    return {
        "Visual Representation": label,
        "Identifier": control_id,
        "Key Code": code,
        "Modifier Flags": flags,
    }


def action(region, variant, device_bits):
    """One move & zoom action for a region, in one of its two hotkey flavours."""
    control_id = identifier(region["id"], variant)
    title = region["title"] if variant == "controller" else f"{region['title']} (direct)"
    return {
        "Identifier": control_id,
        "Title": title,
        "Action": MOVE_AND_ZOOM,
        "Relative Frame": frame_string(region),
        "Configuration Grid": {
            "Configuration Grid: Columns": spec.GRID_COLUMNS,
            "Configuration Grid: Rows": spec.GRID_ROWS,
        },
        "Hot Key": hot_key(region["key"], control_id, variant == "hyper", device_bits),
    }


def header(title):
    return {
        "Identifier": identifier(title, "header"),
        "Title": title,
        "Action": SECTION_HEADER,
    }


def build_controls(entries, device_bits, controller_keys, hyper_keys):
    """The generated Custom Controls array, grouped by region family."""
    controls, index_of, group = [], {}, None
    for region in entries:
        if region["group"] != group:
            group = region["group"]
            controls.append(header(group))
        if controller_keys:
            index_of[region["id"]] = len(controls)
            controls.append(action(region, "controller", device_bits))
        if hyper_keys:
            index_of.setdefault(region["id"], len(controls))
            controls.append(action(region, "hyper", device_bits))
    return controls, index_of


def preserved(existing, generated_ids, keep_existing):
    """Existing controls to carry across: saved layouts always, others on ask."""
    kept = []
    for control in existing:
        if control.get("Identifier") in generated_ids:
            continue
        if keep_existing or control.get("Action") == SAVED_LAYOUT:
            kept.append(control)
    return kept


def cheat_sheet(entries, width, height):
    """A printable reference laid out like the keys themselves."""
    by_key = {region["key"]: region for region in entries}
    lines = [
        "# Window regions",
        "",
        f"Generated by `moom-gen.py` from `regions.py`. Screen {width} x {height}.",
        "",
        "Hold **Caps Lock** for the window layer, then the key below. The same "
        "key also works after **⌥`** (Moom's keyboard controller) if the layer "
        "is not to hand.",
        "",
        "```",
    ]

    for row in spec.PHYSICAL_ROWS:
        keys, labels = [], []
        for key in row:
            if key is None:
                keys.append(" " * 6)
                labels.append(" " * 6)
                continue
            region = by_key[key]
            short = COLUMN_SHORT[region["column_band"]] + ROW_SHORT[region["row_band"]]
            cell = max(6, len(short) + 2, len(key) + 2)
            keys.append(key.center(cell))
            labels.append(short.center(cell))
        lines.append("".join(keys).rstrip())
        lines.append("".join(labels).rstrip())
        lines.append("")
    lines += ["```", ""]

    lines += [
        "| Key | Region | Columns (of 12) | Rows (of 10) | Pixels |",
        "| --- | --- | --- | --- | --- |",
    ]
    for region in entries:
        left, right = region["columns"]
        top, bottom = region["rows"]
        x, y, w, h = spec.pixels(region, width, height)
        lines.append(
            f"| `{region['key']}` | {region['title']} | {left}–{right} | "
            f"{top}–{bottom} | {w}×{h} at {x},{y} |"
        )

    lines += [
        "",
        "## Keyboard layer",
        "",
        "Each key on the window layer sends its region's Hyper chord. In "
        "Keychron Launcher these go in as custom (`Any`) keycodes:",
        "",
        "| Key | QMK keycode |",
        "| --- | --- |",
    ]
    for region in entries:
        lines.append(f"| `{region['key']}` | `HYPR({spec.KEYS[region['key']][1]})` |")
    lines += [
        "",
        "Caps Lock is `LT(<window layer>, KC_ESC)`: held it selects the layer, "
        "tapped it is still Escape. Keys with no region are transparent, so "
        "they type normally.",
        "",
        "## Scripting",
        "",
        "Every region is addressable by title once Moom's AppleScript support "
        "is enabled:",
        "",
        "```applescript",
        'tell application "Moom" to run "Camera stage"',
        "```",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plist", help="exported com.manytricks.Moom plist to build on")
    parser.add_argument("-o", "--output", required=True, help="plist to write")
    parser.add_argument("-c", "--cheatsheet", help="also write a markdown cheat sheet here")
    parser.add_argument("--resolution", default="5120x2160",
                        help="screen size for the cheat sheet's pixel column")
    parser.add_argument("--keep-existing", action="store_true",
                        help="keep the hand-drawn actions instead of replacing them")
    parser.add_argument("--no-controller-keys", action="store_true",
                        help="skip the ⌥`-only single-key twins")
    parser.add_argument("--no-hyper-keys", action="store_true",
                        help="skip the global Hyper twins")
    parser.add_argument("--no-device-bits", action="store_true",
                        help="omit the left-modifier device bits from Hyper chords")
    parser.add_argument("--binary", action="store_true", help="write a binary plist")
    args = parser.parse_args()

    width, height = (int(part) for part in args.resolution.lower().split("x"))
    entries = spec.regions()

    with open(args.plist, "rb") as handle:
        prefs = plistlib.load(handle)

    generated, index_of = build_controls(
        entries,
        device_bits=not args.no_device_bits,
        controller_keys=not args.no_controller_keys,
        hyper_keys=not args.no_hyper_keys,
    )
    generated_ids = {control["Identifier"] for control in generated}
    existing = prefs.get("Custom Controls (4001)") or []
    kept = preserved(existing, generated_ids, args.keep_existing)

    controls = generated + kept  # generated first, so palette indices are stable
    prefs["Custom Controls (4001)"] = controls
    prefs["Configuration Grid: Columns"] = spec.GRID_COLUMNS
    prefs["Configuration Grid: Rows"] = spec.GRID_ROWS

    palette = {}
    for slot, region_id in zip(spec.PALETTE_SLOTS, spec.PALETTE_REGIONS):
        if region_id in index_of:
            palette[slot] = index_of[region_id]
    prefs["Palette"] = palette

    fmt = plistlib.FMT_BINARY if args.binary else plistlib.FMT_XML
    with open(args.output, "wb") as handle:
        plistlib.dump(prefs, handle, fmt=fmt, sort_keys=True)

    dropped = len(existing) - len(kept)
    print(f"{len(entries)} regions -> {len(generated)} actions "
          f"({len(kept)} existing kept, {dropped} replaced)")
    print(f"wrote {args.output}")

    if args.cheatsheet:
        Path(args.cheatsheet).write_text(cheat_sheet(entries, width, height))
        print(f"wrote {args.cheatsheet}")

    print("\nTo apply:")
    print("  osascript -e 'quit app \"Moom\"'")
    print(f"  defaults import com.manytricks.Moom {args.output}")
    print("  open -a Moom")
    return 0


if __name__ == "__main__":
    sys.exit(main())
