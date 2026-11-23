# Food System: the Kitchen

**Status:** The kitchen rebuild (2026-11-14, `COOKING_REBUILD_PLAN_2026_11_14.md`, slice K1:
data, engine and menu functions; slice K2: the tabbed cook menu built on them, `ui.md` §13).
Harvest and the cook are one question each, as since v2.6 (harvest v4, cook v2).

**Owner:** Brandon (RaynfallLabs).

**Supersedes:** the one-cut-per-monster book (516 "X Prime Cut" / "X Pristine Marrow" parts,
`prime_cuts.json`), the outcome-archetype table (`cook_outcomes.json`, `outcome_id`), and the rule
that every meal fed the stat stamped on its meat (`cut_stat`). Older history: Harvest v3 (chain
mode, a T1-T5 stack of parts), the potency formulas, the Single tab.

---

## 1. Core design rules

- **Flow over gradient.** Harvest and cook are high-frequency actions: ONE question each, pass
  or fail (`feedback_flow_over_gradient.md`).
- **Resource loss IS the penalty.** The corpse (harvest) or the ingredients (cook) are used up on
  the attempt either way; no stun, no debuff (`feedback_resource_loss_is_the_penalty.md`).
- **SP soft boundary by generous supply.** Every dish gives SP; starvation at SP 0 stays as the
  failsafe (`feedback_sp_soft_boundary.md`). Do not remove starvation damage.
- **Nothing spoils.** A part saved on floor 3 still cooks on floor 40. Ingredients weigh nothing
  (Brandon, 2026-11-16; rations and dishes still weigh what they weigh), so saving is a choice
  paid only in the meal not eaten now.
- **People are not harvested** (Brandon, 2026-11-16: "that's weird, we're not cannibals"). A
  person's body is searched for the food he carried (§8.1); no dish holds a part of a person.
- **You are what you eat, at every depth.** Every stat has stat dishes at every tier, built from
  parts a hero can get at that depth (§4.3).
- **A special find is worth cooking.** Every quest, key or one-of-a-kind food has a decent dish
  of its own (§4.4); cooking it uses it up.
- **LORE, NOT FLOOR.** A dish's numbers come from its tier (the band of its deepest ingredient, a
  tier more for a dish of four parts or more: §5) in
  `data/cooking_rules.json`. Nothing is multiplied by the floor the hero stands on.

---

## 2. Code and data map

| File | Role |
|------|------|
| `src/kitchen.py` | Pure (no pygame). The book (`book`, `recipe`, `single_dish_for`, `dishes_with`), kin (`ingredient_for_monster`, `resolve`), a dish's numbers (`dish_outcome`, `dish_tab`, `dish_tier`, `dish_worth`), applying one (`apply_dish`, `salvage_dish`), the menu functions (`MENU_TABS`, `dish_effects`, `menu_rows`, `opening_tab`), the Kit line (`nature_line`), old saves (`migrate_ingredient`, `merge_stacks`). |
| `src/food_system.py` | The two quiz flows: `harvest_corpse`, `cook_compound_recipe` (and the unreached `cook_ingredient`); `_apply_recipe_outcome` (right: `kitchen.apply_dish`; wrong: ruined, or Persephone's salvage); the trophy powers (`_apply_permanent_power`); eating (`eat_food`, `eat_raw`); potions (`drink_potion`); `make_corpse`. |
| `src/main.py` | `Game._harvest`, `Game._cook_compound` (the quirk callback), `Game._cook_item` (unreached safety net), `_outcome_bonus_category` (Circe), `_migrate_legacy_ingredients` (old saves), the encyclopedia's Recipes page. |
| `src/game_menus.py` / `src/game_render.py` | The cook menu (`_open_cook_menu`, `_cook_menu_input`, `_draw_cook_menu`): a tab per main benefit, each with Ready to Cook, Building Toward and Legendary Feasts, the chosen dish's picture large (`ui.md` §13). The corpse dossier's "Harvest: X" line. |
| `src/cook_menu.py` | Pure: the cook menu's words (why it opened where, a row's chip and second line, what to do about a missing part, the empty tab's line) and the list window. |
| `src/player.py` | The caps: `feed_cut_stat(stat, tier)` (the floor's stat lesson, a whole point), `cut_stat_block(stat, tier)`, `stat_cap_for_tier`, `depth_tier`, `try_apply_cook_hp_gain` (max HP: the floor's cap only), `try_apply_cook_stat_gain`, `cooking_stat_softcap`, `food_taught`, `reset_floor_cook_caps`; `cooking_mp_gained` (max MP from feasts, read with `getattr`). |
| `src/status_effects.py` | `apply_effect(..., cap=)`: a meal's power may run past the usual 60 turns, up to its `max_turns`. |
| `data/items/ingredient.json` | Every ingredient (§3). Built. |
| `data/items/harvest_map.json` | Monster -> ingredient; retired ids -> kept ids (§3.2); `people`, the kinds searched, never harvested, and `people_parts`, what an old save's part of a person becomes (§3.5). Built. |
| `data/items/recipes.json` | The recipe book (§4). Built. |
| `data/cooking_rules.json` | Every number a dish gives (§5), and `search`: what a person's body gives when searched (§8.1). Hand-written. |
| `data/items/food.json` | Rations: eaten as they are, and called for by many dishes. `special: true` marks the special foods, each in a dish of its own (§4.4). |
| `tools/content/kitchen/` | `build_kitchen.py` (the build and every check), the content (`kin_groups.txt`, `people.txt`, `ingredients_*.txt`, `dishes_*.txt`), the frozen structure (`structure.json`), `dish_art.py` (which picture each dish shows, §4.2), the catalogue of what each picture shows (`dish_pictures.json`), the record it writes (`dish_art.json`) and the dishes still waiting for a fair picture (`dish_art_no_match.json`), snapshots of the old data it reads colours and trophy text from. Keeping the book cookable (§4.1): `part_freq.json` (how often each part turns up in a simulated run), `part_freq.py` (makes it), `part_rules.py` (the rules), `restructure.py` (edits the structure by them). |

The old generators (`tools/gen_recipes*.py`, `tools/gen_ingredients_v265.py`,
`tools/tune_sp_soft_boundary.py`, `tools/balance/fix_broken_ingredients.py`,
`tools/balance/generators/generate_ingredients_recipes.py`) are marked RETIRED and refuse to run.

### 2.1 Rebuilding the data

1. Edit the content: `kin_groups.txt` (who shares), `people.txt` (who is a person: searched,
   in no kin group; the build fails on a monster in neither), `ingredients_*.txt` (`key | nature |
   name | description | single dish | flavour`), `dishes_*.txt` (`dish_id | Name | flavour`). A
   hand-made dish is a row added to `structure.json` and named in `dishes_4.txt` (as the
   special-food and stat dishes of 2026-11-16 were).
2. `py tools/content/kitchen/build_kitchen.py` merges them with the frozen `structure.json`,
   writes the three JSON files and checks every rule (one single and two multi-dishes per
   ingredient, 2-5 parts, no forbidden food, banned words, the name says the part, every picture,
   unique names). Each dish's `art` comes from `dish_art.py` (§4.2), so renamed or new dishes
   get the right picture with no table to edit.
3. `--structure` regenerates the structure (who goes into which dish) and the naming skeleton.
   Its dish ids change, so every multi-dish must be renamed: do it only for a real redesign.
4. When spawns, the harvest map or the kin groups change: `py tools/content/kitchen/part_freq.py`
   (about 17 s a simulated run; 15 by default) rewrites `part_freq.json`. If the build then fails a
   cookable rule, `py tools/content/kitchen/restructure.py --log FILE` swaps the rare parts out
   (its `KEEP` / `SWAP` tables hold the hand-picked choices), adds dishes for parts left short,
   and writes a naming worksheet; name the new dishes in `dishes_3.txt` and rebuild.

---

## 3. Ingredients

**306 ingredients:** 282 monster parts, 14 boss trophies, 10 foraged finds (cave mushroom, swamp
moss, river salt, crystal shard, holy water, altar incense, deep-iron shaving, abyssal kelp, and
the quest pets' Starnut and Sunroot, which also grow as ordinary forage from floors 25 and 40).

### 3.1 Names and pictures

Each part has a vivid name of its own that keeps the kind of part its picture shows (the old
name's last words told it): a cut stays a cut (Goblin Gristle, Basilisk Tail Steak, Ogre Bangers),
a marrow picture stays bone or ectoplasm (Zombie Shinbone, Wraith Ectoplasm), an ichor stays a
liquid (Hezrou Toad Venom), a sac a gland or bladder (Rust Monster Rust Gland), a core a stone
heart (Clay Golem Amber Heart), a mote a glowing acorn or spark, an essence a jar (Bottled Blizzard), a
scale a scale, heartwood a log or stalk. `part` in the data names the kind; the build and
`tests/test_kitchen_rebuild.py` check the name says it. No "Prime Cut", "Choice Cut",
"Pristine", "Pure", "Concentrated", "Engorged" or "Glittering". People give no part at all
(§3.5).

Every ingredient keeps its own existing picture (`assets/tiles/items/<id>.png`); no new art. The
Calydonian Boar, which had none, took the unused `asterion_minotaur_prime` ham.

Each ingredient has a `description` (its lore line in the Kit) saying what it is and hinting what
it is good for in a kitchen, and the Kit's summary line says its nature and how many dishes call
for it (`kitchen.nature_line`: "Arcane: MP dishes | In 4 dishes").

### 3.2 Kin share (`harvest_map.json`)

Close kin that differ only by rank or role share one ingredient: every goblin, goblin shaman,
sniper, warpriest and kingslayer gives Goblin Gristle; orcs from scout to warlord give Orc Salted
Haunch; liches from thrall to arch-lich give Lich Frost-Bone. Named creatures, bosses and kinds
with lore of their own keep their own (the goblin king's Royal Sausage; the seven seal demons;
every trophy). A creature with no picture of its own joins its nearest kin (the Greater Erinyes
the Furies' ichor, Stheno and Euryale Medusa's links). The kept id is one member's
`<monster>_prime`. An ingredient's floor (`min_level`) is the median of its pictured members'
peak floors.

Every retired id is in `aliases` (`goblin_shaman_prime` -> `goblin_prime`): harvest
(`load_ingredient_for`), recipes, the pack's counts and old saves all read through
`kitchen.resolve`. The full sharing list is `tools/content/kitchen/kin_groups.txt`.

### 3.3 Nature

What a part is rich in, from its lore: `hp` (hearty: a troll, a bear), `sp` (filling: a mimic's
glue, an ogre's bangers), `mp` (arcane: a wraith's ectoplasm, a lich's bone), `stat` with its
stat (`stat_grant`: a cobra sharpens DEX), or `special` with a timed power (`temp_power`: a
shade's gloom-jelly gives Dark Vision, a basilisk's tail a Body Ward). Counts: 47
hp, 51 sp, 42 mp, 94 stat (STR 26, DEX 16, INT 14, CON 13, PER 13, WIS 12 with the forage), 72
special. Every nature has parts in every depth band; casters find arcane parts from floor 1 to
floor 97.

### 3.4 Secrets

`secret: true` marks the cow level's two parts (Hell Bovine Sirloin, Cow King's Royal Bacon). A
dish needing one never shows on the menu until the hero holds that part. (The Stray Kids zombies
leave no corpse; the deadites and Old Nickel share the zombie's and the goblin's part.)

### 3.5 People are not harvested (Brandon, 2026-11-16)

"Humans are not harvested. That's weird, we're not cannibals." Who is a person is decided by
lore, in `tools/content/kitchen/people.txt` (the build writes it to `harvest_map.json`
`people`, 58 kinds): humans and the human-like folk. That is every one of the mortals (the
bandits, cultists, knights, guards, the angry villagers, witches, assassins, the Iron Patriarch,
the Black Knight, the sown men, the mind flayer's thrall, the necromancer's apprentice), the
horns' allies (Robin Hood's men, Arthur's knights, the einherjar, Charlemagne's host), and the
elves, the hidden folk and the Nibelung dwarf. Goblinoids, orcs, gnolls, kobolds (Old Nickel
too), lizardfolk, giants, ogres and the undead stay as they were, and so do the were-beasts, the
serpent folk, the hags, Baba Yaga, the Green Knight, the Erlking and the fairies (people.txt says
why for each). A creature monsters.json does not know is a person when its body says it is one
of the mortals (Gilt Varro: `kitchen.is_person`).

A person is in no kin group and yields no ingredient; his body is searched instead (§8.1). The
twelve parts that came from people (Bandit Trail Ham, Cultist Blood Sausage, Knight's Marching
Ham, Battle Mage's Salt Ham, Assassin's Shadow Ham, Witch's Hedge Sausage, Snake Charmer's Spiced
Ham, Inquisitor's Fasting Ham, Iron Patriarch's Feast Links, Thrall's Pickled Ham, Drow
Spider-Sausage, Elf-Light Acorn) and their single dishes are gone; each of the 52 multi-dishes
that held one has a creature's part, a ration or a foraged find in its place, its benefit kept
(each one is listed in the commit message of 2026-11-16). `people_parts` maps every part a
person ever gave to the ordinary food it was in his pack: an old save's held one loads as dried
meat (the elves' acorn as elvish bread), the same count, where it lay.

---

## 4. The recipe book (`recipes.json`)

**1,097 dishes**, 334 of them on the two low rungs (§4.5). The rebuilt book of 2026-11-16 had 703: 306 single dishes (one per ingredient: the everyday choice) and 397
multi-ingredient dishes of 2 to 5 different ingredients. Every ingredient is in exactly one single
dish and at least two multi-dishes. 36 multi-dishes are legendary feasts; 142 are cross-depth. No
dish is named just like an ingredient (the build checks).

| Field | Meaning |
|-------|---------|
| `name`, `flavor` | The dish and its line. Real cooking with a dungeon twist; no two share a name. |
| `ingredients` | Ingredient ids and ration ids. One of each is taken from the pack. |
| `benefit` | The main benefit, which is the menu tab: `hp`, `sp`, `mp`, a stat, or a power id. |
| `legendary` | A five-ingredient feast with a permanent bonus (§5.3). |
| `trophy`, `permanent` | A boss trophy's own dish and its lasting power (§6). |
| `rung` | `plain` or `step`: one of the two low rungs (§4.5). No other dish has it. |
| `cross_depth` | Joins an early part (floors 1-20) with a deep one (40+). |
| `art` | The dish's picture (§4.2): `dish_<kind>_t<tier>_<tab>` for an ordinary dish, `feast_<name>` for a legendary feast, the boss's own `recipe_<id>` for a trophy dish. |

- **Single dishes** are `cook_<kin>` ("Goblin Gristle Stew"); trophy dishes keep their ids
  (`trophy_<boss>_recipe`) and names.
- **Common food goes in:** bread, dried meat, hard cheese, wild mushroom, apple, trail rations,
  healing herb, elvish bread, and the forage. Rare food (philosopher's tea; deep fungi and the
  void ration are in no dish now) counts as an uncommon part (§4.1). A special food (the dungeon
  carrot, the Starnut Tart, Tantalus' plum, the golden apple, ambrosia, the peach) goes only into
  its own dish (§4.4); the hearty stew, a meal already, only into the two low rungs (§4.5). The cook takes the ration from
  the pack.
- **Cross-depth:** about a third of the multi-dishes join an early part with a deep one: Goblin
  Gristle from floor 3 goes into the Gristle-and-Locust Harvest Pie with a floor-74 locust.
- **Legendary feasts:** 36, five ingredients each, deep (their deepest part tier 3+, so tier 4+ as big dishes): each of the 14 trophies anchors
  two, and the seven seal demons and Baba Yaga one each.

### 4.1 A book a run can cook (`part_freq.json`, `part_rules.py`)

The simulator measured, for every part, the share of mastery runs it turns up in and the floor it
is first found on. A part is **common** when it turns up in 90% of runs or more, or it is common
food or forage. The build fails on any dish that breaks these rules
(`tests/test_kitchen_part_freq.py` pins them from the game data):

1. **A feast's gate is its trophy** (its first ingredient; for the seal demons' and Baba Yaga's
   feasts, the boss part). Every other part is common, or an early part (first found by floor 20)
   that turns up in 75% of runs: the hunt is the gate, the rest is saving. Rare optional-boss
   trophies stay rare (Nidhoggr 7%, the Crone 13%): a feast keyed to one is the reward for
   hunting him.
2. **An ordinary multi-dish holds at most one uncommon part**, so finding a rare part means its
   dishes can be cooked.
3. About a third of the multi-dishes (the two low rungs aside) span depths, nine in ten of them joining an early common
   part (a saved part, a ration, cheese) with a deep one.

Before this (K1's book): 8 of 36 feasts and 109 of 257 multi-dishes were cookable in half of
runs. Now: all 36 feasts once the trophy is won (19 counting the trophy's own odds) and 229 of
375 multi-dishes. The eight that a simulated run never cooks hold a part the simulator never
meets: the cow level's two (secret), the mimic (it waits in chests) and Charybdis (summoned by
her scroll); each pairs only with common partners.

Dishes per tab and tier (`kitchen.dish_tier`: the deepest ingredient's band, a tier more for a
big dish, §5; before the big-dish rule of 2026-11-16 in brackets):

| Tab | T1 | T2 | T3 | T4 | T5 |
|-----|-----:|------:|------:|------:|-------:|
| HP | 36 (45) | 20 (15) | 12 (10) | 4 (4) | 16 (14) |
| SP | 62 (78) | 26 (10) | 4 (4) | 9 (11) | 7 (5) |
| MP | 41 (46) | 13 (10) | 13 (12) | 4 (4) | 14 (13) |
| Stat | 109 (140) | 60 (38) | 32 (32) | 25 (18) | 28 (26) |
| Special | 67 (80) | 42 (42) | 26 (18) | 10 (8) | 23 (20) |
| All | 315 (389) | 161 (115) | 87 (76) | 52 (45) | 88 (78) |

### 4.3 Every stat at every tier (Brandon, 2026-11-16)

"Fill the stat dishes in every tier." The dish's tier caps how far food and the altar can raise
its stat (§5), so a stat with no deep dishes stopped early: Dexterity had nothing at tiers 4 and
5 (it stopped at +18), Intelligence nothing at 4, Perception nothing at 5. Fifteen stat dishes
were added (dish_345 to dish_359), lore first: a deep part of the right depth whose lore is the
stat, often with a shallower one carried down.

Stat dishes per tier now (with the big-dish rule of §5):

| Stat | T1 | T2 | T3 | T4 | T5 | Added |
|------|-----:|------:|------:|------:|-------:|-------|
| STR | 26 | 20 | 5 | 4 | 8 | Forge-Giant's Anvil Links, Lion-Strangler Roast (T3) |
| CON | 14 | 9 | 3 | 3 | 7 | Old-Root Moss Pottage (T3); the Hesperides Garden Supper (T4) and the Monkey King's Stolen Peach Supper (T5) of §4.4 |
| DEX | 28 | 9 | 6 | 3 | 2 | Coiling Serpent Skewers, Leaping Locust Fritters (T4); Night-and-Coil Wyrm Kebabs, Sky-Rider's Hunt Supper (T5) |
| INT | 20 | 5 | 5 | 2 | 5 | Faust's Bargain Tea (T3); Dreaming Mind Broth, Frost-Bone Scholar Stew (T4) |
| PER | 15 | 11 | 5 | 4 | 2 | Night Watch Skewers (T2); Morning Star Watch Supper, Dragon's-Eye Night Skewers (T5); the Night-Owl Carrot Stew (T2) of §4.4 |
| WIS | 6 | 6 | 8 | 9 | 4 | Titan's Forethought Roast, Job's Whirlwind Supper (T4) |

The gate (`tests/test_cooking_rulings_2026_11_16.py`): every stat has at least two stat dishes at
every tier whose parts a hero can get at that depth: each part's creature spawns by the end of
the band (the spawn pool's bell, `dungeon._build_spawn_pool`) and its harvest gives the part, or
the part is found there (forage from its first floor, food where it spawns), and the deepest part
can be had within its own band (for a big dish, the band below the dish's tier).

### 4.4 Special food (Brandon, 2026-11-16)

"Every special item is used in at least one decent recipe, so a player is tempted to cook it
rather than save it for its special event." A special food (`food.json` `special: true`) goes
into one dish of its own (`build_kitchen.SPECIAL_FOOD`) and no other. Holding it shows that dish
under Building Toward, as a harvested part does (`kitchen.is_keystone`), and the detail pane says
"Find" (or "Cook" for the tart) where a ration says "Find or buy" (`cook_menu.part_source`).
Cooking it uses it up (`consume_ingredients`), so its event can no longer have that one; the
events are unchanged. Each dish is four or five parts, its deepest part of a tier where the food is found (the dish a tier richer: big dishes, §5), its
other parts common (§4.1).

| Food | Its event | Dish | Tier (deepest part) | Gives |
|------|-----------|------|-----:|-------|
| Magic Dungeon Carrot | the unicorn's trust | Night-Owl Carrot Stew (carrot, owlbear, beholder eyestalk, wild mushroom) | 2 (1) | PER (the night pilots' carrots) |
| Starnut Tart | the Mooble | Wishing-Star Miner's Pie (tart, star spawn ink, crystal shard, glabrezu ichor) | 3 (2) | MP |
| Tantalus's Plum | eaten, a big heal | Out-of-Reach Plum Pudding (plum, harpy, roc, healing herb) | 2 (1) | HP |
| Golden Apple of Hesperides | eaten, CON | Hesperides Garden Supper (apple, young dragon, hydra, Nemean lion, apple) | 4 (3) | CON |
| Ambrosia | eaten, every stat | Olympian Victory Banquet (ambrosia, titan, storm giant, pegasus, holy water) | 5 (4) | HP |
| Peach of Immortality | eaten, a stat | Monkey King's Stolen Peach Supper (peach, young dragon, fallen angel, apple, healing herb) | 5 (5) | CON |

Confirmed, not changed: the Mooble's Starnut and the Bococho's Sunroot (forage) each go into a
single dish and two or more multi-dishes; caviar and tater tots make the dish that plays
Brandon's song (§5.6); holy water (a coating too) is in 17 dishes. Not food, so not here:
Gleipnir's six impossible things (the fetter's, not the kitchen's), Idunn's Apple (a worn
accessory) and Soma (a potion). The hearty stew is an ordinary find, a meal already.

### 4.2 Pictures (`tools/content/kitchen/dish_art.py`)

Brandon, 2026-11-22: "a Goblin Cheese grill looks like a steak, tomatoes, and sausage... we need
to review our recipe art for consistency". The rule since then: **a dish's picture is of its
form, and shows no food the dish does not contain.** Then, where a picture allows, it keeps the
two cues every picture carries:

- **its tier**, by the vessel: dark walnut wood (1), tawny clay (2), black iron (3), bright silver
  (4), jewelled gold (5). A drink is in a cup, mug, tankard or goblet of that material, a pickle
  in a keg or urn;
- **its main benefit** (menu tab), by one colour cue: warm red for HP, amber-gold for SP, glowing
  deep blue for MP, emerald green for Stat, violet for Special (a broth, filling or sauce of that
  colour, or honey, leaves or flowers on solid food).

The pieces, all in `tools/content/kitchen/`:

- **The catalogue** (`dish_pictures.json`): every `dish_<form>_t<tier>_<tab>.png` looked at one by
  one: the form it looks like (a steak on a plate, a stew in a pot, a drink in a mug...), what you
  can see on it (`sees`), the foods on it (meat, bone, sausage, a whole bird, cheese, bread,
  tomatoes, mushrooms) and its colour garnish. A food marked `counts: false` is read as part of
  the form (a stew's potatoes, a stir-fry's onion shreds); the herb sprig, the violets, the honey,
  the blue glow and the red broth are the benefit's colour, never a food. The old HP pictures'
  red berries read as tomatoes, so they count.
- **The dish's form**, from its name (`FORM_WORDS`): the last form word decides ("Kuo-Toa Brine
  Ham Stew" is a stew), after a few phrases that end a name ("black pudding" is a sausage, "mixed
  grill" a fry-up, "leg roast" a leg; "Black Pudding Pie" stays a pie). A grill is a steak, a
  posset a drink, a bake a roast or a crust, a fondue a pot of melted cheese; a supper, feast or
  banquet names no form, so what it holds picks a stew or a platter. A name with no form word is
  a stew.
- **What it contains** (`contents`), from its ingredients: a creature's cut is meat on the bone, a
  bone part is bone and marrow, a gland or bladder is offal (meat), but an ooze's sac and a ghost's
  ectoplasm are slime, ichor is blood, a scale is scale, and a construct's core, a fey mote and an
  elemental's jar are no flesh at all; a bird's cut may roast whole; a part that is a sausage
  (Bugbear Bangers) is one. Staples are what they say (trail rations are jerky and hardtack). The
  form makes its own: sausages of meat or blood for a sausage dish or a fry-up, bread for a
  sandwich or toast.
- **The choice** (`judge`): a picture is FAIR when its form is the dish's own or one that reads
  the same (`FORM_FIT` rank 0 or 1: a platter as a carved roast, a bun as a stuffed roll, a jelly
  as a pudding) and it shows no counted food the dish lacks. Of the fair ones the dish takes its
  own tier (else the nearest), its own form, its own benefit (else the nearest colour: red and
  amber stand for each other, blue and violet), then the picture showing most of what it holds.

So the Goblin Cheese Grill (goblin gristle and hard cheese) shows the one grilled fillet with
nothing beside it, not the steak, sausage and tomatoes; a blood pottage shows a meatless pottage;
an HP dish whose form's red pictures all have tomatoes shows that form's amber or green one.
A dish with **no fair picture** (a meatless sandwich, a stir-fry of mushrooms or vines, a flambe
of ichor, a cheese board) shows the least wrong one (a near stand-in such as fritters for a
stir-fry costs less than a food it lacks; a far one, a dumpling for a sandwich, costs more) and
is listed in `dish_art_no_match.json` with what its own picture should show; its `wanted` counts
the dishes per form, tier and benefit that show another form, tier or benefit today: the list
for new art (a steak with no sausage at every tier first). The list only shrinks.

The rule reads only the name, ingredients, tier and benefit: a new or renamed dish needs no table
edit (`build_kitchen.py` calls it), and a new picture is used once it has a catalogue row.
`py tools/content/kitchen/dish_art.py` prints what it would change; `--write` re-places every
dish and writes `recipes.json` `art`, the record `dish_art.json` and the no-match list. Each
legendary feast has its own `feast_<name>.png` (`dish_art.FEASTS`), drawn for it from its name,
flavour and lore; the 14 trophy dishes keep their boss's `recipe_<id>.png`; a song's dish its
song's. The briefs are `tools/content/genart/briefs/items_dishes.json` and `items_feasts.json`;
the review sheets are `DISH_ART_REVIEW_2026_11_22_*.png` in the project root.

### 4.5 The two low rungs (2026-11-22)

Brandon: "I have to lug around all these ingredients with no way to use them (rations, bread,
cheese)... there should be more recipes that use these ONLY... as well as monster recipes that
are just ONE step above a single monster ingredient... so there is a strong mix and progression".

The nine staples are bread, dried meat, hard cheese, apple, trail rations, wild mushroom, healing
herb, elvish bread and hearty stew. Tea, deep fungi and the void ration are left to be eaten for
their stat.

- **Plain fare** (`rung: plain`, `fare_*`, 49 dishes): any two different staples make a dish, and
  there are eight threes and five fours. HP, SP, MP or a small power, never a stat. Its main
  benefit is `rungs.plain.main` (0.6) of a dish's, it adds no max HP ("you are what you eat": a
  creature's part builds the hero), and it has no snack's heal.
- **One step up** (`rung: step`, `step_*`, 285 dishes, two of them a part's second; 15 older pairs already served): every part
  of a creature has a dish of that part and one staple, the staple chosen by lore and by what
  drops at that depth. An HP, MP or Special part keeps its nature. A Stat or SP part's dish is a
  meal or a small power instead: the lesson is the part's own dish, and SP is useless on a full
  belly.
- **Reflex Ward** (`save_guard_DEX`: the DEX save against Slowed and Immobilized) is on these
  rungs in every tier: the pemmican of staples alone from floor 1, then kobold, blink dog, Cath
  Palug, marilith, wyrm, and a second step for the locust swarmlord and Pazuzu's spawn (Brandon's
  approval of the monster-effects proposal, 2026-11-22). The census holds it to every tier.
- **Both** give at least `rungs.cooked_over_raw` (1.25) of the SP and HP their ingredients give
  eaten as they are.

A step whose part is the hero's only one, and would teach him this floor cooked alone, is listed
last among the ready dishes and says "Cooked alone, Cobra Tail Steak teaches DEX +1"
(`kitchen.lesson_spent`, `lesson_line`): without it the simulated committed build lost the
lesson on about one floor in fifteen.

So the ladder is: two staples (worth 0.72), the part alone (1.0), three staples (1.2), part and
staple (1.8, as four staples), two parts (2.4), and the big dishes above them.

The content is `tools/content/kitchen/rungs_plain.txt` and `rungs_step_*.txt`.
`py tools/content/kitchen/build_kitchen.py --rungs` writes those dishes only and is idempotent.
(The full build refuses to run since the kinds of 2026-11-19 were written straight into the data.)
`tests/test_kitchen_rungs.py` pins the rules.

---

### 4.6 Variety: each part's strength and side gift (2026-11-22)

Brandon, on 3.6.1: "Recipes are not variable enough... many do EXACTLY the same thing, with
different art and ingredients". On 3.6.1, 1,097 dishes gave 523 different results: a dish's
numbers came only from its tab, its tier and a count of kinds of ingredient, so a rat gave what a
cave bear gave.

- **Strength** (`ingredient.json` `richness`, 0.75-1.35): a part's worth in a dish. It comes from
  its creature's hit points against its tier's typical creature, squashed smoothly so no creature
  ties with a smaller one, a little more for a named one, then reviewed by hand. Each tier
  averages about 1.0, so cooking's curve of max HP and stats holds.
- **Side gift** (`ingredient.json` `side`; the staples' in `cooking_rules.json` `sides.staples`):
  a small extra by lore. A power lasts 60 / 75 / 90 / 105 / 120 turns by the dish's tier, a heal
  adds 4-8% of max HP, mana 2-6 points. It is drawn from the element the creature strikes with,
  else an arcane part's mana, else its family's gift (a troll regenerates, a ghost lends sight of
  the unseen, a goblin dark vision), else a little healing. Every dish carries the sides of all its
  ingredients, once each and never its own power twice, and the menu shows them under "Also".
  A heal side is counted in the dish's own heal, which every card says (on the HP tab first; on
  any other beside its SP: "+150 SP, +31 HP"), since every dish heals. A gift this very meal makes
  lasting (a feast's resistance, a boss trophy's) is said only under For Good, never as timed
  (`kitchen.made_lasting`).
  The nine staples each give a different one: bread Fearless, dried meat Warning, cheese Cold
  Resist, apple Mind Ward, trail rations Searching, mushroom Dark Vision, herb Regenerating,
  elvish bread mana, stew a heal.
- **No side is poison resistance or the body's save,** agreed with the effects branch, which
  tunes poison. Nor is one of the strong defences (haste, shield, displacement).
- **Stat dishes** still teach one point, and carry their sides.
- **Every stat early** (Brandon: "I see a lot of some, but very few for other stats... players should
  be able to have enough choices early on"). On 3.6.1 a kid on floors 1-5 met DEX parts in 6.5% of
  what spawns and WIS parts in 0.1%. Five common early parts teach a stat by their creature's lore
  (`part_natures.txt`): kobolds INT (cunning trap-makers), the giant frog and cave toad WIS (the
  jewelled toad of the tales), myconids WIS (one mind through their spores), giant beetles CON
  (the shell), zombies CON (the dead never tire). Only the part's own single dish changes. Now each
  stat has 4-6 kinds on floors 1-10, and the largest share is under twice the smallest
  (`tests/test_kitchen_variety.py`).
- **Poison, agreed with the effects branch:** a poison dish of staples alone gives Venom Ward (a
  bite at half strength, for half its turns: `src/venom.py` on that branch), and only a creature's
  part, the venom's own antidote, gives Poison Resist. No side gift is either.

The content is `tools/content/kitchen/ingredient_lore.txt`, drafted by `draft_lore.py` (with the
review's corrections in its `HAND`), and written by
`py tools/content/kitchen/build_kitchen.py --lore`. `tests/test_kitchen_variety.py` holds every
tier and tab to 95% different results.

## 5. What a dish gives (`data/cooking_rules.json`, `kitchen.dish_outcome`)

**Tier** = the band of the deepest ingredient (floors 1-20 tier 1 ... 81-100 tier 5), and **a big
dish one tier richer** (Brandon, 2026-11-16: "Big dishes +1 tier", on a five-part Wild Game Pie
of floors 1 to 4 that was only tier 1): a dish of four or more different ingredients
(`cooking_rules.json` `big_dish`: `parts` 4, `tier_bonus` 1) is a tier above its deepest part's
band, at most 5 (`kitchen.dish_tier`, `base_tier`, `big_dish_bonus`). That tier is the dish's
everywhere: the cooking question, the stat cap it teaches to, its numbers, its picture's vessel,
the menu's "Question: Tier N", with one line under it saying why ("Five ingredients: one tier
richer.": `kitchen.big_dish_line`), the census and the simulator. The size bonus is apart and
unchanged.

**Worth** = what the ingredients add (a monster part its own `richness`, a trophy 1, a foraged
find 0.6, a ration 0.5; §4.6) times the **size bonus** for the number of different ingredients (1.0, 1.2, 1.35, 1.5, 1.6
for one to five). So a dish of N parts gives about 1.2x (two) to 1.6x (five) what the same parts
give cooked one at a time: saving and hunting for a dish pays, and eating as you go is never
wrong. A legendary feast or a trophy's dish multiplies its main benefit by 1.5 on top.

### 5.1 Every dish (food is food)

- **SP:** 24 / 32 / 42 / 50 / 60 by tier, times worth (shown capped at the bar). It was 60-150
  until 2026-11-22, when every meal fed half a belly and SP stopped mattering; halved, then
  tuned down a step more against the hunger targets in the simulator.
- **A heal:** `food_system.meal_mend_share` of 3 / 6 / 9 / 14 / 20 written (6% + written/80 of
  max HP: about 10% at tier 1, a third at tier 5).
- **Max HP:** +2 toward the floor's cap (5 a floor; `try_apply_cook_hp_gain`). That is the only
  cap on max HP from meals: none across floors (Brandon, 2026-11-16: "there should be a per floor
  limit to hp gained, but not a max across several floors... that encourages cooking"). Until then
  a lifetime cap (`Player.cooking_softcap`: 4 a floor reached, at least 20) also held it, and the
  sidebar said "Meals: go deeper for HP" once it was met; an old save's tally
  (`cooking_hp_gained`) is kept and stops nothing.

These keep a single dish of a tier near the old tier bands, so the simulator's baseline holds.
Plain fare is the exception to the heal and the max HP, and both low rungs to the least SP (§4.5).

### 5.2 The five main benefits (one per dish: its tab)

| Tab | What it does (single dish, by tier 1..5; times worth) | The choice it makes |
|-----|------|------|
| **HP** | Heals 18 / 22 / 26 / 30 / 34% of max HP (at most all of it), and +1 / 1 / 2 / 2 / 3 max HP on top of the 2 (inside the floor's cap). | Hurt, or building a tank. |
| **SP** | 100 / 125 / 150 / 175 / 200 SP in place of the usual. A dish of three ingredients or more, or a feast, also leaves you Sustained (hunger at half pace) for 60 / 75 / 90 / 105 / 120 turns, flat (until 2026-11-22: every SP dish, 100-800 turns, on for most of a careful player's turns). | Long floors, saving rations. |
| **MP** | Restores 25 / 27 / 30 / 32 / 35% of max MP, or 4 / 6 / 8 / 10 / 12 MP if that is more (max MP is small while INT is low). | Casters, before a boss. |
| **Stat** | The floor's stat lesson (`feed_cut_stat`): one whole point. How far a dish can raise its stat is set by its tier (`cooking_rules.json` 'stat' `cap_by_tier` 8 / 13 / 18 / 23 / 28 points over the start, Wisdom `wis_cap_by_tier` 4 / 6 / 9 / 11 / 14), and the altar's points count against it (`food_taught`). | The build. |
| **Special** | A timed power for 100 / 130 / 160 / 200 / 240 turns, at most the power's `max_turns` (Dark Vision 800, resistances 600, Haste 40, Shielded 60...). A ward (`save_guard_*`) is +1, +2 from worth 2, +3 from worth 3.5. | The fight ahead. |

A meal's power runs past the usual 60-turn status cap (`apply_effect(..., cap=max_turns)`): the
old book wrote 100-300 turns and every one was cut to 60 while the message said otherwise.

### 5.3 Legendary feasts: permanent bonuses

On top of the 1.5x main benefit, by tab:

- **HP:** +4 / 4 / 4 / 6 / 8 max HP, past the floor's cap (there is none across floors).
- **MP:** +2 / 2 / 2 / 3 / 4 max MP, at most 4 a floor from feasts and no cap across floors
  (Brandon, 2026-11-17: "same as HP"; `kitchen.feast_mp_cap`, cooking_rules `max_mp_floor_cap`;
  `Player._feast_mp_gain_this_floor`, reset by `reset_floor_cook_caps`).
- **Stat:** the floor's lesson (a whole point), and +1 more past the lesson
  (`try_apply_cook_stat_gain(bypass=True, tier=...)`), inside the cap of the feast's tier.
- **Special:** the feast's resistance for good (its own power if a resistance, else one of its
  ingredients', else the fallback order), never one its trophy gives and never one the hero holds
  for good already (`kitchen.feast_resist_for`: Fafnir's Blood gives fire resistance, so Fafnir's
  fire feast gives the next one). A timed power the hero already holds for good says so ("Fire
  Resist: already yours for good") instead of lingering for a number of turns.

Legendary feasts never have SP as their main benefit. A feast holding a boss trophy also gives
the trophy's own power (§6).

### 5.4 What the menu says (`kitchen.dish_effects`)

Plain lines for THIS hero now, main benefit first: "+45 HP", "+3 Max HP", "+12 MP", "Teaches DEX
+1" with "Tier 1 dishes teach DEX up to +8 (now +3)" under it, "Dark Vision, 300 turns", "+4 Max MP
for good", "+60 SP". A cap that would eat the benefit says so: "Max HP full this floor"
(`kitchen.max_hp_room`, the floor's cap), "DEX lesson used this floor", "DEX has learned all a dish this simple can teach" (its tier's cap, with
": deeper creatures teach more" on the limit line), "DEX has learned all food can teach" (the tier-5
cap), "Max MP: all a feast can give on this floor". A feast's For Good lines are held to the same
caps ("+2 Max MP for good" when 2 is what is left; "No more STR for good from a dish this deep";
its max HP has no cap: "+8 Max HP for good"), so the menu never promises more than the meal
gives. Cooked, a stat dish at its tier's cap says
"Your Dexterity has learned all a dish this simple can teach. Deeper creatures teach more."

### 5.5 Cook to carry (`makes`, 2026-11-14)

A dish may be **cooked to carry**: its recipe names `makes`, a food id in `data/items/food.json`,
and cooking it right puts that food in the pack, wrapped, instead of eating it
(`kitchen.make_to_carry`, from `apply_dish`). Nothing is eaten, so the hero's SP, HP and the
cooking quirks are untouched (`Game._cook_compound` tells the quirks only when the food itself
is eaten). A ruined one is wasted like any dish. Ingredients weigh nothing and food does, so the
dish can weigh more than what went into it: when the pack cannot take it, it is set down at the
hero's feet ("your pack is too heavy: you set it down at your feet"; `kitchen.take_set_down`,
emptied onto the floor by `Game._cook_compound`). Its benefit is `carry` (`dish_tab`: Special; `dish_power`: none), its menu lines
are `kitchen.carry_lines` ("Made to carry: one Starnut Tart into your pack", "If eaten: +70 SP,
+6 HP") and its chip says "To Carry" (`cook_menu.main_effect`).

The first is the **Starnut Tart** (`dish_starnut_tart`: Starnut, bread ration and apple), the
Mooble's favourite (`mooble_encounter.py`, `docs/systems/pets.md`). The food `starnut_tart` never
spawns (`floor_spawn_weight` 0), is a special food that goes into one dish of its own besides
(Wishing-Star Miner's Pie, §4.4; never back into the dish that makes it), is
never stolen, given as payment or sold (`items.WITHHELD_IDS`), and shows the dish's picture
(`renderer._UNIQUE_SPRITE_FALLBACK`: `dish_pie_t2_special`) until it has one of its own.

A dish the hero has **learned of** (`player.dishes_learned`, a set of recipe ids: the Mooble
tells of his tart the first time he is met) shows under Building Toward even before any part of
it is held (`menu_rows`). `build_kitchen.py` carries `makes` from `structure.json` and checks
that the food exists, is forbidden or special (`SPECIAL_FOOD`), is never in the dish that makes
it, and that no feast is carried.

### 5.6 A dish that plays a song (`song`, 3.5.2)

A dish may name a **song** (`song`, an id in `data/songs.json`; benefit `song`, so the Special
tab, `dish_power` none). Brandon writes songs as **A Man Before a King**; a song here is one of
his, and its words come from his lyrics. Eaten, the dish gives what every dish gives (§5.1), and
its power is the song's (`songs.begin`, from `apply_dish`): the soundtrack steps aside, the song
plays once, and for exactly as long as it plays, in real seconds, every blow and spell on the hero
does `damage_taken` of its damage (`Player.take_damage`; hunger is not a blow). Then the
soundtrack comes back and the power ends. Its menu lines are `kitchen.song_lines` ("Half damage
taken, for a while": the song is never named, it is the surprise), its chip "Half Damage"
(`kitchen.song_share`), and the
sidebar and character sheet show "Everything's Right 2:10" while it plays
(`songs.effect_label`).

The first is **Caviar and Tater Tots** (`dish_caviar_and_tater_tots`: caviar and tater tots,
the song's own art cut from its album cover). Both foods are rare plain finds (about one food
find in fifty each, every band), good to eat as they are with a line of their own (`eat_line`; a food may also end an ill as it is eaten, `stops`: the healing herb stops bleeding);
caviar sells dear and tater tots for next to nothing (`data/item_worth.json`). They go into no
other dish (`build_kitchen.SONG_FOOD`), and the dish shows on the menu only once both are held
(a ration alone builds toward nothing). Robyn starts with one of each (`_start_food`). Cooking it
earns the secret achievement Caviar and Tater Tots.

How the song runs (`game_songs.SongsMixin._song_frame`, every frame; `music.play_song` /
`end_song`): its clock is on the hero (`player.song_playing`: id, seconds left, muted), so a save
made mid-song plays on from where it was. One song plays at a time: the dish is not cooked while
another song plays (the power Math is Cool plays one too: `docs/systems/progression.md`). It plays
even with the music off; F5 mid-song mutes it
or brings it back (and sets the music to match), and its power keeps its time either way. A
dance's beat (`music.hold`) pauses the song and its clock. A fall ends it; so does the run's end
(the title screen hands the stream back to the soundtrack).

---

## 6. Boss trophies

The 14 trophies keep their permanent powers (`food_system._apply_permanent_power`), given by the
trophy's own dish and by either of the two feasts that hold it:

| Power | Trophy | Effect |
|-------|--------|--------|
| `all_stats_plus_1` | Abaddon | +1 to all six stats. |
| `plus_3_str` | Fenrir | +3 STR. |
| `plus_2_con_petrify_immune` | Hrungnir | +2 CON, Stoneproof. |
| `plus_2_wis_auto_reveal_secret_doors` | the Whispering Crone | +2 WIS, hidden doors near you show. |
| `plus_2_str_confuse_immune` | Asterion | +2 STR, Clear-Headed. |
| `fire_immunity` | Surtur | Fire Resist for good (half damage, never set alight; not immunity, despite the id). |
| `cold_immunity` | Ymir's Last Spawn | Cold Resist for good (half damage, never frozen). |
| `petrify_immunity` | Medusa | Stoneproof. |
| `chromatic_resist_all` | Tiamat | Three levels of fire, cold, lightning, poison and acid resistance (`damage_resistances`, 8% a level: about a fifth less). |
| `one_time_death_save` | Asmodeus | The next death does not take you. |
| `revive_once_at_half_hp` | the Green Knight | Once, rise at half HP. |
| `max_hp_per_floor_descent` | Fafnir | +2 max HP each new floor. |
| `max_mp_per_floor_descent_and_poison_immunity` | Níðhöggr | +2 max MP each new floor, Poison Resist. |
| `lifesteal_5pct_on_melee` | the Blood Archon | 5% melee lifesteal. |

A trophy's dish has a main benefit too (Fafnir's Heart: HP; Níðhöggr's Scale: MP; Fenrir's
Tooth: STR...), at 1.5x.

A raw trophy is never lost without a word (bug bash 3.5.1 Q2, 2026-11-16): eating it raw (Z),
feeding it to a pet or selling it to a trader first asks a yes / no (`MenuMixin._ask_before_trophy_goes`,
the shared `_ask` prompt; `kitchen.is_raw_trophy`, `kitchen.trophy_warning_lines`): one of a kind,
and what its dish gives. Enter or Esc keeps it; Y goes ahead. The cow and the Emberpup never take one.

---

## 7. The cook menu functions (`src/kitchen.py`, pure)

- `MENU_TABS = ('hp', 'sp', 'mp', 'stat', 'special')`, `TAB_NAMES` "HP", "SP", "MP", "Stat",
  "Special". `dish_tab(recipe)` gives a dish's tab.
- `menu_rows(player, inventory, tab)` returns rows (dicts: `id`, `recipe`, `name`, `group`,
  `ready`, `legendary`, `trophy`, `tier`, `have` / `missing` lists of `{id, name, have, need}`,
  `progress` "2 of 4", `value`, `effects`, `hunted`) in three groups:
  1. **ready** — cookable now, the most giving first (`dish_value`: plain fare after every dish
     with a part), and last any that would spend the floor's stat lesson (`lesson`, §4.5);
  2. **building** — the hero holds at least one HARVESTED part of it (a monster part or trophy)
     or a special food of it (§4.4; `is_keystone`; a ration or a foraged find alone does not
     count, or bread would list a hundred dishes) but not all, or the hero has learned of it
     (`player.dishes_learned`, §5.5); the closest first, then fewest missing, then value;
  3. **legendary** — the feasts and trophy dishes, their own group so the big payoff stands out:
     ready ones first, then the closest; shown once any harvested part is held.
  A dish needing a secret part never shows until that part is held.
- `opening_tab(player, inventory)`: among tabs with a dish ready — HP under half: hp; SP under
  30%: sp, else hp; MP under 40% with spells known: mp; else stat while the floor's lesson is open and a
  stat dish would teach; else the tab with the most dishes ready (with none ready, the most rows).
  A hungry hero (SP under 30%) always opens where food is, never on Stat or MP (bug bash 3.5.1
  Q4, 2026-11-16): with no SP or HP dish ready, the SP tab (the HP tab if only it has rows), and
  the line says so ('hungry_missing': "no SP or HP dish is ready: each says what it needs").
  `opening_choice` gives the same tab and why (`OPEN_REASONS`: 'hurt', 'hungry',
  'hungry_missing', 'mana', 'lesson', 'most_ready', 'most_rows', 'nothing'), so the menu can say it.
- `dish_lasting(player, recipe)`: the lines of `dish_effects` that last for good (a feast's
  permanent bonus, a boss trophy's power), shown under their own heading.
- `held_counts(inventory)` counts stacks, rations and old ids; `ready_dishes(inventory)` (every
  dish the pack can cook) is what `food_system.get_available_compound_recipes` returns.
- **Hunting** (Brandon, 2026-11-16): H in the cook menu on a dish still missing parts (Building
  Toward, a feast in progress) hunts it, H again stops; no limit (`toggle_hunt`, `hunted`: the ids
  in `Player.hunted_dishes`, kept in the save; an old save has none). The row reads "Hunting:" in
  gold, its missing parts are gold in the detail pane, and the footer says "H: Hunt" or "H: Stop
  Hunting". `hunted_parts(player)` is what the hunted dishes still lack; under In Sight
  (`hud_context.visible_context_rows`) a creature whose harvest gives one (`monster_hunted`) and a
  part lying in view (`item_hunted`) are drawn gold (`hud_context.HUNT`). A part held in the
  number the dish needs is no longer gold; a dish cooked right leaves the hunt (`apply_dish`).

---

## 8. Harvest (one animal question)

`Game._harvest` (`H`) searches a person's body instead (§8.1). For a creature, it takes the
corpse under the hero off the floor before the question, then
`food_system.harvest_corpse` asks ONE animal question at the corpse's `harvest_tier`, never
harder than the band the monster lives in (`_monster_band_tier`, the game's one band rule
`items._floor_band_tier`: floors 1-20 tier 1 ... 81-100 tier 5, so a gate boss of floor 20 is
tier 1; every kind in monsters.json carries a `harvest_tier` of 1-5). Right: the corpse yields its
kin's ingredient (`kitchen.ingredient_for_monster`; a creature the map does not name borrows its
nearest kin's, `_nearest_kin_ingredient`, by the family and floor in monsters.json or, for a
creature monsters.json does not know, on its corpse; never a person's, who has no kin in the
kitchen; a being of an encounter with no family yields nothing, said before the question by
`Game._harvest` through `food_system.corpse_yield`), plus one portion more for a family the hero has
learned to butcher (`family_edges.harvest_bonus`), never for a boss trophy (one of a kind: a
second Fenrir's Tooth gave its power twice, bug bash 3.5.1). The part remembers the creature it came from
(`source_monster`, read by Siegfried's Bath). Wrong: the corpse is ruined. A part too heavy to
carry stays on the floor. `quirk_system.on_harvest` fires either way (Mithridates).

**Butchered Before** (`src/butchered.py`, Brandon 2026-11-17: "once you have IDENTIFIED AND
SUCCESSFULLY HARVESTED a specific monster ONCE, you can automatically harvest any others"). A right
answer that gains a part remembers the corpse's monster id in `Player.butchered_kinds` (saved; an old
save has none), identified or not; a wrong answer remembers nothing. A later harvest of the SAME
kind skips the question when the hero has also studied that kind himself at that moment, by a corpse
study or the Wand of Probing (`family_lore.studied`; Brandon, 2026-11-17: "Only if studied": a page
opened by the Book of Thoth, Omnisight, a gate boss's quest or the family's tier does not count), so a
success recorded before the kind was studied counts from the moment it is. The free harvest is the right answer's harvest (`food_system._harvest_yield`:
the same part, the family's extra portion, the corpse used up, the turn spent), said by one line first,
the first free harvest of each kind only (`src/said_once.py`; Brandon 2026-11-22: "just noise")
("You know how to butcher a Giant Rat. No question needed."). It starts no quiz, so it sends no
`quiz_answer` (no answer counter, streak or answer quirk moves); the Seeker's `harvest` event carries
`free=True` and still counts toward `harvests`. The corpse dossier and the kind's Bestiary page say
"Butchered before: no question". A different kind, kin or not, asks its own question. The simulator
models it (`difficulty_sim._harvest_all`, with the families knob on).

Untimed: animal questions are never on the clock. Corpses weigh what the body weighs
(`items.corpse_weight`, `data/monster_sizes.json`: 2 lb tiny to 400 lb huge).

### 8.1 Searching a person (Brandon, 2026-11-16)

H on a person's body (§3.5; `food_system.corpse_is_person`) is `Game._search_corpse`: like
picking something up, no question, the body used up, the turn passed. `food_system.search_corpse`
gives one or two ordinary finds from what he carried (`search_finds`, `cooking_rules.json`
`search`): each drawn from `pack` by its weight for the floor's band (bread, dried meat, cheese,
apples and trail rations on top; elvish bread, philosopher's tea, deep fungi and the void ration
deeper down), never one whose own first floor is deeper than the floor; a person of a tag in
`by_tag` or a family in `by_family` carries one of his own first (a cultist his altar incense, a
caster a herb or tea, a bandit dried meat or cheese, an elf his waybread). Never a meat of a
new kind. The line: "You search the brigand corpse and take what was carried: Bread Ration and
Hard Cheese." What does not fit stays at the hero's feet. The corpse dossier says "A person: H
searches the body for food" in place of the Harvest line; under In Sight a person is never gold
for a hunt (he has no harvest). The simulator searches people too (`difficulty_sim._harvest_all`).

---

## 9. Cook (one cooking question)

`Game._cook_compound(recipe)` (the cook menu, `C`) snapshots the dish's tier and its first
ingredient's creature for the quirks, then `food_system.cook_compound_recipe` takes every listed
ingredient and ration out of the pack (`consume_ingredients`: stacks, old ids) and asks ONE
cooking question at the dish's tier. Right: `kitchen.apply_dish`. Wrong: "You ruin the
preparation. The X is wasted." (`food_system.RUINED_PREFIX`; the game reads the prefix, not the
letters "ruin", since a dish may be named for a Ruinous Djinn). Untimed.

### 9.1 Quirks

`on_food_eaten(quality, source_monster, bonus_type, ingredient_id, parts)` after every cook:

- **Tantalus** — 15 ruined dishes: +1 STR.
- **Persephone** — dishes of tier 4+ from 5 different first ingredients: from then on a ruined
  dish still gives half its SP, healing and MP (`kitchen.salvage_dish`; `salvage.share`), nothing
  else.
- **Circe** — five different kinds of dish (`_outcome_bonus_category` = `kitchen.bonus_category`:
  `permanent` for a feast or trophy dish, else the tab `hp` / `sp` / `mp` / `stat` / `special`;
  a ruined dish is no kind at all since 2026-11-14): +4 seconds on the cooking clock.
- **Siegfried** — eats parts of creatures with five different attack effects (the part's
  `source_monster`).
- **The Widow's Jar** (2026-11-14) — ten dishes of two or more parts, cooked right, with a ration
  or a foraged find among them (`parts`, `kitchen.part_kind` `food` or `forage`), the two low
  rungs not counted (§4.5; `rung`): from then on
  plain food eaten as it is gives half again its SP (`eat_food`).
- **The Fatted Calf** (2026-11-14) — a boss trophy carried down to twelve new floors
  (`QuirkSystem.on_stair_use`): from then on a legendary feast also heals fully
  (`_apply_recipe_outcome`).

**The harvest stamp (2026-11-14).** `Game._harvest` stamps every part with `harvest_floor`, the
deepest floor reached when it was harvested; a stack keeps the oldest (`Player.add_to_inventory`).
`main._cook_facts` reads it for the Seeker's Worth the Wait (a part carried thirty floors down).

---

## 10. Eating without cooking

- **Rations** (`eat_food`, `data/items/food.json`): their SP and HP, and a rare food's own stat
  gift (philosopher's tea, the golden apple, ambrosia: outside the floor's lesson, under the
  cap of a dish of the deepest band reached, as an altar's rededication is).
- **Raw** (`eat_raw`): `raw_sp` (10 for every monster part) or the `tier_role` map; monster parts
  are `edible_safe` (never poison); a foraged find can poison (30%) without poison resistance.

---

## 11. Saves

- **Old ingredients** (`Game._migrate_legacy_ingredients`): every Ingredient in the pack, any
  sack, the floor and stored floors: a retired id becomes the kept one, its name and fields come
  from today's data (`kitchen.migrate_ingredient`), and in the pack and sacks two stacks that are
  one ingredient now are joined (`kitchen.merge_stacks`). A part a person once gave
  (`harvest_map.json` `people_parts`) becomes the ordinary food it was in his pack (dried meat;
  the elves' acorn elvish bread), the same count, where it lay. An id the kitchen does not know
  is dropped. A hunt for a dish that is gone is quietly skipped (`hunted_parts`).
- New fields read with defaults: `Player.cooking_mp_gained`.
- Recipe ids already counted toward the Seeker's "recipes cooked" stay counted; the encyclopedia's
  Recipes page lists dishes by name.

---

## 12. Tests

`tests/test_kitchen_rebuild.py` (data: three recipes per ingredient, sizes, food rules, kin,
aliases, banned words, pictures, names say their part, tab x band coverage, legendary count and
depth, cross-depth spans; logic: MP restore, the size bonus, legendary caps, the full stat point,
power turns past 60, Sustained, `menu_rows`, `opening_tab`, secrets, stacks and old ids, rations
consumed, harvest kin, old-save migration, Persephone, Circe; and a real-keys journey: harvest a
goblin, go down, harvest a Charybdis spawn, cook the hotpot that needs both). Rewritten for the new
book: `test_cooking_overhaul.py`, `test_ingredient_rename.py`, `test_harvest_cook_dispatch.py`,
`test_harvest_cook_integration.py`, and cooking tests in `test_status_lock.py`,
`test_stats_and_boons.py`, `test_final_gaps_audit.py`, `test_bugbash4_player_text.py`,
`test_bug_bash_3.py`, `test_balance_review_2026_10_26.py`, `test_balance_pass_2026_10.py`,
`test_audit_2026_10.py`, `test_armour_meals_gates_2026_11_12.py`, `test_yardsticks.py`.
`tests/test_mooble.py`: cook to carry (the tart in the pack uneaten, ruined is wasted, the menu
lines and chip, the learned dish under Building Toward, its art, withheld).
`tests/test_caviar_and_tater_tots.py`: the two rare foods and their lines and prices, the dish on
the Special tab once both are held, half damage while the song plays and not after, the real-time
clock, F5, a dance's hold, a save mid-song, a fall, Robyn's start, the achievement.
`tests/test_dish_art.py`: every picture exists at 64 px and has a catalogue row, feasts own
theirs, every dish shows its form and no food it lacks (the no-match list aside, which is exactly
the dishes without a fair picture and only shrinks), the Goblin Cheese Grill, no tomatoes, tier
and benefit kept where a fair picture has them, names say their form, a new dish placed by the
rule.
`tests/test_cooking_rulings_2026_11_16.py`: every stat at every tier from parts got at that depth
(§4.3); the people list, no part of a person anywhere, the search (no question, one or two
ordinary finds of the band, a cultist's incense, an elf's bread), the corpse dossier, the hunt,
old saves; every special food in a decent dish of its tier, shown when held, used up when cooked
(§4.4).

---

## 13. Change log

| Version | Date | Change |
|---------|------|--------|
| v2.6.1-2.6.5 | 2026-09 | One question to harvest, one to cook; one ingredient per monster. |
| v2.18 | 2026-10-01 | The cook path calls `on_food_eaten` (Tantalus, Persephone, Circe). |
| — | 2026-10-26 | Base max HP on every meal; the floor's stat lesson; the per-stat cap. |
| — | 2026-11-12 | Meals heal 6% + written/80 of the bar. |
| K1 | 2026-11-14 | **The kitchen rebuild.** Kin share ingredients (316: 294 parts, 14 trophies, 8 forage) with vivid names that keep their pictures; `harvest_map.json` with aliases; a 573-dish book where every ingredient is in one single and two+ multi-dishes, rations included, a third cross-depth, 36 legendary feasts; five kinds of meal (HP / SP / MP / Stat / Special) from one rules file, MP restore new, worth and size bonus, legendary permanents inside the lifetime caps; the pure menu functions; old saves migrate. `prime_cuts.json`, `cook_outcomes.json`, `cut_stat` and `outcome_id` retired.
| K1b | 2026-11-14 | **A book a run can cook** (§4.1). From the simulator's part frequencies (`part_freq.json`): 22 feasts swap their rare parts for common or banked early ones (names and themes kept), 90 multi-dishes keep one uncommon part, 113 new dishes give every rare part two dishes with common partners (686 dishes, 370 multi). The build checks the rules and that no dish shares an ingredient's name (Cave Bear Steak's dish is now Hibernation Bear Steak). | |
| P1 | 2026-11-14 | **Cook to carry** (§5.5): a recipe's `makes` puts a food in the pack; the Starnut Tart (Starnut, bread, apple; Special tab) for the Mooble; learned dishes show under Building Toward. 687 dishes. |
| S1 | 2026-11-15 | **A dish that plays a song** (§5.6): Caviar and Tater Tots, Brandon's song as A Man Before a King; caviar and tater tots, rare plain foods; half damage while the song plays; Robyn starts with both; a secret achievement. 694 dishes. |
| SD | 2026-11-16 | **You are what you eat** (Brandon's rulings 1 and 2): one stat dish teaches one whole point, still one lesson a floor (two lessons a point, `COOK_MEALS_PER_STAT_POINT`, the banked meals `cook_stat_meals` and `full_point_worth` retired; an old save's half-point banked is dropped). A dish's tier caps how far it can raise a stat (`cap_by_tier`), replacing the cap that grew with the deepest floor (3 + floor / 4); the altar and rare foods go by the deepest band. |
| HU | 2026-11-16 | **Hunting for a dish** (§7): H in the cook menu; what a hunted dish still needs shows gold under In Sight. |
| BD | 2026-11-16 | **Big dishes +1 tier** (§5): a dish of four or more different ingredients is a tier above its deepest part's band, at most 5 (`cooking_rules.json` `big_dish`; `kitchen.dish_tier`, `base_tier`, `big_dish_bonus`, `big_dish_line`); the question, the numbers, the stat cap, the picture's vessel and the menu (with "Five ingredients: one tier richer.") all read it. 129 dishes rose a tier (T1 389 to 315, T2 115 to 161, T3 76 to 87, T4 45 to 52, T5 78 to 88). Two new pictures (a tier-2 Stat pie and platter) keep most dishes showing their own kind. |
| HC | 2026-11-16 | **No cap across floors on max HP from meals** (Brandon: "there should be a per floor limit to hp gained, but not a max across several floors... that encourages cooking"). The lifetime cap (`Player.cooking_softcap`: 4 a floor reached, at least 20; `kitchen.lifetime_hp_room`; "Max HP: all cooking can give at this depth"; the sidebar's "Meals: go deeper for HP") is gone; the floor's cap (+5 a floor) stays, and a feast's lasting max HP always lands. |
| PS | 2026-11-16 | **Brandon's three rulings.** People are searched, never harvested (§3.5, §8.1): 58 kinds in `people.txt`, twelve parts and their single dishes gone, 52 dishes re-sourced, old saves' parts become food. Every stat at every tier (§4.3): 15 stat dishes. Every special food in a dish of its own (§4.4): 6 dishes. Ingredients weigh nothing (a carried dish that does not fit is set down). 703 dishes, 306 ingredients. `part_rules.rare_foods` reads `floorSpawnWeight` too (the mythic fruits were counted common). |
| LR | 2026-11-22 | **The two low rungs** (§4.5): plain fare (any two staples) and one part with one staple for every part. 334 dishes, 1,097 in all; a Reflex Ward dish in every tier; the older 763 unchanged. The SP and MP tabs' tier gaps closed. The Widow's Jar doesn't count the rungs. |
| KV | 2026-11-22 | **Variety and hunger** (§4.6): each part's lore strength and side gift (1,097 dishes from 523 different results to nearly all different); hunger every 3 steps; Sustained only from SP dishes of three or more and feasts, 60-120 turns flat; dishes off the SP tab feed half as much; Hungry, Weak and Starving statuses (`src/hunger.py`). |
| KA | 2026-11-14 | **Dish pictures.** 134 kind pictures (20 kinds; vessel = tier, one colour cue = main benefit; stew and roast at every tier and tab) picked by `dish_art.py` from the name, and 36 feasts drawn one by one; the old cluster picker and `art_clusters.json` retired. |
| DA | 2026-11-22 | **Every dish's picture fits the dish** (§4.2; Brandon: the Goblin Cheese Grill showed a steak, tomatoes and sausage). The 180 dish pictures catalogued by what each shows (`dish_pictures.json`); `dish_art.py` places a dish by its form and its ingredients first (no food it lacks), then tier and benefit; `FALLBACK` and the kind-only pick retired. 418 dishes changed picture; 63 with no fair picture are listed for new art (`dish_art_no_match.json`). |
