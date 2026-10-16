# assets/ui — the UI art kit

Optional painted art for the game's panels, headers, dividers, buttons, rows,
chips and icons. It is loaded **once at startup** by `src/ui_theme.py`
(`ui_theme.load()`, called from `main()` right after the window opens).
Draw code never loads or rescales art.

**Everything here is optional.** Any piece that is missing, unreadable, or
too big for the box it is asked to fill is simply skipped, and that UI
element draws exactly as it did before the kit existed (procedural midnight
panels, gold borders). With only this README in the folder the game looks
exactly like the procedural UI. That is tested (`tests/test_ui_theme.py`).

Only `.png`, `.json` and `.md` files may live here (the folder ships inside
the exe; `tests/test_packaging.py` enforces it). Sources (`.psd`, `.kra`),
ComfyUI workflows and drafts belong in `_genart/`.

## manifest.json

```json
{
  "version": 1,
  "scale": 2,
  "pixel_art": false,
  "pieces": {
    "panel": {
      "file": "panel.png",
      "slice": [48, 48, 48, 48],
      "body": "fill",
      "body_color": [14, 18, 48],
      "accent": "panel_accent.png"
    },
    "divider": { "file": "divider.png", "slice": [40, 0, 40, 0],
                 "ornament": "divider_gem.png" }
  },
  "icons": { "sizes": [16, 24, 32], "files": { "hp": "icons/hp.png" } }
}
```

| Field | Meaning |
|---|---|
| `version` | Must be `1`. Any other value: the whole kit is ignored. |
| `scale` | The scale the art was painted at. `2` = authored at 2x; every piece is downscaled by half once, at load. Author at 2x. |
| `pixel_art` | Default for pieces: `true` scales with nearest-neighbour (integer factors only), `false` smooth. Per piece: `"pixel_art"`. |
| `pieces.<name>.file` | PNG, relative to this folder. Default `<name>.png`. |
| `pieces.<name>.slice` | Nine-slice border sizes `[left, top, right, bottom]` in **source** px (before `scale`). |
| `pieces.<name>.body` | `"tile"` (default): the centre region is tiled. `"fill"`: the centre is a flat `body_color`. `"none"`: the centre is not drawn. |
| `pieces.<name>.body_color` | RGB for `"fill"`. Panel pieces default to the game's midnight `(14, 18, 48)`. |
| `pieces.<name>.accent` | Optional greyscale PNG, **same size and slice** as `file`. It is multiplied by the element's accent colour (the quiz subject colour, a lore blue, a border colour passed by the code) and drawn over the frame. |
| `pieces.<name>.ornament` | Optional PNG centred on the piece (a divider's centre gem). |
| `icons.sizes` | Icon sizes (px) pre-scaled at load. Other sizes are scaled once on first use and kept. |
| `icons.files` | `name -> PNG`. Sources up to 64 px are treated as pixel art (integer upscale first, like the map sprites). |

### How a piece is drawn

The image is cut into 4 corners, 4 edges and a centre by `slice`. Corners are
blitted as-is; **edges and the centre are tiled, never stretched**, so one
piece fits a box of any size and a panel whose height changes every frame
(the quiz) costs nothing extra. Paint edges so they tile seamlessly along
their length. A box smaller than `left + right` by `top + bottom` falls back
to the procedural drawing, so keep corners small enough for the smallest
use (see the table).

### Two hard rules

1. **Painted gold is never tinted.** Colour that changes per subject or per
   screen lives only in the `accent` layer (a gem, a ribbon, an enamel inlay),
   painted in greyscale: white = full accent colour, black = none, alpha =
   coverage. The frame itself stays its painted colours.
2. **Panel bodies are opaque and flat.** Pieces `panel`, `quiz`, `subpanel`,
   `card`, `input` always get their body colour filled under the centre, so
   nothing behind a panel shows through. Keep the centre dark, flat and
   low-texture: body text contrast is gated by tests (quiz text >= 7:1,
   other text >= 4.5:1, measured against the real pixels behind the text).
   Put the ornament in the border band.

## Pieces

| Name | Used by | Smallest box it must fit |
|---|---|---|
| `panel` | every modal / menu panel (`draw_dark_panel`) | 420 x 150 (the "Dad?" card) |
| `quiz` | the quiz modal (`draw_dark_panel(kind='quiz')`); its `accent` takes the subject colour | about 640 x 300 |
| `header` | header strip at the top of a panel (`draw_header_bar`), 32-48 px tall. The panel's frame is repainted over it, so the frame band frames the header | 32 px tall |
| `header_small` | sidebar section headers | 24 px tall, 228 px wide |
| `divider` | horizontal divider (`draw_divider`); three-slice (`slice` `[l, 0, r, 0]`), drawn at the art's own height centred on the line | 100 px wide |
| `subpanel` | inner labelled box (`_ui_subpanel`) | 200 x 120 |
| `subpanel_header` | the 29 px label strip at the top of a subpanel (optional) | 29 px tall |
| `card` | reserved | |
| `choice`, `choice_selected`, `choice_correct`, `choice_incorrect` | quiz answer cards; the state must read from the frame (green / red), never from the text colour | 300 x 52 |
| `choice_badge` | the 44 px key badge on the left of an answer card. The card frame is redrawn over it | 44 x 52 |
| `row`, `row_selected` | option rows in message cards and NPC encounters (`_ui_action_row`) | 200 x 48 |
| `key` | key-letter badge on an option row | 42 x 32 |
| `chip`, `chip_active` | tab chips (`_ui_chip`) | 60 x 21 |
| `input` | text entry box (`draw_input_box`) | 200 x 38 |
| `scroll_track`, `scroll_thumb` | scrollbars (`_ui_scrollbar`), vertical, 5 px wide | 5 x 20 |
| `bar_track`, `bar_frame` | progress bars (`_ui_progress_bar`); the fill stays a flat colour between them | 60 x 8 |

The authoritative list is `ui_theme.PIECES`; an unknown piece name in the
manifest is reported and ignored.

## Checking art

* `python tools/ui/capture.py` renders every screen (92) at three sizes into
  `_genart/ui/capture/`; `python tools/ui/diff.py` diffs against
  `_genart/ui/baseline/`.
* `pytest tests/test_ui_gates.py` runs the gates every art step must pass:
  frame time, text contrast, text inside its panel at the minimum window,
  and the no-art fallback.
* Problems loading the kit are logged and listed in `ui_theme.kit().errors`.
