# Balance review: loot and food (2026-10-26)

You asked me to review two things: whether there is too much gear and treasure (chests that drop several things at once, such as three rings and some gold, pulling AC down and stats up fast), and whether the stat gains from food are tuned and working.

**Nothing in the game has changed.** This report gives the findings with numbers and file:line evidence. Every proposed change is a decision for you; the questions are in section 5.

## 1. The short answers

**Loot: yes, far too much. The causes are two bugs, generous tables, and nine armor slots plus four stackable ring slots.**

- **Chests.** A floor holds 3.7 to 4.6 chests. The extra-chest roll is made once per room instead of once per floor, giving 2.8 to 4.0 ordinary chests where the comment's rule gives 1.7 (treasuries and throne rooms add a few more).
- **Gear and rings.** By floor 5 a player who finds 85% of a floor has picked up 30 pieces of gear (11 armor, 7 shields), 7 rings and 2 amulets. By floor 10 the totals are 61 gear and 13 rings.
- **The three rings.** What you saw is the jewelry box: at floor 5, 43% of jewelry boxes hold three or four rings or amulets.
- **AC.** The best kit found so far reaches AC 0 by floor 5 and AC -4 by floor 10. The design's luckiest profile was AC -2 at floor 10; the prepared one was AC 4. From floor 5 to about floor 40, ordinary monsters land only the minimum 32% of their blows, however much more armor is worn.
- **Stats.** Four rings and an amulet of one stat can lend +3 by floor 10, +7 by floor 20 and +11 by floor 30. That is more than a focused cook gets.

**Food stats: they work, but they are slow and quiet, three bugs cost players points, and rings swamp them.**

- **It works.** I drove the real Recipes-menu path. A proper meal of a prime cut banks toward that cut's stat; two meals on two new floors make +1.
- **The cap binds early.** The per-stat cap (2 + floor/5) holds a cook who focuses on one stat to one point every five floors after floor 4: +2 by floor 4, +3 by floor 8, +5 by floor 20.
- **It is silent.** A meal that teaches nothing says nothing at all. A player can reasonably conclude it is broken.
- **Bugs.**
  - "All stats" and "two stats" foods raise only one stat.
  - A stat food eaten after a meal is wasted, with a wrong message.
  - 160 recipes give less max HP than a plain meal.

**The catch: the deep game was tuned with today's loot baked in.**

- **Today is on your target.** The committed build wins 44% (your target is 40 to 50%) and the prepared player 38% (plan target 25 to 30%).
- **A blunt cut breaks it.** Chests also carry 45% of the potions and most of the named uniques. A package that cut everything at once took the prepared player from 47% to 0% in a single 60-run cell.
- **The cut I recommend (G1-lite).** It takes a third of the gear and 40% to 57% of the rings and keeps every potion. The kit's AC moves to 3 at floor 5, -1 at floor 10 and -9 at floor 20. It leaves the early game on target: 90% of casual players reach floor 20 and 50% get past Asterion. It still costs the committed build 9 points deep (44% to 35%), all of it between Medusa and Fafnir, where monsters land about 15% more damage on a thinner kit.
- **So the loot change needs a deep re-tune in the same change (R1).** Ease floors 41 to 79 in `monsters.json` until the committed build is back at 40 to 45%. That is data, never a runtime floor multiplier.

## 2. How I measured

- **`tools/balance/loot_census.py`** is a new tool (uncommitted). It counts what a run hands out using only the game's own code:
  - one `LevelManager` per run generates floors 1 to N in order, so named uniques stay once a run;
  - every chest is opened with `container_system._generate_loot_from_template` and `chest_gold`;
  - every monster's death is rolled through `CombatMixin._drop_treasure`;
  - "the kit" is the best non-cursed common piece found so far, worn in every slot.

  The runs used 40 characters, floors 1 to 60, and a player who finds 85% of a floor (the simulator's "prepared" share). Its `--whatif` option tries a change by patching the game's functions in memory only.
- **`tools/balance/difficulty_sim.py`** was run with the same what-if patches, through a runner in my scratchpad. It used the kid model (95% right at tier 1 down to 85% at tier 5), a casual, a prepared and a committed player, and floors 1 to 100. Its floors use unseeded randomness, so one cell swings by about 15 points between seeds. Every win-rate figure below pools 4 seeds × 60 runs.
- **Food:** I called `food_system.cook_compound_recipe` (the function the Recipes menu calls) with a stand-in quiz that always answers right. I checked the stat, max HP and messages floor by floor, plus `Player.feed_cut_stat` over 100 floors.

## 3. Loot volume

### 3.1 What a run hands out

These are cumulative totals for a player who finds 85% of each floor, opens the chests found and kills what is met.

| By floor | Chests | Gear (armor / shields) | Rings | Amulets | Rings and amulets that lend a stat | Potions | Named uniques | Gold | Treasure (value) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 3.9 | 6 (2 / 1) | 1.5 | 0.4 | 0.7 | 4 | 0.1 | 158 | 35 |
| 5 | 19 | 30 (11 / 7) | 7.0 | 1.8 | 3.0 | 22 | 0.6 | 1,308 | 173 |
| 10 | 38 | 61 (22 / 14) | 13 | 4.5 | 6.5 | 44 | 1.9 | 4,387 | 366 |
| 20 | 77 | 150 (50 / 32) | 29 | 14 | 17 | 88 | 4.1 | 15,497 | 1,888 |
| 30 | 120 | 254 (82 / 54) | 42 | 27 | 29 | 121 | 9.4 | 29,851 | 5,033 |
| 60 | 239 | 600 (173 / 129) | 89 | 100 | 71 | 205 | 30 | 106,481 | 46,932 |

Floors 1 to 10 average about 3.9 chests, 6 pieces of gear, 1.3 rings and 4.5 potions each.

**Where it comes from (floors 1 to 30):**

| Kind | Ordinary rooms | Chests | Monster drops | Hidden chambers | Special rooms |
|---|---|---|---|---|---|
| Gear | 38% | 31% | 16% | 12% | 3% |
| Rings | 26% | 45% | 23% | 4% | 2% |
| Potions | 44% | 45% | 9% | 0% | 2% |
| Gold | 16% | 44% | 29% | 0% | 7% (vaults 5%) |

### 3.2 Why there is so much

1. **Extra chests roll once per room, not once per floor (bug).** See `src/dungeon.py:1688-1696`.
   - The comment says the extras run 0.55, then 0.25, then 0.11.
   - The code rolls 55% in each room until one lands, then 25% in each remaining room, and so on. On a floor of ten or more rooms, a second chest is nearly certain and a third is likely.
   - Measured: fixing only this halves the chests, from 120 to 62 by floor 30.
2. **Chests are full.** An opened chest averages 2.9 items.
   - A wooden chest holds 2 or 3; a tier-2 chest holds 2 or 3 plus a bonus (`src/container_system.py:41-47`).
   - The cap is per kind of gear (`container_system.py:51-52`), so a plain chest can hold a weapon, an armor piece and a shield at once.
3. **The jewelry box is your "three rings and some gold."** See `data/chest_templates.json`, `jewelry_box`.
   - Its loot table is accessory 70, gold bonus 30, treasure 8, with 3 or 4 draws.
   - At floor 5: 2% hold no ring or amulet, 17% hold one, 37% two, 34% three and 9% four, with about 100 gold.
   - It is 10% of early chests, so one turns up about every three floors.
4. **Hidden treasure chambers became armories (regression).** See `src/level_manager.py:520-535`.
   - The chamber calls `spawn_items([room, room])` and keeps the first 3 to 5 items.
   - Since `MIN_LOOT_ROOMS` was added for the small maze floors (`src/dungeon.py:1534-1540`), that one room is rolled ten times.
   - Gear and magic are rolled first, so the 3 to 5 kept are almost all gear, rings and wands. The chest the chamber was meant to hold almost never makes the cut.
   - Hidden chambers supply 12% of all gear.
5. **Ordinary rooms.** Each loot room rolls gear 33% (`src/dungeon.py:1548-1562`) and a magic item 25% (`dungeon.py:1570-1581`). The class-balanced pool (`dungeon.py:2423`, 20 slots per class) makes a quarter of those magic items rings and amulets.
6. **Monster drops favour rings.** Half of an item drop is a "magic" item whose class is picked by how many kinds it has (`src/game_combat.py:1586-1602`, `src/container_system.py:474-478`). Accessories have the most kinds, so 31% to 39% of those drops are rings or amulets.
7. **Structure (not a bug, but it multiplies everything above):**
   - 8 armor slots plus a shield (`src/player.py:45`), each piece worth at least 1 AC;
   - 4 ring slots plus an amulet and a belt (`player.py:46`);
   - any blessed piece, ring and amulet included, worth 1 more AC (`player.py:994-1009`);
   - rings of the same stat stack (`player.py:2059-2066`).

   An armor piece is worth little (at floor 10 every slot but the body averages about 1 AC), but nine slots fill up by about floor 8 at almost any rate of finds.

### 3.3 What it does to AC

The kit's AC is the median of 40 runs. The design profiles come from `tools/balance/CURVE.md` sections 4 and 5 (UP = unprepared, P = prepared, SL = skilled and lucky). It is the only written AC yardstick, from before the 2026-10 changes. Hit chance is `Monster.attack` against the floor's median ordinary monster (`src/monster.py:1134-1157`, `MIN_HIT_ORDINARY` 0.30 at `monster.py:47`).

| Floor | Kit AC today | Design UP / P / SL | Monster hits AC 10 | Hits the design P | Hits the kit |
|---|---|---|---|---|---|
| 1 | 7 | 10 / 7 / 4 | 64% | 53% | 53% |
| 5 | 0 to 1 | about 9 / 5.5 / 1 | 67% | 50% | 32% to 36% |
| 10 | -4 | 8 / 4 / -2 | 78% | 57% | 32% |
| 19 | -12 | 6 / 0 / -8 (floor 20) | 95% | 60% | 32% |

From floor 5 the kit puts ordinary monsters on the 32% floor. Between floors 5 and 20 that cuts the hits the design expected by a third to a half.

Deep down, monster to-hit falls fast enough that AC counts again, which is part of why a blunt cut hurts late. At floor 50 a typical monster needs 19 or more on the die against AC -22, against 17 or more at AC -20.

### 3.4 Stats from rings

| Floor | Total stat points four rings and an amulet lend | Most points of ONE stat they stack | If only the best ring of a stat counted |
|---|---|---|---|
| 5 | 2.2 | 1.2 | 0.9 |
| 10 | 5.9 | 3.3 | 1.9 |
| 20 | 9.6 | 6.9 | 2.1 |
| 30 | 14.4 | 11.4 | 3.0 |
| 60 | 19.4 | 18.7 | 4.2 |

The stacking table (`REBALANCE_MASTER_PLAN.md` section 3) gives a whole stat build 1.6x, about +20 Strength. Rings alone reach +19 of one stat by floor 60, on top of cooking (+13 of one stat by then) and the gate-boss gifts (+4 to +7 each).

The deep stat rings are what make it possible: +4 rings from floor 45 and +5 amulets from floor 65 (`data/items/accessory.json`).

### 3.5 Gold and treasure are on the designed line

Gold by floor 5, 10 and 30 is 1,308, 4,387 and 29,851 for an 85% finder. The economy's income line is 1,790, 5,480 and 39,240 for a full explorer, with encounters, graves and thrones adding the rest. Gold was rebased on 2026-10-17 and is not the problem. Treasure is about 5,000 by floor 30.

Chests carry 44% of the gold, so cutting chests cuts gold; see decision L1.

### 3.6 Named uniques

The census counts 9 to 10 named uniques by floor 30 and 30 by floor 60, mostly from chests (the unique chance is doubled on a successful pick). Halving the chest count halves this unless the chance per chest is raised.

## 4. Food and stats

### 4.1 How it works, end to end

1. **Kill and harvest.** A kill leaves a corpse. Harvesting is one animal question (`src/food_system.py:655-715`) and yields that monster's prime cut. Each of the 516 prime cuts carries a `stat_grant` in `data/items/ingredient.json`: STR 194, DEX 88, WIS 87, INT 59, CON 53, PER 35.
2. **Cook.** The Recipes menu calls `cook_compound_recipe` (`food_system.py:601-638`), which stamps the cut's stat on the recipe.
3. **On a right answer** (`food_system.py:350-467`), the meal restores SP and heals. It adds max HP: 2 a meal, at most 5 a floor and 4 for each floor of depth (`player.py:561-571, 619-672`). Then it feeds the stat through `Player.feed_cut_stat` (`player.py:586-605`).
4. **`feed_cut_stat`.**
   - Only the first stat-bearing meal on a floor reached for the first time counts (`PER_FLOOR_STAT_CAP` 1). The counter resets only on new depth (`src/main.py:1868-1874`).
   - Two such meals of the same stat make +1 (`COOK_MEALS_PER_STAT_POINT` 2).
   - A stat's lifetime cap is 2 + deepest floor / 5, half that for Wisdom (`player.py:607-613`).
5. **Stat foods** (philosopher's tea, golden apple, ambrosia, peach of immortality) give a whole point through `try_apply_cook_stat_gain`, using the same once-a-floor slot (`food_system.py:796-866`, `player.py:622-642`).

### 4.2 Verified on the real menu path

- **A.** One Strength meal first on every floor, three meals a floor: Strength +1 on floor 2, +1 on floor 4, then capped (cap 2). It rises again on floor 6 (cap 3) and is +5 at floor 20. Max HP grows 4 a floor, as designed.
- **B.** Alternating Strength and Constitution meals: +2 each after 10 floors (each stat banks on its own).
- **C.** Going back up and down a stair does not refill the floor's lesson. Correct.
- **D. Bug.** Ambrosia ("all stats +1") on a fresh floor: Strength +1, every other stat +0, and the message says "A glow spreads — most of your stats edge upward."
- **E. Bug.** Philosopher's tea after one cooked meal on the same floor: Wisdom +0, with the message "Your wisdom cannot grow further from food." The true reason is that the floor's lesson was already used.

### 4.3 How fast stats climb, by source

| By floor | Cooking, one stat focused | Cooking, all stats together | Depth Wisdom | Gate gifts (one stat) | Stacked rings of one stat (today) |
|---|---|---|---|---|---|
| 5 | +2 | +2 | +1 | none | +1.2 |
| 10 | +3 | +4 | +3 | none | +3.3 |
| 20 | +5 | +9 | +6 | +4 (+1 with the quest) | +6.9 |
| 30 | +7 | +14 | +10 | +4 | +11.4 |
| 60 | +13 | +29 | +20 | up to +4, +5, +6 | +18.7 |
| 100 | +21 | +49 | +33 | up to +7 more | about +20 |

The trait and fortune allowances add at most 6 and 5 by floor 20, if earned. In the simulator, a prepared cook who feeds random stats ends floor 20 with about +1.5 in each stat and floor 60 with 27 points cooked in all.

### 4.4 What is wrong

- **Three bugs.**
  - (a) "All stats" and "two stats" foods (`food_system.py:832-851`) run each stat through the once-a-floor cap, so only the first stat rises. The message promises more.
  - (b) A stat food uses the floor's lesson. Eaten after a meal it gives nothing and blames the cap (`food_system.py:859`); eaten before, it silently costs that floor's cooking lesson.
  - (c) 160 recipes (the bone broths and others with `max_hp_bonus: 1` in `cook_outcomes.json`) add 1 max HP instead of the 2 every ordinary meal adds. `food_system.py:376-396` takes the recipe's bonus in place of the base, and the menu advertises "+1maxHP" (`src/game_render.py:4334`).
- **Silence.** A meal that teaches nothing prints nothing about stats (`food_system.py:415-420`). That happens when the floor's lesson is used, or when the stat has reached its cap for this depth.
  - The sidebar shows only "Meals: +x/5 Max HP" (`src/hud_context.py:109-124`).
  - A cook who feeds one stat sees "+1" on floors 2, 4, 6, 11 and 16, and nothing at all on floors 7 to 9, 12 to 14 and 17 to 19.
- **The first meal decides.** The floor's lesson goes to whichever stat-bearing meal is cooked first. The Recipes list sorts single-ingredient dishes alphabetically, not by stat (`food_system.py:225`), so a player who does not know the rule feeds a random stat.
- **Tuning.** Within its own design it does what the comment in `player.py:573-584` promises: a point every two floors, about 50 in a run, a ceiling of +22 in one stat. But:
  - the per-stat cap binds a focused build to one point per five floors after floor 4;
  - rings lend more than cooking from floor 10;
  - `CURVE.md` principle 9 says cooking is the levelling track, and today rings are.
- **Stale docs.** `docs/systems/food_system.md`:
  - never mentions `feed_cut_stat` or the two-meal bank;
  - section 4 (line 197) says single-ingredient recipes are filtered out, though they were restored on 2026-10-03;
  - section 7.1 (line 338) and line 415 describe the old routing.

## 5. Proposed changes: decisions for you

### 5.1 The packages, measured

All of them keep the potions; the first package I tried cut them and broke the deep game.

- **G1-lite (my recommendation):**
  - L2: at most one piece of gear in a plain chest, its slot refilled from the chest's other contents;
  - L3: the jewelry box holds jewellery;
  - L4: hidden chambers hold a cache;
  - L5: ordinary-room gear 25% instead of 33%, a third fewer rings and amulets on the floor;
  - L6: a third fewer rings and amulets in monster drops.

  The chest count is unchanged.
- **G1:** the same, but a harder cut: room gear 20%, and half the rings and amulets on the floor and in drops.
- **G1 + F3:** G1 with the cooking-cap raise in F3.
- **G2:** G1, plus L1 (the chest count fixed to the comment's rule) and one more potion on every floor.
- **G2r:** G2, plus every chest's named-unique chance doubled, so a run finds as many uniques as today.

**Census** (85% finder, floors 1 to 60):

| | Today | G1-lite | G1 | G2r |
|---|---|---|---|---|
| Chests by floor 10 / 30 | 38 / 119 | 38 / 118 | 38 / 117 | 22 / 61 |
| Gear by floor 10 / 30 | 60 / 246 | 40 / 179 | 35 / 162 | 28 / 132 |
| Rings by floor 10 / 30 | 14 / 44 | 6 / 26 | 7 / 23 | 5 / 17 |
| Potions by floor 30 | 119 | 130 | 134 | 129 |
| Named uniques by floor 30 | 10 | 9 | 9 | 9 |
| Kit AC at floor 5 / 10 / 20 | 1 / -4 / -12 | 3 / -1 / -9 | 3 / -1 / -9 | 4 / 1 / -8 |
| One stat from stacked rings, floor 20 / 60 | +6.9 / +18.7 | +4.8 / +18.4 | +4.6 / +17.6 | +3.6 / +16.2 |
| Gold by floor 30 | 29,784 | 28,347 | 28,083 | 22,285 |

G2 cuts gold by a quarter unless each chest's `gold_share` rises about 2.3x (half as many chests have to carry the same coin); see L1. Even the leanest package leaves the kit at AC -8 by floor 20, the design's luckiest line. The nine slots set the curve more than the finds do; see L8.

**Simulator** (kid model, 4 seeds × 60 runs per cell, 240 runs each; ± is the standard error across seeds; differences under about 5 points are noise):

| Package | Casual reaches floor 20 | Casual past Asterion | Prepared wins | Committed past Fafnir | Committed wins | Kit AC, floors 10-19 |
|---|---|---|---|---|---|---|
| Today | 88% ± 2 | 54% ± 4 | 38% ± 2 | 73% ± 4 | 44% ± 4 | -3 to -4 |
| **G1-lite** | 90% ± 1 | 50% ± 2 | 25% ± 2 | 60% ± 4 | 35% ± 2 | -2 |
| G1 | 93% ± 1 | 53% ± 1 | 21% ± 2 | 57% ± 2 | 31% ± 2 | -2 |
| G1 + F3 | 82% ± 1 | 45% ± 2 | 28% ± 2 | 51% ± 4 | 30% ± 2 | -2 |
| G2 | 85% ± 0 | 41% ± 6 | 20% ± 2 | 40% ± 2 | 21% ± 1 | -1 |
| G2r | 79% ± 3 | 37% ± 3 | 16% ± 2 | 50% ± 4 | 28% ± 2 | -1 |

The targets are yours and the master plan's: most casual players reach floor 20, about half get past Asterion, the prepared player wins 25 to 30%, and the committed build wins 40 to 50%.

- **The early game holds.** Every G1 variant keeps the casual targets. The G1 + F3 casual row is probably cell noise, since F3 gives a casual cook more, not less.
- **The deep game drops.** It loses 9 to 13 points for the committed build, all of it between Medusa and Fafnir. The simulator never swaps a ring once its four slots are full, so it already understates today's ring stacking; L7 will move it less than the census suggests.
- **F3 is neutral on win rates** within the noise. It changes how stats are earned, not how hard the game is.

### 5.2 Loot decisions

**L1. Chest count (bug).** Fix the extra-chest roll to the commented per-floor rule: about 1.7 ordinary chests a floor instead of about 3.4 (2.8 to 4.0 by room count).
- Chests carry 45% of the potions, 44% of the gold and most of the uniques. So, with the fix, add one potion to each floor, raise every chest template's `gold_share` about 2.3x (so the gold line holds), and double each template's unique chance (G2r)?
- *My recommendation:* leave the count, and correct the comment to say what the code does (about 3.4 a floor). I measured the fix with potions and uniques both compensated (G2r against G1).
  - Fewer chests still cost the casual player at Asterion: 37% get past him instead of 53%, and 79% reach floor 20 instead of 93%.
  - They also cost 3 to 5 more points of deep win rate.
  - Early chests are where a new character's scrolls, wands and lucky uniques come from.

  L2 and L3 already take the "several things at once, three rings and gold" out of each chest. If you want fewer chests anyway, take it with the compensation, and Asterion will need easing for casual players.
- *Changes:* `src/dungeon.py:1688-1696`, `src/dungeon.py:1752`, `data/chest_templates.json`.

**L2. Gear in plain chests.** A wooden chest, iron lockbox, jewelry box, apothecary chest or merchant strongbox (tiers 1 and 2) holds at most one piece of gear. A draw over that comes from the chest's other categories (potions, scrolls, ammo, wands) instead, so the chest is not emptier. War chests and the deep chests keep two.
- *Recommendation:* yes. It is the main cut in gear (31% of it comes from chests), and the lore fits: a traveller's chest holds provisions and maybe one blade.
- *Changes:* `MAX_SAME_GEAR_PER_CHEST` becomes a total cap in `src/container_system.py:51, 561-578`.

**L3. The jewelry box holds jewellery.** The loot table becomes treasure 60, accessory 20, gold bonus 20 (today 8 / 70 / 30). Gems, brooches and plain gold rings are treasure (`src/treasure.py`); a ring with a power in it becomes the lucky find. A box then averages about 0.7 rings or amulets instead of 2.3.

*As built (2026-10-26): treasure 15 / accessory 20 / gold bonus 65.* At treasure 60 a deep box held 1.5 floors' income in gems, a second income this report missed. At 15 a box holds about 0.4 of a floor's income in treasure deep and still about 0.7 rings.
- *Recommendation:* yes. This is the exact thing you saw, and the lore fix is the data fix.
- *Changes:* `data/chest_templates.json` only.

**L4. Hidden chambers (regression).** A hidden treasure chamber holds a cache: coin, treasure, potions, scrolls. It holds no gear, rings or chests. In the code, the chamber's own pass skips the `MIN_LOOT_ROOMS` repeat and the gear and magic rolls.
- *Recommendation:* yes. It is a bug, the chamber was never meant to be an armory, and a secret door that hides a smuggler's cache is better lore.
- *Changes:* `src/level_manager.py:520-535`, plus a flag on `spawn_items`.

**L5. Ordinary rooms.** Per-room gear chance 0.33 → 0.25 (`src/dungeon.py:1549`), and rings and amulets take two thirds of their share of the floor's magic pool (`dungeon.py:2423`: 13 slots for the accessory class instead of 20). G1's harder version is 0.20 and half the share.
- *Recommendation:* yes, the G1-lite numbers. They give the same AC curve as G1 and cost a little less deep down; tune after a play-test.
- *Changes:* `src/dungeon.py` only.

**L6. Monster drops.** In the magic half of a death drop, pick the class from a written share instead of by number of kinds. For example: potion 33, scroll 20, wand 20, accessory 22, ammo 5. Today accessory is 31% to 39%, so this is the third fewer rings G1-lite measured (G1's half would be accessory 15). A goblin carries a dagger or a potion more often than a ring of power.
- *Recommendation:* yes, at the G1-lite share.
- *Changes:* `src/game_combat.py:1586-1602` (and the same table for any other caller of `_weighted_common_pick` that wants it).

**L7. Stat rings of the same stat.** Today four Rings of Greater Strength and an Amulet of Strength give +10 Strength by floor 8.
- *(a)* Only the strongest ring or amulet of each stat counts. Four different stat rings still work, and two of one stat give the larger only. Lore: the stronger ring's virtue drowns the weaker.
- *(b)* Two ring slots instead of four. In single 100-run cells, two slots cost another 5 to 9 points of win rate on top of G2.
- *(c)* Leave it.
- *Recommendation:* (a). It cuts the stacking (one stat from rings: +2 at floor 20 and +4 at floor 60, against +7 and +19), keeps four slots for utility rings (regeneration, resistances, see invisible) and leaves the build to cooking and gifts.
- *Changes:* `src/player.py:2005-2066` (apply only the gain over the best worn source of that stat) and the three accessory-unequip sites in `src/main.py:7320-7344`, `src/game_combat.py:975`, `src/game_encounters.py:1582-1620`.

**L8. Armor slots.** Even G2r leaves the kit at AC 1 at floor 10 and -8 at floor 20, because 9 slots each worth at least 1 AC fill by about floor 8. The design's prepared line (AC 4 at floor 10, 0 at floor 20) would need one of two things:
- far fewer armor finds again; or
- light pieces in the minor slots (arms, hands, legs, feet, cloak, shirt) worth 0 AC, keeping their resistances and specials.
- *Recommendation:* not now. Do L2 to L7, play, and decide L8 from how it feels. Deep down, AC matters to survival again.

**R1. Put the deep game back on target after the loot change.** With G1-lite the committed build wins 35% instead of 44%, under your 40 to 50%. The loss sits between Medusa and Fafnir (floors 41 to 60).
- The lever is monster data, never runtime: ease the ordinary monsters on floors 41 to 79 in `data/monsters.json` with `tools/balance/scale_monsters.py`. The first thing to try is their damage, and Fafnir's own numbers if the gate is the step.
- The simulator picks the factor (pooled seeds) until the committed build is back at 40 to 45% and the prepared player at 25 to 30%.
- *Recommendation:* yes, in the same change as the loot, so the game is never shipped harder than your target.

### 5.3 Food decisions

**F1. Fix the three bugs.**
- (a) "All stats" and "two stats" foods count as one lesson, but every stat they name rises.
- (b) Stat foods are their own gift, outside the cooking lesson. Or, if you prefer them inside it, the message says the floor's lesson was already used.
- (c) A recipe's `max_hp_bonus` is added on top of the base 2, never in place of it.
- *Recommendation:* yes to all three. Your rule is "make a designed mechanic work, then balance."

**F2. Make the lesson visible.**
- Every proper meal says what it did for the stat: "+1 Strength", "Strength: 1 of 2 meals", "You have already learned from a meal on this floor", or "Your Strength has learned all it can at this depth; go deeper".
- The sidebar gets a line beside "Meals": "Lesson: open / used".
- *Recommendation:* yes. Today most meals say nothing about stats, which reads as "food stats don't work."

**F3. Let a focused cook keep growing.** Raise the per-stat cap from 2 + floor/5 to 3 + floor/4 (Wisdom keeps half). A focused stat then gets a point every two floors to about floor 12, then one every four: +4 by floor 8, +6 by floor 12, +8 by floor 20, +10 by floor 30, +28 by floor 100. Today those are +3, +4, +5, +7 and +22. The total stays half a point a floor.
- *Recommendation:* yes, together with L7(a). Stat power then moves from random rings to the build the player chooses, which is what `CURVE.md` principle 9 and your "much higher stat builds" ruling ask for.
- The cap stays an allowance read from the deepest floor reached, like today's. Nothing is multiplied by the floor.
- *Changes:* `src/player.py:578-579`.

**F4. Docs.** Rewrite `docs/systems/food_system.md` sections 4 and 7 in the same commit as F1 to F3 (system-change sweep rule).
- *Recommendation:* yes.

### 5.4 Questions for you

1. **Chest count (L1):** leave it at about 3.4 a floor and correct the comment (my recommendation)? Or fix it to about 1.7, with one more potion a floor, about 2.3x gold per chest and double the unique chance, accepting that Asterion gets harder for casual players?
2. **Chest contents and the jewelry box (L2, L3):** yes to at most one piece of gear in a plain chest, and to a jewelry box of jewellery rather than rings?
3. **Hidden chambers, floor rooms, drops (L4 to L6):** yes to a cache instead of an armory, room gear at 25%, and a third fewer rings and amulets on the floor and in drops (G1-lite)? Or the harder G1: 20% and half?
4. **Stat rings (L7):** (a) best of each stat counts, (b) two ring slots, or (c) leave it?
5. **Armor slots (L8):** leave it until after a play-test of the rest?
6. **Deep re-tune (R1):** ease floors 41 to 79 in `monsters.json` until the committed build is back at 40 to 45%, in the same change?
7. **Food (F1 to F4):** yes to fixing the three bugs, adding the stat messages and the sidebar line, raising the cap to 3 + floor/4, and the doc rewrite?

When you answer, I will make the changes in data and code (never by floor at runtime), re-run the census and the simulator against your win-rate targets, and hand you one consolidated play-test list. The loot changes are reachable within minutes of play, so they need your play-test before they count as done.

## 6. As built (2026-10-26, after your answers)

You answered: leave the chest count, L2 to L7 at the G1-lite numbers with L7(a), R1, F1 to F4, and L8 after a play-test. All of it is built, with two changes from what the report said.

### 6.1 What changed from the report

- **The jewelry box is treasure 15 / accessory 20 / gold bonus 65, not 60 / 20 / 20.**
  - At 60, a deep box held 1.5 floors' income in gems: a second income I missed, because the report showed gold but not treasure.
  - At 15, a box holds about 0.4 of a floor's income in treasure deep and 0.7 rings or amulets; three or more rings turn up in 1% of boxes (43% before).
  - This deviated from what you approved, in the direction of your complaint. You approved 15 / 20 / 65 on 2026-10-26.
- **R1 needed no monster change.** The game as built, measured with 8 seeds × 60 runs, already has the committed build at 41%, inside your 40 to 50%. G1-lite had predicted 35%; the gap is that monster drops now give more potions.
  - A half-size ease of floors 41 to 79 (`mon_dmg` 1:1:1:0.975:0.94:0.94:0.96:0.98:1) would have pushed the committed build to 47% and the prepared player to 44%.
  - So `monsters.json` is untouched. That schedule is ready to bake with `tools/balance/scale_monsters.py` if the deep floors feel too hard in play.

### 6.2 Measured as built

**Simulator** (kid model; "today" is 4 seeds and "as built" 8 seeds × 60 runs):

| | Today | As built |
|---|---|---|
| Casual reaches floor 20 | 88% | 87% |
| Casual past Asterion | 54% | 55% |
| Prepared wins | 38% | 38% |
| Committed wins | 44% | 41% |

**Census** (85% finder, floors 1 to 60):

| | Today | As built |
|---|---|---|
| Gear by floor 10 / 30 | 62 / 260 | 38 / 174 |
| Rings by floor 10 / 30 | 14 / 42 | 7 / 23 |
| Kit AC at floor 5 / 10 / 20 | 1 / -4 / -12 | 3 / -2 / -10 |
| One stat from rings, floor 20 | +6.9 (stacked) | +2.1 (strongest counts) |
| Potions by floor 30 | 120 | 154 |
| Gold by floor 30 | 29,633 | 30,701 |
| Treasure value by floor 30 | 4,926 | about 9,000 to 11,000 |

The extra treasure comes mostly from hidden chambers, which now hold coin and gems instead of the gear they used to hold. The independent wiring audit made two more cuts after the first measurement: a plain chest's freed gear draw no longer goes to rings, and the Kit's ring comparison and the equip message now follow the strongest-counts rule.

### 6.3 Where it is in the code

| Change | Code |
|---|---|
| L1: chest count kept, comment corrected | `src/dungeon.py`, extra-chest loop |
| L2: one piece of common gear per plain chest | `container_system.MAX_GEAR_PLAIN_CHEST` |
| L3: the jewelry box table | `data/chest_templates.json` |
| L4: chamber cache | `dungeon.spawn_chamber_cache`, `economy.CACHE_COIN_SHARE` |
| L5: room gear chance and the rings' pool share | `dungeon.ROOM_GEAR_CHANCE` 0.25, `CLASS_POOL_SLOTS` (accessory 13) |
| L6: monster drop classes | `container_system.DROP_MAGIC_SHARE` and `pick_by_class_share` |
| L7a: strongest ring of each stat counts | `Player.sync_worn_stats` / `accessory_off` / `_worn_stat_ledger`, with old saves migrated in `Player.__setstate__` |
| F1: the three food bugs | `food_system._apply_outcome_body` (bonus max HP on top of the base) and `_apply_bonus` (stat foods outside the lesson) |
| F2: a meal says why it taught nothing; sidebar Lesson line | `Player.cut_stat_block`, `hud_context.cooking_lesson_line` |
| F3: food cap 3 + depth/4 | `player.py` `COOK_STAT_CAP_*` |
| F4: docs and help | `docs/systems` (food_system, containers_lockpick, items, world, monsters, pets) and the help page `data/ui/how_quizzes_work.json` |

Tests: `tests/test_balance_review_2026_10_26.py`.

Your Cain save loads cleanly: it wears two Rings of Wisdom +1, so Wisdom drops by one on load, once.

### 6.4 Play-test list

These are all reachable within minutes, on your Cain save or a new hero.

1. **Chests on floors 1 to 5.** A wooden chest or lockbox holds at most one weapon, armor piece or shield; the rest is potions, scrolls and ammo. Is it still worth opening?
2. **Gear on the ground.** About 3 to 4 pieces of gear a floor instead of 6 to 7. Does it still feel like you find upgrades often enough?
3. **A jewelry box.** Coin, maybe a brooch or a gem, now and then one ring; never three.
4. **Two rings of one stat.** Put on two Rings of Strength. The second says only the strongest counts, and the stat rises once. Take off the stronger one and the weaker takes over.
5. **Your Cain save.** Wisdom is one lower on load (two Rings of Wisdom), and nothing else moves.
6. **Cooking.**
   - Under "Meals" the sidebar says "Lesson: open". After the first prime-cut meal of a floor it says "Lesson: learned this floor", with the stat banked ("STR 1/2").
   - A second stat meal that floor says you already learned from a meal on this floor.
   - The next new floor opens the lesson again.
   - A bone broth adds 3 max HP (it used to add 1).
7. **A hidden chamber** (search for secret doors): coin, gems, potions and scrolls, no gear.
8. **AC on the character sheet** should come down more slowly: about 3 at floor 5 and 0 to -2 by floor 10, instead of 0 and -4.

Not play-testable in a few minutes, so covered by tests and the simulator instead: deep floors, stat foods (floor 15 and beyond), the food cap at depth.

### 6.5 Left as found

- **Chain-equip legends.** Their earned tier bonuses (`stat_bonus_*` in `tier_bonuses`) stay outside the strongest-counts rule: they are the reward for each legend's chain quiz. Nine legends carry them, and three Intelligence legends worn together still lend about +17 INT. The exception is written in `docs/systems/items.md` §5; say so if you want them under the rule too.
- **Two older bugs next to this change**, not caused by it:
  - a cursed Scroll of Enchant Accessory on a ring with a negative bonus sets it to 0 and removes the penalty (`game_magic.py`, `max(0, old + bonus)`);
  - an encounter that takes a worn ring removes its status without checking whether anything else still grants it (`game_encounters._npc_remove_item_by_id`).
- **One test failed once** (`test_the_cow_kings_horns_drop_where_he_falls`) in one full parallel run and passed alone and in three later full runs: an ordering flake.
