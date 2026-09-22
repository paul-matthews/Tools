#!/usr/bin/env python3
"""Generate the AppleScripts and cheat sheet for the actions layer.

One script per app and per mode, written into `scripts/` beside this file and
committed, so a `git pull` delivers them to any machine — nothing to copy
around, and Alfred can point straight at the checkout.

    ./actions-gen.py -c ACTIONS.md
    osascript scripts/mode-meeting.applescript

That second line runs a mode there and then: no editor, no hotkey, nothing to
paste. Alfred binds each script to its Meh chord (⌃⌥⇧ + the action's key),
and the keyboard's actions layer sends that chord.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config as config_module  # noqa: E402

GLYPHS = {"hyper": "⌃⌥⇧⌘", "meh": "⌃⌥⇧"}


def applescript(action):
    """The script for one action, as lines."""
    if action["kind"] == "app":
        return [f'-- Focus {action["name"]}',
                f'tell application id "{action["bundle"]}" to activate']

    lines = [f'-- {action["name"]}']
    for step in action["steps"]:
        kind = step[0]
        if kind == "layout":
            lines.append(f'tell application "Moom" to run "{step[1]}"')
        elif kind == "focus":
            lines.append(f'tell application id "{step[1]}" to activate')
        elif kind == "place":
            lines += [f'tell application id "{step[1]}" to activate',
                      "delay 0.2",
                      f'tell application "Moom" to run "{step[2]}"']
        elif kind == "shortcut":
            lines.append('do shell script "shortcuts run " & quoted form of '
                         f'"{step[1]}"')
        elif kind == "url":
            lines.append(f'open location "{step[1]}"')
    return lines


def cheat_sheet(cfg, glyphs):
    lines = [
        "# Actions", "",
        "Generated from `config.yaml`. Hold **Tab** for the actions layer, then "
        f"the key. Each key sends {glyphs} and itself, which Alfred turns into "
        "the script.", "",
        "| Key | Chord | Does |", "| --- | --- | --- |",
    ]
    for action in cfg.actions:
        what = (f'Focus {action["name"]}' if action["kind"] == "app"
                else f'{action["name"]} — {len(action["steps"])} steps')
        lines.append(f'| `{action["key"]}` | {glyphs}`{action["key"]}` | {what} |')

    lines += ["", "## Binding them in Alfred", "",
              "Each script needs one Alfred hotkey, once. In a workflow, add a "
              "**Hotkey** trigger, record the chord, and connect it to a "
              "**Run Script** action set to `/usr/bin/osascript` with the "
              "script's path in this checkout. Powerpack required.", "",
              "## Modes", ""]
    for action in cfg.modes:
        lines += [f'### {action["name"]} (`{action["key"]}`)', ""]
        for step in action["steps"]:
            lines.append(f'* `{step[0]}` — '
                         + ", ".join(str(part) for part in step[1:]))
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-o", "--output",
                        default=str(Path(__file__).resolve().parent / "scripts"),
                        help="directory to write the AppleScripts into "
                             "(default: scripts/ beside this file)")
    parser.add_argument("-c", "--cheatsheet", help="also write a markdown cheat sheet")
    args = parser.parse_args()

    cfg = config_module.load()
    print(f"read {config_module.CONFIG.name} with {cfg.parser}\n")

    out = Path(args.output).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    written = set()
    for action in cfg.actions:
        name = action["name"].lower().replace(" ", "-")
        path = out / f'{action["kind"]}-{name}.applescript'
        path.write_text("\n".join(applescript(action)) + "\n")
        written.add(path.name)
        print(f'{action["key"]}  {action["name"]:<12} {path}')

    # Rename an action and its old script would linger, still bound in Alfred
    # and still doing the old thing. This directory is generated, so anything
    # not written this time does not belong.
    for stale in sorted(out.glob("*.applescript")):
        if stale.name not in written:
            stale.unlink()
            print(f"   removed stale {stale.name}")

    if args.cheatsheet:
        glyphs = GLYPHS[cfg.layer("actions_layer").get("chord", "meh")]
        Path(args.cheatsheet).write_text(cheat_sheet(cfg, glyphs))
        print(f"\nwrote {args.cheatsheet}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # piping into head and friends
        sys.exit(0)
