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
