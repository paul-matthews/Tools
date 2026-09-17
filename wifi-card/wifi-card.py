#!/usr/bin/env python3
"""Generate a printable Wi-Fi card: QR code + human-readable credentials.

Outputs a self-contained HTML file sized in real millimetres, ready to
"Print to PDF" from any browser. The QR uses the standard `WIFI:` URI that
iOS (Camera app, iOS 11+) and Android (Camera / Settings, Android 10+) both
join networks from.

    ./wifi-card.py --ssid "Casa Matthews" --title "Guest Wi-Fi"

Requires segno (pure Python, no other dependencies):

    pip install segno
"""

from __future__ import annotations

import argparse
import getpass
import html
import subprocess
import sys
import shutil
from dataclasses import dataclass, field
from pathlib import Path

try:
    import segno
except ImportError:  # pragma: no cover - dependency guidance
    sys.exit(
        "wifi-card needs the 'segno' QR library.\n"
        "  pip install segno        (or: pipx install segno, brew install segno)"
    )

# ---------------------------------------------------------------------------
# Card sizes, in millimetres (width, height)
# ---------------------------------------------------------------------------

SIZES = {
    "business": (85.0, 55.0),   # UK/EU business card
    "cr80": (85.6, 53.98),      # credit-card / ISO 7810 ID-1
    "a7": (74.0, 105.0),        # portrait, bedside-table sized
    "a6": (105.0, 148.0),       # portrait, postcard
    "a5": (148.0, 210.0),       # portrait, fridge or utility-room poster
    "a4": (210.0, 297.0),       # portrait, full page
}

SHEETS = {"a4": (210.0, 297.0), "letter": (215.9, 279.4)}

# Characters guests routinely mistype when copying a password by eye.
CONFUSABLES = {
    "0": "zero",
    "O": "capital O",
    "o": "lowercase o",
    "1": "one",
    "l": "lowercase L",
    "I": "capital i",
    "5": "five",
    "S": "capital S",
    "2": "two",
    "Z": "capital Z",
    "8": "eight",
    "B": "capital B",
    "6": "six",
    "b": "lowercase b",
    "9": "nine",
    "g": "lowercase g",
    "q": "lowercase q",
}


@dataclass
class Card:
    ssid: str
    password: str
    security: str = "WPA"
    hidden: bool = False
    title: str = "Wi-Fi"
    subtitle: str = ""
    note: str = ""
    extras: list[tuple[str, str]] = field(default_factory=list)
    show_password: bool = True
    spell_out: bool = False
    theme: str = "light"
    error: str = "m"


# ---------------------------------------------------------------------------
# WIFI: URI  (ZXing format, the one phone cameras understand)
# ---------------------------------------------------------------------------

def escape_wifi(value: str) -> str:
    """Backslash-escape the characters that delimit a WIFI: URI."""
    out = []
    for char in value:
        if char in '\;,:"':
            out.append("\\")
        out.append(char)
    return "".join(out)


def wifi_uri(card: Card) -> str:
    """Build the WIFI: URI encoded into the QR code."""
    ssid = escape_wifi(card.ssid)
    # An all-hex SSID would be read as hex bytes, so quote it to force literal.
    if all(c in "0123456789abcdefABCDEF" for c in card.ssid) and card.ssid:
        ssid = f'"{ssid}"'

    parts = [f"T:{card.security}", f"S:{ssid}"]
    if card.security != "nopass":
        parts.append(f"P:{escape_wifi(card.password)}")
    if card.hidden:
        parts.append("H:true")
    return "WIFI:" + ";".join(parts) + ";;"


def warnings_for(card: Card) -> list[str]:
    """Things that silently break QR joining. Worth saying out loud."""
    warns = []
    if card.ssid != card.ssid.strip():
        warns.append("SSID has leading/trailing whitespace — check it matches the router exactly.")
    if card.password != card.password.strip():
        warns.append("Password has leading/trailing whitespace — usually a copy/paste slip.")
    if card.security != "nopass" and len(card.password) < 8:
        warns.append("WPA passwords are 8-63 characters; this one is shorter.")
    if not card.ssid.isascii():
        warns.append("SSID has non-ASCII characters — some older phones mis-decode these.")
    if card.hidden:
        warns.append("Hidden network: QR joining works, but some Android builds still need the SSID typed.")
    if card.security == "WEP":
        warns.append("WEP is broken and modern phones may refuse it. Move to WPA2 if you can.")
    if card.security == "nopass":
        warns.append("Open network — anyone in range can read your guests' traffic.")
    return warns


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def qr_svg(card: Card, dark: str) -> str:
    """Inline SVG for the QR, scaled by CSS rather than by pixel size."""
    qr = segno.make(wifi_uri(card), error=card.error)
    # omitsize gives the SVG a viewBox instead of fixed px, so CSS can scale it.
    return qr.svg_inline(scale=10, border=2, dark=dark, light=None, omitsize=True)


def legend_for(password: str) -> str:
    """A key for the characters guests are most likely to misread."""
    seen = {}
    for char in password:
        if char in CONFUSABLES and char not in seen:
            seen[char] = CONFUSABLES[char]
    return "  ·  ".join(f"{c} = {name}" for c, name in seen.items())


def card_html(card: Card) -> str:
    """Markup for a single card. Wide cards go side-by-side, tall ones stack."""
    e = html.escape
    rows = [f'<div class="field"><span class="label">Network</span>'
            f'<span class="value">{e(card.ssid)}</span></div>']

    if card.security == "nopass":
        rows.append('<div class="field"><span class="label">Password</span>'
                    '<span class="value muted">No password needed</span></div>')
    elif card.show_password:
        rows.append(f'<div class="field"><span class="label">Password</span>'
                    f'<span class="value">{e(card.password)}</span></div>')

    if card.spell_out and card.show_password and card.security != "nopass":
        legend = legend_for(card.password)
        if legend:
            rows.append(f'<div class="legend">{e(legend)}</div>')

    for label, value in card.extras:
        rows.append(f'<div class="field extra"><span class="label">{e(label)}</span>'
                    f'<span class="value">{e(value)}</span></div>')

    note = f'<p class="note">{e(card.note)}</p>' if card.note else ""
    subtitle = f'<p class="subtitle">{e(card.subtitle)}</p>' if card.subtitle else ""

    return f"""    <section class="card">
      <header>
        <h1>{e(card.title)}</h1>
        {subtitle}
      </header>
      <div class="body">
        <figure class="qr">
          {qr_svg(card, "#000000")}
          <figcaption>Point your camera here</figcaption>
        </figure>
        <div class="details">
          {"".join(rows)}
        </div>
      </div>
      {note}
    </section>"""


def document_html(card: Card, size: str, copies: int, sheet: str | None) -> str:
    width, height = SIZES[size]
    landscape = width > height

    if sheet:
        page_w, page_h = SHEETS[sheet]
        page_rule = f"@page {{ size: {page_w}mm {page_h}mm; margin: 8mm; }}"
    else:
        page_rule = f"@page {{ size: {width}mm {height}mm; margin: 0; }}"

    if card.theme == "dark":
        palette = """
      --ink: #f4f4f5;
      --ink-soft: #a1a1aa;
      --paper: #18181b;
      --rule: #3f3f46;"""
    else:
        palette = """
      --ink: #18181b;
      --ink-soft: #71717a;
      --paper: #ffffff;
      --rule: #e4e4e7;"""

    if landscape:
        # QR sits beside the text, so its ceiling is the card's short side.
        layout, qr_size = "row", "calc(var(--card-h) * .44)"
    else:
        layout, qr_size = "column", "calc(var(--card-w) * .45)"

    cards = "\n".join(card_html(card) for _ in range(copies))

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html.escape(card.title)} — {html.escape(card.ssid)}</title>
<style>
  {page_rule}

  :root {{{palette}
    --card-w: {width}mm;
    --card-h: {height}mm;
    --qr-size: {qr_size};
    /* One unit == 1% of the card width, so type scales with the card. */
    --u: calc(var(--card-w) / 100);
  }}

  * {{ box-sizing: border-box; }}

  body {{
    margin: 0;
    font-family: "Helvetica Neue", Helvetica, Arial, system-ui, sans-serif;
    color: var(--ink);
    background: #d4d4d8;
    display: flex;
    flex-wrap: wrap;
    gap: 6mm;
    padding: 6mm;
    align-content: flex-start;
  }}

  .card {{
    width: var(--card-w);
    height: var(--card-h);
    padding: calc(var(--u) * 4.5);
    background: var(--paper);
    display: flex;
    flex-direction: column;
    gap: calc(var(--u) * 2);
    overflow: hidden;
    /* Screen-only framing; print gets a hairline cut guide instead. */
    box-shadow: 0 1mm 3mm rgba(0, 0, 0, .25);
  }}

  /* Only .body flexes — a shrinking header would overlap the text under it. */
  header, .note {{ flex: 0 0 auto; }}

  header h1 {{
    margin: 0;
    font-size: calc(var(--u) * 4.5);
    letter-spacing: calc(var(--u) * -.05);
  }}

  .subtitle {{
    margin: calc(var(--u) * .5) 0 0;
    font-size: calc(var(--u) * 2.8);
    color: var(--ink-soft);
  }}

  .body {{
    flex: 1 1 auto;
    min-height: 0;
    display: flex;
    flex-direction: {layout};
    align-items: center;
    justify-content: center;
    gap: calc(var(--u) * 3.5);
  }}

  .qr {{
    margin: 0;
    flex: 0 0 auto;
    width: var(--qr-size);
    max-height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: calc(var(--u) * 1);
  }}

  /* The QR stays dark-on-white whatever the theme: scanners need contrast. */
  .qr svg {{
    display: block;
    width: 100%;
    height: auto;
    /* Last-resort shrink so an overfull card letterboxes instead of clipping. */
    max-height: calc(100% - var(--u) * 4);
    background: #fff;
  }}

  .qr figcaption {{
    font-size: calc(var(--u) * 2.2);
    color: var(--ink-soft);
    text-align: center;
  }}

  .details {{
    /* Never grow: in column layout that would strand the fields at the top. */
    flex: 0 1 auto;
    min-width: 0;
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: calc(var(--u) * 2);
  }}

  .field {{ display: flex; flex-direction: column; min-width: 0; }}

  .label {{
    font-size: calc(var(--u) * 2.2);
    text-transform: uppercase;
    letter-spacing: calc(var(--u) * .12);
    color: var(--ink-soft);
  }}

  .value {{
    /* Monospace disambiguates 0/O and 1/l, which is the whole point. */
    font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
    font-size: calc(var(--u) * 4);
    line-height: 1.3;
    /* Break at spaces first; split mid-token only for an unbroken password. */
    overflow-wrap: break-word;
  }}

  .extra .value {{ font-size: calc(var(--u) * 3); }}
  .value.muted {{ font-family: inherit; color: var(--ink-soft); }}

  .legend {{
    font-size: calc(var(--u) * 2.2);
    line-height: 1.4;
    color: var(--ink-soft);
  }}

  .note {{
    margin: 0;
    font-size: calc(var(--u) * 2.4);
    line-height: 1.35;
    color: var(--ink-soft);
    border-top: .2mm solid var(--rule);
    padding-top: calc(var(--u) * 2);
  }}

  @media print {{
    body {{ background: #fff; gap: 0; padding: 0; }}
    .card {{
      box-shadow: none;
      outline: .1mm dashed var(--rule);  /* cut guide */
      break-inside: avoid;
    }}
  }}
</style>
</head>
<body>
{cards}
</body>
</html>
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_extra(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError(f"--extra needs Label=Value, got {value!r}")
    label, _, text = value.partition("=")
    return label.strip(), text.strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a printable Wi-Fi card (QR + credentials).",
        epilog="Password is prompted for if not supplied, keeping it out of shell history.",
    )
    parser.add_argument("--ssid", required=True, help="network name, exactly as broadcast")
    parser.add_argument("--password", help="network password (prompted if omitted)")
    parser.add_argument("--password-stdin", action="store_true",
                        help="read the password from stdin instead of prompting")
    parser.add_argument("--security", choices=["WPA", "WEP", "nopass"], default="WPA",
                        help="WPA covers WPA/WPA2/WPA3 (default: WPA)")
    parser.add_argument("--hidden", action="store_true", help="network does not broadcast its SSID")

    parser.add_argument("--title", default="Guest Wi-Fi", help="heading on the card")
    parser.add_argument("--subtitle", default="", help="smaller line under the heading")
    parser.add_argument("--note", default="", help="footer line, e.g. house rules")
    parser.add_argument("--extra", action="append", type=parse_extra, default=[],
                        metavar="LABEL=VALUE", help="extra row, repeatable")

    parser.add_argument("--size", choices=sorted(SIZES), default="business")
    parser.add_argument("--copies", type=int, default=1, help="cards per sheet")
    parser.add_argument("--sheet", choices=sorted(SHEETS),
                        help="paper size to tile onto (default: a4 when --copies > 1)")
    parser.add_argument("--theme", choices=["light", "dark"], default="light")
    parser.add_argument("--error", choices=["l", "m", "q", "h"], default="m",
                        help="QR error correction (default: m)")
    parser.add_argument("--hide-password", action="store_true",
                        help="QR only — no readable password on the card")
    parser.add_argument("--spell-out", action="store_true",
                        help="add a key for easily-misread characters")

    parser.add_argument("-o", "--output", type=Path, default=Path("wifi-card.html"))
    parser.add_argument("--qr-only", type=Path, metavar="FILE",
                        help="also write the bare QR to FILE (.svg or .png)")
    parser.add_argument("--open", action="store_true", help="open the result in your browser")
    return parser


def resolve_password(args: argparse.Namespace) -> str:
    if args.security == "nopass":
        return ""
    if args.password_stdin:
        return sys.stdin.readline().rstrip("\n")
    if args.password is not None:
        return args.password
    return getpass.getpass(f"Password for {args.ssid}: ")


def open_file(path: Path) -> None:
    for opener in ("open", "xdg-open"):
        if shutil.which(opener):
            subprocess.run([opener, str(path)], check=False)
            return
    print(f"Could not find an opener; the file is at {path}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.copies < 1:
        parser.error("--copies must be at least 1")

    card = Card(
        ssid=args.ssid,
        password=resolve_password(args),
        security=args.security,
        hidden=args.hidden,
        title=args.title,
        subtitle=args.subtitle,
        note=args.note,
        extras=args.extra,
        show_password=not args.hide_password,
        spell_out=args.spell_out,
        theme=args.theme,
        error=args.error,
    )

    sheet = args.sheet or ("a4" if args.copies > 1 else None)
    args.output.write_text(document_html(card, args.size, args.copies, sheet), encoding="utf-8")

    if args.qr_only:
        qr = segno.make(wifi_uri(card), error=card.error)
        qr.save(str(args.qr_only), scale=12, border=2)

    for warning in warnings_for(card):
        print(f"warning: {warning}", file=sys.stderr)

    w, h = SIZES[args.size]
    print(f"Wrote {args.output} — {args.copies} × {args.size} card ({w:g}×{h:g}mm).")
    print("Open it in a browser and print at 100% scale (no 'fit to page').")

    if args.open:
        open_file(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
