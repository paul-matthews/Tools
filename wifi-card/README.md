# wifi-card

Generates a printable Wi-Fi card for guests: a QR code they can scan plus
credentials they can read and type. Output is a self-contained HTML file sized
in real millimetres — open it in a browser and "Print to PDF".

## Does the QR actually work on an iPhone?

Yes. The iOS Camera app has joined networks from `WIFI:` QR codes since iOS 11
(2017) — no app, no setup. If it has failed for you before, it was almost
certainly one of these:

* **Scanned from inside the wrong app.** A banking or scanner app that reads
  QR codes will happily decode the text and do nothing useful with it. It has
  to be the Camera app (or Control Centre's code scanner).
* **The notification banner was missed.** iOS shows a "Join *network*" banner
  at the top of the screen rather than joining silently. It disappears after a
  few seconds and people scan again instead of tapping it.
* **The QR was too small or too low-contrast.** Below roughly 20mm printed, or
  with no white margin around it, phone cameras struggle. This tool prints at
  ~24mm on a business card and ~47mm on A6, always dark-on-white with the
  quiet zone intact.
* **The password contains `;` `,` `:` `"` or `\`.** These delimit the `WIFI:`
  URI and must be escaped. Most online generators do not bother. This one does.
* **WPA2-Enterprise.** The `WIFI:` format cannot express enterprise auth. Not
  a home problem, but worth knowing.

What genuinely does *not* work from a QR is Apple's own "Share Your Wi-Fi"
prompt — that needs both phones to have each other in Contacts, which is why
it never fires for house guests. The QR is the fix for that, not the problem.

## What to put on the card

Non-negotiable:

* **Network name**, exactly as broadcast, including case. If you have separate
  2.4GHz and 5GHz SSIDs, name the one you actually want guests on.
* **Password**, in monospace. Guests will retype it on a laptop, a Kindle, or
  a games console that cannot scan anything.
* **The QR code**, at least 20mm across with white space around it.
* **One line of instruction.** A bare QR makes people hesitate — "Point your
  camera here" removes the guesswork.

Worth adding:

* A **title** that says whose network it is, so the card still makes sense on a
  fridge next to four others.
* **House notes** — printer name, smart TV, bin day. Guests ask anyway.
* A **character key** (`--spell-out`) if the password mixes `0`/`O` or `1`/`l`.

Leave off: your router admin password, anything identifying the address, and
the main network's password. Which brings us to —

## Put guests on a guest network

Print a card for your router's **guest SSID**, not your main one. A card in a
spare room is a password written down in a room you do not control, and anyone
on your main network can see every other device on it. Most routers can give
the guest network client isolation and no LAN access in a couple of clicks.

## Usage

```sh
pip install segno

./wifi-card.py --ssid "Casa Matthews"
```

The password is prompted for interactively, so it stays out of your shell
history. A full example:

```sh
./wifi-card.py \
  --ssid "Casa Matthews Guest" \
  --title "Guest Wi-Fi" \
  --subtitle "Make yourself at home" \
  --note "Smart TV and printer are on this network too." \
  --spell-out \
  --size a6 \
  --open
```

Eight business cards on one A4 sheet, with cut guides:

```sh
./wifi-card.py --ssid "Casa Matthews Guest" --copies 8
```

Scripted, without a prompt:

```sh
pass show wifi/guest | ./wifi-card.py --ssid "Casa Matthews Guest" --password-stdin
```

### Options

| Flag | Notes |
| --- | --- |
| `--ssid` | Required. Exactly as broadcast. |
| `--password` / `--password-stdin` | Omit both to be prompted. |
| `--security` | `WPA` (covers WPA/WPA2/WPA3), `WEP`, `nopass`. |
| `--hidden` | For networks that do not broadcast their SSID. |
| `--size` | `business` (default), `cr80`, `a7`, `a6`, `a5`, `a4`. |
| `--copies` / `--sheet` | Tile N cards onto `a4` (default) or `letter`. |
| `--theme` | `light` or `dark`. The QR stays dark-on-white either way. |
| `--spell-out` | Adds a key for easily-misread characters. |
| `--hide-password` | QR only — for a card left somewhere semi-public. |
| `--error` | QR error correction, `l`/`m`/`q`/`h`. Default `m`. |
| `--qr-only` | Also write the bare QR to a `.svg` or `.png`. |
| `--open` | Open the result in your browser. |

The script warns on stderr about things that silently break QR joining: short
passwords, stray whitespace, non-ASCII SSIDs, WEP, open networks.

## Printing

Print at **100% scale** — "fit to page" or "shrink to fit" will resize the card
and shrink the QR below the reliable scanning threshold. Matte card stock beats
glossy; a gloss finish under a ceiling light reflects straight back into the
camera. Laminating is fine and does not affect scanning.
