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
- **Nothing spoils.** A part saved on floor 3 still cooks on floor 40: saving is a choice, paid in
  weight.
- **LORE, NOT FLOOR.** A dish's numbers come from its tier (the band of its deepest ingredient) in
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
| `src/player.py` | The caps: `feed_cut_stat(stat, lessons)` (the floor's stat lesson), `cut_stat_block`, `try_apply_cook_hp_gain`, `try_apply_cook_stat_gain`, `cooking_softcap`, `cooking_stat_softcap`, `food_taught`, `reset_floor_cook_caps`; `cooking_mp_gained` (max MP from feasts, read with `getattr`). |
| `src/status_effects.py` | `apply_effect(..., cap=)`: a meal's power may run past the usual 60 turns, up to its `max_turns`. |
| `data/items/ingredient.json` | Every ingredient (§3). Built. |
| `data/items/harvest_map.json` | Monster -> ingredient; retired ids -> kept ids (§3.2). Built. |
| `data/items/recipes.json` | The recipe book (§4). Built. |
| `data/cooking_rules.json` | Every number a dish gives (§5). Hand-written. |
| `data/items/food.json` | Rations: eaten as they are, and called for by many dishes. |
| `tools/content/kitchen/` | `build_kitchen.py` (the build and every check), the content (`kin_groups.txt`, `ingredients_*.txt`, `dishes_*.txt`), the frozen structure (`structure.json`), `dish_art.py` (which picture each dish shows) and the record it writes (`dish_art.json`), snapshots of the old data it reads colours and trophy text from. Keeping the book cookable (§4.1): `part_freq.json` (how often each part turns up in a simulated run), `part_freq.py` (makes it), `part_rules.py` (the rules), `restructure.py` (edits the structure by them). |

The old generators (`tools/gen_recipes*.py`, `tools/gen_ingredients_v265.py`,
`tools/tune_sp_soft_boundary.py`, `tools/balance/fix_broken_ingredients.py`,
`tools/balance/generators/generate_ingredients_recipes.py`) are marked RETIRED and refuse to run.

### 2.1 Rebuilding the data

1. Edit the content: `kin_groups.txt` (who shares), `ingredients_*.txt` (`key | nature | name |
   description | single dish | flavour`), `dishes_*.txt` (`dish_id | Name | flavour`).
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

**318 ingredients:** 294 monster parts, 14 boss trophies, 10 foraged finds (cave mushroom, swamp
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
"Pristine", "Pure", "Concentrated", "Engorged" or "Glittering". Human mortals give what they
carried (Bandit Trail Ham, Cultist Blood Sausage), not themselves.

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
hp, 55 sp, 44 mp, 100 stat (STR 26, DEX 16, INT 15, WIS 15, CON 14, PER 14 with the forage), 72
special. Every nature has parts in every depth band; casters find arcane parts from floor 1 to
floor 97.

### 3.4 Secrets

`secret: true` marks the cow level's two parts (Hell Bovine Sirloin, Cow King's Royal Bacon). A
dish needing one never shows on the menu until the hero holds that part. (The Stray Kids zombies
leave no corpse; the deadites and Old Nickel share the zombie's and the goblin's part.)

---

## 4. The recipe book (`recipes.json`)

**693 dishes:** 318 single dishes (one per ingredient: the everyday choice) and 375
multi-ingredient dishes of 2 to 5 different ingredients. Every ingredient is in exactly one single
dish and at least two multi-dishes. 36 multi-dishes are legendary feasts; 126 are cross-depth. No
dish is named just like an ingredient (the build checks).

| Field | Meaning |
|-------|---------|
| `name`, `flavor` | The dish and its line. Real cooking with a dungeon twist; no two share a name. |
| `ingredients` | Ingredient ids and ration ids. One of each is taken from the pack. |
| `benefit` | The main benefit, which is the menu tab: `hp`, `sp`, `mp`, a stat, or a power id. |
| `legendary` | A five-ingredient feast with a permanent bonus (§5.3). |
| `trophy`, `permanent` | A boss trophy's own dish and its lasting power (§6). |
| `cross_depth` | Joins an early part (floors 1-20) with a deep one (40+). |
| `art` | The dish's picture (§4.2): `dish_<kind>_t<tier>_<tab>` for an ordinary dish, `feast_<name>` for a legendary feast, the boss's own `recipe_<id>` for a trophy dish. |

- **Single dishes** are `cook_<kin>` ("Goblin Gristle Stew"); trophy dishes keep their ids
  (`trophy_<boss>_recipe`) and names.
- **Common food goes in:** bread, dried meat, hard cheese, wild mushroom, apple, trail rations,
  healing herb, elvish bread, and the forage. Rare food (philosopher's tea; deep fungi and the
  void ration are in no dish now) counts as an uncommon part (§4.1). Never quest, secret or one-shot food (the dungeon carrot, Tantalus' plum, the
  peach, ambrosia, the golden apple). The cook takes the ration from the pack.
- **Cross-depth:** about a third of the multi-dishes join an early part with a deep one: Goblin
  Gristle from floor 3 goes into the Gristle-and-Locust Harvest Pie with a floor-74 locust.
- **Legendary feasts:** 36, five ingredients each, deep (tier 3+): each of the 14 trophies anchors
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
3. About a third of the multi-dishes span depths, nine in ten of them joining an early common
   part (a saved part, a ration, cheese) with a deep one.

Before this (K1's book): 8 of 36 feasts and 109 of 257 multi-dishes were cookable in half of
runs. Now: all 36 feasts once the trophy is won (19 counting the trophy's own odds) and 229 of
375 multi-dishes. The eight that a simulated run never cooks hold a part the simulator never
meets: the cow level's two (secret), the mimic (it waits in chests) and Charybdis (summoned by
her scroll); each pairs only with common partners.

Dishes per tab and depth band (the tier of the deepest ingredient):

| Tab | 1-20 | 21-40 | 41-60 | 61-80 | 81-100 |
|-----|-----:|------:|------:|------:|-------:|
| HP | 44 | 15 | 10 | 3 | 14 |
| SP | 81 | 10 | 5 | 11 | 5 |
| MP | 48 | 9 | 12 | 4 | 13 |
| Stat | 143 | 36 | 25 | 17 | 21 |
| Special | 79 | 41 | 19 | 8 | 20 |

### 4.2 Pictures (`tools/content/kitchen/dish_art.py`)

A dish's picture says three things at a glance:

- **its kind**, from its name: soup, stew, chowder, porridge, drink, pickle, roast, leg, steak,
  sausage, skewer, stir-fry, fritter, flambe, platter, pie, dumpling, bread, jelly, pudding. The
  last kind word of the name decides ("Kuo-Toa Brine Ham Stew" is a stew), after a few phrases
  ("black pudding" is a sausage, "leg roast" a leg); a name with no kind word is a stew;
- **its tier**, by the vessel: dark walnut wood (1), tawny clay (2), black iron (3), bright silver
  (4), jewelled gold (5). A drink is in a cup, mug, tankard or goblet of that material, a pickle
  in a crock or jar;
- **its main benefit** (menu tab), by one colour cue: warm red for HP, amber-gold for SP, glowing
  deep blue for MP, emerald green for Stat, violet for Special (a broth, filling or sauce of that
  colour, or berries, honey, leaves or flowers on solid food).

The pictures are `assets/tiles/items/dish_<kind>_t<tier>_<tab>.png`. Stew and roast are drawn
at all 25 tiers and tabs; the other kinds where the book has two or more dishes of them. A dish
whose kind has no picture at its tier and tab shows the nearest kind drawn there
(`dish_art.FALLBACK`: a pie a dumpling, then bread, then a roast; every chain ends at the stew),
so its vessel and colour are always true. The pick reads only the name, tier and benefit: a
renamed or new dish needs no table edit, and a new picture dropped into the folder under that
name is used on the next build. Each legendary feast has its own `feast_<name>.png`
(`dish_art.FEASTS`), drawn for it from its name, flavour and lore; the 14 trophy dishes keep
their boss's `recipe_<id>.png`. The briefs are `tools/content/genart/briefs/items_dishes.json`
and `items_feasts.json`.

---

## 5. What a dish gives (`data/cooking_rules.json`, `kitchen.dish_outcome`)

**Tier** = the band of the deepest ingredient (floors 1-20 tier 1 ... 81-100 tier 5). It is also
the cooking question's tier.

**Worth** = what the ingredients add (a monster part or trophy 1, a foraged find 0.6, a ration
0.5) times the **size bonus** for the number of different ingredients (1.0, 1.2, 1.35, 1.5, 1.6
for one to five). So a dish of N parts gives about 1.2x (two) to 1.6x (five) what the same parts
give cooked one at a time: saving and hunting for a dish pays, and eating as you go is never
wrong. A legendary feast or a trophy's dish multiplies its main benefit by 1.5 on top.

### 5.1 Every dish (food is food)

- **SP:** 60 / 80 / 105 / 125 / 150 by tier, times worth (shown capped at the bar).
- **A heal:** `food_system.meal_mend_share` of 3 / 6 / 9 / 14 / 20 written (6% + written/80 of
  max HP: about 10% at tier 1, a third at tier 5).
- **Max HP:** +2 toward the floor's cap (5 a floor; `try_apply_cook_hp_gain`).

These keep a single dish of a tier near the old tier bands, so the simulator's baseline holds.

### 5.2 The five main benefits (one per dish: its tab)

| Tab | What it does (single dish, by tier 1..5; times worth) | The choice it makes |
|-----|------|------|
| **HP** | Heals 18 / 22 / 26 / 30 / 34% of max HP (at most all of it), and +1 / 1 / 2 / 2 / 3 max HP on top of the 2 (inside the floor's cap). | Hurt, or building a tank. |
| **SP** | 100 / 125 / 150 / 175 / 200 SP in place of the usual, and Sustained (hunger at half pace) for the same number of turns, at most 800. | Long floors, saving rations. |
| **MP** | Restores 25 / 27 / 30 / 32 / 35% of max MP, or 4 / 6 / 8 / 10 / 12 MP if that is more (max MP is small while INT is low). | Casters, before a boss. |
| **Stat** | The floor's stat lesson (`feed_cut_stat`): two lessons make a point. A dish of worth 2.5 or more teaches the whole point at once (two lessons), still the floor's one lesson, still under the lifetime cap (which counts the altar's points: `food_taught`). | The build. |
| **Special** | A timed power for 100 / 130 / 160 / 200 / 240 turns, at most the power's `max_turns` (Dark Vision 800, resistances 600, Haste 40, Shielded 60...). A ward (`save_guard_*`) is +1, +2 from worth 2, +3 from worth 3.5. | The fight ahead. |

A meal's power runs past the usual 60-turn status cap (`apply_effect(..., cap=max_turns)`): the
old book wrote 100-300 turns and every one was cut to 60 while the message said otherwise.

### 5.3 Legendary feasts: permanent bonuses

On top of the 1.5x main benefit, by tab:

- **HP:** +4 / 4 / 4 / 6 / 8 max HP, past the floor's cap but inside the lifetime cooking cap
  (`cooking_softcap`, 4 a floor of depth).
- **MP:** +2 / 2 / 2 / 3 / 4 max MP, inside the lifetime feast cap: a quarter of the deepest
  floor reached, at least 4 (`kitchen.feast_mp_cap`; `Player.cooking_mp_gained`).
- **Stat:** the floor's lesson as a whole point, and +1 more past the lesson
  (`try_apply_cook_stat_gain(bypass=True)`), inside the stat's lifetime cap.
- **Special:** the feast's resistance for good (its own power if a resistance, else one of its
  ingredients', else the fallback order), never one its trophy gives and never one the hero holds
  for good already (`kitchen.feast_resist_for`: Fafnir's Blood gives fire resistance, so Fafnir's
  fire feast gives the next one). A timed power the hero already holds for good says so ("Fire
  Resist: already yours for good") instead of lingering for a number of turns.

Legendary feasts never have SP as their main benefit. A feast holding a boss trophy also gives
the trophy's own power (§6).

### 5.4 What the menu says (`kitchen.dish_effects`)

Plain lines for THIS hero now, main benefit first: "+45 HP", "+3 Max HP", "+12 MP", "Teaches DEX
(a full point)", "Dark Vision, 300 turns", "+4 Max MP for good", "+60 SP". A cap that would eat
the benefit says so: "Max HP full this floor", "Max HP: all cooking can give at this depth" (the
lifetime cap, `kitchen.max_hp_room` reads both), "DEX lesson used this floor", "DEX has learned all
food can teach here", "Max MP: all feasts can give at this depth". A feast's For Good lines are held
to the same lifetime caps ("+3 Max HP for good" when 3 is what is left; "No more STR for good at
this depth"), so the menu never promises more than the meal gives.

### 5.5 Cook to carry (`makes`, 2026-11-14)

A dish may be **cooked to carry**: its recipe names `makes`, a food id in `data/items/food.json`,
and cooking it right puts that food in the pack, wrapped, instead of eating it
(`kitchen.make_to_carry`, from `apply_dish`). Nothing is eaten, so the hero's SP, HP and the
cooking quirks are untouched (`Game._cook_compound` tells the quirks only when the food itself
is eaten). A ruined one is wasted like any dish. The food weighs less than what went into it, so
it always fits. Its benefit is `carry` (`dish_tab`: Special; `dish_power`: none), its menu lines
are `kitchen.carry_lines` ("Made to carry: one Starnut Tart into your pack", "If eaten: +70 SP,
+6 HP") and its chip says "To Carry" (`cook_menu.main_effect`).

The first is the **Starnut Tart** (`dish_starnut_tart`: Starnut, bread ration and apple), the
Mooble's favourite (`mooble_encounter.py`, `docs/systems/pets.md`). The food `starnut_tart` never
spawns (`floor_spawn_weight` 0), is never an ingredient (`build_kitchen.FORBIDDEN_FOOD`), is
never stolen, given as payment or sold (`items.WITHHELD_IDS`), and shows the dish's picture
(`renderer._UNIQUE_SPRITE_FALLBACK`: `dish_pie_t2_special`) until it has one of its own.

A dish the hero has **learned of** (`player.dishes_learned`, a set of recipe ids: the Mooble
tells of his tart the first time he is met) shows under Building Toward even before any part of
it is held (`menu_rows`). `build_kitchen.py` carries `makes` from `structure.json` and checks
that the food exists, is forbidden as an ingredient, and that no feast is carried.

### 5.6 A dish that plays a song (`song`, 3.5.2)

A dish may name a **song** (`song`, an id in `data/songs.json`; benefit `song`, so the Special
tab, `dish_power` none). Brandon writes songs as **A Man Before a King**; a song here is one of
his, and its words come from his lyrics. Eaten, the dish gives what every dish gives (§5.1), and
its power is the song's (`songs.begin`, from `apply_dish`): the soundtrack steps aside, the song
plays once, and for exactly as long as it plays, in real seconds, every blow and spell on the hero
does `damage_taken` of its damage (`Player.take_damage`; hunger is not a blow). Then the
soundtrack comes back and the power ends. Its menu lines are `kitchen.song_lines` ("Half damage
taken, 2:44 (while the song plays)"), its chip "Half Damage" (`kitchen.song_share`), and the
sidebar and character sheet show "Everything's Right 2:10" while it plays
(`songs.effect_label`).

The first is **Caviar and Tater Tots** (`dish_caviar_and_tater_tots`: caviar and tater tots,
the song's own art cut from its album cover). Both foods are rare plain finds (about one food
find in fifty each, every band), good to eat as they are with a line of their own (`eat_line`);
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

---

## 7. The cook menu functions (`src/kitchen.py`, pure)

- `MENU_TABS = ('hp', 'sp', 'mp', 'stat', 'special')`, `TAB_NAMES` "HP", "SP", "MP", "Stat",
  "Special". `dish_tab(recipe)` gives a dish's tab.
- `menu_rows(player, inventory, tab)` returns rows (dicts: `id`, `recipe`, `name`, `group`,
  `ready`, `legendary`, `trophy`, `tier`, `have` / `missing` lists of `{id, name, have, need}`,
  `progress` "2 of 4", `value`, `effects`) in three groups:
  1. **ready** — cookable now, the most giving first (`dish_value`);
  2. **building** — the hero holds at least one HARVESTED part of it (a monster part or trophy;
     a ration or a foraged find alone does not count, or bread would list a hundred dishes) but
     not all, or the hero has learned of it (`player.dishes_learned`, §5.5); the closest first,
     then fewest missing, then value;
  3. **legendary** — the feasts and trophy dishes, their own group so the big payoff stands out:
     ready ones first, then the closest; shown once any harvested part is held.
  A dish needing a secret part never shows until that part is held.
- `opening_tab(player, inventory)`: among tabs with a dish ready — HP under half: hp; SP under
  30%: sp; MP under 40% with spells known: mp; else stat while the floor's lesson is open and a
  stat dish would teach; else the tab with the most dishes ready (with none ready, the most rows).
  `opening_choice` gives the same tab and why (`OPEN_REASONS`: 'hurt', 'hungry', 'mana',
  'lesson', 'most_ready', 'most_rows', 'nothing'), so the menu can say it.
- `dish_lasting(player, recipe)`: the lines of `dish_effects` that last for good (a feast's
  permanent bonus, a boss trophy's power), shown under their own heading.
- `held_counts(inventory)` counts stacks, rations and old ids; `ready_dishes(inventory)` (every
  dish the pack can cook) is what `food_system.get_available_compound_recipes` returns.

---

## 8. Harvest (one animal question)

`Game._harvest` (`H`) takes the corpse under the hero off the floor before the question, then
`food_system.harvest_corpse` asks ONE animal question at the corpse's `harvest_tier`, never
harder than the band the monster lives in (`_monster_band_tier`). Right: the corpse yields its
kin's ingredient (`kitchen.ingredient_for_monster`; a creature the map does not name borrows its
nearest kin's, `_nearest_kin_ingredient`, by the family and floor in monsters.json or, for a
creature monsters.json does not know, on its corpse: Gilt Varro, a mortal, gives a mortal's
provisions; a person of an encounter with no family yields nothing, said before the question by
`Game._harvest` through `food_system.corpse_yield`), plus one portion more for a family the hero has
learned to butcher (`family_edges.harvest_bonus`), never for a boss trophy (one of a kind: a
second Fenrir's Tooth gave its power twice, bug bash 3.5.1). The part remembers the creature it came from
(`source_monster`, read by Siegfried's Bath). Wrong: the corpse is ruined. A part too heavy to
carry stays on the floor. `quirk_system.on_harvest` fires either way (Mithridates).

Untimed: animal questions are never on the clock. Corpses weigh what the body weighs
(`items.corpse_weight`, `data/monster_sizes.json`: 2 lb tiny to 400 lb huge).

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
  or a foraged find among them (`parts`, `kitchen.part_kind` `food` or `forage`): from then on
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
  lifetime cap).
- **Raw** (`eat_raw`): `raw_sp` (10 for every monster part) or the `tier_role` map; monster parts
  are `edible_safe` (never poison); a foraged find can poison (30%) without poison resistance.

---

## 11. Saves

- **Old ingredients** (`Game._migrate_legacy_ingredients`): every Ingredient in the pack, any
  sack, the floor and stored floors: a retired id becomes the kept one, its name and fields come
  from today's data (`kitchen.migrate_ingredient`), and in the pack and sacks two stacks that are
  one ingredient now are joined (`kitchen.merge_stacks`). An id the kitchen does not know is
  dropped.
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
`tests/test_dish_art.py`: every picture exists at 64 px, feasts own theirs, a shared picture is
one tier and one tab, names say their kind, any renamed dish finds a true vessel and colour.

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
| KA | 2026-11-14 | **Dish pictures.** 134 kind pictures (20 kinds; vessel = tier, one colour cue = main benefit; stew and roast at every tier and tab) picked by `dish_art.py` from the name, and 36 feasts drawn one by one; the old cluster picker and `art_clusters.json` retired. |
