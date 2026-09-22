"""QMK keycode numbers, names and the encodings Launcher exports use.

Keychron Launcher stores raw numeric keycodes, so both reading and writing a
keymap means knowing the quantum ranges. Only the parts needed here are
modelled; anything unrecognised is rendered by range rather than named.
"""

# Basic keycodes (USB HID usage IDs, as QMK numbers them).
BASIC = {
    0: "NO", 1: "TRNS",
    40: "Enter", 41: "Esc", 42: "Bspc", 43: "Tab", 44: "Space", 45: "-",
    46: "=", 47: "[", 48: "]", 49: "\\", 50: "NUHS", 51: ";", 52: "'",
    53: "`", 54: ",", 55: ".", 56: "/", 57: "Caps",
    70: "PrtSc", 71: "ScrLk", 72: "Pause", 73: "Ins",
    74: "Home", 75: "PgUp", 76: "Del", 77: "End", 78: "PgDn",
    79: "Right", 80: "Left", 81: "Down", 82: "Up",
    224: "LCtl", 225: "LSft", 226: "LAlt", 227: "LGui",
    228: "RCtl", 229: "RSft", 230: "RAlt", 231: "RGui",
}
for _i in range(26):
    BASIC[4 + _i] = chr(ord("A") + _i)
for _i, _digit in enumerate("1234567890"):
    BASIC[30 + _i] = _digit
for _i in range(12):
    BASIC[58 + _i] = f"F{_i + 1}"

# Quantum ranges.
MODIFIED = 0x0100        # modifier(s) applied to a basic keycode
LAYER_TAP = 0x4000       # LT(layer, kc)
LAYER_MOD = 0x5000       # LM(layer, mod)
MOMENTARY = 0x5220       # MO(layer)
LIGHTING = 0x7800        # RGB and backlight controls
KEYBOARD = 0x7E00        # vendor keycodes — Keychron's Mac modifiers live here

# Modifier bits, as used by both MODIFIED and LM.
MOD_LCTL, MOD_LSFT, MOD_LALT, MOD_LGUI = 0x01, 0x02, 0x04, 0x08
HYPER_MODS = MOD_LCTL | MOD_LSFT | MOD_LALT | MOD_LGUI
MEH_MODS = MOD_LCTL | MOD_LSFT | MOD_LALT

# Keychron's Mac-flavoured modifiers, which stand in for the standard ones on
# the macOS layers: left Option is KB0 rather than KC_LALT.
KEYCHRON_LEFT_OPTION = KEYBOARD + 0
KEYCHRON_LEFT_COMMAND = KEYBOARD + 2


# QMK keycode names -> numbers, for the subset regions.py can use.
CODES = {f"KC_{chr(ord('A') + i)}": 4 + i for i in range(26)}
CODES.update({f"KC_{d}": 30 + i for i, d in enumerate("1234567890")})
CODES.update({
    "KC_ENT": 40, "KC_ESC": 41, "KC_BSPC": 42, "KC_TAB": 43, "KC_SPC": 44,
    "KC_MINS": 45, "KC_EQL": 46, "KC_LBRC": 47, "KC_RBRC": 48, "KC_BSLS": 49,
    "KC_SCLN": 51, "KC_QUOT": 52, "KC_GRV": 53, "KC_COMM": 54, "KC_DOT": 55,
    "KC_SLSH": 56, "KC_CAPS": 57,
    "KC_LCTL": 224, "KC_LSFT": 225, "KC_LALT": 226, "KC_LGUI": 227,
    "KC_RCTL": 228, "KC_RSFT": 229, "KC_RALT": 230, "KC_RGUI": 231,
    # Keychron's Mac-flavoured modifiers, which stand in for the standard ones
    # on the macOS layers: left Option is KB0, not KC_LALT.
    "KC_LOPTN": KEYBOARD + 0, "KC_LCMMD": KEYBOARD + 2,
})

TRANSPARENT = 1

def chord(mods, keycode):
    """A basic keycode with modifiers held, e.g. HYPR(KC_K)."""
    return (mods << 8) | keycode


def layer_tap(layer, keycode):
    """LT(layer, kc): hold for the layer, tap for the key."""
    return LAYER_TAP | ((layer & 0xF) << 8) | (keycode & 0xFF)


def layer_mod(layer, mods):
    """LM(layer, mod): hold for the layer with modifiers applied."""
    return LAYER_MOD | ((layer & 0xF) << 5) | (mods & 0x1F)


def momentary(layer):
    return MOMENTARY | (layer & 0xF)


def describe(value):
    """Best-effort name for a raw keycode, for inspection output."""
    if value in BASIC:
        return BASIC[value]
    if MODIFIED <= value <= 0x1FFF:
        mods, base = (value >> 8) & 0x1F, value & 0xFF
        names = "".join(glyph for bit, glyph in
                        ((MOD_LCTL, "⌃"), (MOD_LSFT, "⇧"),
                         (MOD_LALT, "⌥"), (MOD_LGUI, "⌘")) if mods & bit)
        side = "R" if mods & 0x10 else ""
        return f"{side}{names}{BASIC.get(base, base)}"
    if LAYER_TAP <= value <= 0x4FFF:
        return f"LT({(value >> 8) & 0xF},{BASIC.get(value & 0xFF, value & 0xFF)})"
    if LAYER_MOD <= value <= 0x51FF:
        return f"LM({(value >> 5) & 0xF},{value & 0x1F:#04x})"
    for base, label in ((0x5200, "TO"), (MOMENTARY, "MO"), (0x5240, "DF"),
                        (0x5260, "TG"), (0x5280, "OSL"), (0x52C0, "TT")):
        if base <= value < base + 0x20:
            return f"{label}({value - base})"
    if 0x7700 <= value < 0x7800:
        return f"MACRO{value - 0x7700}"
    if LIGHTING <= value < 0x7900:
        return f"LIGHT{value - LIGHTING}"
    if KEYBOARD <= value < 0x7F00:
        return f"KB{value - KEYBOARD}"
    return str(value)
