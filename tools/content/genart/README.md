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
| `lift` | Optional number, default 1.0. Above 1 (try 1.3 to 1.6) brightens the midtones when the sprite is cut, for a dark thing that vanishes on the dark floor. It needs no redraw: change it and rerun with `--sheets-only`. |
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
- **Winged four-legged beasts stand up like men.** "One front claw raised",
  "rearing" or "chest out" turned nearly every dragon into an upright muscle-man.
  Put "walks on all four legs like a huge lizard" in `what`, and "all four of its
  feet are planted on the ground and its body is horizontal" in the pose.
- **"Half folded" wings come out fully spread.** Say "folded shut, lying closed
  along its back like a furled umbrella".
- **A long breath runs off the picture or turns into a rope or a held thing.** Say
  "one short jet shooting straight out of its mouth, joined to the mouth, no longer
  than its own head".
- **White or pale lightning on a magenta backdrop turns into a pink cone.** Bright
  yellow zigzag lightning survives.
- **"A ball of light the size of an apple" has drawn a literal apple.** Say "a
  round ball of flame as big as her fist".
- **Dragons grow a second head now and then.** `must_not_show` does not always
  stop it; reroll.
- **"Death-blue" skin comes out bright blue.** Say "very dark slate-grey with a
  blue-black tinge".
- **"Bulb" draws a glass light bulb; "pearl-white scale" draws a pearl.** Say "a
  glowing spot in the shell", "one pale scale".
- **"Greatclub" draws a mallet; a morningstar with a long handle becomes a staff.**
  Say "one straight length of wood, narrow at the grip, swelling to a knobbly end,
  nothing fixed to it", and "a short thick handle" for a mace or morningstar.
- **"Ruddy" or "sunburnt" skin goes bright orange.** Say "weather-beaten light tan".
- **A bird with a woman's head keeps the beak.** Lead with "the head of a human
  woman", list nose, lips and chin, and turn the face to the viewer.
- **A stone creature called a "statue" comes out as a flesh-toned bodybuilder.** Say
  "built of rough-hewn blocks like a castle wall, black seams between".
- **A side-view centipede turns into a shrimp.** Say "seen from above, an S-curve, a
  row of legs down each edge".
- **A ghost's gear takes its natural colour** (a brown wooden shield). Say the gear
  is the same ghost colour as the body.
- **A calm pose is ignored.** "Walks like a sleepwalker" drew a man strolling;
  "lurches, jaw open, arms reaching" is kept.
- **After changing a creature's `key`, redraw it** before any other call, or its
  old candidates are cut with the wrong backdrop and listed as failures.
- **A white beard, red mantle and white fur on an armoured king draws Father
  Christmas.** Change one of the three.
- **A shape word used for a detail gets stamped everywhere.** "Cross-shaped eye
  slit" put gold crosses on the chest and hammer.
- **"Beetle's shell, domed back" draws a turtle.** Say "ridged horny plates, banded
  across the chest, spikes down the spine".
- **A limb that ends in a blade or hook:** raised overhead it becomes a horn; called
  a "hook" it becomes a held tool. Say "from the elbow down the arm is one curved
  blade of pale bone, shaped like a crescent moon", and keep the arms in front of
  the chest.
- **A small painted mark tints the whole body its colour** (a blue woad spiral made
  a blue coat). Drop the mark or expect to reroll.
- **"Earth-brown" drifts to bright orange.** Say "dark mud-brown, the colour of wet
  peat".
- **A sting:** "ends in a sting" draws a plain tail; "a swollen black bulb with one
  curved needle-point" draws a scorpion's.
- **A creature made of metal that has a living form (an iron horse) comes out
  alive with tack on.** Give the metal its own parts: "the mane is a row of iron
  spikes, the tail a bundle of iron chains, no hair".
- **A lance or spear points wherever it likes** unless placed in the picture: "flat
  and horizontal, its point sticking out in front of the horse's nose at the left".
- **A monstrous hag given an unusual skin colour can come out as an ordinary living
  woman of that colouring.** Make the skin plainly unnatural (stone-blue, corpse
  grey, bark green) and give her inhuman features: iron claws, tusks, lamp eyes.
- **A food simile for a colour brings the food.** "Like lime jelly" drew a slice of
  lime. "Ropes of jelly" drew braided rope. Name the colour plainly; say "strands".
- **A helmet or boot inside a slime** becomes a bottle, or the slime becomes a man
  wearing it. Put "head wearing the helmet" in `must_not_show`.
- **Rust:** "rust-brown and orange-brown" armour comes out bright orange. Say "very
  dark brown, the colour of an old iron nail, nearly black in the shadows".
- **A beast with a human head** (sphinx, manticore, lamassu) keeps the beast's face
  unless the brief leads with "the head of a human man", lists nose, lips and chin,
  and turns the face to the viewer. "Ape's arms" gave an ape's face: describe the
  arms as "long thick shaggy arms".
- **Dull grey-blue on a magenta backdrop came out mint green.** Say "pale icy
  blue, the blue of a winter sky".
- **A short rod still draws a floor-length staff.** Say "gripped at its lower end,
  comes nowhere near the ground, like a king's mace".
- **A robed or caped lord in a still pose is a playing-card king.** Give him a
  stride with the weapon swung back.
- **A plain emblem ban is not kept** (a faint cross appeared on a tabard). Say what
  the surface is instead: "a plain black shield with a dented rim".
- **A golem called "man-shaped", with a torso, chest and face, is a bodybuilder
  painted in that material.** Describe it as a carved statue of something clothed
  or armoured ("a granite statue of a helmeted sentinel", "an oak statue of a
  door-warden in a long coat"). Building it from plain parts ("a log trunk, a log
  head with two notches") gives a toy puppet instead. For a brute: "hunched and
  neckless, small head sunk between the shoulders, arms thicker than its legs".
- **"Terracotta" clay comes out as bright orange skin;** "red-brown brick earth"
  gives a red ogre. Say "pale dried river clay, cracked".
- **Many small eyes and mouths become dots at 64 px.** Say "five big eyes and five
  big mouths, each a quarter of the body wide".
- **A dead guardian needs the word "corpse"** and a dead face (lips dried back from
  the teeth, skin shrunk on the skull); "withered" alone gives a living old man.
- **A glow "like a glove" draws white gloves.** Say "sparks crackle round the fist".
- **"Hanging from a ceiling" draws the ceiling and crops the figure.** Say "caught
  in mid-air as it falls".
- **A flail's ball on a chain is cut off as a loose piece.** Prefer a mace, or have
  the chain lie against the body.
- **A wyvern grows small arms on its chest.** Say "its wings are its only front
  limbs, like a bat's; it has two legs and no arms" and reroll if they appear.
- **To go back to an earlier round, copy that round's files back** from `_rN` into
  the creature's folder and rerun with `--sheets-only`.
- **"Yellowed" bone comes out as polished gold.** Say "dull grey-brown, dug from a
  grave, never gold" or "chalk grey-white".
- **A trail under a floating thing cuts out as a string** (a floating skull looked
  like a balloon). Ask for nothing beneath it.
- **A skull with its jaw wide open grows a red tongue** unless the inside is "only
  empty pitch-black darkness".
- **Eye beams are drawn as lines across the whole picture.** Ask for sockets
  "filled to the brim with solid light".
- **A pale head in front of a pale headdress vanishes at 64 px.** Make whatever is
  behind the head dark.
- **"Big, heavy, broad" with a beard, helmet and mail draws a living dwarf.** For an
  undead lord say "very tall, gaunt, long-limbed, never stout".
- **A withered face still draws a skull** unless the soft parts are listed: ears,
  nose, eyelids, lips.
- **A thing held near a flame catches fire too.** Say it is "cold, with no flame
  and no glow on it", and hold it low, away from the flame.
- **A missing limb is not drawn; both arms come back.** Do not design around a
  stump. **A two-handed sword is drawn one-handed, and a short sceptre as a tall
  rod:** accept it or describe the grip in the picture.
- **The backdrop check reads denials too.** "Never living pink" trips the magenta
  rule. Move the creature to another key rather than fight it.
- **Ten of one kind can be ten different creatures.** Give each its own robe
  colour, headgear, magic colour and one signature object from its lore (g11's
  liches: lantern and keys; a carried skull; Koschei's egg; spears through the
  ribs; a comb; an ermine mantle and ledger).
- **The backdrop colour tints skin.** Grey-green orcs on a blue backdrop came out
  yellow, brown or pink; on magenta they stayed green. Keep a whole family on one
  backdrop, and prefer magenta for green skin.
- **"Smeared with pale ash" removes the skin colour.** Say "broad stripes of white
  ash painted across".
- **"Single-bladed axe" draws a double axe.** Say "the blade sticks out on one side
  of the haft only; the other side is bare wood". A flame on a club is a torch.
- **Slimes, molds and oozes: words that worked and did not.** "Lobes" drew dead
  leaves, "round domes" furry fruit, "bloated folds" a muscle-man, "grit and
  mineral crust" a rock. "One rounded mound, soft all over, a front lip curling"
  and "one ragged uneven crust, no two lumps alike" drew a slime. A round shield
  sunk in a slime becomes an eye; broken blades sticking out are safe. Keep the
  colours dull and dirty, never glassy or candy-bright.
- **"Warty as a toad's" draws a toad's head.** Say "covered in warts".
- **A fat giant with plain skin is a fat pink man.** Give him a monster's face
  (jutting fanged jaw, pointed ears) and unnatural skin.
- **A boss told to "stamp forward" stands still facing the viewer.** Say "seen from
  the side, running at full tilt, body pitched far forward, one knee driving up".
- **A woman-serpent in a long dress becomes a woman sitting on a snake.** End the
  tunic at the belt, say "her snake body stands straight up under her like a
  pillar for the length of her torso, then coils", and give dress and scales
  different colours.
- **Yellow cloth:** "sand-yellow" comes out bright yellow and "cloth-of-gold" a
  yellow bathrobe. Say "undyed pale sand-beige linen", or "old dark gold brocade,
  the brown-gold of tarnished brass".
- **Hair "bound up in a column" draws a white post or a chef's hat.** Say "every
  strand floats straight upward, a tapering plume".
- **A covering over a woman's mouth is ignored however it is worded.** A gesture
  (finger at the lips) is kept.
- **"A ball of smoke in the palm" draws a solid orb.** Say "one small twisting wisp
  of smoke rising from the palm, joined to the hand".
- **A fish-man described feature by feature is an old zombie.** Say "the head of a
  fish set on a man's shoulders".
- **Several limbs round a centre all point down** unless each is given a direction
  ("one straight up, one left, one right, two down").
- **Glowing fists drawn as flat pale yellow look like cartoon gloves.** Give the
  glow a rim and keep the hand's knuckles and shape dark inside it.
- **Shadow creatures.** "A torn shroud of soot-black smoke hanging in the air with
  nothing inside it" draws a dark, folded, readable body. "The shape of a man made
  of smoke" or "a man's shadow" draws a naked man, an alien or a bodybuilder.
  Shade it "coal-black in the folds, dark slate-grey on the ridges" ("paler grey
  highlights on every fold" gives a pale gargoyle). The rim light is "one thin
  bright line of amber along its edge" ("a broad band of light" tints the whole
  body). "Cloak" comes out brown burlap: say "shroud of smoke, black as coal and
  never brown". Give it pale claws, a mask or a crown so the sprite reads on a dark
  floor.
- **A ghost that is dark all over is ignored and a living person is drawn.** A
  one-colour ghost has to be pale: "made entirely of pale ghost-light, every part
  the same pale colour". "Rose-white" gives candy pink: say "pale ash-grey with a
  faint dull mauve tint".
- **Smoke on a green backdrop leaves a green fringe.** Put smoky creatures on blue
  or magenta. **Legs that "dissolve into smoke" cut out as loose pieces:** have the
  smoke stream from the back, joined to the body.
- **Faces in a mass of souls:** "bone-white theatre masks of grief, hairless, black
  eye and mouth holes" survive at 64 px; "pale faces" gives realistic portraits.
- **A giant skeleton is an ordinary skeleton** until given a squat build ("nearly
  as wide as tall, skull sunk between the shoulders") and a small whole human
  skeleton in its fist for scale.
- **"Dark dead skin" on an undead draws a living dark-skinned person.** Undead
  skin must be a colour no living person has: "cold chalk-grey", "blue-grey like
  a drowned man", "grey-green", with sunken blank white eyes and lips dried back
  from the teeth. Check every wight, ghoul and hag for this.
- **A void creature given a "front end" and bracing limbs is a four-legged
  beast.** Say "one great knot of thick tentacles and nothing else, round a
  central mound no bigger than a barrel".
- **A black creature with "thin silver edges" is plain dark grey.** Name whole
  bright parts (silver-white horns, spine ridge, belly plates, claws) and a few
  large marks ("five very large stars, each as big as its paw").
- **Six wings:** counts and spokes give two. Say "a large upper pair; a second,
  separate, smaller pair from the small of its back, tips pointing at the lower
  corners; two more folded shut round its lower body like a sheath".
- **Leather "over" mail hides the mail.** Say the mail "covers his arms to the
  wrists and his thighs" and the leather is "on his chest only".
- **An undead warrior in full gear is a living Viking.** Bare the arms so dead skin
  shows.
- **A ball of light with flame tongues is a cartoon sun, and lightning on it is an
  onion with roots.** A wisp is "a small pale flame shaped like a candle flame, a
  white core, a faint trailing tail", and nothing else.
- **Length:** "four times as long as it is tall, belly on the ground" gets a long
  serpent where "immensely long" does not.
- **A made metal beast needs to look made:** "like a suit of armour in the shape of
  a bull, big riveted plates, jointed legs, black gaps between the plates".
- **A swarm asked for as "many" or "a dense cloud" draws texture or the wrong
  animal.** Count and place them: "five, each a third of the picture, bunched two
  in front, one above, one below, one behind, overlapping so no backdrop shows
  between them", or for a heap "about fifteen, each a fifth of the heap wide".
  Ask for it "wholly inside the picture": a wave of them runs off the frame.
- **A simile for behaviour is drawn too.** "Like a swarm of angry wasps" turned
  pixies into flies; "like the spikes of a thistle" turned a nailed club into a
  cactus.
- **A headless figure keeps a head on its neck** unless told "the body ends at the
  shoulders; the only head in the picture is the one he carries". Expect 1 in 3.
- **"Bald, domed skull" with a rock beside the ear draws a man holding a skull.**
  Say "hairless head, a living face" and "a jagged lump of quarry stone".
- **A jelly "slab of wall" is carved stone.** Say "soft, wet, bulging faces,
  rounded corners, things inside dim and blurred".
- **Six arms:** name the pairs ("top pair raised, middle pair sideways, bottom pair
  low; six swords in all, nothing behind her"). "Three on each side" gives a dozen.
- **A rock giant is "three boulders to an arm, one after the other, touching; legs
  are pillars of stacked slabs".** Moss turns it green all over: leave moss off.
- **A thin living servant comes out young and handsome** unless given an age,
  stubble, straggling hair and a stoop.
- **Keep denials ("no red", "never green") out of the `colours` field:** the
  backdrop check reads them as colours.
- **Wyvern:** "shaped like a pterodactyl; its wings are its arms; its two legs hang
  beneath its hips" removes the chest arms about half the time. "Talons thrust
  forward" brings four legs back.
- **A sting or club simile is drawn as its own object** ("like a scorpion's tail"
  drew a scorpion beside it; "round like a plum" drew a plum). Say "the tail
  swells into a fat glossy black club ending in a curved spike".
- **"Wildcat" or "tabby" draws a house cat at any size.** Say "a sabre-toothed cat,
  a smilodon", or "a heavy black panther with a broad blunt muzzle".
- **A drooping neck on a hoofed beast is ignored.** Say "head lowered to the level
  of its front hooves like a beast grazing".
- **A jewel on a forehead** "as large as its ear" is a balloon; "set flat like a
  third eye" replaces an eye. Say "a red gem the size of a walnut set in the
  middle of its brow, both eyes below it".
- **An animal's head on another animal's body only reads if the two are different
  colours** (pale barred feathers over dark fur for an owlbear).
- **Extra pairs of legs do not draw** (a six-legged beast came out with four in six
  candidates). Do not make them a `must_show`; carry the creature with another
  feature.
- **Demons need not be red horned bat-winged muscle-men.** Give each its own body
  plan and colour from its tradition (g18: a vulture-headed vrock, a toad-bodied
  hezrou, a jackal-headed glabrezu with crab pincers, a Maya death bat, a Balinese
  masked Rangda, one giant jewelled arm). Write the design table first, with the
  already-drawn creature each must not be confused with.
- **A hairy folk creature** "like an old sheepdog" gets a goat's head, and a "brown
  weather-beaten face" makes it a living bearded man. Describe the hair plainly,
  list a goblin face, and give stone-grey skin and pointed ears.
- **"Barrel-shaped" with eyes round the middle is a grinning cartoon egg.** Say "a
  massive upright boulder like a standing stone, plainly stone".
- **Something growing from the chest (a horn, a mouth) goes to the face in a side
  view.** Use a front view: "sunk into its ribcage and opening toward the viewer".
- **A legless djinn keeps its legs.** Say "the sash is the bottom edge of its body;
  directly under it one column of flame pours straight down".
- **Yellow skin words ("tallow", "ochre") come out gold or orange.** Say "cold
  grey-white like a wax candle".
- **Broad stripes on a robe draw a clown in pyjamas.** Use a plain dark robe with
  one patterned sash.
- **An empty suit of armour with a closed visor is a knight.** Raise the visor over
  "one large pure black hole" and put a black rent in the breastplate.
- **Thin head spikes vanish at 64 px.** Make each "as long as his face and as thick
  as a finger". **A wide-winged flier is cropped** unless the wings are "bent
  sharply at the wrist like two tall arches, tips pointing down".
- **"Bark-brown" or "resin-brown" undead skin also draws a living person.** For a
  mummy say no skin shows anywhere and the head is "a bundle of bandages with no
  face"; a gold collar or "Egyptian lord" draws a bare-headed man in jewellery.
- **Grey undead skin on a blue backdrop turned bright green, tan or living.** Put
  undead on green or magenta.
- **"Shirt and trousers" on a corpse draws a modern jacket and jeans.** Say "a
  medieval peasant's knee-length homespun tunic, rope belt, rag leg-wrappings".
- **Things stuck in a body are not drawn** (arrows became a quiver, a sword through
  the chest vanished). Use something worn instead: a noose, a broken chain.
- **A dead animal described as "dried hide over bones" is a healthy animal.**
  Describe its skeleton with a few tatters of hide, and name the skull's shape ("a
  dog's long narrow skull") or it gets a human one.
- **"Full profile like a figure on a coin" on an undead draws a living portrait.**
  Keep that wording for archers and riders.
- **Ghost-light:** "sea-green-white" comes out saturated mint. Say "pale bone-white
  with a faint grey-green tint, nearly white".
- **A fat undead ("belly like a drum") is a jolly fat man.** If the lore needs the
  bloat, make every other feature dead: grey skin, blank eyes, burial clothes,
  grave earth.
- **Eyes on a dark shapeless creature survive at 64 px** when written as "the two
  brightest things in the picture, each as long as a quarter of the body is wide",
  slanted, with no pupils.
- **"Shroud of ash" draws a cloth ghost;** "pillar of crumbling ash and cinders"
  draws a solid thing.
- **A lion's mane beats a man's face on a manticore.** Give the head human hair, say
  "no mane", and add a piece of human headgear; "as large as the lion's chest"
  makes the head oversized.
- **A slime that is "lumpy, clotted" with bones in it grows a face;** "smooth
  unbroken skin, nothing in it" does not. Scattered eyes and mouths collapse into
  one giant face unless each one's position is named.
- **Green cloth:** "moss-green" and "bottle-green" come out brown or olive; "deep
  emerald-green" gives green.
- **A caster's idle hand keeps growing props** until it is "a bare open palm turned
  to the viewer, nothing in it or near it".
- **"Bony brow, deep-set eyes, slit nostrils" on a bald monster draws a skull;**
  "broad fleshy face, jowls, thick lips" gives a living one.
- **A single eye the model will not draw on a face is drawn when something
  physical forces it:** a helmet face-plate with one round hole.
- **Three heads on one body:** "cheek to cheek so that they touch, chins level", a
  crown on every head, and no cloak behind them (a cloak makes the side heads
  look like animals standing behind him). A toad's head needs "hairless, no ears,
  no whiskers, mouth one slit the full width, eyes on top".
- **Burning fists:** "on fire like the head of a burning torch, the dark knuckles
  showing in the middle". A "thin white-hot rim" cuts out as a white outline.
- **Six arms, second recipe:** "three growing from each side, one below the other,
  like the spokes of a wheel".
- **A female figure's armour must be a different colour from her skin,** or it
  reads as bare at 64 px.
- **A leather coat over a furred humanoid's chest stops the bodybuilder torso.**
- **A long brief on a blue backdrop can come back as a sky gradient** and fail the
  cut-out; move it to green or magenta.
- **A blank or unfinished face needs a hood or a bald head round it.** With hair on
  the head the model always paints a finished face.
- **A coloured thing held in the hand can tint the whole creature** (a red gem made
  a rock creature maroon). Hold something of the body's own colour family.
- **A master's mark on a thrall works as a creature riding the skull;** a forehead
  mark and an eye glow do not draw.
- **Mark a legless flier "body": "shapeless" and never name its limbs:** that
  removed hind legs nine earlier candidates had kept.
- **"Starved" with a forked neck adds a third head.** **"Wing-flaps" on a flat
  lurker draw bat wings:** say "two triangular fins of solid flesh".
- **Making a dark sprite "brighter" can make it gaudy.** Prefer a lit edge and one
  bright feature to brightening the whole figure.
- **"Gaunt" with "bone-grey plates" on a fiend draws a ribcage and skull face.** Say
  "lean, wiry, fully fleshed". A demon is told apart most cheaply by giving its
  wings a different material and colour from its body (patched sailcloth, moth
  wings, vulture feathers).
- **Clay:** "two deep black holes for eyes" draws a skull; "two dark pebbles pressed
  in" does not.
- **Faces "sunk in the chest" draws flat masks in the flesh;** "faces on the
  shoulders" draws extra heads.
- **A prop that reads as the wrong object is fixed by listing its parts** (a
  saddle's high front, side flaps and stirrup irons). A small thing hung on the
  chest never reads; held up against the backdrop, it does.
- **To change one part of a good pick, reuse its seed** and change only that
  paragraph of the brief: the rest of the composition holds.
- **Objects (`"body": "object"`).** Stairs draw a person on them: say "the stairway
  is empty" and reroll. Floor slabs come out cornerwise unless "seen from directly
  above like a floor tile on a game map, edges parallel to the edges of the
  picture". Pale wood words ("ash", "ivory", "golden oak") come out as cream toys:
  use dark walnut or dark oak, "scuffed, darkened with age". "Satchel" is a modern
  handbag and "tan leather" bright orange: say "old courier's satchel of dark
  scuffed chestnut leather". A chair on legs is not a throne: give it "a solid box
  beneath the seat that goes straight down to the ground". Gas does not draw as
  gas. For a set of ten containers, settle each one's material and colour first.
- **A flat material is not a "face".** "The dressed face of a stone block" painted
  a carved human face on every wall. Say "a flat blank surface, nothing carved".
  Water and lava paint a bullseye unless told "the same everywhere, no centre, no
  rings, no part of the picture differs from any other".
- **A skin colour leaks into the clothes** ("grey-green skin" gave a green tunic).
  Name the cloth with its own strong colour. **Boils or sores on a bare chest read
  as a bare female chest at 64 px:** clothe the chest and put them on the head
  and hands.
- **To dull a good slime, change only its `colours` line.** Changing its shape
  words draws a crouching ogre.
- **When a pose keeps failing, change the action** (an archer holding the bow out
  with no arrow nocked drew cleanly where three draw poses failed).
- **A dark sprite redrawn with bright parts needs little or no `lift`:** 1.3 on top
  of a good redraw greys it.
- **A curved horn:** "bend in kinks" or "zigzag" is drawn straight; "one long single
  horn in the shape of a crescent moon, in one bold arc" is drawn curved.
- **A misshapen creature described deformity-first becomes another animal** (a
  bloated dragon was a rhinoceros). List the creature's own parts first (long neck,
  horned head, long tail), then the deformity.
- **Breath still runs off the edge:** stand the beast "in the right-hand two thirds
  of the picture; the whole left quarter is empty backdrop".
- **Close-fitting dark clothing on a dark-skinned figure reads as bare skin.** Give
  the clothing its own colour. **A gaunt animal comes out well fed** unless the body
  sentence leads with "starving, as thin as a greyhound".
- **Eyes at 64 px:** "one round spot of solid bright red light as big as its nose".
- **A sphinx with a large woman's head gets a woman's bare chest.** Say "the deep
  furred chest of a lion between its front legs" and give it a broad collar.
- **Crossbow:** "a capital T made of two thick parts: the upright is the stock, the
  crossbar is the bow, bent in a deep curve with both ends swept far back" draws
  reliably (upright; the diagonal pose is ignored). "Broad flat bar" gives a mallet.
- **A thick bow stave:** "a heavy curved beam of timber, as thick as a fence post
  along its whole length, only seven times as long as it is thick".
- **Mail mesh at 64 px needs a ring count:** "every ring as big as a man's open
  hand, only six across the chest, fourteen rows neck to hem".
- **Templates: use two greys** (dark charcoal hide, bright pale iron hoops) so bands
  survive every tint.
- **Oddly coloured meat:** put the colour on the hide or rind; keep the cut face
  ordinary red or pink with white fat and a bone, or it becomes a vegetable.
- **A sac** drawn upright with a neck is a potion flask; lying on its side with a
  limp tied tail it is a sac. A dark mass "seen through the skin" drifts to an eye;
  an opaque warty skin, longer than tall, drifts to a cucumber.
- **A glint of light:** "a plus sign: one spike up, one down, one left, one right";
  "four-pointed star" draws five points.
- **Place a part by picture position** ("the crossguard exactly at the middle of the
  picture") when length ratios fail.
- **Lead: never `git checkout` a briefs file while a batch's edits are uncommitted.**
- **Tendrils "curling" on a flame close into loops** that read as handles. Use
  "broad streamers curved like a sabre blade, two swept up, two swept down".
- **A void:** "one round hole of pitch black with a thick bright rim, as round as the
  moon", masonry "touching the rim, half swallowed". "Torn rent" gives shards.
- **An abstract creature needs one concrete emblem** (an hourglass for entropy),
  "compact, wholly inside the picture, clear backdrop on every side".
- **Pale grey skin on magenta comes out mint green**; use the green or blue backdrop.
- **"Murky slime" draws a mossy stone block.** Keep "see-through jelly" and dull the
  colour: "dull dark olive-green like bottle glass full of ditch water".
- **Clay:** "pale dried river clay with wide black cracks" draws the cracks.
- **A construct as "a cask of oak staves" is a toy barrel.** "An enormous suit of
  armour in the shape of a hunched guardsman, nobody inside" worked.
- **Manticore:** a black mane brings the lion's face back; give human hair, a human
  beard and a brow band.
- **Eyestalks need a thickness and a small count** ("seven, each as thick as an arm").
- **Gorgon as monster:** "the gorgon mask from an old Greek shield", hunched, claws
  thrust out; skirt "whole and closed all the way round, hides both legs".
- **Dulled green skin on a blue backdrop is lost** ("pond scum", "sage" drew living
  people). On magenta, "dark pond-weed green, plainly green, a green no living person
  has" drew green skin.
- **A flame in the hand:** "the whole hand is wrapped in fire, like the head of a
  burning torch; he holds no candle, no torch, no stick". "A candle flame rising from
  the palm" draws a candle.
- **A skull carried in the hand turns the carrier's face into a skull** unless the
  face's soft parts are listed (nose, ears, eyelids, lips).
- **A beast-man "covered in hide" with a bare chest is a grey bodybuilder.** Armour
  the chest and name the hide patches on face, forearm and thighs.
- **"Coal-black lava rock; it is rock and not skin"** stops a fire giant coming out
  as a brown-skinned man.
- **Crown:** "low, flat-topped, shaped like a drum, with bull's horns from its sides".
  "Cone-shaped crown" is a wizard's hat.
- **A sober lion:** "tawny straw-gold with a dull sheen" and a near-black mane;
  "burnished gold" gives orange.
- **A pale hooded coat with red drifts toward a trademarked game assassin**; check
  each candidate.
- **`lift` below 1 (0.6 to 0.8) cuts darker** with no redraw; it does not desaturate.
- **"Rust-red" fur is bright orange.** "Dark red-brown, the colour of old mahogany,
  nearly black along the spine" is sober.
- **"Pale amber glue" in an open chest is lava.** "Dull grey-white, the colour of old
  candle wax", the inside "nearly black", gives a mimic.
- **A slime "sagging in heavy rolls one above the other" is a coiled snake.**
- **A pale mask under pale hair has no face at 64 px.** A black iron mask with
  eye-holes "filled to the brim with solid light, each a third of the mask wide" reads.
- **A snake-woman's scales must be neither skin colour nor her dress colour**
  ("pale grey-green, the colour of dry sage leaves").
- **Ghost white:** "pale ash-white, the colour of fog and old bone"; "bone-white with
  a grey-green tint" comes out mint on magenta. **A female ghost's gown must be "a
  second, much darker ghost-colour"**, loose, or she reads as bare.
- **"Light brown skin" round a masked man's eyes turns his black clothes brown.**
- **A steel plate under a hanging chain cuts out as a white ball**; make it dark.
- **A thing "raised to the chin" hides the face**; say "a hand's width below his
  chin, his whole face showing above".
- **The blue backdrop is behind most orange drift** on tawny beasts (sphinx, griffin,
  peryton). Move to magenta with "dusty sand-brown, the dull dun colour of a real lion".
- **Sand or dust trails on green leave an olive fringe**, as smoke does.
- **A black creature reads when its extremities are named pale** ("pale bone-grey
  horns, claws and shroud").
- **A sober cockatrice:** "black feathers with a dark green sheen, a collar of dull
  straw-gold hackle feathers, grey legs and beak"; any "tawny gold" gives a rooster.
- **A swarm of three, "each half the picture wide"**, reads at 64 px; five do not.
- **"Big bright eyes" on a spider draws a cartoon face.** "A tight cluster of eight
  small round black eyes like beads, the blank head of a real spider, with no face".
- **Sphinx redraws still give one bare-chested candidate in three**; check every one.
- **Plain steel takes the backdrop's opposite tint** (rose on green, brass on blue).
  "Blackened iron, dark gunmetal grey, with bright pale steel-white worn edges" on
  magenta gives true grey steel.
- **Do not ask a dark rock creature for "mid-grey rock with pale lit edges"** (pale
  bodybuilders); keep the dark wording and use `lift`.
- **Rock head:** "a lumpy boulder of the very same basalt as the body, wider than
  tall, set low between the shoulders".
- **Stairs down:** "every step one wide flat bar of stone with a black shadow under
  it, the top step as pale as the rim", the hole two thirds of the slab.
- **Gas trap:** wispy smoke over a grille with a pale green stain on the stone; the
  stain carries the "gas" read.
- **"Bright jade green" is neon**; "dull dark jade stone, a greyed deep green".
- **An identity cap (redcap)** needs "strong, saturated blood red, by far the
  brightest colour in the picture" over a pale garment.
- **A scourge has no reliable wording yet** (thick ropes: giant loops; thin cords: a
  paddle).
- **A mirror-bright surface:** "brightest in the centre, shading to the rim, with two
  broad slanting streaks of white light, like sunlight on a window pane". "Upper left
  half bright, lower right half dark" draws a hard two-tone split.
- **A T-shirt-shaped armour** is fixed by removing the sleeves and making the hem a
  row of scale tips or a fringe of tabs; "neutral iron-grey with no other colour in
  it" stops lilac drift on green.
- **Scars as "three slanting pale slashes" become candy stripes.**
- **Ancient sandals:** thin sole, "mostly open air: a sole and a few thongs"; high
  ones "a tall open lattice of straps standing up by itself like an empty cage".
- **A hand-wrap** needs "four short open finger tubes, each showing a dark empty
  hole", in the gauntlet pose, or it is leg guards.
- **Black lacquer with red lacing becomes tartan**; "one small red knot in the middle
  of every plate" keeps it black.
- **Lift above about 1.35 greys cloth and leather**; 1.2 to 1.3 is enough.
- **A single giant scale still has no reliable wording** (tortoise rings: a whole
  shell; bell outline: a skirt; teardrop: a ribbed pod).
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
