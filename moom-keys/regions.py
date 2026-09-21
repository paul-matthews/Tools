"""The region table: single source of truth for Moom actions and the keyboard.

Everything else in this directory is generated from here. A region is a
column band crossed with a row band, both expressed in whole cells of the
configuration grid so that every generated frame lands exactly on it.

Screen geometry assumed (Dell U4025QW, 5120 x 2160):

    one column cell = 426.7px      one row cell = 216px

Layout of the window layer on the keyboard — physical position mirrors
position on screen, row chooses the vertical anchor:

    number row        7           8                       0
                      narrow L    centre third            narrow R

    top row      Y    U    I    O    P        top-anchored
    home row  G  H    J    K    L    ;  '     full height
    bottom row   N    M    ,    .    /        bottom-anchored

              ⅓L   ½L  centre ½R   ⅓R         (G / ' = the two-thirds)

Space is the whole screen. Held Caps Lock selects the layer; tapped, it is
still Escape.
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

# Row bands, as [start, end) cells of 10. Vertical thirds are deliberately
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
    "G": (5, "KC_G"),     "H": (4, "KC_H"),     "J": (38, "KC_J"),
    "K": (40, "KC_K"),    "L": (37, "KC_L"),    ";": (41, "KC_SCLN"),
    "'": (39, "KC_QUOT"),
    "Y": (16, "KC_Y"),    "U": (32, "KC_U"),    "I": (34, "KC_I"),
    "O": (31, "KC_O"),    "P": (35, "KC_P"),
    "N": (45, "KC_N"),    "M": (46, "KC_M"),    ",": (43, "KC_COMM"),
    ".": (47, "KC_DOT"),  "/": (44, "KC_SLSH"),
    "7": (26, "KC_7"),    "8": (28, "KC_8"),    "0": (29, "KC_0"),
    "Space": (49, "KC_SPC"),
}

# Physical rows of the window layer, for the cheat sheet. None is a gap.
PHYSICAL_ROWS = [
    [None, "7", "8", None, "0"],
    [None, "Y", "U", "I", "O", "P"],
    ["G", "H", "J", "K", "L", ";", "'"],
    [None, "N", "M", ",", ".", "/"],
    ["Space"],
]

# id, title, column band, row band, key. Title is what AppleScript addresses
# (`tell application "Moom" to run "Centre half"`) and what the ⌥` overlay
# shows, so it has to be unique and readable.
REGIONS = [
    # group, id, title, columns, rows, key
    ("Full height", "full-screen",  "Full screen",      "full",    "full", "Space"),
    ("Full height", "third-left",   "Left third",       "third-l", "full", "H"),
    ("Full height", "half-left",    "Left half",        "half-l",  "full", "J"),
    ("Full height", "half-centre",  "Centre half",      "half-c",  "full", "K"),
    ("Full height", "half-right",   "Right half",       "half-r",  "full", "L"),
    ("Full height", "third-right",  "Right third",      "third-r", "full", ";"),
    ("Full height", "two3-left",    "Left two-thirds",  "two3-l",  "full", "G"),
    ("Full height", "two3-right",   "Right two-thirds", "two3-r",  "full", "'"),
    ("Full height", "side-left",    "Narrow left",      "side-l",  "full", "7"),
    ("Full height", "third-centre", "Centre third",     "third-c", "full", "8"),
    ("Full height", "side-right",   "Narrow right",     "side-r",  "full", "0"),

    ("Top anchored", "third-left-top",  "Left third, top",   "third-l", "upper", "Y"),
    ("Top anchored", "half-left-top",   "Left half, top",    "half-l",  "upper", "U"),
    ("Top anchored", "camera",          "Camera stage",      "half-c",  "cam",   "I"),
    ("Top anchored", "half-right-top",  "Right half, top",   "half-r",  "upper", "O"),
    ("Top anchored", "third-right-top", "Right third, top",  "third-r", "upper", "P"),

    ("Bottom anchored", "third-left-bottom",  "Left third, bottom",  "third-l", "lower", "N"),
    ("Bottom anchored", "half-left-bottom",   "Left half, bottom",   "half-l",  "lower", "M"),
    ("Bottom anchored", "below-camera",       "Below camera",        "half-c",  "stage", ","),
    ("Bottom anchored", "half-right-bottom",  "Right half, bottom",  "half-r",  "lower", "."),
    ("Bottom anchored", "third-right-bottom", "Right third, bottom", "third-r", "lower", "/"),
]

# Palette slots (Moom's pop-up over the green button), left to right. These are
# the five home-row regions, so the palette mirrors the keyboard too.
PALETTE_SLOTS = ["3-3", "4-3", "5-3", "6-3", "7-3"]
PALETTE_REGIONS = ["third-left", "half-left", "half-centre", "half-right", "third-right"]


def regions():
    """The region table as dictionaries, validated against the bands."""
    seen_keys, seen_titles, out = {}, set(), []
    for group, region_id, title, columns, rows, key in REGIONS:
        if columns not in COLUMN_BANDS:
            raise ValueError(f"{region_id}: unknown column band {columns!r}")
        if rows not in ROW_BANDS:
            raise ValueError(f"{region_id}: unknown row band {rows!r}")
        if key not in KEYS:
            raise ValueError(f"{region_id}: unknown key {key!r}")
        if key in seen_keys:
            raise ValueError(f"{region_id}: key {key!r} already used by {seen_keys[key]}")
        if title in seen_titles:
            raise ValueError(f"{region_id}: title {title!r} is not unique")
        seen_keys[key] = region_id
        seen_titles.add(title)
        out.append({
            "group": group,
            "id": region_id,
            "title": title,
            "columns": COLUMN_BANDS[columns],
            "rows": ROW_BANDS[rows],
            "column_band": columns,
            "row_band": rows,
            "key": key,
        })
    return out


def frame(region):
    """Region -> (x, y, w, h) as fractions of the screen, origin top-left."""
    left, right = region["columns"]
    top, bottom = region["rows"]
    return (
        left / GRID_COLUMNS,
        top / GRID_ROWS,
        (right - left) / GRID_COLUMNS,
        (bottom - top) / GRID_ROWS,
    )


def pixels(region, width, height):
    """Region -> (x, y, w, h) in pixels on a screen of this size."""
    x, y, w, h = frame(region)
    return round(x * width), round(y * height), round(w * width), round(h * height)
