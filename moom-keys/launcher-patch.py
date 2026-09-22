#!/usr/bin/env python3
"""Write both layers into an exported Keychron Launcher keymap.

Launcher stores one raw keycode per (row, column) per layer, so a key is
located by what it types on the base layer rather than by matrix position:
`D` on layer 0 and the region key on the window layer are the same physical
key by construction, whatever the layout.

    ./launcher-inspect.py Keymap-K3_Max_RGB.json        # which layers are free?
    ./launcher-patch.py Keymap-K3_Max_RGB.json -o Keymap-new.json
    ./launcher-inspect.py Keymap-new.json --layer 2 --layer 3

Layers, chords and the keys that hold them all come from config.yaml. Every
other key on a written layer is left transparent, so it still types normally
while the layer is held, and the keymap's checksum is recomputed so Launcher
accepts the file back.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config as config_module  # noqa: E402
import qmk  # noqa: E402

CHORD_MODS = {"hyper": qmk.HYPER_MODS, "meh": qmk.MEH_MODS}


def checksum(keymap):
    return hashlib.md5(json.dumps(keymap, separators=(",", ":")).encode()).hexdigest()


def positions(layer):
    found = {}
    for entry in layer:
        found.setdefault(entry["val"], []).append((entry["row"], entry["col"]))
    return found


def locate(found, candidates, what, warnings):
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


def hold_keys(spec, base, found, index, warnings):
    """Bind the base-layer keys that hold this layer."""
    for name in spec.get("held_by") or []:
        how = config_module.HELD_BY[name]
        candidates = [qmk.CODES[label] for label in how["find"] if label in qmk.CODES]
        place = locate(found, candidates, f"{name} (holds layer {index})", warnings)
        if not place:
            continue
        if how["bind"] == "tap":
            write(base, place, qmk.layer_tap(index, qmk.CODES[how["tap"]]))
        elif how["bind"] == "momentary":
            write(base, place, qmk.momentary(index))
        else:
            write(base, place, qmk.layer_mod(index, getattr(qmk, how["mod"])))


def patch_layer(export, spec, pairs, base_index, blank, warnings):
    """Write one layer: each (physical key, chord key) pair as a chord."""
    index = int(spec["layer"])
    layers = export["keymap"]
    if not 0 <= index < len(layers):
        raise SystemExit(f"no layer {index}: this keyboard has {len(layers)}")
    if index == base_index:
        raise SystemExit("a generated layer cannot be the base layer")

    base, layer = layers[base_index], layers[index]
    found = positions(base)
    if blank:
        for entry in layer:
            entry["val"] = qmk.TRANSPARENT

    mods = CHORD_MODS[spec.get("chord", "hyper")]
    placed = 0
    for key, chord_key, what in pairs:
        keycode = qmk.CODES[config_module.KEYS[chord_key][1]]
        target = qmk.CODES[config_module.KEYS[key][1]]
        place = locate(found, [target], f"{what} ({key})", warnings)
        if place and write(layer, place, qmk.chord(mods, keycode)):
            placed += 1

    hold_keys(spec, base, found, index, warnings)
    return index, placed


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("keymap", help="exported Launcher keymap JSON")
    parser.add_argument("-o", "--output", required=True, help="JSON to write")
    parser.add_argument("--keep-layer", action="store_true",
                        help="keep whatever is already on the written layers")
    args = parser.parse_args()

    cfg = config_module.load()
    print(f"read {config_module.CONFIG.name} with {cfg.parser}\n")

    with open(args.keymap) as handle:
        export = json.load(handle)
    if "keymap" not in export:
        raise SystemExit(f"{args.keymap}: no 'keymap' — is this a Launcher export?")

    base_index = int(cfg.keyboard.get("base_layer", 0))
    warnings = []

    windows = [(key, region["chord"], region["title"])
               for region in cfg.regions
               for key in (region["left"], region["right"])]
    index, placed = patch_layer(export, cfg.layer("window_layer"), windows,
                                base_index, not args.keep_layer, warnings)
    print(f"layer {index}: {placed} keys (windows)")

    actions = [(action["key"], action["key"], action["name"])
               for action in cfg.actions]
    index, placed = patch_layer(export, cfg.layer("actions_layer"), actions,
                                base_index, not args.keep_layer, warnings)
    print(f"layer {index}: {placed} keys (actions)")

    export["MD5"] = checksum(export["keymap"])
    Path(args.output).write_text(json.dumps(export, separators=(",", ":")))
    print(f"\nwrote {args.output}")
    for warning in warnings:
        print(f"  warning: {warning}")
    print('\nLoad it back with Launcher\'s "Import Keymap", wired over USB.')
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
