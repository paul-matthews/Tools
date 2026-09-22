"""A parser for the small slice of YAML the config files use.

macOS ships a Python with no YAML library, and `pip install` is friction this
is meant to avoid — so rather than take a dependency for a few dozen lines of
config, this reads the subset directly. The files stay valid YAML; they just
do not need anything installed to be read.

What is supported: mappings, lists, nesting by indentation, `# comments`,
quoted or bare scalars, and inline collections — `{a: 1, b: 2}` and `[1, 2]` —
because a table of regions reads far better one line per row. What is not:
anchors, multi-line strings, types. **Every scalar is a string** — no guessing
that `1` is a number or that `no` is a boolean.

Anything it does not understand raises ConfigError naming the line, because
these files are meant to be edited by hand.
"""

from __future__ import annotations


class ConfigError(Exception):
    """A config file that could not be read, with the line that broke it."""


def _lines(text):
    """(indent, content, line number) for each line that carries anything."""
    out = []
    for number, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if " #" in stripped and stripped.count('"') % 2 == 0:
            stripped = stripped.split(" #")[0].rstrip()
        out.append((len(raw) - len(raw.lstrip(" ")), stripped, number))
    return out


def _pieces(text):
    """Split on top-level commas, ignoring those inside quotes or brackets."""
    parts, depth, quote, current = [], 0, None, []
    for character in text:
        if quote:
            current.append(character)
            if character == quote:
                quote = None
            continue
        if character in "\"'":
            quote = character
        elif character in "{[":
            depth += 1
        elif character in "}]":
            depth -= 1
        elif character == "," and depth == 0:
            parts.append("".join(current))
            current = []
            continue
        current.append(character)
    if "".join(current).strip():
        parts.append("".join(current))
    return [part.strip() for part in parts]


def _pair(text):
    """Split `key: value` at the first colon outside quotes and brackets."""
    depth, quote = 0, None
    for index, character in enumerate(text):
        if quote:
            if character == quote:
                quote = None
            continue
        if character in "\"'":
            quote = character
        elif character in "{[":
            depth += 1
        elif character in "}]":
            depth -= 1
        elif character == ":" and depth == 0:
            return text[:index], text[index + 1:]
    raise ConfigError(f"expected 'key: value' inside {{...}}, got {text!r}")


def _scalar(text):
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    if text.startswith("{") and text.endswith("}"):
        result = {}
        for piece in _pieces(text[1:-1]):
            key, value = _pair(piece)
            result[_scalar(key)] = _scalar(value)
        return result
    if text.startswith("[") and text.endswith("]"):
        return [_scalar(piece) for piece in _pieces(text[1:-1])]
    return text


def _split(content, number):
    if ":" not in content:
        raise ConfigError(f"line {number}: expected 'key: value', got {content!r}")
    key, _, value = content.partition(":")
    return _scalar(key), value.strip()


def _block(lines, index, indent):
    if lines[index][1].startswith("- "):
        return _list(lines, index, indent)
    return _mapping(lines, index, indent)


def _mapping(lines, index, indent):
    result = {}
    while index < len(lines):
        level, content, number = lines[index]
        if level < indent:
            break
        if level > indent:
            raise ConfigError(f"line {number}: unexpected indentation")
        if content.startswith("- "):
            raise ConfigError(f"line {number}: list item where a key was expected")
        key, value = _split(content, number)
        if value:
            result[key] = _scalar(value)
            index += 1
            continue
        if index + 1 < len(lines) and lines[index + 1][0] > indent:
            result[key], index = _block(lines, index + 1, lines[index + 1][0])
        else:
            result[key] = None
            index += 1
    return result, index


def _list(lines, index, indent):
    items = []
    while index < len(lines) and lines[index][0] == indent \
            and lines[index][1].startswith("- "):
        head = lines[index][1][2:].strip()
        number = lines[index][2]
        # Continuation lines of a list item sit under the text after "- ".
        inner = [(indent + 2, head, number)]
        index += 1
        while index < len(lines) and lines[index][0] > indent:
            inner.append(lines[index])
            index += 1
        if head.startswith("{") or head.startswith("["):
            if len(inner) > 1:
                raise ConfigError(f"line {number}: cannot nest under an inline item")
            items.append(_scalar(head))
        elif ":" in head:
            value, _ = _mapping(inner, 0, indent + 2)
            items.append(value)
        elif len(inner) > 1:
            raise ConfigError(f"line {number}: cannot nest under a plain list item")
        else:
            items.append(_scalar(head))
    return items, index


def parse(text):
    """Parse a config file into nested dicts, lists and strings."""
    lines = _lines(text)
    if not lines:
        return {}
    value, index = _block(lines, 0, lines[0][0])
    if index != len(lines):
        raise ConfigError(f"line {lines[index][2]}: unexpected indentation")
    return value


def load(path):
    with open(path) as handle:
        return parse(handle.read())
