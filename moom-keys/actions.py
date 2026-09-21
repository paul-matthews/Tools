"""The actions table: apps to focus and modes to enter, one key each.

The window layer is spatial — position on the keyboard means position on the
screen — so it is mirrored under both hands. Actions are the opposite: the
*letter* carries the meaning, `C` for Chrome, so there is one key per action
and no mirror.

Actions use Meh chords (⌃⌥⇧) rather than Hyper, because the window layer has
already claimed Hyper on most letters. Alfred listens for them.

Bundle identifiers beat application names: they survive renames, and they are
the only way to address a Chrome PWA, which is a real application bundle with
a generated identifier rather than a window of Chrome.
"""

# key, what it is called, bundle identifier
APPS = [
    ("C", "Chrome", "com.google.chrome"),
    ("T", "iTerm2", "com.googlecode.iterm2"),
    ("V", "VSCodium", "com.vscodium"),
    ("O", "Obsidian", "md.obsidian"),
    ("A", "Calendar", "com.google.chrome.app.kjbdgfilnfhdoflbpgamdcdgpehopbep"),
    ("W", "Chat", "com.google.chrome.app.mdpkiolbdkhdjpekfbkbmhigcaggjagi"),
    ("G", "Gemini", "com.google.geminimacos"),
    ("D", "Drive", "com.google.drivefs"),
    ("F", "Finder", "com.apple.finder"),
    ("P", "1Password", "com.1password.1password"),
]

# Steps a mode can take. Each is a tuple whose first element names the kind:
#
#   ("layout", "Meeting")          run a saved Moom layout by title — use this
#                                  when several windows of one app must be
#                                  placed, which region moves cannot express
#   ("place", "com.x.y", "Region") activate that app, then run that region's
#                                  Moom action by title, from regions.py
#   ("focus", "com.x.y")           activate an app and leave it where it is
#   ("shortcut", "Deep Work")      run a shortcut from Shortcuts.app — this is
#                                  how Focus modes, Do Not Disturb and
#                                  anything else scriptable gets done
#   ("url", "https://…")           open a link in the default browser
#
# The modes below are a starting shape, not a claim about how you work. The
# Moom region titles they use come straight from regions.py.
MODES = [
    ("1", "Meeting", [
        ("place", "com.google.chrome.app.kjbdgfilnfhdoflbpgamdcdgpehopbep", "Camera stage"),
        ("place", "md.obsidian", "Below camera"),
    ]),
    ("2", "Deep work", [
        ("place", "com.vscodium", "Left two-thirds"),
        ("place", "com.googlecode.iterm2", "Right third"),
        ("shortcut", "Deep Work"),
    ]),
    ("3", "Review", [
        ("place", "com.google.chrome", "Left half"),
        ("place", "com.googlecode.iterm2", "Right half"),
    ]),
]


def actions():
    """Apps and modes as one validated list, in key order."""
    seen, out = {}, []
    for key, name, bundle in APPS:
        out.append({"kind": "app", "key": key, "name": name, "bundle": bundle})
    for key, name, steps in MODES:
        for step in steps:
            if step[0] not in ("layout", "place", "focus", "shortcut", "url"):
                raise ValueError(f"{name}: unknown step kind {step[0]!r}")
        out.append({"kind": "mode", "key": key, "name": name, "steps": steps})
    for action in out:
        if action["key"] in seen:
            raise ValueError(f"{action['name']}: key {action['key']!r} already "
                             f"used by {seen[action['key']]}")
        seen[action["key"]] = action["name"]
    return out
