"""The region table: single source of truth for Moom actions and the keyboard.

Everything else in this directory is generated from here. A region is a
column band crossed with a row band, both expressed in whole cells of the
configuration grid so that every generated frame lands exactly on it.

Screen geometry assumed (Dell U4025QW, 5120 x 2160):

    one column cell = 426.7px      one row cell = 216px

The window layer carries the same map twice, once under each hand, so it can
be driven one-handed with the other hand on the mouse. Physical position
mirrors position on screen; the row chooses the vertical anchor:

    left hand                        right hand

    1  2  3  4  5                    6  7  8  9  0     width variants
    Q  W  E  R  T                    Y  U  I  O  P     top-anchored
    A  S  D  F  G                    H  J  K  L  ;     full height
    Z  X  C  V  B                    N  M  ,  .  /     bottom-anchored
    Tab  full screen                 '                 full screen

` is left unmapped on purpose: held left Option, it still sends ⌥` and
opens Moom's keyboard controller.

       ⅓L ½L ½C ½R ⅓R                   ⅓L ½L ½C ½R ⅓R

Both keys of a pair send the same chord, so Moom sees one action either way.

The chord a region uses is chosen separately from the keys that send it, and
is always a letter or a digit. Punctuation under Hyper is where macOS keeps
system shortcuts — ⌃⌥⌘, and ⌃⌥⌘. adjust contrast, ⇧⌘/ opens Help — and
those chords never reached Moom. So the bottom row's keys send the chords of
the letters beneath the left hand, and nothing is bound to ⌃⌥⇧⌘, at all.

"""

# The configuration grid every band is expressed in. Matches Moom's own
# "Configuration Grid" setting, so the mouse grid can reproduce any region.
GRID_COLUMNS = 12
GRID_ROWS = 10

# Column bands, as [start, end) cells of 12.
COLUMN_BANDS = {
    "full":     (0, 12),   # 5120px
    "third-l":  (0, 4),    # 1707px
    "third-c":  (4, 8),
    "third-r":  (8, 12),
    "half-l":   (0, 6),    # 2560px
    "half-c":   (3, 9),    # centred half — the workhorse
    "half-r":   (6, 12),
    "two3-l":   (0, 8),    # 3413px
    "two3-r":   (4, 12),
    "side-l":   (0, 3),    # 1280px — the "small" side windows
    "side-r":   (9, 12),
}

# Row bands, as [start, end) cells of 10 counted DOWN FROM THE TOP, which is
# how people describe them. Moom stores frames in AppKit coordinates with the
# origin at the bottom left, so frame() flips them. Vertical thirds are
# deliberately
# 30/70 rather than 33/67: a 10-row grid cannot express thirds, and 72px of
# difference on a 2160px screen is not worth an off-grid frame.
ROW_BANDS = {
    "full":   (0, 10),   # 2160px
    "cam":    (0, 6),    # top 60%, 1296px — window sits under the webcam
    "stage":  (5, 10),   # bottom 50%, 1080px — overlaps `cam` by one cell
    "upper":  (0, 7),    # top 70%, 1512px
    "lower":  (3, 10),   # bottom 70%
}

# Key labels -> (macOS virtual key code, QMK keycode). The macOS code goes in
# the Moom plist; the QMK one goes on the keyboard layer, wrapped in HYPR().
KEYS = {
    # right-hand block
    "Y": (16, "KC_Y"), "U": (32, "KC_U"), "I": (34, "KC_I"),
    "O": (31, "KC_O"), "P": (35, "KC_P"),
    "H": (4, "KC_H"),  "J": (38, "KC_J"), "K": (40, "KC_K"),
    "L": (37, "KC_L"), ";": (41, "KC_SCLN"),
    "N": (45, "KC_N"), "M": (46, "KC_M"), ",": (43, "KC_COMM"),
    ".": (47, "KC_DOT"), "/": (44, "KC_SLSH"),
    "6": (22, "KC_6"), "7": (26, "KC_7"), "8": (28, "KC_8"),
    "9": (25, "KC_9"), "0": (29, "KC_0"), "'": (39, "KC_QUOT"),
    # left-hand block
    "Q": (12, "KC_Q"), "W": (13, "KC_W"), "E": (14, "KC_E"),
    "R": (15, "KC_R"), "T": (17, "KC_T"),
    "A": (0, "KC_A"),  "S": (1, "KC_S"),  "D": (2, "KC_D"),
    "F": (3, "KC_F"),  "G": (5, "KC_G"),
    "Z": (6, "KC_Z"),  "X": (7, "KC_X"),  "C": (8, "KC_C"),
    "V": (9, "KC_V"),  "B": (11, "KC_B"),
    "1": (18, "KC_1"), "2": (19, "KC_2"), "3": (20, "KC_3"),
    "4": (21, "KC_4"), "5": (23, "KC_5"), "Tab": (48, "KC_TAB"),
    # Full screen's chord: Tab would collide with the app switcher under
    # Command, which Hyper contains, so the Tab key sends Return's chord.
    "Enter": (36, "KC_ENT"),
}

# The window layer, one block per hand, for the cheat sheet. None is a gap.
LAYOUTS = {
    "Right hand": [
        ["6", "7", "8", "9", "0"],
        ["Y", "U", "I", "O", "P"],
        ["H", "J", "K", "L", ";"],
        ["N", "M", ",", ".", "/"],
        ["'"],
    ],
    "Left hand": [
        ["1", "2", "3", "4", "5"],
        ["Q", "W", "E", "R", "T"],
        ["A", "S", "D", "F", "G"],
        ["Z", "X", "C", "V", "B"],
        ["Tab"],
    ],
}

# id, title, column band, row band, key. Title is what AppleScript addresses
# (`tell application "Moom" to run "Centre half"`) and what the ⌥` overlay
# shows, so it has to be unique and readable.
REGIONS = [
    # group, id, title, columns, rows, chord, left key, right key
    ("Full height", "full-screen",  "Full screen",      "full",    "full", "Enter", "Tab", "'"),
    ("Full height", "third-left",   "Left third",       "third-l", "full", "A", "A", "H"),
    ("Full height", "half-left",    "Left half",        "half-l",  "full", "S", "S", "J"),
    ("Full height", "half-centre",  "Centre half",      "half-c",  "full", "D", "D", "K"),
    ("Full height", "half-right",   "Right half",       "half-r",  "full", "F", "F", "L"),
    ("Full height", "third-right",  "Right third",      "third-r", "full", "G", "G", ";"),

    ("Width variants", "side-left",    "Narrow left",      "side-l",  "full", "1", "1", "6"),
    ("Width variants", "two3-left",    "Left two-thirds",  "two3-l",  "full", "2", "2", "7"),
    ("Width variants", "third-centre", "Centre third",     "third-c", "full", "3", "3", "8"),
    ("Width variants", "two3-right",   "Right two-thirds", "two3-r",  "full", "4", "4", "9"),
    ("Width variants", "side-right",   "Narrow right",     "side-r",  "full", "5", "5", "0"),

    ("Top anchored", "third-left-top",  "Left third, top",  "third-l", "upper", "Q", "Q", "Y"),
    ("Top anchored", "half-left-top",   "Left half, top",   "half-l",  "upper", "W", "W", "U"),
    ("Top anchored", "camera",          "Camera stage",     "half-c",  "cam",   "E", "E", "I"),
    ("Top anchored", "half-right-top",  "Right half, top",  "half-r",  "upper", "R", "R", "O"),
    ("Top anchored", "third-right-top", "Right third, top", "third-r", "upper", "T", "T", "P"),

    ("Bottom anchored", "third-left-bottom",  "Left third, bottom",  "third-l", "lower", "Z", "Z", "N"),
    ("Bottom anchored", "half-left-bottom",   "Left half, bottom",   "half-l",  "lower", "X", "X", "M"),
    ("Bottom anchored", "below-camera",       "Below camera",        "half-c",  "stage", "C", "C", ","),
    ("Bottom anchored", "half-right-bottom",  "Right half, bottom",  "half-r",  "lower", "V", "V", "."),
    ("Bottom anchored", "third-right-bottom", "Right third, bottom", "third-r", "lower", "B", "B", "/"),
]

# Palette slots (Moom's pop-up over the green button), left to right. These are
# the five home-row regions, so the palette mirrors the keyboard too.
PALETTE_SLOTS = ["3-3", "4-3", "5-3", "6-3", "7-3"]
PALETTE_REGIONS = ["third-left", "half-left", "half-centre", "half-right", "third-right"]


def regions():
    """The region table as dictionaries, validated against the bands."""
    seen_keys, seen_chords, seen_titles, out = {}, set(), set(), []
    for group, region_id, title, columns, rows, chord, left, right in REGIONS:
        if columns not in COLUMN_BANDS:
            raise ValueError(f"{region_id}: unknown column band {columns!r}")
        if rows not in ROW_BANDS:
            raise ValueError(f"{region_id}: unknown row band {rows!r}")
        if title in seen_titles:
            raise ValueError(f"{region_id}: title {title!r} is not unique")
        if chord not in KEYS:
            raise ValueError(f"{region_id}: unknown chord key {chord!r}")
        if KEYS[chord][0] in seen_chords:
            raise ValueError(f"{region_id}: chord {chord!r} already bound")
        for label in (left, right):
            if label not in KEYS:
                raise ValueError(f"{region_id}: unknown key {label!r}")
            if label in seen_keys:
                raise ValueError(f"{region_id}: key {label!r} already used "
                                 f"by {seen_keys[label]}")
            seen_keys[label] = region_id
        seen_chords.add(KEYS[chord][0])
        seen_titles.add(title)
        out.append({
            "group": group,
            "id": region_id,
            "title": title,
            "columns": COLUMN_BANDS[columns],
            "rows": ROW_BANDS[rows],
            "column_band": columns,
            "row_band": rows,
            "chord": chord,   # the key Moom binds, always a letter or digit
            "left": left,     # the two physical keys that send that chord
            "right": right,
        })
    return out


def frame(region):
    """Region -> (x, y, w, h) as fractions, in Moom's own coordinates.

    Moom measures y from the BOTTOM of the screen (AppKit convention: the
    menu bar comes off the top while the origin stays at the bottom), so the
    top-down row band is flipped here and nowhere else.
    """
    left, right = region["columns"]
    top, bottom = region["rows"]
    return (
        left / GRID_COLUMNS,
        (GRID_ROWS - bottom) / GRID_ROWS,
        (right - left) / GRID_COLUMNS,
        (bottom - top) / GRID_ROWS,
    )


def pixels(region, width, height):
    """Region -> (x, y, w, h) in pixels, y from the TOP, for human-readable output."""
    left, right = region["columns"]
    top, bottom = region["rows"]
    return (
        round(left / GRID_COLUMNS * width),
        round(top / GRID_ROWS * height),
        round((right - left) / GRID_COLUMNS * width),
        round((bottom - top) / GRID_ROWS * height),
    )
