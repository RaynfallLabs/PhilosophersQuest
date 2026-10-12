# Generated sprite pipeline

Draws creature sprites with image models running on this machine (ComfyUI), then
turns each picture into a 64 px game sprite in code. Nothing here runs at game time.

    <ComfyUI python> tools/content/genart/pipeline.py tools/content/genart/briefs/pilot.json --n 3

ComfyUI must be running on 127.0.0.1:8188 (`ComfyUI_windows_portable`, started with
`--listen 127.0.0.1 --port 8188`). Use ComfyUI's own Python: it has scipy and Pillow.
Output goes to `_genart/` (not committed).

## How a sprite is made

1. **Brief** (`briefs/*.json`): a person writes what the creature is. This is where
   the creature's identity and tier are decided, before anything is drawn.
2. **Draft** (FLUX.2 klein 4B): paints the brief as a classic high-fantasy oil
   illustration. It decides WHAT is drawn: the pose, what each hand holds, one figure,
   a flat key-colour background.
3. **Pixel pass** (SDXL pixel-art model, image-to-image, low strength): keeps the
   painting and sharpens it into pixel edges.
4. **Convert** (`convert.py`): removes the key colour wherever it appears (so the
   gap between two legs goes, and no ground shadow survives), shrinks to 64 px,
   lifts the midtones, cuts to 32 colours, adds the outline.
5. **Checks**: mechanical ones in code, then a reviewer marks each candidate against
   the brief's lists on the family review sheet.

## Writing a brief

| Field | What it is for |
|---|---|
| `id` | The monster's id in `data/monsters.json`. |
| `family`, `rank` | Creatures reviewed side by side, lowest tier first. |
| `what` | One sentence: the body. Say the size relative to its relatives. |
| `colours` | Name every main colour. An unnamed colour drifts to blue or purple. |
| `wears` | Clothing and armour that fit the TIER. A base creature wears little. |
| `holds` | Exactly what is in each hand, with the word "exactly". Empty hands are stated. |
| `pose` | An action. For a beast, say "seen from the side" and "on four legs". |
| `must_show` | What makes it this creature and this tier. The reviewer checks each. |
| `must_not_show` | What belongs to its relatives or to a mistake seen before. Also sent to the model as things to avoid. |
| `key` | The backdrop colour: `magenta`, `green` or `blue`. It must be a colour the creature does not have, or the cut-out eats part of it. `pipeline.py` refuses a brief whose `colours` name the key. |

The style is the one Brandon chose from a board of six on 2026-10-11: painted
high fantasy, not a bright game sprite, at 64 px.

Rules learned the hard way:

- **Tier must be readable.** A plain skeleton is bare bones; mail and a shield make
  it a skeleton warrior. Write the difference into both creatures' lists.
- **A variant must look like its name.** A goblin shaman needs the mask and rattle
  in `must_show`, and `sword`, `armour` in `must_not_show`.
- **Take the facts from the data.** The attack names say what it fights with
  ("Rusty Knife", "Crossbow Bolt"); the lore says what it wears. Do not use the
  `color` field: that is the old map glyph colour.
- **An action pose can break the body.** "Charging" turned a minotaur into a bull on
  four legs. State the body plan in the pose as well ("on two legs, leaning forward").
- **No shadows.** The prompt asks for none and the key colour removes what remains.
- **Never redraw Brandon's own portraits** (`player_ranger`, `player_wizard_f`,
  `player_robyn`).

## Review

`_genart/<run>/REVIEW_<family>.png` shows each creature's candidates with its lists
beside them and a lineup of the family at the bottom. For each creature the reviewer
records in `review.json`: every `must_show` item present, no `must_not_show` item
present, the hands hold what `holds` says, and in the lineup each tier is told
apart from the one below. A creature with no passing candidate gets its brief
reworded and is drawn again; it is not passed with a note.
