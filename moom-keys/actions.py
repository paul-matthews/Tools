"""Load and validate actions.yaml.

The window layer is spatial — position on the keyboard means position on the
screen — so it is mirrored under both hands. Actions are the opposite: the
*letter* carries the meaning, `C` for Chrome, so there is one key per action
and no mirror.

Actions use Meh chords (⌃⌥⇧) rather than Hyper, because the window layer has
already claimed Hyper on most letters. Alfred listens for them.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import miniyaml  # noqa: E402

CONFIG = Path(__file__).resolve().parent / "actions.yaml"

# Step kind -> the extra field it takes, if any.
STEP_FIELDS = {
    "layout": None,
    "place": "region",
    "focus": None,
    "shortcut": None,
    "url": None,
}


def _step(raw, apps, where):
    """One YAML step mapping -> a tuple the generator can render."""
    kinds = [key for key in raw if key in STEP_FIELDS]
    if len(kinds) != 1:
        raise miniyaml.ConfigError(
            f"{where}: a step needs exactly one of "
            f"{', '.join(sorted(STEP_FIELDS))}, got {sorted(raw)}")
    kind = kinds[0]
    value, extra = raw[kind], STEP_FIELDS[kind]

    unexpected = set(raw) - {kind} - ({extra} if extra else set())
    if unexpected:
        raise miniyaml.ConfigError(
            f"{where}: '{kind}' does not take {', '.join(sorted(unexpected))}")

    if kind in ("place", "focus"):
        if value not in apps:
            raise miniyaml.ConfigError(
                f"{where}: no app named {value!r}. Known: "
                f"{', '.join(sorted(apps))}")
        bundle = apps[value]
        if kind == "focus":
            return ("focus", bundle)
        if not raw.get("region"):
            raise miniyaml.ConfigError(f"{where}: 'place' needs a 'region'")
        return ("place", bundle, raw["region"])
    return (kind, value)


def actions(path=CONFIG):
    """Apps and modes from the config, validated, in file order."""
    config = miniyaml.load(path)
    for section in ("apps", "modes"):
        if not isinstance(config.get(section), dict):
            raise miniyaml.ConfigError(f"{path}: missing a '{section}:' section")

    bundles, out = {}, []
    for name, entry in config["apps"].items():
        for field in ("key", "bundle"):
            if not (entry or {}).get(field):
                raise miniyaml.ConfigError(f"app {name!r}: needs a '{field}'")
        bundles[name] = entry["bundle"]
        out.append({"kind": "app", "key": entry["key"], "name": name,
                    "bundle": entry["bundle"]})

    for name, entry in config["modes"].items():
        if not (entry or {}).get("key"):
            raise miniyaml.ConfigError(f"mode {name!r}: needs a 'key'")
        steps = entry.get("steps") or []
        if not steps:
            raise miniyaml.ConfigError(f"mode {name!r}: needs at least one step")
        out.append({"kind": "mode", "key": entry["key"], "name": name,
                    "steps": [_step(step, bundles, f"mode {name!r}")
                              for step in steps]})

    seen = {}
    for action in out:
        if action["key"] in seen:
            raise miniyaml.ConfigError(
                f"{action['name']}: key {action['key']!r} already used "
                f"by {seen[action['key']]}")
        seen[action["key"]] = action["name"]
    return out
