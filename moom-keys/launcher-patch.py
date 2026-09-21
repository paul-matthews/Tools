#!/usr/bin/env python3
"""Write the window layer into an exported Keychron Launcher keymap.

Launcher stores one raw keycode per (row, column) per layer, so a key is
located by what it types on the base layer rather than by matrix position:
`D` on layer 0 and the region key on the window layer are the same physical
key by construction, whatever the layout.

    ./launcher-inspect.py Keymap-K3_Max_RGB.json     # which layers are free?
    ./launcher-patch.py Keymap-K3_Max_RGB.json --layer 3 -o Keymap-windows.json

Places every region's chord on both hands of the window layer, `LM(layer,
MOD_LALT)` on left Option and `LT(layer, KC_ESC)` on Caps Lock, and leaves the
rest of the layer transparent so unmapped keys still type normally. The
keymap's checksum is recomputed, so Launcher accepts the file back.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import qmk  # noqa: E402
import regions as spec  # noqa: E402

CHORDS = {"HYPR": qmk.HYPER_MODS, "MEH": qmk.MEH_MODS}
# Left Option is KC_LALT on the Windows layers and Keychron's own Mac
# modifier on the macOS ones.
LEFT_OPTION = (226, qmk.KEYCHRON_LEFT_OPTION)


def checksum(keymap):
    return hashlib.md5(json.dumps(keymap, separators=(",", ":")).encode()).hexdigest()


def positions(layer):
    """Keycode -> [(row, column)] for everything on a layer."""
    found = {}
    for entry in layer:
        found.setdefault(entry["val"], []).append((entry["row"], entry["col"]))
    return found


def locate(found, candidates, what, warnings):
    """The one position typing any of `candidates` on the base layer."""
    matches = [place for value in candidates for place in found.get(value, [])]
    if not matches:
        warnings.append(f"no key found for {what}")
        return None
    if len(matches) > 1:
        warnings.append(f"{what} matched {len(matches)} keys, using the first")
    return matches[0]


def write(layer, place, value):
    for entry in layer:
        if (entry["row"], entry["col"]) == place:
            entry["val"] = value
            return True
    return False


def patch(export, layer_index, base_index, mods, blank, caps, left_option):
    layers = export["keymap"]
    if not 0 <= layer_index < len(layers):
        raise SystemExit(f"no layer {layer_index}: this keyboard has {len(layers)}")
    if layer_index == base_index:
        raise SystemExit("the window layer cannot be the base layer")

    base, window = layers[base_index], layers[layer_index]
    found = positions(base)
    warnings, placed = [], 0

    if blank:
        for entry in window:
            entry["val"] = qmk.TRANSPARENT

    for region in spec.regions():
        keycode = qmk.CODES[spec.KEYS[region["key"]][1]]
        for label in (region["key"], region["mirror"]):
            target = qmk.CODES[spec.KEYS[label][1]]
            place = locate(found, [target], f"{region['title']} ({label})", warnings)
            if place and write(window, place, qmk.chord(mods, keycode)):
                placed += 1

    if caps:
        place = locate(found, [qmk.CODES["KC_CAPS"]], "Caps Lock", warnings)
        if place:
            write(base, place, qmk.layer_tap(layer_index, qmk.CODES["KC_ESC"]))
    if left_option:
        place = locate(found, LEFT_OPTION, "left Option", warnings)
        if place:
            write(base, place, qmk.layer_mod(layer_index, qmk.MOD_LALT))

    export["MD5"] = checksum(layers)
    return placed, warnings


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("keymap", help="exported Launcher keymap JSON")
    parser.add_argument("-o", "--output", required=True, help="JSON to write")
    parser.add_argument("--layer", type=int, default=3,
                        help="layer to write the window map into (default: 3)")
    parser.add_argument("--base-layer", type=int, default=0,
                        help="layer the physical keys are identified from (default: 0)")
    parser.add_argument("--chord", default="HYPR", choices=sorted(CHORDS),
                        help="chord wrapper, matching moom-gen.py (default: HYPR)")
    parser.add_argument("--keep-layer", action="store_true",
                        help="keep whatever is already on the window layer")
    parser.add_argument("--no-caps", action="store_true", help="leave Caps Lock alone")
    parser.add_argument("--no-left-option", action="store_true",
                        help="leave left Option alone")
    args = parser.parse_args()

    with open(args.keymap) as handle:
        export = json.load(handle)
    if "keymap" not in export:
        raise SystemExit(f"{args.keymap}: no 'keymap' — is this a Launcher export?")

    placed, warnings = patch(
        export,
        layer_index=args.layer,
        base_index=args.base_layer,
        mods=CHORDS[args.chord],
        blank=not args.keep_layer,
        caps=not args.no_caps,
        left_option=not args.no_left_option,
    )

    Path(args.output).write_text(json.dumps(export, separators=(",", ":")))
    print(f"placed {placed} keys on layer {args.layer}, wrote {args.output}")
    for warning in warnings:
        print(f"  warning: {warning}")
    print("\nLoad it back with Launcher's \"Import Keymap\", wired over USB.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
