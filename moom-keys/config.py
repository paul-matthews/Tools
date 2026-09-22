"""Load and validate config.yaml, the single source of truth.

Everything else in this directory reads the config through here: the Moom
generator, the keyboard patcher and the AppleScript generator. Nothing but
this module knows how the file is shaped.

Read with PyYAML where it is installed and with miniyaml.py where it is not,
because macOS ships a Python without one and `pip install` is friction worth
avoiding. Scalars are normalised to strings so the two parsers cannot
disagree about whether `1` is a number or `no` is a boolean.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import miniyaml  # noqa: E402
from miniyaml import ConfigError  # noqa: E402  (re-exported)

try:
    import yaml
except ImportError:  # macOS ships a Python without it
    yaml = None

CONFIG = Path(__file__).resolve().parent / "config.yaml"

# Key label -> (macOS virtual key code, QMK keycode). Not configuration: these
# are what the hardware and the OS call each key.
KEYS = {
    "A": (0, "KC_A"),    "B": (11, "KC_B"),   "C": (8, "KC_C"),
    "D": (2, "KC_D"),    "E": (14, "KC_E"),   "F": (3, "KC_F"),
    "G": (5, "KC_G"),    "H": (4, "KC_H"),    "I": (34, "KC_I"),
    "J": (38, "KC_J"),   "K": (40, "KC_K"),   "L": (37, "KC_L"),
    "M": (46, "KC_M"),   "N": (45, "KC_N"),   "O": (31, "KC_O"),
    "P": (35, "KC_P"),   "Q": (12, "KC_Q"),   "R": (15, "KC_R"),
    "S": (1, "KC_S"),    "T": (17, "KC_T"),   "U": (32, "KC_U"),
    "V": (9, "KC_V"),    "W": (13, "KC_W"),   "X": (7, "KC_X"),
    "Y": (16, "KC_Y"),   "Z": (6, "KC_Z"),
    "1": (18, "KC_1"),   "2": (19, "KC_2"),   "3": (20, "KC_3"),
    "4": (21, "KC_4"),   "5": (23, "KC_5"),   "6": (22, "KC_6"),
    "7": (26, "KC_7"),   "8": (28, "KC_8"),   "9": (25, "KC_9"),
    "0": (29, "KC_0"),
    ";": (41, "KC_SCLN"), "'": (39, "KC_QUOT"), ",": (43, "KC_COMM"),
    ".": (47, "KC_DOT"),  "/": (44, "KC_SLSH"), "`": (50, "KC_GRV"),
    "Tab": (48, "KC_TAB"), "Enter": (36, "KC_ENT"), "Space": (49, "KC_SPC"),
    "Esc": (53, "KC_ESC"),
}

# How a layer can be held. Each names the key to find on the base layer and
# how it should be rebound: "tap" keeps a tap meaning, "mod" keeps a modifier
# live while the layer is active.
HELD_BY = {
    "caps": {"find": ["KC_CAPS"], "bind": "tap", "tap": "KC_ESC"},
    "tab": {"find": ["KC_TAB"], "bind": "tap", "tap": "KC_TAB"},
    # Two candidates: the macOS layers carry Keychron's own Option keycode.
    "left-option": {"find": ["KC_LALT", "KC_LOPTN"], "bind": "mod",
                    "mod": "MOD_LALT"},
    # A plain momentary layer: the key stops doing what it did. Right Command
    # is the cheapest key to spend, since shortcuts are typed with the left.
    "right-command": {"find": ["KC_RGUI", "KC_RCMMD"], "bind": "momentary"},
}


def _strings(value):
    """Every scalar as a string, so the two parsers cannot disagree."""
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
    """The parsed file, and the name of the parser that read it."""
    if yaml is None:
        return _strings(miniyaml.load(path)), "built-in subset parser"

    with open(path) as handle:
        try:
            config = _strings(yaml.safe_load(handle))
        except yaml.YAMLError as error:
            raise ConfigError(f"{path}: {error}") from error

    # A machine with PyYAML will happily read YAML the fallback cannot, and
    # the file would then fail on a machine without it. Say so here rather
    # than let it be discovered somewhere less convenient.
    note = "PyYAML"
    try:
        if _strings(miniyaml.load(path)) != config:
            note += " (the fallback parser reads this file differently)"
    except ConfigError as error:
        note += (" — WARNING: the fallback parser cannot read this file, so it "
                 f"will fail where PyYAML is not installed: {error}")
    return config, note


def _cells(pair, limit, where):
    try:
        first, last = (int(value) for value in pair)
    except (TypeError, ValueError):
        raise ConfigError(f"{where}: expected two cell numbers, got {pair!r}")
    if not 0 <= first < last <= limit:
        raise ConfigError(f"{where}: {first}-{last} is not inside 0-{limit}")
    return first, last


class Config:
    """The config, validated, with the geometry helpers that go with it."""

    def __init__(self, raw, parser):
        self.parser = parser
        screen = raw.get("screen") or {}
        grid = screen.get("grid") or {}
        size = screen.get("size") or {}
        self.columns = int(grid.get("columns", 12))
        self.rows = int(grid.get("rows", 10))
        self.width = int(size.get("width", 5120))
        self.height = int(size.get("height", 2160))

        bands = raw.get("bands") or {}
        self.column_bands = {name: _cells(pair, self.columns, f"column band {name!r}")
                             for name, pair in (bands.get("columns") or {}).items()}
        self.row_bands = {name: _cells(pair, self.rows, f"row band {name!r}")
                          for name, pair in (bands.get("rows") or {}).items()}

        self.keyboard = raw.get("keyboard") or {}
        self.regions = self._regions(raw.get("regions") or {})
        self.apps, self.modes = self._actions(raw)
        self.palette = [str(name) for name in (raw.get("palette") or [])]

        known = {region["id"] for region in self.regions}
        for name in self.palette:
            if name not in known:
                raise ConfigError(f"palette: no region with id {name!r}")

    def _regions(self, groups):
        if not groups:
            raise ConfigError("config: no regions")
        out, keys, chords, titles = [], {}, {}, set()
        for group, entries in groups.items():
            for entry in entries or []:
                where = f"region {entry.get('title', entry)!r}"
                for field in ("id", "title", "columns", "rows", "chord", "keys"):
                    if not entry.get(field):
                        raise ConfigError(f"{where}: needs a '{field}'")
                if entry["columns"] not in self.column_bands:
                    raise ConfigError(f"{where}: unknown column band "
                                      f"{entry['columns']!r}")
                if entry["rows"] not in self.row_bands:
                    raise ConfigError(f"{where}: unknown row band {entry['rows']!r}")
                if entry["title"] in titles:
                    raise ConfigError(f"{where}: title is not unique — Moom "
                                      "addresses actions by title")
                titles.add(entry["title"])

                if len(entry["keys"]) != 2:
                    raise ConfigError(f"{where}: 'keys' takes exactly two keys, "
                                      "left hand then right")
                for label in list(entry["keys"]) + [entry["chord"]]:
                    if label not in KEYS:
                        raise ConfigError(f"{where}: unknown key {label!r}")
                for label in entry["keys"]:
                    if label in keys:
                        raise ConfigError(f"{where}: key {label!r} already used "
                                          f"by {keys[label]}")
                    keys[label] = entry["title"]
                if entry["chord"] in chords:
                    raise ConfigError(f"{where}: chord {entry['chord']!r} already "
                                      f"used by {chords[entry['chord']]}")
                chords[entry["chord"]] = entry["title"]

                out.append({
                    "group": group,
                    "id": entry["id"],
                    "title": entry["title"],
                    "column_band": entry["columns"],
                    "row_band": entry["rows"],
                    "columns": self.column_bands[entry["columns"]],
                    "rows": self.row_bands[entry["rows"]],
                    "chord": entry["chord"],
                    "left": entry["keys"][0],
                    "right": entry["keys"][1],
                    "overlay": entry.get("overlay") == "true",
                })
        return out

    def _actions(self, raw):
        apps, modes, keys = [], [], {}
        bundles = {}
        for name, entry in (raw.get("apps") or {}).items():
            for field in ("key", "bundle"):
                if not (entry or {}).get(field):
                    raise ConfigError(f"app {name!r}: needs a '{field}'")
            bundles[name] = entry["bundle"]
            apps.append({"kind": "app", "key": entry["key"], "name": name,
                         "bundle": entry["bundle"]})
        for name, entry in (raw.get("modes") or {}).items():
            if not (entry or {}).get("key"):
                raise ConfigError(f"mode {name!r}: needs a 'key'")
            steps = entry.get("steps") or []
            if not steps:
                raise ConfigError(f"mode {name!r}: needs at least one step")
            modes.append({"kind": "mode", "key": entry["key"], "name": name,
                          "steps": [self._step(step, bundles, f"mode {name!r}")
                                    for step in steps]})
        for action in apps + modes:
            if action["key"] in keys:
                raise ConfigError(f"{action['name']}: key {action['key']!r} "
                                  f"already used by {keys[action['key']]}")
            keys[action["key"]] = action["name"]
        return apps, modes

    def _step(self, raw, bundles, where):
        fields = {"layout": None, "place": "region", "focus": None,
                  "shortcut": None, "url": None}
        kinds = [key for key in raw if key in fields]
        if len(kinds) != 1:
            raise ConfigError(f"{where}: a step needs exactly one of "
                              f"{', '.join(sorted(fields))}, got {sorted(raw)}")
        kind = kinds[0]
        extra = fields[kind]
        unexpected = set(raw) - {kind} - ({extra} if extra else set())
        if unexpected:
            raise ConfigError(f"{where}: '{kind}' does not take "
                              f"{', '.join(sorted(unexpected))}")
        if kind in ("place", "focus"):
            if raw[kind] not in bundles:
                raise ConfigError(f"{where}: no app named {raw[kind]!r}. Known: "
                                  f"{', '.join(sorted(bundles))}")
            if kind == "focus":
                return ("focus", bundles[raw[kind]])
            if not raw.get("region"):
                raise ConfigError(f"{where}: 'place' needs a 'region'")
            titles = {region["title"] for region in self.regions}
            if raw["region"] not in titles:
                raise ConfigError(f"{where}: no region titled {raw['region']!r}")
            return ("place", bundles[raw[kind]], raw["region"])
        return (kind, raw[kind])

    @property
    def actions(self):
        """Apps then modes, the order they appear on the actions layer."""
        return self.apps + self.modes

    def layer(self, name):
        """One of the keyboard's layers, as a validated dictionary."""
        entry = (self.keyboard or {}).get(name)
        if not entry:
            raise ConfigError(f"keyboard: no '{name}'")
        for held in entry.get("held_by") or []:
            if held not in HELD_BY:
                raise ConfigError(f"keyboard.{name}: cannot hold a layer with "
                                  f"{held!r}. Known: {', '.join(sorted(HELD_BY))}")
        return entry

    def frame(self, region):
        """(x, y, w, h) as fractions, in Moom's own coordinates.

        Moom measures y from the BOTTOM of the screen — AppKit convention, the
        menu bar comes off the top while the origin stays at the bottom — so
        the top-down row band is flipped here and nowhere else.
        """
        left, right = region["columns"]
        top, bottom = region["rows"]
        return (left / self.columns,
                (self.rows - bottom) / self.rows,
                (right - left) / self.columns,
                (bottom - top) / self.rows)

    def pixels(self, region):
        """(x, y, w, h) in pixels, y from the TOP, for human-readable output."""
        left, right = region["columns"]
        top, bottom = region["rows"]
        return (round(left / self.columns * self.width),
                round(top / self.rows * self.height),
                round((right - left) / self.columns * self.width),
                round((bottom - top) / self.rows * self.height))


def load(path=CONFIG):
    raw, parser = read(path)
    return Config(raw, parser)
