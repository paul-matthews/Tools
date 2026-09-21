#!/usr/bin/env python3
"""Inspect a Keychron Launcher keymap export: every layer, decoded.

Launcher's "Export Keymap" writes raw numeric keycodes per (row, column), so
the file is unreadable as it stands. This prints each layer as a grid and
reports which layers are reachable from which, so it is clear which one is
free to take a new layer.

    ./launcher-inspect.py Keymap-K3_Max_RGB.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import qmk  # noqa: E402


def load(path):
    with open(path) as handle:
        export = json.load(handle)
    if "keymap" not in export:
        raise SystemExit(f"{path}: no 'keymap' — is this a Launcher export?")
    return export


def checksum(export):
    """Launcher signs the keymap array as compact JSON."""
    return hashlib.md5(
        json.dumps(export["keymap"], separators=(",", ":")).encode()).hexdigest()


def grid(layer):
    return {(entry["row"], entry["col"]): entry["val"] for entry in layer}


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("keymap", help="exported Launcher keymap JSON")
    parser.add_argument("--layer", type=int, action="append",
                        help="only show this layer (repeatable)")
    args = parser.parse_args()

    export = load(args.keymap)
    stored, computed = export.get("MD5"), checksum(export)
    print(f"device id : {export.get('id')}  version {export.get('version')}")
    print(f"checksum  : {stored} {'ok' if stored == computed else f'STALE (now {computed})'}")
    print(f"layers    : {len(export['keymap'])}")

    reachable = {}
    for index, layer in enumerate(export["keymap"]):
        for entry in layer:
            value = entry["val"]
            for low, high in ((0x5200, 0x52DF), (qmk.LAYER_TAP, 0x4FFF),
                              (qmk.LAYER_MOD, 0x51FF)):
                if low <= value <= high:
                    target = ((value >> 8) & 0xF) if value < 0x5000 else (
                        ((value >> 5) & 0xF) if value < 0x5200 else value & 0xF)
                    reachable.setdefault(target, set()).add(index)
    for target in sorted(reachable):
        sources = ", ".join(str(source) for source in sorted(reachable[target]))
        print(f"  layer {target} reachable from layer(s) {sources}")
    free = [index for index in range(len(export["keymap"])) if index not in reachable]
    if free:
        print(f"  layer(s) {', '.join(str(index) for index in free)} "
              "not reachable from any other layer")

    for index, layer in enumerate(export["keymap"]):
        if args.layer and index not in args.layer:
            continue
        print(f"\n--- layer {index}")
        cells = grid(layer)
        rows = sorted({row for row, _ in cells})
        for row in rows:
            columns = sorted(column for r, column in cells if r == row)
            names = [qmk.describe(cells[(row, column)]) for column in columns]
            if set(names) <= {"NO"}:
                continue
            print(f"  r{row}: " + " ".join(name.ljust(7) for name in names).rstrip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
