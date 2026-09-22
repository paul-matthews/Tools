#!/usr/bin/env python3
"""Inspect a Moom preferences plist: grid, hotkeys and every custom action.

Moom stores its custom actions in ~/Library/Preferences/com.manytricks.Moom.plist
as opaque relative frames. This prints them as grid coordinates on the
configuration grid, with an ASCII map of each region, so a keyboard strategy
can be designed against what is actually configured.

    defaults export com.manytricks.Moom ~/Desktop/Moom.plist
    ./moom-inspect.py ~/Desktop/Moom.plist

Pure standard library; plistlib reads both binary and XML plists.
"""

from __future__ import annotations

import argparse
import plistlib
import re
import sys

# Moom's "Action" integers, as observed in exported preferences.
ACTIONS = {
    -101: "section header",
    0: "separator",
    19: "move & zoom",
    1001: "saved layout (snapshot)",
}

# macOS virtual key codes (ANSI). Enough to name anything usable as a hotkey.
KEY_CODES = {
    0: "A", 1: "S", 2: "D", 3: "F", 4: "H", 5: "G", 6: "Z", 7: "X", 8: "C",
    9: "V", 11: "B", 12: "Q", 13: "W", 14: "E", 15: "R", 16: "Y", 17: "T",
    18: "1", 19: "2", 20: "3", 21: "4", 22: "6", 23: "5", 24: "=", 25: "9",
    26: "7", 27: "-", 28: "8", 29: "0", 30: "]", 31: "O", 32: "U", 33: "[",
    34: "I", 35: "P", 36: "Return", 37: "L", 38: "J", 39: "'", 40: "K",
    41: ";", 42: "\\", 43: ",", 44: "/", 45: "N", 46: "M", 47: ".",
    48: "Tab", 49: "Space", 50: "`", 51: "Delete", 53: "Escape",
    65: "Keypad.", 67: "Keypad*", 69: "Keypad+", 71: "KeypadClear",
    75: "Keypad/", 76: "KeypadEnter", 78: "Keypad-", 81: "Keypad=",
    82: "Keypad0", 83: "Keypad1", 84: "Keypad2", 85: "Keypad3",
    86: "Keypad4", 87: "Keypad5", 88: "Keypad6", 89: "Keypad7",
    91: "Keypad8", 92: "Keypad9",
    96: "F5", 97: "F6", 98: "F7", 99: "F3", 100: "F8", 101: "F9", 103: "F11",
    105: "F13", 107: "F14", 109: "F10", 111: "F12", 113: "F15", 114: "Help",
    115: "Home", 116: "PageUp", 117: "ForwardDelete", 118: "F4", 119: "End",
    120: "F2", 121: "PageDown", 122: "F1", 123: "Left", 124: "Right",
    125: "Down", 126: "Up",
}

# NSEvent device-independent modifier bits. Moom always sets the low 0x100 bit,
# so a hotkey with no bits above 0x10000 is a single-key (controller-only) one.
MODIFIERS = (
    (1 << 16, "Caps"),
    (1 << 17, "Shift"),
    (1 << 18, "Control"),
    (1 << 19, "Option"),
    (1 << 20, "Command"),
    (1 << 23, "Fn"),
)
MODIFIER_MASK = sum(bit for bit, _ in MODIFIERS)

FRAME_RE = re.compile(
    r"\{\{\s*([-0-9.e]+)\s*,\s*([-0-9.e]+)\s*\}\s*,\s*"
    r"\{\s*([-0-9.e]+)\s*,\s*([-0-9.e]+)\s*\}\}"
)


def parse_frame(text):
    """'{{x, y}, {w, h}}' -> (x, y, w, h) as floats, or None."""
    match = FRAME_RE.match(text or "")
    return tuple(float(g) for g in match.groups()) if match else None


def describe_hotkey(hotkey):
    """Render a Moom hot key dict as (label, scope)."""
    if not hotkey:
        return "—", "none"
    flags = int(hotkey.get("Modifier Flags", 0))
    names = [name for bit, name in MODIFIERS if flags & bit]
    key = KEY_CODES.get(hotkey.get("Key Code"), f"key#{hotkey.get('Key Code')}")
    label = "+".join(names + [key])
    scope = "GLOBAL" if flags & MODIFIER_MASK else "controller-only"
    return label, scope


def to_cells(value, divisions):
    """Fraction -> grid cell index, plus whether it lands exactly on the grid."""
    exact = value * divisions
    rounded = round(exact)
    return rounded, abs(exact - rounded) < 1e-6


def ascii_map(frame, columns, rows):
    """Draw the region on the configuration grid, top row first."""
    x, y, w, h = frame
    left, _ = to_cells(x, columns)
    right, _ = to_cells(x + w, columns)
    top, bottom = rows_from_top(y, h, rows)
    lines = []
    for row in range(rows):
        cells = "".join(
            "#" if left <= col < right and top <= row < bottom else "."
            for col in range(columns)
        )
        lines.append(f"    |{cells}|")
    return lines, (left, top, right, bottom)


def rows_from_top(y, h, rows):
    """Moom's y is measured from the bottom; report rows counting from the top."""
    return round((1 - (y + h)) * rows), round((1 - y) * rows)


def grid_for(control, columns, rows):
    """Per-action configuration grid override, if it has one."""
    grid = control.get("Configuration Grid") or {}
    return (
        int(grid.get("Configuration Grid: Columns", columns)),
        int(grid.get("Configuration Grid: Rows", rows)),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plist", help="path to an exported com.manytricks.Moom plist")
    parser.add_argument("--no-map", action="store_true", help="omit the ASCII grid maps")
    args = parser.parse_args()

    with open(args.plist, "rb") as handle:
        prefs = plistlib.load(handle)

    columns = int(prefs.get("Configuration Grid: Columns", 12))
    rows = int(prefs.get("Configuration Grid: Rows", 10))
    print(f"Configuration grid : {columns} x {rows}")
    print(f"Grid spacing       : {prefs.get('Grid Spacing')} (gap {prefs.get('Grid Spacing: Gap')})")
    print(f"Snap               : {prefs.get('Snap')}")
    print(f"Dismiss after move : {prefs.get('Dismiss After Moving')}")

    controller, scope = describe_hotkey(prefs.get("Keyboard Controls"))
    print(f"Keyboard controller: {controller} ({scope})")

    controls = prefs.get("Custom Controls (4001)") or prefs.get("Custom Controls") or []
    print(f"Custom actions     : {len(controls)}")

    # Layouts are recorded by hand and cannot be regenerated, so say plainly
    # whether this file still has them.
    layouts = [control for key in ("Custom Controls (4001)", "Custom Controls")
               for control in (prefs.get(key) or [])
               if control.get("Snapshot") or control.get("Action") == 1001]
    if layouts:
        print("Saved layouts      : " + ", ".join(
            f'{control.get("Title") or "(untitled)"} '
            f'({len(control.get("Snapshot") or [])} windows)' for control in layouts))
    else:
        print("Saved layouts      : none")
    print()

    seen = {}
    for index, control in enumerate(controls):
        action = control.get("Action")
        kind = ACTIONS.get(action, f"action {action}")
        title = control.get("Title")
        hotkey, hotkey_scope = describe_hotkey(control.get("Hot Key"))

        if action == -101:
            print(f"[{index:2}] ── {title} ──")
            continue
        if action == 0:
            print(f"[{index:2}] ──────────")
            continue

        frame = parse_frame(control.get("Relative Frame", ""))
        header = f"[{index:2}] {hotkey:<18} {kind}"
        if title:
            header += f"  “{title}”"
        print(header)

        if frame is None:
            print("     (no relative frame)")
            print()
            continue

        cols, rws = grid_for(control, columns, rows)
        if (cols, rws) != (columns, rows):
            print(f"     authored on a {cols} x {rws} grid")

        x, y, w, h = frame
        left, left_ok = to_cells(x, columns)
        right, right_ok = to_cells(x + w, columns)
        _, top_ok = to_cells(y, rows)
        _, bottom_ok = to_cells(y + h, rows)
        top, bottom = rows_from_top(y, h, rows)
        aligned = all((left_ok, top_ok, right_ok, bottom_ok))
        print(f"     x {x:.4f} y {y:.4f} w {w:.4f} h {h:.4f}")
        print(f"     cells columns {left}-{right} of {columns}, "
              f"rows {top}-{bottom} of {rows} from the top"
              f"{'' if aligned else '  (OFF-GRID)'}")

        # Twins of one region (single key + global chord) are expected;
        # only flag repeats within the same hotkey scope.
        key = (hotkey_scope, round(x, 4), round(y, 4), round(w, 4), round(h, 4))
        if key in seen:
            print(f"     duplicate of [{seen[key]}]")
        else:
            seen[key] = index

        if not args.no_map:
            lines, _ = ascii_map(frame, columns, rows)
            print("\n".join(lines))
        print()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # piping into head and friends
        sys.exit(0)
