# Bosses and Quests — Comprehensive Reference

Mapping of every named boss and every discoverable quest layer that touches each
boss. Every claim is cited with `file:line`. This document is read-only — it
maps the system, it does not propose fixes. Incomplete or under-implemented
mechanics are flagged `INCOMPLETE`. Open questions to the developer live in a
per-boss section.

Scope: only quest content that connects to a boss. The wider altar system, full
karma table, and unrelated mystery encounters are the subject of sibling
audits; only the boss-relevant slices are mapped here.

---

## Overview — The Layered Design Philosophy

Every floor-20-multiple is a fixed hand-crafted arena (`src/boss_levels.py:15`,
`BOSS_LEVELS = {20, 40, 60, 80, 100}`). The base monster is intentionally
tuned to be very hard. **Around each boss, the designer has built one or more
discoverable quest paths that bend the fight in the player's favor** — a thread
that defangs the AI, a mirror that defeats the gaze, a pit ritual that
quadruples damage, a binding ribbon that paralyzes the wolf, holy fire that
strips resistances. None of these paths are required to win; they are the
mythological "right answer" that a learning player slowly discovers across
runs.

Pattern repeats five times:

1. **The base fight** — JSON-driven stats in `data/monsters.json`, AI in
   `src/monster.py`, baseline lore drop.
2. **Boss reward scroll** — every boss drops a `scroll_of_<theme>` whose
   `effect: "boss_reward"` is a real-world reward code for the developer's
   kids (`data/items/scroll.json:146-247` etc., `src/game_combat.py:651-653`).
3. **A primary quest layer** — keyed myth artifact built across earlier
   floors and applied at the arena.
4. **One or more secret quest layers** — even further-back myth (Vidar's
   Sandal, Gram-reforged-over-altar) that flip the fight from "winnable" to
   "trivial".
5. **A chronicle stamp** on first kill (`game_combat.py:608-615`) plus a
   `STORY_CONTENT` popup with the historical narrative
   (`main.py:3382-3464`).

Below: per-boss breakdown. Cow King (L30-39 secret) and the Seal Demon
sub-track (L83-L97 gate) get their own sections because both are quest layers
rather than full hand-crafted boss arenas.

---

## Asterion the Minotaur (L20)

### Arena

Hand-crafted level `_level_20_labyrinth` (`src/boss_levels.py:91-194`).

- 80x50 maze: three parallel east-west corridors at y=14, y=20, y=26
  (`boss_levels.py:104-106`).
- Vertical connectors between corridors are partially walled off
  (`boss_levels.py:119-127`) to make a real maze.
- Dead-end alcoves seeded along each corridor (`boss_levels.py:132-138`).
- Entry chamber top-left with STAIRS_UP (`boss_levels.py:99-102`).
- Boss chamber at (39, 35), 21x15 with dramatic DOOR entry
  (`boss_levels.py:140-144`).
- Two treasure alcoves flanking boss chamber (`boss_levels.py:149-153`).
- Exit chamber bottom-right with STAIRS_DOWN (`boss_levels.py:155-159`).
- **Phasing walls** (`dungeon.phasing_walls` set, `boss_levels.py:166-192`):
  vertical shortcuts between corridors and along blocked connectors. Only
  Asterion (`can_phase_walls: true`, `monsters.json:19682`) can pathfind
  through these — he ambushes from any wall.

**No altar** in the L20 arena.

### Base stats (`data/monsters.json:19634-19683`)

- HP 800; THAC0 4; speed 8.
- Attacks: `gore` (2d12+1 slash), `trample` (1d8 blunt).
- AI: `hit_and_run` (`monster.py:408-410`, `monster.py:_hit_and_run_turn`).
  Engages, lands hits, retreats via phasing walls.
- Resists: `blunt`. Weak: `pierce`.
- Harvest tier 5, threshold 3 → `minotaur_horn` ingredient.
- Treasure: 150-300 gold, item_tier 4, `boss_scroll_id:
  scroll_of_the_labyrinth` (`monsters.json:19680`).
- `can_phase_walls: true` (`monsters.json:19682`).

### Quest Layer 1 — Ariadne's Thread (the defang)

**What it is mechanically.** When the player carries an item with
`id == 'ariadnes_thread'`, every monster on the level with
`can_phase_walls=True` is mutated each turn:

```
m.can_phase_walls = False
m.speed = min(m.speed, 6)             # slowed
if m.ai_pattern == 'hit_and_run':
    m.ai_pattern = 'aggressive'        # can't hide
```
(`src/game_combat.py:1384-1393`)

Asterion is one of the three `can_phase_walls: true` monsters
(`monsters.json:19682`; the other two are elder_vampire / ancient_vampire_lord
— this leak is flagged in `data/audit/consensus.json` and quoted in
`REVERSE_ENGINEERED.md:285`).

Mechanical effect on fight: hit-and-run becomes a straight-up brawl, speed
drops from 8 to 6 (skips ~25% of turns by speed math at
`monster.py:386-390`). The Minotaur's signature mobility is gone.

**Discovery path.**

1. **Bronze Bull Idol** — guaranteed spawn on L12
   (`src/dungeon.py:1486-1499`). `monsters.json` lore: "The idol still smells
   faintly of sea-foam." T2 hint at `data/hints.json:107` tells the player
   directly that the bull belongs to "sacred waters."
2. **Drop bronze bull at a fountain** (any level with FOUNTAIN tile). The
   `_do_drop_item` handler detects this (`main.py:3730-3734`) and calls
   `_activate_ariadne_shrine` (`game_divine.py:362-385`). The shrine door
   carved on L17 by `_create_ariadne_shrine`
   (`dungeon.py:1501-1503,1600-1696`) opens, revealing Ariadne's Thread
   placed inside the sealed 3x3 chamber (`dungeon.py:1682-1694`).
3. Pick up thread; carry through the labyrinth.
4. T1 hint hammers the canon: "an old myth tells of a thread that once tamed
   the labyrinth itself" (`data/hints.json:95`). T3 traces the chain
   ("bronze idol... sacred waters... gift that revealed every hidden passage",
   `data/hints.json:107, 158`).

**Reward beyond the fight.** Ariadne's Thread is itself an amulet-slot
accessory with WIS +2 and permanent `searching` status
(`data/items/accessory.json:4674-4703`); equipping it requires a
threshold-3 history quiz. The amulet keeps working past the boss.

**Code trigger:**
- Thread item: `data/items/accessory.json:4674-4703` (accessory)
  and `data/items/artifact.json:26-37` (loose artifact form spawned by
  shrine).
- Per-turn defang: `game_combat.py:1384-1393`.
- Shrine carve: `dungeon.py:1600-1696`.
- Shrine activation: `game_divine.py:362-385`.

### Quest Layer 2 — Theseus quirk (unlock arc)

`theseus` quirk (`quirk_system.py:319-327, 1129, 1190`): full exploration of
5 floors awards "Theseus in the Labyrinth" → PER +1 (`quirk_system.py:1507`).
Lore quote: "The labyrinth is only dangerous to those who do not map it.
-- Theseus" (`quirk_system.py:1400`). T3 hint: "The hero who once slew the
Minotaur walks as a hidden character — his helmet and noble lineage mark him
as a balanced warrior who feels strangely at home in labyrinths."
(`data/hints.json:111`).

Not a quest layer that affects the fight directly, but the canonical chain
of association: bull → fountain → thread → labyrinth → hero.

### Cross-system interactions

- **Items:** Bronze Bull Idol (`bronze_bull`, `artifact.json:14-25`,
  `dungeon.py:1486-1499`), Eye of Graeae item is in the same artifact file but
  belongs to Medusa, Ariadne's Thread (two definitions — accessory +
  artifact). Minotaur horn ingredient `minotaur_horn`
  (`ingredient.json:9156`).
- **Fountains:** Quest fountain on L12-17 (Ariadne shrine carving at L17,
  `dungeon.py:1501-1503`).
- **Chronicle:** `"Killed the Minotaur. Asterion. He was bigger than I
  expected. The labyrinth is quiet now."` (`game_combat.py:609`). Chronicle
  stamp for the bull discovery `"Found a bronze idol shaped like a bull."`
  (`main.py:2131`).
- **Story popup:** `boss_asterion` content closes with "Today, that thread
  was your knowledge" (`main.py:3382-3398`). Pre-identified.
- **Boss scroll:** `scroll_of_the_labyrinth` → code `LABYRINTH-MMXXV-I`
  (`data/items/scroll.json:146-166`).
- **Hints:** T1 (`hints.json:95`), T2 (`hints.json:107`), T3
  (`hints.json:111, 158`).
- **Quirks:** `theseus` (PER +1, 5 fully-explored floors,
  `quirk_system.py:319-327`).

### Open questions

- **Phase-walls leak.** `can_phase_walls` is on 3 monsters total
  (Asterion + elder_vampire + ancient_vampire_lord). Carrying Ariadne's
  Thread permanently defangs the two vampires too. Was that intentional or
  is the Thread supposed to be Minotaur-locked? Flagged in
  `data/audit/consensus.json` and `REVERSE_ENGINEERED.md:285`.
- I find no L20-specific altar mechanic — the arena has no ALTAR tile
  (`boss_levels.py:91-194`). Was an altar layer ever considered for L20?

---

## Medusa the Gorgon (L40)

### Arena

`_level_40_temple` (`src/boss_levels.py:201-268`).

- Hellenic temple layout: entry portico (39,4); main nave 39,22 spanning 12
  wide x 28 deep (`boss_levels.py:210-216`).
- **ALTAR placed in center of nave** (`boss_levels.py:221`):
  `tiles[nave.center[1]][nave.center[0]] = ALTAR`. This is the only altar in
  the boss-floor arena. Note: this is *not* the L99 Abaddon-style
  resistance-strip altar; it's a generic altar usable for prayer/BUC.
- Pillars in nave (WALL tiles at y=13/18/24/29 x=35/43) and **in the boss
  room** (`boss_levels.py:258-259`): "LOS blockers against Medusa's gaze".
  Four wall pillars at (35,41), (43,41), (35,45), (43,45).
- Inner sanctum boss room at (39, 43) (`boss_levels.py:251-254`).
- Two pairs of side chapels left/right of nave (`boss_levels.py:228-249`).
- Exit corridor at (68, 43) with STAIRS_DOWN (`boss_levels.py:262-265`).

### Base stats (`data/monsters.json:19684-19742`)

- HP 1500; THAC0 -3; speed 10.
- Attacks: `serpent_fang` (2d8+2 pierce), `venom_strike` (2d6+2 poison),
  `petrifying_gaze` (1d8+1 magic, `effect: paralyzed`, 45% chance, 4 turns).
- AI: `dancer` (`monster.py:413-414`, `monster.py:985-1018`). Sidesteps to a
  different tile adjacent to the player every turn she attacks — chokepoints
  are her counter, which is why the boss room has columns.
- Special: `gaze_paralyze: 3`, `gaze_cooldown: 4`
  (`monsters.json:19718-19719`).
- Resists: `poison`. Weak: `slash`.
- Harvest tier 5, threshold 3 → `medusa_blood`.
- Treasure: 200-400 gold, item_tier 5, `boss_scroll_id:
  scroll_of_the_gorgon` (`monsters.json:19740`).

### Quest Layer 1 — Aegis of Athena (the mirror path)

**What it is mechanically.** When the player has shield with id
`aegis_of_athena` or `greater_aegis_of_athena` equipped, Medusa's gaze flips:

```python
elif getattr(player.shield, 'id', '') in ('aegis_of_athena', 'greater_aegis_of_athena'):
    self.status_effects['paralyzed'] = 1
    gaze_msg = (f"The {self.name} meets her own reflection in your shield "
                f"and is turned to stone for a moment!")
```
(`src/monster.py:215-219`)

Medusa paralyzes *herself* for 1 turn each time she initiates her gaze. The
gaze cooldown is 4, so she effectively loses ~25% of her actions any time
she gets adjacent.

**Discovery path.**

1. **Eye of the Graeae** — guaranteed spawn on L29 (`dungeon.py:1505-1520`).
   T3 hint `data/hints.json:97` introduces the Grey Sisters: "Perseus once
   stole it — and traded it for something far more valuable than sight."
   Item lore in `data/items/artifact.json:38-49`: "The gods rewarded his
   cunning at a sacred place."
2. **Drop Eye of the Graeae on any altar.** Detected at
   `main.py:3736-3740` → `_activate_athena_shrine`
   (`game_divine.py:387-409`). The L37 carve
   (`dungeon.py:1522-1524, 1699-1786`) seals a 3x3 chamber containing the
   Aegis of Athena shield (`data/items/shield.json:466-489`). Dropping the
   Eye opens that door.
3. Equip the Aegis (`equip_threshold: 3`, geography quiz).
4. T3 confirms strategy: "Perseus defeated the Gorgon with a mirror and a
   blindfold. The Grey Sisters' Eye was the price he paid for divine aid."
   (`data/hints.json:159`)

**Reward beyond the fight.** The Aegis is a permanent shield — bronze
material, AC +4, 50% magic resistance, `petrifying: 1.0` damage resistance
(`shield.json:466-489`). Greater Aegis (L65+ generic find,
`shield.json:284-313`) has higher AC, fire/cold/magic resistance and
`petrifying: 1.0`.

**Code trigger:**
- Item: `data/items/shield.json:466-489` (Aegis), 284-313 (Greater Aegis).
- Mirror flip: `monster.py:215-219`.
- Athena shrine carve: `dungeon.py:1522-1524, 1699-1786`.
- Athena shrine activation: `game_divine.py:387-409`.
- Eye spawn: `dungeon.py:1505-1520`.

### Quest Layer 2 — Blindfold path

**What it is mechanically.** Total blindness negates the gaze
(`monster.py:213-214`):

```python
if player.get_sight_radius() == 0:
    gaze_msg = f"The {self.name} locks eyes on you, but you are blind to her gaze!"
```

A blinded player still gets attacked normally but the gaze does not trigger
paralyze (no gaze_msg returns prematurely — falls through to normal attack
sequence). Sight-radius zero is the gating condition.

**Discovery path.** T3 hint (`data/hints.json:159`): "Perseus defeated the
Gorgon with a mirror **and a blindfold**." T1 hint (`hints.json:96`):
"heroes found ways to fight without looking."

**Mechanical effect on fight.** Player still takes pierce/venom damage but
the chain-breaker (paralyze + bypass) is gone. Sustainable for the duration
of the fight if the player has a way to inflict `blinded` on themselves
(e.g., specific scroll, status).

INCOMPLETE: I find no canonical "blindfold" item the player equips
intentionally. The mechanic exists in code but seems to rely on the player
either being incidentally blinded (debuff) or deliberately drinking/reading
something that blinds. No item with `effect: blind_self` is in the data set
I scanned. The mechanic is implemented but the discovery vector is weak.

### Quest Layer 3 — LOS pillars (arena tactic)

**What it is.** The four WALL pillars inside the boss chamber
(`boss_levels.py:258-259`) are LOS blockers. Medusa's gaze code requires LOS
to the player (gaze is treated as a melee/adjacency attack — see
`monster.py:209-244`); the pillars let a player position so Medusa cannot
see the player while the player attacks past the pillar. Combined with the
nave columns at y=13/18/24/29 (`boss_levels.py:223-225`), the temple is
specifically built as a "chokepoint + LOS-break" arena.

**Discovery path.** Implicit / map-reading. No hint specifically calls out
"use the pillars" but the level commentary in `boss_levels.py:258` does:
"LOS blockers against Medusa's gaze".

**Mechanical effect.** Player can break the dancer pattern by hiding around
a pillar, forcing Medusa back into approach mode while the player attacks.

### Quest Layer 4 — Medusa quirk (passive unlock arc)

`medusa` quirk (`quirk_system.py:365-371, 1142`): answer correctly while
blinded in 5 separate blinded episodes → "Medusa's Gaze" → DEX +2
(`quirk_system.py:1520`). Lore: "She turned those who stared to stone — but
not those who studied" (`quirk_system.py:1413`).

### Quest Layer 5 — Petrify-on-crit weapons

Weapons with `petrify_on_crit: true` (e.g., the Harpe, used by Perseus in
myth; `combat.py:111-113`) can apply `petrifying` to Medusa on a chain-max
crit. After 3 turns of petrifying she dies outright (`monster.py:150-152`,
`if name == 'petrifying': self.hp = 0; self.alive = False`).

Not Medusa-specific in code but mythologically linked (the Harpe is the
sword Perseus used). T5 hint `data/hints.json:175` mentions "the gods reward
the faithful" — not Medusa-direct, but the petrify mechanic is generic
endgame tech.

### Cross-system interactions

- **Items:** Eye of the Graeae (`artifact.json:38-49`), Aegis of Athena
  (`shield.json:466-489`), Greater Aegis (`shield.json:284-313`), Harpe (any
  petrify_on_crit weapon).
- **Altars:** Generic altar in nave center for prayer/BUC/identification;
  the Athena shrine sealed altar exists *elsewhere* on L36-39.
- **Chronicle:** `"Medusa is dead. I couldn't look at her directly. Even the
  snakes were afraid at the end."` (`game_combat.py:610`).
- **Boss scroll:** `scroll_of_the_gorgon` → code `GORGON-MMXXV-II`
  (`data/items/scroll.json:167-187`).
- **Story popup:** `boss_medusa` (`main.py:3399-3414`).
- **Hints:** T1 (`hints.json:96`), T3 (`hints.json:97, 111-canon, 159`).
- **Quirks:** `medusa` (DEX +2, 5 blinded-correct episodes,
  `quirk_system.py:365-371`); `perseus` (Perseus' Reflection: enemy status
  effects 50% shorter, 5 reflected effects, `quirk_system.py:1037-1040`).
- **Recipes:** `medusa_blood` is a high-tier ingredient
  (`ingredient.json:593`) used in multiple recipes
  (`recipes.json:220, 320, 711, 1210`).

### Open questions

- The blindfold path has no clear self-blind item. Was a "Blindfold of
  Perseus" item supposed to exist? Not in `data/items/armor.json`.
- The nave-center altar (`boss_levels.py:221`) is a generic altar — was a
  Medusa-specific holy-fire prayer mechanic planned (analogous to L100's
  resistance-strip)? I find no code that treats L40 altar prayers
  specially.

---

## Fafnir the Dragon (L60)

### Arena

`_level_60_lair` (`src/boss_levels.py:275-342`).

- Cave entrance (10, 5) → twisting passages (`boss_levels.py:284-304`).
- Wide central hoard chamber 42, 28 (29x19, `boss_levels.py:307-308`) with
  stalagmite WALL pillars (`boss_levels.py:313-314`) and four treasure
  alcoves at corners (`boss_levels.py:316-323`).
- Dragon's lair at (42, 43) 25x11 (`boss_levels.py:326-329`).
- **Critical arena element:** rock formations at (36,41), (36,42), (48,44),
  (48,45) (`boss_levels.py:332-334`) explicitly commented "cover to dig pits
  behind". The arena is shaped to support the Sigurd pit ritual.
- Exit at (70, 43) (`boss_levels.py:336-339`).

**No altar** in the L60 arena.

### Base stats (`data/monsters.json:19743-19802`)

- HP 2500; THAC0 -12; speed 10.
- Attacks: `rending_claw` (4d12+5 slash), `fire_breath` (3d10+3 fire,
  piercing — bypasses fire_resist defense), `venomous_bite` (2d8+2 poison).
- AI: `ranged` (`monster.py:429-436`). Maintains distance, prefers
  breath/spit at range.
- **`dragon_scales: 0.8`** — Fafnir absorbs 80% of all incoming damage
  (`monsters.json:19775`, applied at `combat.py:148-154`):

  ```python
  dragon_scales = getattr(monster, 'dragon_scales', 0)
  if dragon_scales > 0 and not getattr(weapon, 'ignore_resistances', False):
      if player.has_effect('in_pit'):
          damage = damage * 4
      else:
          damage = max(1, int(damage * (1.0 - dragon_scales)))
  ```

  This is the load-bearing mechanic. **Without bypass: 20% damage. With
  player-in-pit: 4x damage (20x net swing relative to standing fight).**
  With `ignore_resistances` weapon: full damage (no pit bonus, no scales
  reduction).

- Resists: fire, poison, blunt, slash, pierce, holy, magic (everything that
  isn't `cold`, `lightning`, `acid`, `drain`, `void`).
- Weak: none.
- Harvest tier 5, threshold 4 → `dragon_scale`.
- Treasure: 500-1000 gold, item_tier 6, `boss_scroll_id:
  scroll_of_the_hoard` (`monsters.json:19800`).

### Quest Layer 1 — Sigurd's pit ritual (the legitimate kill)

**What it is mechanically.** The player digs a pit on the floor, then
intentionally falls in. Player-in-pit means the dragon-scales reduction is
inverted to a 4x damage *multiplier* (`combat.py:151-152`). Net effective
damage vs Fafnir: standing = 0.2x, in-pit = 4.0x = **20x relative damage
amplification**.

The pit is dug with a `can_dig: true` weapon equipped
(`game_combat.py:1141-1147`, `_dig_pit` at `1160-1179`). Costs 30 SP and 3
turns (during which monsters get free actions).

**Discovery path.**

1. **Broken Blade of Gram** — guaranteed spawn on L48
   (`dungeon.py:1527-1536`). T3 hint chain
   (`data/hints.json:160`): "Sigurd slew Fafnir by digging beneath him and
   striking upward through the soft belly. Before the killing blow, he
   carried a broken blade — and before the blade was whole, a god had to
   intervene." T1: "Sigurd struck from below, where the scales are softest"
   (`hints.json:98`).
2. **Odin's Altar** — guaranteed on L53 (`dungeon.py:1538-1540,
   1789-1859`). The altar is in a random non-start room
   (`dungeon.py:1796-1805`) with a 3x3 sealed shrine carved nearby.
3. **Player drops Broken Gram on the altar:** detected at
   `main.py:3742-3749` (only if the player is *on* the altar tile and the
   tile matches `odin_altar_pos`). Calls `_activate_odin_shrine` with
   `reforge=False` (`game_divine.py:411-461`). Blade dissolves; Odin
   "speaks of digging, of secrets beneath the earth"
   (`game_divine.py:449-450`). Shrine door opens.
4. **Sigurd's Shovel** drops in the shrine (`dungeon.py:1851-1857`,
   item at `data/items/weapon.json:5943-5985`). It's a 1H iron club, 7
   base dmg, max chain 4 — but `can_dig: true`.
5. **In the L60 arena:** the player equips the shovel (or any can_dig
   weapon), uses melee attack on an empty floor tile (`game_combat.py:1139-
   1147`) to dig a pit, walks into the pit (`_player_fall_in_pit`,
   `game_combat.py:1181-1192`), and attacks Fafnir from below.

**Mechanical effect on fight.** Each player attack with `in_pit` effect
gets the 4x dragon-scales multiplier. The fight goes from "spongy disaster"
to "doable in a handful of chains."

**Reward beyond the fight.** Sigurd's Shovel itself stays usable. The Lore
quote: *"It's just an ordinary shovel. Really. Not everything has to be a
magic sword."* (`weapon.json:5984`)

### Quest Layer 2 — Reforged Gram (the SECRET — throw over the altar)

**What it is mechanically.** Instead of dropping the Broken Gram on Odin's
altar, the player **throws** it over the altar (`game_combat.py:286-303`)
— i.e. stands on one side, throws toward a target on the other side, with
the altar in between. `_throw_crosses_tile` detects the line crossing
(`game_combat.py:282-303`). On throw-over with `weapon.id == 'broken_gram'`:

```python
self.player.remove_from_inventory(weapon)
self._activate_odin_shrine(weapon, reforge=True)
```
(`game_combat.py:293-298`)

`_activate_odin_shrine(..., reforge=True)` (`game_divine.py:411-462`) spawns
the fully-reforged **Gram** weapon at the altar
(`game_divine.py:435-443`). Gram (`data/items/weapon.json:5853-5901`):

- T5 adamantine, base 24, max chain 9, multipliers up to 9.0x.
- `damageTypes: ["slash", "pierce"]`
- `critMultiplier: 2.5`
- **`ignore_resistances: true`** (`weapon.json:5899`).

**Mechanical effect on fight.** Gram bypasses dragon_scales entirely
(`combat.py:84-85, 150`). The fight against Fafnir becomes a normal-damage
brawl with a max-tier weapon. The player still benefits from in-pit 4x —
wait, no: pit bonus only applies if `not getattr(weapon, 'ignore_resistances',
False)`. With Gram, the pit bonus is zeroed but the dragon_scales 0.8
absorption is also zeroed → net is straight full damage. Pit is therefore
*redundant* with Gram, but still legal.

**Discovery path.** This is the *secret* layer. Cues:

- **Drink Fafnir's Blood** (consumable potion dropped on Fafnir's death,
  `game_combat.py:617-618`, `main.py:3008-3021`, recipe at
  `data/items/potion.json:880-896`). Effect handler at
  `food_system.py:675-685`:

  ```
  "As the blood settles, visions flash: a broken blade tumbling through the air
   over a sacred altar... and being reborn in divine fire."
  ```

  This is the ONLY explicit hint inside the game world that the throw-over
  reforge exists. **But** this hint only fires *after* Fafnir is killed —
  it's an across-runs payoff, not a current-run guide. (Reverse-logic: the
  player kills Fafnir the hard way first, learns the secret, applies it on
  the next run.)
- T3 lore hint (`data/hints.json:160`): "before the blade was whole, a god
  had to intervene. Odin's methods are not always what you'd expect."
- Gram weapon lore (`weapon.json:5900`): "Odin thrust Gram into the
  Branstock oak... His son Sigurd had the pieces reforged."
- The Bronze Bull-to-fountain mechanic for L20 trains the player on
  "drop quest item on terrain feature." The throw-over is the *next* layer
  of that puzzle pattern.

**Reward beyond the fight.** Gram persists as a T5 weapon with
`ignore_resistances`. Comparable to Sword of Michael in power tier (`Gram
base 24 vs SoM base 45`, max-chain mult 9.0 vs 16.0, no
abaddon_bonus_damage, no auto-bonus vs Abaddon).

**Code trigger map:**
- Broken Gram item: `data/items/weapon.json:5902-5941`.
- Reforged Gram item: `data/items/weapon.json:5853-5901`.
- Reforge logic: `game_combat.py:286-303` (throw detection) →
  `game_divine.py:411-462` (reforge or normal path).
- Odin's Shrine carve: `dungeon.py:1789-1859`.
- Fafnir's Blood vision: `food_system.py:675-685`.
- Pit dig: `game_combat.py:1139-1179`.
- Pit-bonus damage: `combat.py:148-154`.

### Quest Layer 3 — Fafnir's Blood (permanent fire-resist)

**What it is.** Quaffing Fafnir's Blood:

```python
amt = player.max_hp - player.hp
player.restore_hp(amt)
player.add_effect('fire_resist', -1)  # permanent
```
(`food_system.py:677-679`)

Full heal + permanent fire resistance + the lore vision hint.

**Discovery path.** Drops automatically on Fafnir's death
(`game_combat.py:617-618`). Player learns by drinking; the lore prose
embeds the throw-over hint.

**Mechanical effect.** No effect on the Fafnir fight (it drops after the
kill). Permanent fire-resist matters for L100 (Abaddon's `hellfire` 4d8+4)
and is generally strong against fire breaths late-game.

### Cross-system interactions

- **Items:** Bronze Bull (no — that's L20). For Fafnir: Broken Gram, Gram,
  Sigurd's Shovel, Fafnir's Blood, dragon_scale ingredient.
- **Altars:** Odin's Altar on L53 (`dungeon.py:1538-1540`) — handled by
  this quest specifically. Throw-over mechanic uses standard ALTAR tile.
- **Chronicle:** `"Fafnir fell. The dragon's scales were like iron. I still
  smell the smoke."` (`game_combat.py:611`). Reforge chronicle: *"I threw
  the broken blade over the altar like a madman. Lightning struck. When the
  light cleared, Gram lay whole on the stone, reforged. Odin called me
  worthy."* (`game_divine.py:459`). Non-reforge: "Laid the broken blade on
  the altar. It dissolved. Odin spoke of digging" (`game_divine.py:461`).
  Fafnir blood drop: `main.py:3019`.
- **Boss scroll:** `scroll_of_the_hoard` → `DRAGONHOARD-MMXXV-III`
  (`scroll.json:188-208`).
- **Story popup:** `boss_fafnir` (`main.py:3415-3431`).
- **Hints:** T1 (`hints.json:98`), T3 (`hints.json:160`).
- **Quirks:** Odin's Vigil (12,960 turns waited — Odin only, no Fafnir
  quirk; `quirk_system.py:221-222`).
- **Pit-dig system:** general mechanic, but the L60 arena is shaped
  specifically for it (rock formations as cover, `boss_levels.py:332-334`).

### Open questions

- Two valid paths kill Fafnir: pit-dig (no Gram) OR reforged Gram (no pit
  needed). Was the design intent that a player should do *both* — pit-dig
  with Gram for synergy? With Gram equipped the pit bonus is suppressed
  (`combat.py:150-154`), so it isn't synergistic by code.
- The Cretan Bull idol cross-reference in artifact lore says "King Minos
  was given such a bull by Poseidon" — this is the Asterion line, not
  Fafnir. Just confirming there's no second bronze-bull-for-Fafnir layer
  I'm missing; the Bronze Bull is Ariadne/Theseus only.
- INCOMPLETE: I find no in-game hint that explicitly mentions the
  throw-over reforge mechanism *before* Fafnir dies. The Fafnir's Blood
  vision is the post-fact reveal. T3 says "Odin's methods are not always
  what you'd expect" — that's the only pre-fight nudge.

---

## Fenrir the Wolf of Ragnarok (L80)

### Arena

`_level_80_hall` (`src/boss_levels.py:349-412`).

- Main entrance gate at (39, 4) (`boss_levels.py:357-360`).
- Grand hall at (39, 17) 25x13 (`boss_levels.py:363-365`).
- **ALTAR of Odin in center of Grand Hall** (`boss_levels.py:369`):
  `tiles[hall.center[1]][hall.center[0]] = ALTAR`. Generic altar; no
  Fenrir-specific resistance-strip behavior in code.
- 4 side rooms off Grand Hall (`boss_levels.py:372-375`).
- Secondary hall at (39, 31) (`boss_levels.py:378-381`).
- More side rooms (`boss_levels.py:384-387`).
- Throne room (boss chamber) at (39, 43) 29x9 (`boss_levels.py:390-392`).
- **Frozen pillars** (WALL tiles) at (31,42), (35,44), (43,44), (47,42)
  (`boss_levels.py:395-397`) — LOS cover.
- **Ice patches** (ICE tile) — three patches at left/center/right of the
  boss room (`boss_levels.py:399-403`). ICE is slippery terrain.

### Base stats (`data/monsters.json:19803-19859`)

- HP 3000; THAC0 -16; speed 12.
- Attacks: `devouring_bite` (5d10+9 slash), `frost_howl` (3d8+4 cold),
  `crushing_paw` (2d8+3 blunt).
- AI: `fenrir_rage` (`monster.py:416-418`, `_fenrir_rage_turn` at
  `monster.py:864-893`). Every 4 turns gains a rage stack
  (`rage_interval: 4`, `monsters.json:19834`):
  - Each rage stack adds `1d6` damage *per stack* per attack
    (`rage_damage_bonus: "1d6"`, `monster.py:317-319`).
  - At 3+ rage stacks: speed jumps to 14 (`monster.py:889-890`), giving
    double-move per turn.
  - At 3+ rage stacks: `_fenrir_multi_attack` triggers — Fenrir uses
    **all 3 attacks in one turn** (`monster.py:246-248`, `_fenrir_multi_attack`
    at `monster.py:955-983`). Each is its own to-hit roll, each gets the
    rage damage bonus.
- Rage escalation messages (`monster.py:872-880`): "Fenrir snarls and grows
  larger!" → "Fenrir's hackles rise" → "Fenrir HOWLS!" → "Ragnarok fury!" →
  "The World-Wolf's shadow swallows the light!"
- Resists: cold, slash. Weak: fire.
- Harvest tier 5, threshold 4 → `fenrir_fang`.
- Treasure: 800-1500 gold, item_tier 7, `boss_scroll_id:
  scroll_of_ragnarok` (`monsters.json:19857`).

### Quest Layer 1 — Gleipnir (the core canonical quest — REQUIRED for the boss)

**What it is mechanically.** A Power action `bind_odinkiller` is unlocked
when the player carries Gleipnir (`game_menus.py:981-1008`). Activating it:

```python
fenrir.reset_rage()                   # rage_stacks = 0, _rage_turn_counter = 0
fenrir.status_effects['paralyzed'] = 2
```

Rage resets to 0. Fenrir paralyzed for 2 turns. **And** the player loses 1
stat point on a rotating cycle STR → DEX → CON
(`game_menus.py:996-1008`) — "The binding tears something from you."

Repeated binds: tracked via `_gleipnir_bind_count` (`game_menus.py:999`).
Each successive use rotates the stat tax.

**Discovery and assembly path.**

1. **Six impossible ingredients** spawned across L62, L65, L68, L71, L74,
   L77 (`dungeon.py:1559-1570`, `_create_gleipnir_room` ref):
   - L62: Sound of a Cat's Footstep (`cats_footstep`)
   - L65: Roots of a Woman's Beard (`womans_beard`)
   - L68: Root of a Mountain (`mountain_root`)
   - L71: Breath of a Fish (`fish_breath`)
   - L74: Spittle of a Bird (`bird_spittle`)
   - L77: Sinew of a Bear's Sensitivity (`bear_sinew`)

   All defined as artifacts in `data/items/artifact.json:50-130` range
   (verified `cats_footstep` at line 50-62, `womans_beard` at 63-75).
2. **Dwarven Forge** — guaranteed on L76 (`dungeon.py:1572-1574`,
   `_create_dwarven_forge` at `dungeon.py:2133-2142`). Visually an ALTAR
   tile, position stored on `dungeon.dwarven_forge_pos`.
3. **Drop all 6 components on the forge tile**: `_do_drop_item` detects
   forge-pos drops (`main.py:3751-3756`), calls `_check_gleipnir_forge`
   (`game_divine.py:472-497`). When `found_ids == _GLEIPNIR_COMPONENT_IDS`
   (frozenset at `game_divine.py:467-470`), all 6 are consumed and the
   Gleipnir artifact materializes.
4. Pick up Gleipnir; enter L80; use it as an active power on Fenrir.

T2 hints: `data/hints.json:101-102`:
- "The dwarves of Svartalfheim forged Gleipnir from six things that do not
  exist. Adventurers have found strange objects in unusual rooms between
  the dragon's lair and the wolf's den."
- "A forge of dwarven make has been discovered in the deep floors before
  Fenrir's hall."

T3 (`hints.json:161`): "Fenrir's hide turns aside most blows. Enchantment
and relentless chains of correct answers are the wolf-binders' tools — the
ribbon was made of impossible things."

**Mechanical effect on fight.** Each use resets rage stacks (no
double-move, no rage damage bonus, no multi-attack) and gives 2 paralyzed
turns. Each use costs 1 stat permanently. Player needs to time binds for
when Fenrir hits the 3-stack threshold.

**Reward beyond the fight.** None directly — Gleipnir is consumed in use
(it's an active power not a kept item).

### Quest Layer 2 — Vidar's Sandal (the MEGA SECRET — instant kill)

**What it is mechanically.** While the player has an item with
`id == 'vidars_sandal'` in inventory, the very first time they hit Fenrir
with any chain ≥ 1:

```python
elif (chain >= 1 and monster.kind == 'fenrir_wolf' and monster.alive
      and any(getattr(i, 'id', '') == 'vidars_sandal'
              for i in self.player.inventory)):
    # Vidar's Sandal instant kill!
    monster.hp = 0
    monster.alive = False
```
(`src/game_combat.py:1292-1311`)

Combat sequence:
1. "You plant Vidar's Sandal against Fenrir's lower jaw!"
2. "With impossible strength, you wrench the great wolf's mouth apart!"
3. "FENRIR, THE WORLD-WOLF, IS TORN ASUNDER!"

Then `_on_monster_killed` fires normally — boss scroll, chronicle, etc.

**Discovery and assembly path.**

1. **10 leather scraps** scattered on L5, L13, L21, L28, L35, L42, L50,
   L58, L66, L73 (`dungeon.py:1542-1556`). Each is a guaranteed single
   spawn — leather_scrap artifact, item_class artifact, weight 2.0
   (`dungeon.py:1547-1553`). Lore: "Useless scrap left over from
   leather-working. Too small for armor, too stiff for bandages."
2. **Vidar's Altar** — guaranteed on L79 (`dungeon.py:1576-1578`,
   `_create_vidar_altar` at `dungeon.py:2145-2154`). Stored on
   `dungeon.vidar_altar_pos`. Visually a generic ALTAR tile.
3. **Drop 10 leather scraps on Vidar's altar**: detected at
   `main.py:3758-3763` → `_check_vidar_altar`
   (`game_divine.py:499-521`). When ≥10 scraps present, consumed; spawn
   Vidar's Sandal armor on the altar (`game_divine.py:504-520`). Sandal at
   `data/items/armor.json:3725-3751`: T5 divine feet armor, AC +3, slash
   resist 0.25, blunt resist 0.25, can_be_cursed false, equip_threshold 2,
   quiz_tier 4.
4. Pick up sandal, carry to L80 (no need to equip — inventory presence is
   the trigger condition at `game_combat.py:1292-1294`).

**Discovery lore.** Very subtle. Direct in-game hints I find:
- The Sandal's lore (`armor.json:3749`): *"Vidar the Silent, son of Odin,
  wore it when he avenged his father — planting his foot on the lower jaw
  of the World-Wolf and tearing the beast apart with his bare hands."* This
  is the canonical Norse-mythological reference and the secret's only
  in-game explanation.
- T3 hint via Recall Lore could reveal Vidar — search `data/hints.json`
  for "vidar" / "silent god" — I find no T1-T5 hint that names Vidar
  directly. The discovery is meant to come through accumulating 10 leather
  scraps and noticing the L79 altar.

INCOMPLETE: I find no explicit lore hint about leather scraps' purpose.
The player discovers the secret by finding 10 random "useless" scraps,
finding the altar on L79, and either dumping items on the altar
experimentally or noticing the chronicle stamp on assembly. This *is*
deliberate — the developer brief explicitly marks the Sandal as a "MEGA
SECRET" — but it's worth noting how thin the discovery surface is.

**Mechanical effect on fight.** First swing wins. Skips the entire
Gleipnir mechanic and the Fenrir rage AI.

**Reward beyond the fight.** Vidar's Sandal is itself a powerful armor
piece with permanent 0.25 slash/blunt resistance. The L80 boss scroll
drops normally.

**Code trigger map:**
- Sandal item: `data/items/armor.json:3725-3751`.
- Instant-kill condition: `game_combat.py:1292-1311`.
- Vidar altar carve: `dungeon.py:2145-2154`.
- Sandal assembly: `game_divine.py:499-521`.
- Leather scrap spawning: `dungeon.py:1542-1556`.

### Quest Layer 3 — ICE patches (arena tactic)

ICE tiles in the boss room (`boss_levels.py:399-403`) — slippery terrain.
This is environmental and not boss-specific code, but its tactical effect
is positioning challenges: if Fenrir or the player end a movement on ICE,
they slide. The frozen pillars provide LOS-break tactic similar to L40
Medusa's columns.

### Quest Layer 4 — Fire weakness (the dumb-simple path)

Fenrir is `weaknesses: ["fire"]` (`monsters.json:19841`). Any fire-type
attack deals bonus damage via `_damage_multiplier`. Mechanically simple,
mythologically off-canon but tactically real. T3 hint `hints.json:161`:
"Fenrir's hide turns aside most blows. Enchantment and relentless chains
of correct answers are the wolf-binders' tools" — the implication being
that ordinary fire weapons aren't enough on their own.

### Cross-system interactions

- **Items:** 6 Gleipnir components, leather scraps, Gleipnir (assembled),
  Vidar's Sandal, fenrir_fang ingredient.
- **Altars:** Generic altar in Grand Hall (no special handler), Dwarven
  Forge (L76, special detection), Vidar's Altar (L79, special detection).
- **Chronicle:** `"Fenrir is bound. Or dead. I'm not sure which. The wolf
  was... vast. The ground still shakes."` (`game_combat.py:612`). Forge
  chronicle: "Fed six impossible things to the Dwarven Forge"
  (`game_divine.py:497`). Sandal: "Piled leather scraps on an ancient
  altar... Vidar's Sandal. The Silent God's secret weapon."
  (`game_divine.py:521`).
- **Boss scroll:** `scroll_of_ragnarok` → `RAGNAROK-MMXXV-IV`
  (`scroll.json:209-228`).
- **Story popup:** `boss_fenrir` (`main.py:3432-3447`).
- **Hints:** T2 (`hints.json:101-102`), T3 (`hints.json:161`). Vidar
  himself is not named in any hint I can find.
- **Quirks:** `fenrir` (Fenrir's Chains: CON +1, 150 turns under debuffs;
  `quirk_system.py:901-907`). This quirk is about debuff endurance, not
  killing Fenrir.
- **FenrirPet:** Independent of the boss — the XYZZY tier-5 reward
  summons a Fenrir wolf pet (`main.py:2643-2655`, `pet_system.py:286-329`).
  Pet has 500 HP, 45 base damage, double-move, regen 3/turn. Pet does not
  appear in the L80 fight unless the player has used XYZZY.

### Open questions

- **The core quest is Gleipnir, the mega-secret is Vidar's Sandal.** The
  developer brief is explicit. Confirmed in code:
  Gleipnir = power, partial nerf, stat tax; Vidar = instant-kill.
- INCOMPLETE: no T3-T5 hint names Vidar directly. The Sandal's only
  discovery surface is the leather scrap accumulation and the L79 altar.
  Was a Vidar hint planned for `hints.json`?
- The Grand Hall altar at L80 (`boss_levels.py:369`) has no Fenrir-specific
  prayer mechanic. Was a faith-driven rage-suppression considered?

---

## Abaddon the Destroyer (L100)

### Arena

`_level_100_abyss` (`src/boss_levels.py:419-498`).

- Narrow ledge entry at (39, 4) with STAIRS_UP (`boss_levels.py:430-433`).
- Descent corridor down to y=15 (`boss_levels.py:435-436`).
- **Ring of 6 chambers around the void** at NW, NE, W, E, SW, SE
  (`boss_levels.py:440-447`). Cross-connected by L-corridors.
- **Spoke corridors** from each ring chamber inward to center (39, 28)
  (`boss_levels.py:460-466`).
- **SIX ALTARS arranged in a ring around the boss chamber**
  (`boss_levels.py:468-478`):
  ```
  (center_x - 8, center_y)
  (center_x + 8, center_y)
  (center_x, center_y - 8)
  (center_x, center_y + 8)
  (center_x - 6, center_y - 6)
  (center_x + 6, center_y - 6)
  ```
  i.e., (31,28), (47,28), (39,20), (39,36), (33,22), (45,22). Each is an
  ALTAR tile. **These are the resistance-strip altars.** Code comment
  (`boss_levels.py:468`): "Altar ring around the boss chamber (6 altars
  for holy fire prayers)".
- Boss arena (Void Throne) at (39, 28), 21x15 (`boss_levels.py:480-482`).
- Two crumbled void-throne WALL pillars at (37, 27) and (41, 29)
  (`boss_levels.py:484-486`) — "minimal cover against locust swarms".
- Four DOORs framing the boss room (`boss_levels.py:489-492`).
- **No STAIRS_DOWN.** L100 is terminal. `_place_stone` in
  `level_manager.py:306-328` puts the Philosopher's Stone in the last
  room.

### Base stats (`data/monsters.json:19860-19942`)

- HP 5000; THAC0 -16; speed 10.
- Attacks (5 total):
  - `apocalypse_blast` (6d10+8 magic, piercing — bypasses magic_resist)
  - `hellfire` (4d8+4 fire)
  - `plague_breath` (3d10+4 poison, piercing)
  - `soul_chill` (3d8+3 cold)
  - `abyssal_claw` (2d10+3 slash)
- AI: `abaddon` (`monster.py:421-422`, `_abaddon_turn` at
  `monster.py:900-913`). Aggressive movement; sets
  `_wants_locust_spawn = True` every 4 turns (`locust_interval: 4`,
  `monsters.json:19903`).
- **Locust swarm spawn** (`game_combat.py:1432-1434`, `_spawn_abaddon_locusts`
  at `main.py:3023-3094`). 3-5 locusts per swarm (`locust_count: [3, 5]`,
  `monsters.json:19904-19907`). With negative-karma `_locusts_strengthened`
  flag, lo += 2 and hi += 3 → 5-8 locusts (`main.py:3037-3040`).
- Resists: poison, cold, fire, slash, blunt (5 of 8 main damage types,
  `monsters.json:19908-19914`). The 3 unblocked are: magic (Abaddon's own
  apocalypse_blast type), holy (his weakness), and the unmentioned drain/
  lightning/acid which most weapons don't natively deal.
- **`base_resistances` stored separately** (`monsters.json:19915-19921`,
  `monster.py:83`) for the altar-strip restoration logic.
- Weak: holy.
- Tags: demon, celestial.
- Harvest tier 5, threshold 5 → `void_essence`.
- Treasure: 2000-5000 gold, item_tier 10, `boss_scroll_id:
  scroll_of_the_abyss` (`monsters.json:19940`).

### Quest Layer 0 — The Seven Seals (REQUIRED gate, L83-L97)

**What it is mechanically.** L99 has no descent path until 7 seal demons
are killed (`main.py:1210-1217`):

```python
if self.dungeon_level == 99 and len(self.seals_broken) < 7:
    remaining = 7 - len(self.seals_broken)
    self.add_message(
        f"Seven seals hold the Pit closed. {remaining} remain unbroken.", 'warning')
    self.add_message(
        "You must slay the seven guardians before the way opens.", 'info')
    return
```

Seal demons are guaranteed spawns on L83/85/87/89/91/93/97
(`level_manager.py:152-202`, `_SEAL_DEMON_LEVELS`). On kill,
`game_combat.py:619-630` adds the corresponding seal_id to the
`seals_broken` set; at count 7 emits the gate message: *"ALL SEVEN SEALS
ARE BROKEN. The way to the Pit stands open."*

**The seven seal demons** (`monsters.json:21084-21510`):
1. **Amon, Demon of Wrath** — L83, HP 1200, fire-focused, weak to
   cold/holy.
2. **Buer, Demon of Pestilence** — L85, HP 850, ranged poison, weak to
   fire/holy.
3. **Mammon, Demon of Famine** — L87, HP 900, speed 12, has `sp_drain:
   15`, weak to fire/holy.
4. **Bael, Demon of War** — L89, HP 950, slash/blunt focus, weak to
   magic/holy.
5. **Samael, Demon of Death** — L91, HP 1000, magic/cold, weak to
   fire/holy.
6. **Beleth, Demon of the Earthquake** — L93, HP 1050, speed 8, weak to
   magic/holy.
7. **Abyzou, Demon of Silence** — L97, HP 1100, speed 12, `dancer` AI,
   inflicts confused/silenced, weak to slash/holy.

Each drops a unique `seal_of_<theme>` artifact (`treasure.unique_drop_id`)
and 200-400 gold; item_tier 4 item drops; **no boss_scroll_id** (the
reward is the Abaddon scroll itself).

**Discovery path.** The gate message at L99 is the explicit funnel. T3
hint `hints.json:113`: *"Ancient theology speaks of a second death... what
they face at the very bottom."* T5 lore (`hints.json:157`): "Abaddon
resists nearly everything... faith as the only weapon that drew blood — a
blade that was earned, not found."

**Mechanical effect on Abaddon fight.** None directly; this is the
descent gate. But killing seal demons is the only time the player can
explore L83-L97 for the curated late items (adamantine wave at L81+, the
Greater Aegis spawn at L65+).

**Reward beyond the fight.** 7 seal artifacts (`seal_of_wrath`,
`seal_of_pestilence`, etc., `monsters.json:21138, 21198, 21258, 21323,
21383, 21443, 21506`). These appear to be display-only artifacts; I find
no code that gives them mechanical effects beyond inventory presence.

### Quest Layer 1 — L99 Altar of the Last Judgment (Michael's gifts)

**What it is mechanically.** L99 has a single special altar
(`judgment_altar_pos`, `dungeon.py:1580-1582, 2157-2167`) placed in the
largest non-start room. Praying *while standing on this altar* triggers
`_resolve_judgment` (`game_divine.py:684-693` → `game_encounters.py:928-989`).
Single-use; sets `_judgment_resolved = True`.

The outcome is determined by current `karma` score (-10 to +10,
`npc_encounters.py:2030-2045`, `_JUDGMENT_TIERS` at lines 1987-2027):

| Karma | Outcome | Effect |
|------:|---|---|
| **+10** | `sword_and_scales` | Grant **Sword of Michael** AND **Scales of Michael**; title set to **Paladin**. |
| +1 to +9 | `scales_granted` | Grant **Scales of Michael** only. |
| 0 | `silence` | Nothing. |
| -1 to -5 | `locusts_strengthened` | L100 locust swarms +2-3 per spawn (`main.py:3037-3040`). |
| -10 to -6 | `abaddon_empowered` | L100 Abaddon +50% HP (`main.py:464-472`). |

**The Sword of Michael** (`data/items/weapon.json:8591-8640`):
- T5 divine sword, base 45, max chain 9.
- Multipliers up to 16.0x.
- `damageTypes: ["holy", "slash"]`, `critMultiplier: 4.0`.
- `ignoreShield: true`, `ignore_resistances: true`,
  `abaddon_bonus_damage: "6d10"` (`combat.py:156-160`: adds 6d10 every hit
  vs Abaddon).
- Abaddon is `weak: holy` (`monsters.json:19922-19924`). Damage flow:
  base 45 × chain mult × 4× crit × 1.5× holy weakness × ignore_resistances
  + 6d10 bonus. (REVERSE_ENGINEERED.md calculates ~5650 at max.)

**The Scales of Michael** (`data/items/artifact.json:245-256`): an
inventory artifact. Grants the *Summon the Heavenly Host* power
(`game_menus.py:697-705`), `1 use`, `0 cooldown`. Activation
(`game_menus.py:1010-1017`) sets `heavenly_host_active = True`. While
active, every Abaddon locust spawn triggers a matching `heavenly_angel`
spawn (`main.py:3078-3094`). Angels (`monsters.json:21562-21601`) use the
`seek_locust` AI (`monster.py:915-953`) — they move toward the nearest
locust and, on adjacency, annihilate both bodies in a single turn.
"An angel meets a locust in a blaze of holy fire! Both are consumed!"
(`game_combat.py:1399-1411`).

**Discovery path.** T2 hint `hints.json:123`: "A sealed tribunal near the
thirtieth depth..." (misleadingly cites L30, probably error or
non-specific). T5 `hints.json:157`: "faith as the only weapon that drew
blood — a blade that was earned, not found."

INCOMPLETE: T2 hint says "thirtieth depth" but the Judgment Altar is on
L99 (`dungeon.py:1580-1582`). Either the hint is intentionally cryptic or
it's a leftover from an earlier design.

**Karma accumulation.** Each NPC encounter on the way down adjusts karma
(`game_encounters.py:729-733`, `_apply_karma`). The whole karma system is
its own audit; the relevant slice here is *Abaddon-affecting karma is
finalized at the L99 prayer*. Once the player stands on the altar and
prays, the outcome is locked.

### Quest Layer 2 — L100 Altar Holy Fire (resistance strip — Layer 1 of the boss fight itself)

**What it is mechanically.** When the player is on any L100 altar and
prays (`game_divine.py:749-777`):

```python
if self.dungeon_level == 100 and at_altar:
    pos = (p.x, p.y)
    if pos in self._l100_altars_used:
        self.add_message("This altar's holy power has been spent.", 'info')
    elif chain > 0:
        turns = chain * 2
        self.abaddon_resist_removed_turns += turns
        abaddon = next((m for m in self.monsters
                        if m.alive and m.kind == 'abaddon_destroyer'), None)
        if abaddon:
            abaddon.resistances = []
            self.add_message(
                f"Holy fire surges around the Destroyer! "
                f"His defenses crumble for {turns} turns!", 'success')
```

Chain N (capped 0-8) → `turns = chain * 2`, max 16 turns of zero
resistances. Each altar is single-use (`_l100_altars_used` set,
`main.py:179, 322`). **Six altars per arena** (`boss_levels.py:468-478`)
× chain-5 prayer = 10 × 6 = 60 turns max stripped if perfectly orchestrated.

Restoration runs in `main.py:1543-1549`: when
`abaddon_resist_removed_turns` decrements to 0, Abaddon's resistances are
restored from `base_resistances`.

Cooldown on the prayer itself: `prayer_cooldown = max(100, 80 + effective
* 25)` = 105-280 turns base. Fisher King quirk halves it; Fisher King
mystery halves it AGAIN, stacking (`game_divine.py:781-785`).

**Discovery path.** T2 hint `hints.json:34`: "Strange altars sometimes
appear in the dungeon. Those who approach and kneel before them discover
ancient challenges — and ancient rewards." T2 `hints.json:37`: "Prayer is
not merely a comfort for the frightened. Those who speak to the gods at
the right place and the right time receive answers more tangible than
peace of mind." T5 `hints.json:175`: "Three boons are available to those
who pray at the right altars with the right knowledge — and the gods do
not offer them twice."

**Mechanical effect on fight.** During a strip window, Abaddon's
poison/cold/fire/slash/blunt all do full damage. With one weapon swing
during a strip = ~5× damage vs default. With chain-5 prayers × 6 altars
the player has roughly 60 turns of clean burst — practically the entire
fight.

**Reward beyond the fight.** None — altars are consumed in use.

### Quest Layer 3 — Sword of Michael special interactions (Layer 2 of the fight)

Already documented in Layer 1 (Judgment). When equipped, Sword of Michael:
- Bypasses resistances entirely (`combat.py:84-85`).
- Adds 6d10 every hit vs Abaddon (`combat.py:156-160`).
- Bypasses shields (`ignoreShield: true`).
- Crit at 4x (max-chain on the Sword's 16x multiplier = crit window).
- Holy weakness 1.5x.

Synergizes additively with altar strips on raw damage (the 6d10 bonus +
holy weakness apply on top of the resist-strip — though resist-strip is
redundant with `ignore_resistances`, the holy weakness still multiplies).

### Quest Layer 4 — Heavenly Host counter (Layer 2.5 of the fight)

Scales of Michael power activated → matching angels spawn for each
Abaddon locust (`main.py:3078-3094`). This is a swarm control system: by
default Abaddon's 4-turn locust cadence pressures the player; with Host
active each swarm is met by an equal angel force that annihilates them
1-for-1.

### Quest Layer 5 — The Abyss (Layer 3 — kill Death itself, the secret victory)

**What it is mechanically.** The Tablet of Second Death + Philosopher's
Stone + Lake of Fire scroll + Abyssal Shimmer + Death-pursuit, all
combined, opens the Abyss and consumes Death itself (`main.py:1374-1407`,
triggered from `game_magic.py:1953-1979`).

Conditions for `_trigger_abyss(shimmer)`:

```python
shimmer = next((g for g in self.ground_items if g.id == 'abyssal_shimmer' and g.activated), None)
complete_on_shimmer = shimmer and any(
    g.id == 'complete_tablet_of_second_death'
    and g.x == shimmer.x and g.y == shimmer.y
    for g in self.ground_items)
death_on_shimmer = (self.death_pursues and self.death_monster is not None
                    and shimmer is not None
                    and self.death_monster.x == shimmer.x
                    and self.death_monster.y == shimmer.y)
if shimmer and complete_on_shimmer and death_on_shimmer:
    self._trigger_abyss(shimmer)
```
(`game_magic.py:1962-1979`)

I.e., the player must:
1. Have killed Abaddon and have the Philosopher's Stone.
2. Have found the Tablet of Second Death on L80-99 (lore-level random).
3. Have combined Stone + Tablet using the Philosopher's Wrench
   (`main.py:1318-1344`, found L21-49) → Complete Tablet.
4. Have found the Abyssal Shimmer (L1-20) — a fixed terrain tile.
5. Drop the Complete Tablet on the Shimmer tile → Shimmer activates
   (`main.py:3713-3728`).
6. Have triggered Death pursuit by ascending L100 with the Stone
   (`main.py:1240-1247`).
7. Lure Death onto the Shimmer tile.
8. Read the Lake of Fire scroll (`game_magic.py:1953-1979`).

When triggered (`main.py:1374-1407`):
- Death is destroyed (`self.death_pursues = False; self.death_monster =
  None`).
- Player gets **Scroll of Death's Bane** (`make_death_bane_scroll`,
  `items.py:573-589`, code `ABYSSAL-VICTOR`).
- Message: *"Take this code to your father proudly — you have shown true
  Wisdom and Courage."* (`main.py:1392-1394`).
- Chronicle: *"I killed Death. The lake of fire opened beneath it and
  swallowed it whole. The silence afterwards was the loudest thing I've
  ever heard."* (`main.py:1400`).

**Discovery path.** Many threaded T3-T5 hints (`hints.json:91, 92, 113,
172`):
- "An old alchemist's journal mentions a tool that joins rather than
  separates. 'The Wrench completes what is broken,' he wrote. 'Stone into
  Tablet, purpose into form.'"
- "Theologians call certain ground 'thresholds' — places where the boundary
  between life and death grows weak. Scripture marks these places."
- "Ancient theology speaks of a second death — one the oldest texts say
  even Death himself cannot escape."
- Plus the unidentified Lake of Fire scroll's inscription
  `"Revelation 20:14"` shown on Shimmer-step (`main.py:1156`).
- Plus the Lake of Fire scroll lore (`items.py:518`): "The last line is
  underlined twice: 'This is the second death, the lake of fire.'"

**Mechanical effect on fight.** Doesn't change the Abaddon fight directly;
it changes the *escape* from a "survive Death's chase" run to an
"annihilate Death" victory. The lore-items spawn levels are randomized per
run (`main.py:114-122`), so the player can't farm the secret deterministically
without enough Recall Lore hints.

### Cross-system interactions

- **Items:**
  - Sword of Michael (`weapon.json:8591-8640`).
  - Scales of Michael (`artifact.json:245-256`).
  - 7 seal artifacts (per-demon `unique_drop_id`).
  - Philosopher's Stone (`artifact.json:2-13`, spawned by
    `level_manager.py:306-328`).
  - Tablet of Second Death (`items.py:481-498`).
  - Philosopher's Wrench (`items.py:525-549`).
  - Complete Tablet of Second Death (`items.py:552-570`).
  - Abyssal Shimmer (`items.py:464-478`).
  - Scroll of the Lake of Fire (`items.py:501-522`).
  - Scroll of Death's Bane (`items.py:573-589`, reward).
  - Scroll of the Abyss (`scroll.json:230-247`, boss reward, code
    `ABYSS-MMXXV-V`).
  - void_essence ingredient.
- **Altars:** 6 L100 altars (resistance strip), 1 L99 Judgment altar
  (Michael gift). All single-use.
- **Karma:** Mandatory feeder system — every NPC choice on the way down
  (`game_encounters.py:729-733`) compounds toward the L99 verdict.
- **Chronicle:** First-Abaddon-sight stamp ("Abaddon. The Destroyer. He's
  real. He's here. This is it.", `game_combat.py:1267-1269`). Kill
  ("Abaddon is destroyed. The Pit is sealed. I can barely hold the pen.",
  `game_combat.py:613`). Each seal break (`game_combat.py:626`). Stone
  pickup (`main.py:2129`). Tablet/Wrench/Shimmer milestones
  (`main.py:2129-2148`). Stone-out (`game_combat.py:1255-1265`,
  `main.py:1265`).
- **Story popups:** `boss_abaddon` (`main.py:3449-3464`), `exit_with_stone`
  (`main.py:3466-3487`, code `QUEST-COMPLETE`), `exit_without_stone`
  (`main.py:3489-3510`).
- **Boss scroll:** `scroll_of_the_abyss` → `ABYSS-MMXXV-V`
  (`scroll.json:230-247`).
- **Hints:** T2 (`hints.json:34, 37, 123`), T3 (`hints.json:91, 113`),
  T5 (`hints.json:157, 175`). Plus the L99 altar Bible-verse rotation
  (`game_divine.py:735-744`).
- **Quirks:** No Abaddon-specific quirk. The L100 fight benefits from any
  endgame quirk (Caesar, Leonidas, Battle Trance, etc.).
- **Death-chase mechanic:** Tied to L100 via Stone exit
  (`main.py:1240-1247`). Death freeze via prayer (`game_divine.py:791-797`).
- **Locust spawn:** `main.py:3023-3094`.
- **Heavenly Host counter-spawn:** `main.py:3078-3094`.

### Phase structure of the fight itself

Implicit phases (not state-machine-driven):

1. **Approach phase (turns 0-3).** Walk in, Abaddon registers, spawns first
   locust swarm at turn ~4. Player should use the first altar
   pre-engagement.
2. **Locust-pressure phase (recurring every 4 turns).** Swarm pressure
   forces the player to deal with multiple targets; SP drain from locusts
   (`monsters.json:21548`, `sp_drain: 5` — and combat handling at
   `game_combat.py:1483-1488`).
3. **Strip-window phases.** Each successful altar prayer = chain×2 turns
   of full damage. Six altars = up to six windows.
4. **Resistance-restore phase.** When `abaddon_resist_removed_turns`
   ticks to 0, Abaddon's `base_resistances` restored
   (`main.py:1543-1549`). Player switches to magic/holy/lightning damage
   types if available.
5. **End phase.** Boss popup (`main.py:3449`), Stone placed by
   `_place_stone`, Death-chase initiation on ascent
   (`main.py:1240-1247`).

### Open questions

- The Sword of Michael's 4x crit multiplier stacked with 16x max chain
  produces the "one-shot at chain-9-crit" outlier flagged in
  `REVERSE_ENGINEERED.md:107-118`. The Question 6 in REVERSE_ENGINEERED.md
  is whether to nerf the crit, raise Abaddon HP, or accept the synergy.
  Map-only, no fix proposed here.
- **L100 altar discoverability.** T5 hint about "right altars" exists but
  no hint specifically tells the player "stand on the altar during the
  Abaddon fight and pray." Combined with prayer cooldown ≥105 turns, the
  six altars define the fight's tempo — but only a player who *has read
  T2 altar hints + tried prayer + observed the holy-fire message* will
  put the strategy together. By design? Probably yes.
- The seal artifacts (`seal_of_wrath` etc.) appear to be lore-only — no
  mechanical effect I can find. Possibly intentional collectible.
- T2 hint `hints.json:123` says "thirtieth depth" for the tribunal but the
  altar is on L99. Documenting this discrepancy.

---

## Cow King (L30-L39 secret mini-boss, not required)

### Arena

`_level_999_moo_moo_farm` (`src/boss_levels.py:533-615`).

- Reached only through the Secret Cow encounter (`game_encounters.py:83-102`).
- 80x50 vast open pasture at (40, 25), 71x41 (`boss_levels.py:546-547`).
- Cow King's pen (top-right) at (68, 8) (`boss_levels.py:553-554`), 13x9
  with a single DOOR (`boss_levels.py:556-561`).
- ~20 scattered fence-post WALL pillars
  (`boss_levels.py:563-573`).
- STAIRS_DOWN in the entry-area corner = portal back home
  (`boss_levels.py:550`). Re-entry returns to the original level via
  `_exit_cow_level` (`game_encounters.py:104-114`).

### Base stats — Cow King (`data/monsters.json:21653-21709`)

- HP 550; THAC0 2; speed 10.
- Attacks: `royal halberd` (4d6+8 slash), `thunderous charge` (3d8+5
  physical, 30% chance `stunned` 3 turns).
- AI: `aggressive`.
- Resists: blunt, cold. Weak: fire.
- Harvest tier 4, threshold 4 → `royal_beef`.
- `is_mini_boss: true`, `spawn_chance: 0`, `min_level: 30, max_level: 39`.
- Treasure: 200-500 gold, item_tier 3, `unique_drop_id:
  cow_kings_horns`, `boss_scroll_id: scroll_of_the_pasture`.

### Base stats — Hell Bovine (`monsters.json:21603-21651`)

- HP 85; THAC0 6; speed 10.
- Attacks: `halberd swing` (3d6+4 slash), `gore` (2d6+3 pierce).
- Min/max level 30-39, `pack: true`, fire-weak/blunt-resist.
- 40-50 of them spawn in the pasture (`boss_levels.py:582`).

### Quest Layer 1 — The "poke the cow 10 times" entry

**What it is.** Spawn a Secret Cow NPC on one randomly chosen floor L30-39
per run (`main.py:129`, `_cow_level = _lore_rng.randint(30, 39)`). The cow
is placed by `_maybe_spawn_cow` (`game_encounters.py:38-75`). Bumping it
opens a dialog (`game_input.py:512-554`). Three options:

1. **Feed** — consume an ingredient (`_cow_dialog_phase = 'result'`).
2. **Walk away** — random moo message.
3. **Poke** — increments `_cow_poke_count`. **At 10 pokes**
   (`game_input.py:543-545`), `_enter_cow_level()` triggers. Otherwise,
   one of nine increasingly ominous poke responses
   (`main.py:3161-3171`).

`_enter_cow_level` (`game_encounters.py:83-102`): "The cow's eyes glow
red. The ground splits open beneath you! MOO MOO MOO MOO MOO!" Stores the
return level, removes the cow NPC, changes level to `COW_LEVEL = 999`.

**Discovery path.** No T1-T5 hint mentions cows directly. Pure
NetHack-tradition Easter egg. The chronicle on entry is honest about it
(`game_encounters.py:90`): *"I poked a cow too many times. The floor opened
up. Now I'm in some kind of... cow dimension. This is not in any lore I've
read."*

**Mechanical effect.** Player enters a separate dungeon level — 40-50
Hell Bovines as XP/loot harvest fodder + Cow King as the mini-boss.

### Quest Layer 2 — The fight

40-50 Hell Bovines in the pasture (`boss_levels.py:577-598`) — pack
behavior, fire-weak. Cow King in his sealed pen (`boss_levels.py:553-606`).
Player must navigate the pasture (Hell Bovines stream out as they get
within sight), open the pen, and fight the King.

### Quest Layer 3 — Cow King's Horns (post-fight reward)

Unique drop: **Cow King's Horns** (`armor.json:3777-3803`). Head armor, AC
+1, blunt resist 0.15, `quiz_tier: 2`, `chain_bonus: 1`
(`armor.json:3800`). The chain_bonus 1 means *"a free chain hit before the
quiz even begins — making it impossible to miss entirely"* (lore at
`armor.json:3801`).

Plus boss scroll: `scroll_of_the_pasture` (`scroll.json:971+`).

Plus `royal_beef` ingredient.

### Cross-system interactions

- **Items:** Cow King's Horns, royal_beef, scroll_of_the_pasture.
- **Atmosphere messages:** `boss_levels.py:609-613`.
- **No karma effect.** Cow level kills are not flagged for the L99
  judgment.
- **Quirks:** No Cow-specific quirk.
- **Hints:** None in `hints.json`. Pure undocumented.
- **Chronicle:** Entry stamp `game_encounters.py:90`. Exit stamp via
  `_exit_cow_level`.

### Open questions

- The portal exits via STAIRS_DOWN (`boss_levels.py:550`) but the
  exit handler (`main.py:1207-1208`) intercepts it. Looks correct.
- The Cow Level can only be entered once per run (`_cow_level_done` flag,
  `game_encounters.py:106`). Once exited, the cow is gone permanently.

---

## Cross-boss patterns

### Common quest-discovery pattern

Every boss except Abaddon and Cow King has an "altar/shrine quest" arc:

1. Earlier-floor quest item spawn (Bronze Bull L12, Eye L29, Broken Gram
   L48, leather scraps L5-73, Gleipnir components L62-77).
2. Mid-floor altar/shrine placement (Ariadne L17, Athena L37, Odin L53,
   Dwarven Forge L76, Vidar's Altar L79).
3. Player interaction at the altar (drop or throw quest item).
4. Reward item appears (Thread, Aegis, Shovel, Gleipnir, Sandal).
5. Reward is used in the boss arena.

Abaddon's pattern is different: the "shrine" *is* the L99 Judgment Altar,
the player's input is *karma*, and the reward is in-hand at the boss
fight.

Cow King is unstructured: no altar arc, just dialog Easter egg.

### Common AI characteristics

- All bosses have `frequency: 0` — never spawn from random pools.
- All have `min_hit_chance` floor of 25% via `is_boss = True` in spawn
  (`monster.py:286-288, 287, 959-960`). Bosses always have at least 25%
  hit rate regardless of player AC.
- All carry a `boss_scroll_id` (the real-world reward code).
- All have `harvest_tier: 5` (except Cow King = 4).

### Variants in resistance design

| Boss | Resists | Weak | Pattern |
|---|---|---|---|
| Asterion | blunt | pierce | Single resist, single weakness. |
| Medusa | poison | slash | Single resist, single weakness. |
| Fafnir | fire/poison/blunt/slash/pierce/holy/magic | (none) | Almost everything resisted. `dragon_scales` 0.8 absorbs the rest. Only weakness mechanic is the in-pit 4x bonus and `ignore_resistances`. |
| Fenrir | cold, slash | fire | Two resists, fire weak. Rage AI escalates. |
| Abaddon | poison/cold/fire/slash/blunt | holy | Five resists, holy weak. **Altar strip + Sword of Michael are the only paths to consistent damage.** |
| Cow King | blunt, cold | fire | Mini-boss, mild. |

The escalation is intentional: the player learns "fire vs Fenrir" cleanly
at L80, then meets Abaddon where "holy" is the answer — and discovers
holy weapons are rare (Sword of Michael is the only L99 holy weapon).

### Special damage flags shared across boss-related items

- `ignore_resistances`: Gram (reforged) and Sword of Michael. The two
  "Layer 2" weapons.
- `abaddon_bonus_damage`: Sword of Michael only.
- `can_dig`: Sigurd's Shovel (Fafnir quest), and possibly other pickaxe
  weapons used for general pit-tech.

---

## Master cross-system interaction table

| Boss | Arena altar? | Karma touch | Key items | Quirk hooks | Hint tiers used | Chronicle |
|---|---|---|---|---|---|---|
| **Asterion (L20)** | None | None | Bronze Bull, Ariadne's Thread (artifact+accessory), minotaur_horn | `theseus` (PER+1) | T1, T2, T3 | First-kill stamp + bull pickup stamp |
| **Medusa (L40)** | Generic prayer altar in nave center | None | Eye of Graeae, Aegis of Athena, Greater Aegis, medusa_blood | `medusa` (DEX+2), `perseus` (status reflect) | T1, T3 | First-kill stamp |
| **Fafnir (L60)** | None in arena (Odin's altar is L53) | None | Broken Gram, Gram, Sigurd's Shovel, Fafnir's Blood, dragon_scale | None Fafnir-specific (`odin` Vigil unrelated) | T1, T3 | First-kill stamp + shovel/reforge/blood stamps |
| **Fenrir (L80)** | Generic altar in Grand Hall (no special handler) | None | 6 Gleipnir components, Gleipnir, 10 leather scraps, Vidar's Sandal, fenrir_fang | `fenrir` (CON+1, debuff-endurance) | T2, T3 | First-kill stamp + forge/sandal stamps |
| **Abaddon (L100)** | 6 holy-fire altars + L99 Judgment altar | **Yes — full karma scoreboard determines Michael gifts** | Sword of Michael, Scales of Michael, 7 seal artifacts, Philosopher's Stone, Tablet of Second Death, Wrench, Complete Tablet, Lake of Fire scroll, Abyssal Shimmer, Death's Bane scroll, void_essence | None Abaddon-specific | T2, T3, T5 | First-sight stamp + kill stamp + all seal-break stamps + Stone/Tablet/Wrench/Shimmer stamps + Death-kill stamp |
| **Cow King (L30-39 secret)** | None | None | Cow King's Horns (chain_bonus +1), royal_beef | None | (no hints — pure Easter egg) | Entry stamp via `_log_chronicle` |

### NPC encounter touchpoints

Karma accumulation funnels into Abaddon via the L99 altar
(`game_encounters.py:928-989`). The boss layers do not otherwise touch
`npc_encounters.py` directly — Asterion/Medusa/Fafnir/Fenrir do not change
karma when killed.

### Mystery system touchpoints

- Fisher King mystery halves prayer cooldown
  (`game_divine.py:783-785`). Prayer cooldown directly affects how many
  L100 altars the player can fire in one fight. So Fisher King is a
  cross-system multiplier on Abaddon Layer 2.

### Quirk system touchpoints

Boss-named quirks (not boss-killers, but boss-flavored unlock arcs):
- `theseus` — 5 fully-explored floors (`quirk_system.py:319-327`).
- `perseus` — 5 reflected status effects (`quirk_system.py:1037-1040`).
- `medusa` — 5 blinded-correct episodes (`quirk_system.py:365-371`).
- `fenrir` — 150 turns under debuffs (`quirk_system.py:901-907`).

No `asterion`, `fafnir`, `abaddon`, `cow_king` quirk found.

---

## Summary of incomplete / gap-flagged findings

| Boss | Gap |
|---|---|
| Asterion | Ariadne's Thread defangs vampires too (`can_phase_walls` leak). |
| Medusa | Blindfold path has no canonical self-blind item I can find. No L40 altar-specific holy mechanic. |
| Fafnir | No pre-kill in-game hint for the throw-over reforge — Fafnir's Blood vision is post-fact only. |
| Fenrir | Vidar's Sandal has no T1-T5 hint naming Vidar or the leather-scrap purpose. |
| Abaddon | T2 Judgment hint says "thirtieth depth" but altar is L99. Seal artifacts appear to be lore-only — no mechanical effect after carry. No direct prompt to use L100 altars during the fight (player has to combine T2 + T5 hints + experimentation). |
| Cow King | Entirely undocumented in hints. By design probably. |

End of map.
