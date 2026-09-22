# Window regions

Generated from `config.yaml`. Screen 5120 x 2160.

Hold **Caps Lock** or **left Option**, then the key below. The map is mirrored, so either hand can drive it alone while the other stays on the mouse.

**Left hand**

```
  1     2     3     4     5
  ▏L    ⅔L    ⅔C    ⅔R    R▕

  Q     W     E     R     T
 ⅓L▀   ½L▀   ½C▀   ½R▀   ⅓R▀

  A     S     D     F     G
  ⅓L    ½L    ½C    ½R    ⅓R

  Z     X     C     V     B
 ⅓L▄   ½L▄   ½C▄   ½R▄   ⅓R▄

 Tab
 FULL

```

**Right hand**

```
  6     7     8     9     0
  ▏L    ⅔L    ⅔C    ⅔R    R▕

  Y     U     I     O     P
 ⅓L▀   ½L▀   ½C▀   ½R▀   ⅓R▀

  H     J     K     L     ;
  ⅓L    ½L    ½C    ½R    ⅓R

  N     M     ,     .     /
 ⅓L▄   ½L▄   ½C▄   ½R▄   ⅓R▄

  '
 FULL

```

| Keys | Region | Chord | Columns (of 12) | Rows (of 10, from the top) | Pixels |
| --- | --- | --- | --- | --- | --- |
| `A` / `H` | Left third | ⌃⌥⇧⌘`A` | 0–4 | 0–10 | 1707×2160 at 0,0 |
| `S` / `J` | Left half | ⌃⌥⇧⌘`S` | 0–6 | 0–10 | 2560×2160 at 0,0 |
| `D` / `K` | Centre half | ⌃⌥⇧⌘`D` | 3–9 | 0–10 | 2560×2160 at 1280,0 |
| `F` / `L` | Right half | ⌃⌥⇧⌘`F` | 6–12 | 0–10 | 2560×2160 at 2560,0 |
| `G` / `;` | Right third | ⌃⌥⇧⌘`G` | 8–12 | 0–10 | 1707×2160 at 3413,0 |
| `1` / `6` | Narrow left | ⌃⌥⇧⌘`1` | 0–3 | 0–10 | 1280×2160 at 0,0 |
| `2` / `7` | Left two-thirds | ⌃⌥⇧⌘`2` | 0–8 | 0–10 | 3413×2160 at 0,0 |
| `3` / `8` | Centre two-thirds | ⌃⌥⇧⌘`3` | 2–10 | 0–10 | 3413×2160 at 853,0 |
| `4` / `9` | Right two-thirds | ⌃⌥⇧⌘`4` | 4–12 | 0–10 | 3413×2160 at 1707,0 |
| `5` / `0` | Narrow right | ⌃⌥⇧⌘`5` | 9–12 | 0–10 | 1280×2160 at 3840,0 |
| `Q` / `Y` | Left third, top | ⌃⌥⇧⌘`Q` | 0–4 | 0–7 | 1707×1512 at 0,0 |
| `W` / `U` | Left half, top | ⌃⌥⇧⌘`W` | 0–6 | 0–7 | 2560×1512 at 0,0 |
| `E` / `I` | Camera stage | ⌃⌥⇧⌘`E` | 3–9 | 0–6 | 2560×1296 at 1280,0 |
| `R` / `O` | Right half, top | ⌃⌥⇧⌘`R` | 6–12 | 0–7 | 2560×1512 at 2560,0 |
| `T` / `P` | Right third, top | ⌃⌥⇧⌘`T` | 8–12 | 0–7 | 1707×1512 at 3413,0 |
| `Z` / `N` | Left third, bottom | ⌃⌥⇧⌘`Z` | 0–4 | 3–10 | 1707×1512 at 0,648 |
| `X` / `M` | Left half, bottom | ⌃⌥⇧⌘`X` | 0–6 | 3–10 | 2560×1512 at 0,648 |
| `C` / `,` | Below camera | ⌃⌥⇧⌘`C` | 3–9 | 5–10 | 2560×1080 at 1280,1080 |
| `V` / `.` | Right half, bottom | ⌃⌥⇧⌘`V` | 6–12 | 3–10 | 2560×1512 at 2560,648 |
| `B` / `/` | Right third, bottom | ⌃⌥⇧⌘`B` | 8–12 | 3–10 | 1707×1512 at 3413,648 |
| `Tab` / `'` | Full screen | ⌃⌥⇧⌘`Enter` | 0–12 | 0–10 | 5120×2160 at 0,0 |

## Inside the ⌥` overlay

These regions also answer to a bare key while Moom's keyboard controller is on screen:

* `A` — Left third
* `D` — Centre half
* `G` — Right third

## Keyboard layer

Both keys of a pair send the same chord, so Moom sees one action either way. Chords are always a letter or a digit — never punctuation, which is where macOS keeps its own shortcuts.

## Scripting

Every region is addressable by title:

```applescript
tell application "Moom" to run "Camera stage"
```
