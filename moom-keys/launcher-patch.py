#!/usr/bin/env python3
"""Write the window layer into an exported Keychron Launcher / VIA keymap.

Launcher's "Save Current Layout" produces a JSON file holding one flat list of
keycodes per layer. The lists are in the keyboard's own key order, which we do
not need to know: a key is located by what it types on the base layer, so
`KC_D` on layer 0 and the region key on the window layer are the same physical
key by construction.

    ./launcher-patch.py k3max.json --layer 3 -o k3max-windows.json

Writes each region's chord onto both hands of the window layer, `LM(layer,
MOD_LALT)` onto left Option and `LT(layer, KC_ESC)` onto Caps Lock, and leaves
every other key on the layer transparent so it still types normally.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import regions as spec  # noqa: E402

TRANSPARENT = "KC_TRNS"
# Launcher and VIA both use KC_LALT for left Option on Mac layouts, but
# Keychron's own exports have been seen with the Mac-flavoured alias.
LEFT_OPTION = ("KC_LALT", "KC_LOPT")
CAPS_LOCK = ("KC_CAPS", "KC_CAPS_LOCK")


def load(path):
    with open(path) as handle:
        keymap = json.load(handle)
    if "layers" not in keymap:
        raise SystemExit(f"{path}: no 'layers' key — is this a Launcher export?")
    return keymap


def find(layer, candidates, what, warnings):
    """Index of the first key on the base layer typing one of `candidates`."""
    matches = [index for index, code in enumerate(layer) if code in candidates]
    if not matches:
        warnings.append(f"no key found for {what} ({', '.join(candidates)})")
        return None
    if len(matches) > 1:
        warnings.append(f"{what} matched {len(matches)} keys, using the first")
    return matches[0]


def patch(keymap, layer_index, base_index, chord, blank, caps, left_option):
    base = keymap["layers"][base_index]
    while len(keymap["layers"]) <= layer_index:
        keymap["layers"].append([TRANSPARENT] * len(base))

    window = keymap["layers"][layer_index]
    if len(window) != len(base):
        raise SystemExit("layer lengths differ — export looks inconsistent")
    if blank:
        window = [TRANSPARENT] * len(base)

    warnings, placed = [], 0
    for region in spec.regions():
        _, keycode = spec.KEYS[region["key"]]
        for label in (region["key"], region["mirror"]):
            _, target = spec.KEYS[label]
            index = find(base, {target}, f"{region['title']} ({label})", warnings)
            if index is not None:
                window[index] = f"{chord}({keycode})"
                placed += 1

    keymap["layers"][layer_index] = window

    if caps:
        index = find(base, set(CAPS_LOCK), "Caps Lock", warnings)
        if index is not None:
            base[index] = f"LT({layer_index},KC_ESC)"
    if left_option:
        index = find(base, set(LEFT_OPTION), "left Option", warnings)
        if index is not None:
            base[index] = f"LM({layer_index},MOD_LALT)"

    return placed, warnings


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("keymap", help="exported Launcher / VIA layout JSON")
    parser.add_argument("-o", "--output", required=True, help="JSON to write")
    parser.add_argument("--layer", type=int, default=3,
                        help="layer to write the window map into (default: 3)")
    parser.add_argument("--base-layer", type=int, default=0,
                        help="layer the physical keys are identified from (default: 0)")
    parser.add_argument("--chord", default="HYPR", choices=["HYPR", "MEH"],
                        help="QMK chord wrapper, matching moom-gen.py (default: HYPR)")
    parser.add_argument("--keep-layer", action="store_true",
                        help="keep whatever is already on the window layer")
    parser.add_argument("--no-caps", action="store_true",
                        help="leave Caps Lock alone")
    parser.add_argument("--no-left-option", action="store_true",
                        help="leave left Option alone")
    args = parser.parse_args()

    keymap = load(args.keymap)
    if args.base_layer >= len(keymap["layers"]):
        raise SystemExit(f"no layer {args.base_layer} in this export")

    placed, warnings = patch(
        keymap,
        layer_index=args.layer,
        base_index=args.base_layer,
        chord=args.chord,
        blank=not args.keep_layer,
        caps=not args.no_caps,
        left_option=not args.no_left_option,
    )

    Path(args.output).write_text(json.dumps(keymap, indent=2))
    print(f"placed {placed} keys on layer {args.layer}, wrote {args.output}")
    for warning in warnings:
        print(f"  warning: {warning}")
    print("\nLoad it back with Launcher's \"Load Saved Layout\", wired over USB.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
