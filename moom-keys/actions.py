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

try:
    import yaml
except ImportError:  # macOS ships a Python without it
    yaml = None

CONFIG = Path(__file__).resolve().parent / "actions.yaml"


def _strings(value):
    """Every scalar as a string.

    PyYAML types scalars — `1` becomes an int, `no` becomes False — while the
    fallback parser returns strings. Normalising here means the two parsers
    cannot disagree about what the file says.
    """
    if isinstance(value, dict):
        return {str(key): _strings(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_strings(item) for item in value]
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def read(path=CONFIG):
    """Parse the config with PyYAML if it is installed, else the subset parser.

    Returns the parsed file and the name of the parser that read it, so a
    caller can say which one ran.
    """
    if yaml is None:
        return _strings(miniyaml.load(path)), "built-in subset parser"

    with open(path) as handle:
        try:
            config = _strings(yaml.safe_load(handle))
        except yaml.YAMLError as error:
            raise miniyaml.ConfigError(f"{path}: {error}") from error

    # A machine with PyYAML will happily read YAML the fallback parser cannot,
    # and the file would then fail on a machine without it. Say so here rather
    # than let it be discovered somewhere less convenient.
    note = "PyYAML"
    try:
        if _strings(miniyaml.load(path)) != config:
            note += " (the fallback parser reads this file differently)"
    except miniyaml.ConfigError as error:
        note += (f" — WARNING: the fallback parser cannot read this file, so it "
                 f"will fail where PyYAML is not installed: {error}")
    return config, note

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
    config, _parser = read(path)
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
