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
| `body` | Optional. `"shapeless"` for anything with no head, feet or legs (a flame, slime, cloud, whirlwind, eyeball, pillar, swarm, serpent, floating orb). It swaps the fixed prompt wording, which otherwise says "head to the soles of its feet" and "weight on one leg" and so grows legs or a small man under such creatures. |
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

## What goes wrong, and the wording that stops it

Every line here was a real failure in the pilot. Read them before writing a brief,
and look for the same kind of slip when reviewing.

- **A loaded word draws the wrong thing.** "Pony-sized" spider became a unicorn;
  "zombie hulk" became the comic-book Hulk in jeans; "charging" minotaur became a
  bull on four legs. Describe the body in plain parts and leave the loaded word out.
- **One part contradicts the rest.** The burning skeleton had a clean white skull on
  a charred body. When a creature is made of something or is in some state (burnt,
  frozen, rotting, stone, rusted), say it of EVERY part and name the head.
- **The pose word must be the pose.** "Kneels" and "crouches" are different pictures.
  Say where the feet and knees are.
- **Nothing under the figure.** A web, a rock, a patch of ground or a puddle under
  the creature becomes a mess in the cut-out. Never ask for one; a floating or
  hanging creature simply floats.
- **Thin things must be drawn bold.** A bow, wand, string or chain thinner than a
  sprite pixel is lost. Ask for thick, sturdy, slightly oversized held things, held
  clear of the body. A bowstring or a silk thread will not survive: do not make it
  a `must_show`.
- **Describe a weapon by its shape** when its name is not enough: a crossbow is "a
  stock with a short bow fixed crosswise, a T shape, two arms, a string".
- **Extra props appear in idle hands.** State both hands. Casters grow staffs:
  write "no staff" and put the magic "in the palm, touching the hand".
- **A glow becomes a halo or a loose piece.** Keep magic and fire attached to the
  body and small. A cloud of mist round a creature swallows it.
- **Human-shaped creatures get big heads** unless the brief gives the build:
  "realistic adult proportions, small skull, long limbs, about eight heads tall".
- **A beast becomes a muscle-man** unless told it is "a real animal on four legs,
  seen from the side".
- **Tier is shown by gear and build, not size.** Every sprite fills the same tile.
  The lowest tier is plain; each step up adds one or two things the tier below
  must not have, and those go in the lower tier's `must_not_show`.
- **Colours drift.** Name the colour of skin, cloth, metal and magic. The data's
  `color` field is the old map glyph colour: ignore it.
- **Saying what is absent draws it.** "No eyes at the sides of his face" kept two
  eyes; "a cyclops with one giant eye in the centre of his forehead" is what moved
  it. Listing "scraps of armour, a shield rim, a helmet" on a flesh giant drew an
  armoured ogre. Put the denial in `must_not_show`; in `what`, say what IS there.
- **A second head or an animal tail needs its extra body denied.** "A goat's head
  rising from the back" draws a whole goat. Say "one goat neck with one goat head,
  growing from the lion like a second head; no goat body", and for a snake tail,
  "the lion has no lion's tail; the snake is the tail".
- **A dead creature described only by its build comes out alive and pink.** Put
  "dead flesh, corpse-grey, never living pink" in `what` and give it blank eyes.
- **A round mouth seen face-on reads as an eyeball** at 64 px unless the teeth are
  large and white and the hole is "pitch-black, no pupil, no iris".
- **Sea creatures seen face-on grow little legs** unless told "no legs, no feet".
- **Light in a hand:** "a ball of light the size of an apple in the open palm"
  draws; "a small glare" draws nothing. Yellow or white light on a green backdrop
  leaves a fringe: give those creatures a blue or magenta backdrop.
- **A count is not kept.** "Eight tentacles" comes out as twelve. Do not make an
  exact count a `must_show` unless it is the creature's whole identity (one eye,
  three heads), and then say it as a plain positive sentence.
- **Keep earlier rounds.** A rework overwrites a creature's three candidates; copy
  the folder to `_r1`, `_r2` first in case an earlier one was better.
- **A simile is drawn literally, even for one part.** "Legs like a bulldog's" gave
  a bulldog's face; "shaped like a pumpkin" gave a pumpkin with a stem; "parrot's
  beak" gave an eagle's head. Describe the part plainly and put the compared thing
  in `must_not_show`.
- **"Stands", "shoulders" and "mouth" on a shapeless creature give it a gorilla's
  body.** List what it lacks ("no head, no neck, no chest, no arms, no legs") in
  `must_not_show` and say where the features sit ("the eye is set directly in the
  rock", "the entire front is the mouth"). Never give a shapeless creature "a
  woman's face" or any person's: list the features only (two eye-pits, a gash of a
  mouth).
- **Furry humanoids come out with a bare bodybuilder's chest** unless the brief
  says the chest, belly and arms are furred.
- **Natural animal colours drift:** a wolf goes German-shepherd tan, unnamed grey
  goes blue. Name the colour and exclude the drift ("grey and black, no tan, no blue").
- **A creature that is only a big real animal reads as the ordinary animal.** Give
  it a scale prop that touches it (the roc carries a small elephant) or a feature
  the ordinary animal lacks.
- **Archers:** "side-on" is not enough; the model draws the archer front-on with a
  bow arc on each side. Say "seen in full profile like a figure on a coin, the bow
  a single D shape at the left of the picture, entirely in front of him".
- **A big skeleton turns into a muscle-man** on words like "huge fists", "thick as
  tree trunks", "towering giant". Describe it bone by bone, say "no muscle" in the
  body sentence, and put "muscles, bodybuilder body" in `must_not_show`.
- **A size comparison draws the compared animal.** "The size of a hound" gave a dog
  in a beetle's shell. Say "a real scarab, an insect, drawn large".
- **An animal pelt worn as a hood becomes an animal-headed man.** Drop the hood or
  say "a fur cloak; his own human head is bare".
- **A glow's colour tints the whole body.** A yellow-green eye glow turned a bone
  giant green. Keep glows small and say the body's colour again after them.
- **Do not name limbs in the body sentence of a limbless creature, even to deny
  them.** "No arms and no legs" there invites them. List limbs only in
  `must_not_show`.
- **Many small parts wash out at 64 px.** Hundreds of small bones became a pale
  blob. Ask for fewer, larger parts with dark gaps between them.
- **A long dagger is drawn as a second sword**, and "pistol" as a modern revolver.
  Say "a short knife no longer than his hand" and "a single-shot flintlock".
- **A named animal brings its whole look.** "Male lion" forces a mane even with "no
  mane" stated; "looks like an enormous lioness" removed it. "Donkey-like ears" on a
  lion's head made a jackal: say "small round ears".
- **"Flanged mace" draws a hammer.** Say "a round ball on a rod; nothing sticks out
  sideways".
- **"Wrapped in chains", with rust named, drew a skinless red muscle-man.** Say
  "coiled like rope round a post, big oval links, gunmetal grey, no flesh".
- **A magic colour leaks into robes and skin.** State the cloth and skin colours and
  put "green robes, green skin" (or whatever the magic's colour is) in `must_not_show`.
- **A number of wings or heads is ignored; a silhouette is kept.** "Four wings" gave
  two; "two up, two down, an X shape" gave four. Two heads need the necks placed:
  "forks like a Y, one head high, one low".
- **A hood "pushed back" is drawn up.** Write "no hood, bare head".
- **A single eye:** "no ordinary eyes, smooth skin there; one eyeball as wide as
  half his face" worked where "an eye as big as his fist" gave a third eye.
- **A half-and-half face (half skull, half flesh) does not draw.** Pick one.
- **Mark shapeless creatures `"body": "shapeless"`** (see the field table). Without
  it a storm cloud got a small man under it three rounds running.
- **A creature made of an element must not be given a person's parts.** "Head,
  shoulders, arms, upper body" on a fire creature gives a red muscle-man with legs.
  Say "one tall flame; tongues of flame lash out from each side; two eyes set
  directly in the fire".
- **"A chain of boulders" draws metal chains.** Say "an arm made of three boulders,
  one after the other, touching". "Angular blocks" gives toy-block robots: say
  "jagged slabs with slanting broken faces, none of them square".
- **"Hollow eye-pits" draw a skull, on ice or rock too.** Use "two small glowing
  eyes set in the rock". "Eyes bright as lamps" on a shapeless creature gives googly
  cartoon eyes: say "narrow slanted glowing slits, no pupils".
- **"A small sun" draws a sun with a human face.** Say "a ball of fire with spikes
  of flame". "Looming" with "fierce eyes" on an abstract shape draws an old man's face.
- **An abstract creature (void, entropy, shadow) comes out as a flat cartoon blob
  with dot eyes.** Give it painted substance: depth, an edge that catches light,
  torn or boiling texture, and something it is doing.
- **This is a game for children.** No gore, no nudity, no torture. Rot, bones,
  stitches and fangs are fine. Female creatures are clothed like anyone else.

## Review

`_genart/<run>/REVIEW_<family>.png` shows each creature's candidates with its lists
beside them and a lineup of the family at the bottom. For each creature the reviewer
records in `review.json`: every `must_show` item present, no `must_not_show` item
present, the hands hold what `holds` says, and in the lineup each tier is told
apart from the one below. A creature with no passing candidate gets its brief
reworded and is drawn again; it is not passed with a note.

The reviewer also asks, of every pick, the questions that have no line in the brief:

1. Would someone who knows the game name this creature from the sprite alone?
2. Is anything inconsistent inside the figure (a clean part on a ruined body, two
   left hands, a weapon merging into an arm, a face on the wrong side)?
3. Is there anything under, behind or around the figure that is not the figure?
4. Does the 64 px sprite still show what the painting shows (the held thing, the
   face, the key feature)? If the painting passes and the sprite does not, it fails.
5. In the family lineup, can each tier be told from the one below at a glance?

`review.json` holds one entry per creature:
`{"<id>": {"pick": 2, "fails": {"1": "reason", "3": "reason"}, "note": "one line"}}`.
`"pick": null` with a note means no candidate is good enough after rework.
`picks.py` draws the overview sheet from it.
