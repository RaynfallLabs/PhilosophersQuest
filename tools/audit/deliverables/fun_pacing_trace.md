# FUN — Pacing Trace

A minute-by-minute walkthrough of player experience at floors **1**, **10**, **30**, **60**, **90**, and the **Death-chase escape**.

This document is grounded in the actual code paths and data. Findings under `tools/audit/findings/fun/` reference anchors below.

---

## Foundational tempos (constants the player feels)

These numbers drive every checkpoint below. Established at:

- **Per-subject timers** (`player.py:12-30`) — at WIS 10:
  - `math` 16s — combat
  - `grammar` 30s — scrolls / spellbooks
  - `geography` 40s — equip armor/shield
  - `history` 48s — equip accessory
  - `animal` 48s — harvest
  - `philosophy` 55s — identify
  - `cooking` 60s — cooking chain
  - `theology` 65s — pray
  - `economics` 65s — lockpick
  - `science` 36s — wands/spells, `trivia` 38s — recall lore
- **SP drain** (`main.py:2018-2036`) — 1 SP per 2 moves; starvation begins below 0.
- **HP regen** (`main.py:2042-2051`) — 1 HP every 15-20 turns at base, blocked by bleeding/poison. Not enough to recover from any meaningful fight.
- **Stair-rest** (`player.py:172-189`) — **0 HP on descent** (intentional: damage accumulates), **+max(2, 4% of max_hp), cap 22** on ascent. **SP +15, MP +max(2, INT/5).**
- **Wander spawn** (`main.py:1660-1692`) — every `max(10, 22 - level//4)` turns; at L1 ≈ every 22 turns, at L30 ≈ every 14 turns, at L80 ≈ every 10 turns. Cap `min(4 + level//6, 14)` simultaneous alive monsters.
- **Altars** (`dungeon.py:326-336`) — only on levels `L % 15 == 1` → L1, 16, 31, 46, 61, 76, 91. **Seven altars** in the entire procedural dungeon. Plus L100 has six altars in a ring (`boss_levels.py:469-477`).
- **Fountains** (`dungeon.py:540-548`) — 20% chance per floor.
- **Mystery altars** (`mystery_system.py:282-284`) — 60% chance per floor if any mystery is eligible for that level band.
- **NPC moral encounters** (`npc_encounters.py:14-26`) — exactly one per 10-level block (blocks 1-10), guaranteed.
- **Flavor encounters** (`flavor_encounters.py:256-283`) — ~40% per non-boss level. 97 unique encounters in pool (5 in source + 92 in `data/flavor_encounters.json`).
- **Merchant** (`mystery_system.py:608-616`) — 20% chance per floor.
- **Prayer cooldown** (`game_divine.py:780`) — `max(100, 80 + effective_chain * 25)` turns; so a perfect prayer is ~280 turns gated.
- **Recall Lore cooldown** (`game_magic.py:115-122`) — chain 0 → 40 turns silent; chain 1-5 → 65/80/95/110/125 turns.
- **No XP system** (`player.py:171` "HP_PER_LEVEL = 0"). All HP growth comes from **cooking** (potency × quality, softcap at +1000 max_hp, `player.py:194-207`).
- **Death speed escalation by `dungeon_level`** during ascent (`main.py:1283-1316`):
  - L 100 → 75: speed 50%
  - L 75 → 50: speed 75%
  - L 50 → 25: speed 100%
  - L 25 → 1: speed **125%** (faster than player)

---

## Checkpoint A — Floor 1 (first 5 minutes of a fresh run)

**Player loadout from `_give_starting_kit` (`main.py:579-817`):** Philosopher's Shard, iron sword (default), 5 lockpick charges, 1 bread ration, 1 identified healing potion. Stats 10 across the board unless a secret build is active.

**HP profile:** 30/30 (BASE 20 + CON 10). Max SP 210. Max MP 20.

### Turn-by-turn action mix
A typical first 60–80 turns:
1. Move out of starting room, refresh FOV (`main.py:874+`, `_do_move`).
2. Bump first monster (rat / kobold / goblin spawned at L1 — `level_manager.py:46`, `min_m=2 max_m=3`). **Combat quiz** opens: math chain at 16s timer. (`game_combat.py:1242-1345`).
3. Walk between rooms. Pick up the first scroll/potion you find (always unidentified at L1). Trigger **passive trap detection** (`main.py:1980+`) — PER 10 yields ~25% avoid chance per step on traps.
4. ~10 turns in, take an alarm trap or a single bite from a rat. HP drops to ~25.
5. Spot a chest. Walk over. Press `p`. **Economics threshold quiz** (`container_system.py:24-56`). Timer ~65s. Three correct answers needed (T1 chest, threshold 3).
6. Take a corpse from a killed rat. Press `h`. **Animal threshold quiz** (`food_system.py:192-220`). Two correct answers needed.
7. Press `c`. **Cooking escalator chain** (`food_system.py:227-287`). Chain up to 5 for quality 5.
8. Find altar (1-in-15 chance, since L1 is `1 % 15 == 1` — **L1 always has an altar**, `dungeon.py:327`). Walk on. Press `\`. **Theology escalator chain** at 65s/question.
9. Find stairs down. Descend.

### Quiz tempo
- Math (combat) fires every 5–8 turns once a monster is in melee. **By far the dominant subject.**
- Threshold quizzes (animal harvest, economics lockpick, philosophy ID, theology prayer) fire 1–3 times per floor.
- Recall Lore (`n` key, trivia escalator) is **player-initiated** with a 40–125 turn cooldown; first use almost certainly fires by turn 50.
- Reading scrolls (grammar threshold) happens 0–1 times per floor at L1; player usually saves unidentified scrolls.

### Ambient life at L1
- **Guaranteed altar** (since L1 % 15 == 1, `dungeon.py:327`).
- 20% fountain.
- **One NPC moral encounter is assigned to L3-L9 from block 1** (`npc_encounters.py:15`) — not on L1.
- ~40% flavor NPC chance (`flavor_encounters.py:276`).
- Magic Dungeon Carrot appears once between L1-19 (`game_encounters.py:213-245`).
- 60% mystery altar chance — but eligible mysteries at L1 are limited (no mystery has `floor_range` start ≤ 1 except none; nearest is `crucible` at L10-22). So **mysteries effectively don't fire at L1**.
- Bones ghost 50% chance if a bones file matches L1 (`level_manager.py:64-68`).

### Tension curve
**Very forgiving.** HP starts at 30; biggest L1 monster does ~1d4 per hit. Player can fail one combat chain (chain=0) without dying. Stair-rest on ascent **does not heal at L1** because descent caps at 0 HP. Player is expected to descend, not ascend.

### Friction
- **Item identification is gated and slow.** Most items pickedup are unidentified (`philosophers_shard` is identified but useless for that). To ID anything, press `i` → 55s philosophy quiz, threshold = tier+1. At L1 most items are tier 1 (threshold 2 of 3). It is rational to **hoard unidentified items** until you reach an altar at L16 (BUC identify, `game_encounters.py:235`) or save quizzes for late. This makes the first 5 floors feel like inventory clutter.
- **Lockpicking + alerts** — failure has a 30% chance to alert nearby sessile monsters (`container_system.py:97-101`). At L1 there's rarely anything sessile, so the consequence is invisible — the system is teaching itself in the dark.

### Wonder
- **First Recall Lore success is the wonder beat.** A T1 hint about Egyptian eyes of blue faience, or strange altars (`data/hints.json`, sampled in CONTEXT.md). The escalator-chain trivia quiz at chain 1 already produces a usable hint. This is the loop that should hook a kid.
- **First identified scroll/potion** — the lore panel pops via `STATE_LORE` (`game_magic.py:1995-1997`). The first time you ID a "scroll of teleportation" and read its lore, that's wonder.
- **Magic Dungeon Carrot** (in L1-19, guaranteed once) — a glowing carrot with first-person chronicle reaction "A glowing carrot, of all things. Something tells me I shouldn't eat this one." (`main.py:2143`).
- **The dungeon entrance story popup** (`main.py:3340-3367`) sets the stakes: "Your village of Amber is dying… The Philosopher's Stone… No one who has sought it has returned. But you are not no one." Strong opener.

---

## Checkpoint B — Floor 10 (≈ 25–45 min into a successful run)

**Player profile (typical successful run):**
- HP ~45 (cooking has bumped max_hp by +10–15 from 4–5 single cooks).
- One or two stat bumps from cooked compounds (random or combat stats).
- A few identified items, several unidentified.
- Lockpick charges fluctuating: started 5, gained ~10 from picks, spent maybe 6–8.
- Maybe one quirk unlocked (low-bar quirks like Cassandra after ~10 lockpick failures, or Theseus after exploring 5 floors).

### Turn-by-turn action mix
1. New floor entry: ~5 turns to leave the start room and look around.
2. Wander spawn fires every ~20 turns at L10 (`main.py:1664`, interval = `max(10, 22 - 10//4) = 20`).
3. By turn 30: first new combat (math chain, 16s — feels fast and rhythmic).
4. Container or two — economics threshold 3–4 correct at T2 (chest tier scales `(level-1)//20 + 1 ± 1`, `dungeon.py:1222-1223`).
5. **Probable mystery altar** — `crucible` (L10-22, philosophy T1, threshold 3) or `cauldron` (L14-26, needs 3 cooked Foods).
6. Corpse harvests are now T2 animal questions.
7. Block 2 NPC encounter (one floor in L11-19 — not L10 because L10 isn't in block 2's range `11-19`, `npc_encounters.py:16`).

### Quiz tempo
- Math (combat) still dominant — call it 60% of all quizzes.
- Threshold quizzes about 25%.
- Recall Lore + theology + spell/wand: ~15%.

### Ambient life at L10
- No altar (L10 % 15 ≠ 1).
- ~60% chance of mystery altar (5/12 mysteries are eligible: pandora L20-30, crucible L10-22, cauldron L14-26 — only `crucible` straddles 10).
- 40% flavor NPC.
- 20% merchant. Merchant inventories scale to floor — at L10 they sell low-tier weapons/armor/potions.
- 50% bones ghost (if a save bones file is at this level).
- Block 2 NPC encounter (L11-19, range 11-19, max one per block).

### Tension curve
**Mid-rising.** SP drain matters now — 1 SP per 2 moves means by turn 200 you're at SP 110. Hunger isn't a threat yet. HP losses from monsters at L10 (gnoll, ogre, wolf level monsters) are 1d6+1 to 2d4 per hit. A single bad math chain (chain=0) costs ~5–15 HP. Stair-rest on descent **doesn't heal** (`player.py:172`), so damage is durable — cooking and prayer are the only repair paths.

### Friction
- **The identification queue.** By L10 a player has 5–10 unidentified potions, 3–8 unidentified scrolls, and probably an unidentified wand. Each `i` opens a 55s philosophy quiz. At threshold 2 (T1) you might only need 2 right. But there's no batch ID — you either spam the menu or save for a Stone (L100). **The grind of unknown inventory makes the mid-game inventory screen visually noisy.**
- **Wonder subjects have long reading times (40–65s).** When a player is in the rhythm of math combat at 16s, opening a 65s economics quiz to pick a chest is a hard tempo break. The CONTEXT note "math is the snappy combat tempo; theology is the slow contemplative pause" is **correct in design intent** — but the lockpick-during-exploration loop puts economics where math's tempo expectation lives, and that gap can feel jarring on the first few floors before the player adjusts.

### Wonder
- **Crucible mystery** (`mystery_system.py:103-116`) — drinks transmute lead to gold. The riff "From base matter, golden truth" is well-pitched.
- **Block 2 NPC encounter** — the `lost girl` returning the silver pendant is a strong scene; the karma+reward branch is morally textured (`npc_encounters.py:76-129`).
- **First special room** — `library` (3 scrolls, 50% spellbook), `treasury` (gold + chests), `graveyard` (corpses + grave tiles for digging), `swamp` (water pools), `monster_den` (4-8 extra hostiles in one room). The hidden-density feels rich.

---

## Checkpoint C — Floor 30 (≈ 60–90 min in)

**Player profile:**
- HP ~120-200 (cooking compound recipes are landing 30-50 max_hp per quality 4+ cook).
- 1-2 quirks unlocked (Recall Lore uses cresting toward Norns at 20).
- BUC auto-reveal active at L30+ if WIS ≥ 14 (`main.py:2171-2178`).
- Real magical kit: a wand or two, a few potions identified, maybe a spell.
- Lockpicks: fluctuating around 5-15 charges.

### Turn-by-turn action mix
1. L30 is **always a maze level** (`main.py:425` chronicle — "Level 30. A maze again."). Corridors twist, FOV is constricted. Movement is slower per square because corridors create encounter chokepoints.
2. Wander spawn interval is `max(10, 22 - 30//4) = 15` turns. Caps at 9 alive.
3. Monsters at L30 (per `dungeon.py:46` scaling) — `min_m = 4, max_m = 6`. Plus monster-den extras (3-5 in a den).
4. Mystery altars eligible: `sphinx` (philosophy T3, escalator threshold 4/6), `oracle` (theology T3 with 50g cost), `mjolnir` if you have an unfinished hammer (math T3 escalator threshold), `pandora` (economics T2 threshold 4/5 with inverted outcome), `solomon` (history T3 threshold 6/8). **High mystery density** at this band.
5. NPC encounter from block 4 (L31-39, `npc_encounters.py:19`).

### Quiz tempo
- Math still dominant in combat but each fight is now ~3-5 turns of combat = 3-5 chain attempts.
- **Identification slows dramatically.** Items at L30 are T3-T4 — philosophy threshold = tier+1 = 4-5 correct out of 5-7 asked. Each ID quiz takes ~80–120s real-time including timer.
- Spell casting (science escalator chain) is the player's burst-damage button if they learned a fire/cold/lightning spell from a spellbook.

### Ambient life at L30
- No altar (L30 % 15 ≠ 1; nearest is L31).
- 60% mystery (5+ eligible).
- 40% flavor NPC.
- 20% merchant.
- 50% bones ghost.
- **Cow level portal** lurks here — `_cow_level` defaults to 35 (`main.py:351`).

### Tension curve
**Highest sustained pressure of the descent.** HP is meaningful — Death-of-thousand-cuts from wander spawns. SP drain is now in tension with the cooking economy (good cooks restore SP scaled by potency). MP starts mattering for mage-style players. Wander spawn at 15-turn intervals means you can't sit safely in a corridor — but you also can't rest on a stair-up to heal because *descent stairs don't heal*. **Players have to push forward and absorb attrition, then bank gains via cooking and altars.**

### Friction
- **Maze levels** (L10, 20, 30, 50, 70, 90 per chronicle map `main.py:422-432`) constrict FOV. PER 10 gives sight radius 5; mazes have 1-tile corridors. Each new tile reveal is a turn — exploration is slow in mazes and not much rewarded. This is **intentional difficulty**, but combined with wander spawn pressure and slow ID quizzes, the mid-game has a stretch where forward motion feels gated by every system at once.
- **Mystery key items eat inventory space.** Pandora's Key, Mjolnir-unfinished, Boulder (30 weight!), Healing Herb, etc. By L30 a hoarding player has 5+ key items they don't dare drop. STR 10 carry limit is 100 weight (`player.py:8: CARRY_PER_STR = 5`; 50 base + 50 from STR). The Boulder alone is 30 weight.

### Wonder
- **Sphinx mystery**: "Answer my riddles or perish." Philosophy escalator threshold at tier 3 — questions get harder per round. (`mystery_system.py:17-30`).
- **Pandora's Coffer's inversion** — solving the quiz "wrongly" gives the real reward (`mystery_system.py:43`, `invert_result: True`). The kid-philosopher beat: opening Pandora's box was "wrong" mythologically but Hope flew out anyway.
- **Cow level** at L35 — bumping a cow too many times opens a portal to Moo Moo Farm. Pure D&D-tier easter egg. (`game_encounters.py:38-114`).
- **The chronicle entries** for milestone levels are well-written: "Level 30. A maze again. The walls feel like they're watching me." This voice lands.

---

## Checkpoint D — Floor 60 (≈ 2–3 hours in)

**Player profile:** Now an experienced run. HP ~300–500 from compound cooking. Multiple quirks unlocked (the player has seen Recall Lore unlock Norns at 20 uses, Theseus at 5 floors, Cerberus at 300 stair uses approaching). Identified gear is well-curated; the cursed/blessed status is visible to high-WIS players.

### Turn-by-turn action mix
1. L60 is a **boss level** (`boss_levels.py:15`, BOSS_LEVELS = {20, 40, 60, 80, 100}). Hand-crafted layout — not procedural.
2. The player enters a themed arena. Per `boss_levels.py` the L60 boss is **Fafnir the Dragon** (per `main.py:3401-3416` story key).
3. Combat chain quizzes against the boss are sustained — Fafnir has high HP, takes many chain attempts to kill. Each chain is 16s × chain_length per individual question.
4. After the boss kill, story popup fires: "Fafnir was not always a dragon… Cunning over power. Patience over courage alone." (`main.py:3401-3416`).
5. Players who survive heal at the stair-down (`player.on_level_change`); but descent gives **0 HP**, so you walk into L61 still hurt.

### Quiz tempo
- During the boss fight: math math math. The whole fight is **one chain quiz at a time**, each chain potentially 5-15 questions long if the player is on fire.
- Between attacks: turn ticks, monster ticks, status effects.
- After kill: ground items appear, possible boss-drop story screen, then exploration to find stairs down.

### Ambient life at L60
- L60 is a hand-crafted boss room — no procedural special rooms or NPCs.
- The next floor L61 will have a guaranteed altar (`61 % 15 == 1`, `dungeon.py:327`).
- Fafnir's death may chronicle ("Fafnir was not always a dragon…").
- **Fafnir's Blood** drops as a special item (`main.py:2994-3008`).

### Tension curve
**Spike then trough.** Boss = peak. Then floor 61 (which is also an altar floor — strong recovery beat). The boss fights are the only sustained-stakes math chains in the game; everything else is "5 turns of combat then loot" cadence.

### Friction
- **Boss fights are math chain only.** A kid who's a great reader but mediocre at multiplication has zero relief at this beat. Every other action (lockpick, prayer, ID) has a different subject — but combat is locked to math. By L60 a player has been doing math chains for 2+ hours of real time. **Subject monotony in combat is a fatigue risk.** (See finding `fun-combat-math-monotony.md`.)
- **No mid-boss save / mid-boss escape.** Once Fafnir is engaged and the player chains math, there's no graceful exit. If they die mid-fight, the run is over and bones are written. This is intentional difficulty, not a FUN bug — but the design tension is real.

### Wonder
- **The boss story popup** is one of the game's best wonder beats. The story explains the myth, names the lesson ("Cunning over power. Patience over courage alone"), then returns control. This is the kind of moment a kid would talk about at dinner.
- **L61 altar** — first prayer of the new tier, blessing scales with chain count, verses pop ("The LORD is my shepherd; I shall not want" at chain 5, `game_divine.py:741`). Coming right after a boss fight, this is a perfectly-placed catharsis beat.

---

## Checkpoint E — Floor 90 (≈ 3–4 hours, very rare survival)

**Player profile:** A run that reaches L90 is a top-percentile run. HP 500–800. Many quirks. Probably a custom build of identified gear. Has answered ~2000+ correct questions over the run. May have unlocked Sibyl (500 correct), Ramanujan (500 math), Penelope (100 mystery answer streak), etc.

### Turn-by-turn action mix
1. L90 is **another maze level** (chronicle says so: "One last maze."). Tight corridors, broken sight lines.
2. Wander spawn fires every `max(10, 22 - 90//4) = 10` turns — almost continuous pressure.
3. Monster spawn at L90 is `min_m = min(2 + 90//15, 7) = 7`, `max_m = min(3 + 90//8, 11) = 11`. Densest procedural floor.
4. **Seal demons** spawn on the levels L83, L85, L87, L89, L91, L93, L97 (`level_manager.py:152-160`). One of the seven seals **must be broken** on each. Until all 7 seals are broken, the player cannot descend past L99 (`main.py:1210-1216`).
5. NPC block 10 encounter possible (L91-98 — not L90).
6. Mystery: `fisher_king` (L58-72, no), `sisyphus` (L78-92, yes — physical challenge, walk 25 tiles overburdened).

### Quiz tempo
- Math combat is constant. Often multiple chains stacked (a fight, a new wave from wander spawn, another fight).
- Theology fires only at altars (L91 has one) or on prayer cooldown rotation.
- Identification has typically completed because the player either picked up enough scrolls of ID or is saving everything for the Stone.

### Ambient life at L90
- Mystery `sisyphus` possible (physical: walk 25 tiles holding the 30-weight Boulder, `mystery_system.py:159-172`). Pure ambient-mechanical wonder beat.
- No L90 altar (nearest L91).
- Seal demons throw atmosphere ("The Seal of Wrath glows red as the demon falls").
- Bones ghost: 50% chance — but rare to have bones for L90 specifically.

### Tension curve
**Sustained high pressure.** SP drain compounds with attrition. Wander spawns force the player to clear-and-move-clear-and-move. Lower-tier potions don't heal enough to matter (e.g., `potion_of_healing` rolls maybe 1d10+5 vs. 600 HP). The repair path is *cooking* (compound recipes for big perm bonuses), *prayer* (at L91), or *avoidance* (race the stairs).

### Friction
- **Maze + wander spawn + monster density at L90 creates a cumulative attention load.** The player is doing math chains every minute, occasionally interrupted by 65s economics or 55s philosophy quizzes (chest, ID), with hostiles spawning every 10 turns. **A player who slows down dies; a player who speeds through misses ambient encounters.** This may be intentional pressure — but the *Recall Lore* loop becomes essentially unusable: the cooldown is 65-125 turns and getting 5/5 trivia chains while wander mobs pile up is unrealistic. Wonder degrades as the run becomes serious. (See finding `fun-recall-lore-late-game-decay.md`.)

### Wonder
- **Seal demon kills** — each one is uniquely flavored ("Seal of Pestilence shattered. The air clears."). Hand-crafted boss-tier beats every 2 floors in the L83-97 stretch.
- **Sisyphus mystery** — the slow walk under burden is a wonderful tactile change of pace amid math-chain mania. (`mystery_system.py:159-172`).
- **The judgment altar at L99** (`game_divine.py:684-693`) — one-time special prayer, opens the final descent. Distinct from regular altars.

---

## Checkpoint F — The Death-chase Escape (post-L100)

**Trigger:** Player ascends from L100 carrying the Philosopher's Stone or the Complete Tablet of Second Death (`main.py:1239-1246`).

**State at trigger:**
- HP probably 400-800 (depleted from Abaddon fight at L100).
- A few potions left.
- Prayer cooldown maybe at 0 (last altar was at L91), or partly used.
- Lockpick charges variable.
- 99 levels to climb.

### Turn-by-turn action mix at L99→L75

The chronicle entry on Death's arrival: *"Something is following me. I felt it before I saw it. Death itself. I need to run."* (`main.py:1264`).

**Speed 50%** — Death acts on every other turn. The player can outpace Death by *moving* even at 1 tile per turn. Combat is dangerous because every combat round = 1 player turn = 1 Death advance roll.

1. Player ascends from L100 to L99. Death spawns near the down-stairs of L99 (`main.py:1266-1281`).
2. Player begins to climb floors. Each floor transition: Death is re-placed near the L-1 down-stairs, the new floor's monsters are still there from the descent (level state persists, `level_manager.py:15-17`).
3. Wander spawn still fires.
4. Combat: math chain. Each turn the player spends in combat = ~1-2 monster turns = ~1 Death move.
5. Stair-rest healing on ascent: `min(22, max(2, 4% of max_hp))` = 22 HP per stair (`player.py:184-185`).

### Quiz tempo at the chase
- Math combat is constant. Mathchains are the player's *attack* on the obstacles between them and the next stairs.
- Theology prayer can **freeze Death for 4-8 turns** (`game_divine.py:792-797`). This is the **panic-button** of the chase. But prayer cooldown is 100-280 turns, so it fires maybe 4-8 times total over a 99-floor ascent.
- Identify, lockpick, cook — **mostly irrelevant** now. Items are auto-identified from the Stone's `identify_sight` effect (`main.py:2161`). Lockpicks are too slow. Cooking is too slow. Even harvesting is rarely worth the time.

### Tension curve across the four speed phases

| Range | Speed | Vibe |
|---|---|---|
| L99 → L75 | **50%** | Tense but manageable. Player has room to fight wander mobs, occasionally rest. Death is "always somewhere behind." |
| L75 → L50 | **75%** | "Death quickens. The scraping is faster now." — atmospheric `_SPEED_MSGS` (`main.py:1304-1311`). Player must stop fighting most wander mobs and just run. |
| L50 → L25 | **100%** | "Death matches your pace now." — Death keeps up tile-for-tile. Combat becomes a death sentence: every chain attempt = 1 Death move. |
| L25 → L1 | **125%** | "Death is FASTER than you. It's gaining. RUN." — Death has 25% chance of a bonus action per turn (`monster.py:1066-1071`). The player **cannot outrun** by walking — they must use prayer-freezes, hasted potions, teleport scrolls. |

### Ambient life on the way up
- Each floor was previously explored. Items the player dropped, monsters they killed, special rooms — all preserved (`level_manager.py:19-21`).
- Death-proximity warnings fire when Death is visible within 3 or 6 tiles (`main.py:1408-1419`).
- The player still has access to fountains/altars/mysteries they didn't drink/pray/solve, but most are now too costly to detour for.

### Friction in the chase
- **Floors 75-50 (speed 75%) is the longest single tension band — 25 floors.** Atmospherically appropriate, but mechanically repetitive: walk, fight a wander mob, run, take stairs, repeat. The wonder of the descent has been spent.
- **Once Death is at 125% speed (L25-L1), the only meaningful option is consumables.** Players who didn't save a Scroll of Teleportation, a Potion of Haste, the Flux Capacitor (`main.py:1421-1447`), or a prayer charge are essentially doomed. **The chase rewards inventory hoarding from the descent**, which is the *opposite* of the rest of the game's encouragement to use what you find.
- **The Death-chase is "descent in reverse with a monster behind you"** for ~70 of its 99 floors. The chronicle messages add wonder, but the loop itself doesn't change shape until you hit the 125% speed band — by which point it's pure crisis management. **Act III doesn't have its own identity as a climax act.** (See finding `fun-act-three-flatness.md`.)

### Wonder
- **The first Death-proximity message** lands well: "Death looms over you — MOVE!" (`main.py:1417`).
- **Prayer to freeze Death** — the chronicle line "Prayed while Death hunted me. It froze in place. {N} turns. That's all I get." (`game_divine.py:797`) is among the game's strongest text moments.
- **The Secret Victory** (`main.py:1373-1407`) — if the player kept the Tablet of Second Death from L66±, the Wrench from L48±, the Lake of Fire scroll from L33±, and merged them with the Stone, they can find the Abyssal Shimmer and trigger the lake-of-fire ending: "Then Death and Hades were thrown into the lake of fire." Code drop: "Take this code to your father proudly — you have shown true Wisdom and Courage." **This is the maximum wonder moment in the game.** A kid who pulls this off will remember it.
- **The exit popup** on a successful normal ascent — "You have done what many believed impossible… well done." (`main.py:3452-3473`) — closes the loop.

---

## Cross-checkpoint patterns

### Quiz tempo × action frequency match
- Math at 16s (WIS 10) matches combat tempo well — every melee swing fires a quiz, but each quiz is short enough not to break the action.
- Theology at 65s on prayer cooldown 100-280 turns is correctly weighted — prayer is rare and contemplative.
- **Identification at 55s philosophy threshold, philosophy is the one that flares friction.** The threshold scales with item tier (`game_magic.py:2011`: `threshold=id_tier + 1`), meaning T5 identifies need 6 correct out of 9. With a 55s timer and 9 questions, that's potentially **8+ minutes of real time to identify a single high-tier item.** A player who picks up 20 items per floor can't ID them all without abandoning play altogether.
- **Cooking at 60s escalator chain, max chain 5** — well-paced. Cooking gives the player something to do during a "rest" beat at an altar or after a fight.
- **Lockpicking at 65s economics threshold** is too long for an opportunistic loot beat. A chest is a *side detour*, not a main action — but the quiz length makes it feel like one.

### Three acts: do they feel distinct?
- **Act I (Descent, L1-L99):** procedural, exploratory, attritional. Mix of subjects, surprise encounters, NPC moments, altar punctuation.
- **Act II (Boss, L100):** hand-crafted, ritual, single-purpose. Math chain on Abaddon.
- **Act III (Escape, L99→L1):** chase. **Loses the encounter variety of Act I.** Same procedural floors, same monsters, but the player can't engage most systems because of Death pressure. The pace becomes *math chain* + *stairs* + *occasional prayer* + *consumable burn*. Wonder is funneled into the chronicle/proximity messages and the possible Secret Victory.
- Act III is the **least mechanically distinct act**, despite being the dramatic climax.

### Hidden-system density
- Quirks (~80, `quirk_system.py:1097-1199`) — vastly over-supplied; players will unlock maybe 5-15 in a single deep run.
- Mysteries (12, `mystery_system.py:16-186`) — 1-3 will fire per run.
- Flavor encounters (97 across pool, ~40% per non-boss floor) — player sees maybe 15-25 per run.
- NPC moral encounters (30 across 10 blocks, exactly 1 per block) — player sees 5-9 per run.
- Boss story popups (5 — one per boss). All seen on a full run.
- Cow level (1, secret L35 trigger). Maybe 1-in-3 runs.
- Abyss / Secret Victory (1, hidden). Maybe 1-in-20 runs.
- XYZZY hack reality (hidden — backtick key, hinted at in T2 hints).
- Recall Lore (escalator chain, hint pool tiered 1-5).
- **Hidden system density is excellent** — the dungeon does feel alive. But many of these are *single-fire* (mysteries don't repeat per run, NPCs don't repeat per block, quirks unlock once). The dungeon is **dense with first-time wonder and thin with repeat wonder.** A second run will encounter many of the same scripted beats.

### Death curve fairness
- Math chain breaks on a single wrong answer (`quiz_engine.py:187-194`). A kid who *fails* a math fact under time pressure simply doesn't damage the monster that round. **Failure feels like missing a swing in any roguelike, not like the game cheating.**
- Threshold failures (lockpick, ID, harvest) lose the attempt — but on threshold the player gets 1.5× threshold questions to hit the bar, so partial credit is built in.
- Trap deaths fire `_check_floor_trap` with PER-based avoidance (`main.py:1707`). High PER players avoid traps ~37%; this is fair.
- **The biggest unfair-feeling death** is probably a chain-break combat against a high-damage monster where the player gets back-to-back tough math problems and chain=0. The math bank tier scales with floor — but the player has no warning that *this* monster's combat is at a higher tier than the last one.
- Bones writing (`bones.py:26-63`) is excellent for *next-run* sting relief: your previous character's gear shows up as a ghost on the floor you died on. The narrative wrap-around is strong.

### Identification loop
- Threshold philosophy. The interaction is rote (open menu, pick item, quiz). The chronicle line that fires on legendary identifies — "Identified something remarkable: {name}. The lore runs deep." (`game_magic.py:1993`) — is good.
- **Auto-identify-on-stone-pickup** (`main.py:2156-2165`) is a strong reward beat. Locking it to L100 means players grind through ID for 99 floors first. The first floor where ID is *guaranteed* is L30 BUC auto-reveal at WIS 14 — but BUC ≠ identify; the item still doesn't show its type.
- **The grind is real.** A typical L30 inventory has 10-15 unidentified items. Identifying all of them costs ~10-15 minutes of philosophy quizzes. Most players will only ID items they need right now and **carry the rest to the Stone**. (See finding `fun-id-loop-grind.md`.)

### Cooking
- Escalator chain, max 5, quality 0-5 maps to ruin/poor/decent/good/great/perfect.
- Per-ingredient HP/SP rewards scale with sqrt(min_level) — meaning late-game ingredients (dragon, lich, etc.) are massively more potent.
- Compound recipes from `data/items/recipes.json` are the *true* progression vector (`food_system.py:41-46`).
- **Cooking is fun the first 5 times.** Then it's the same 5-question escalator chain. The bonus type (random_stat, combat_stat, two_stats, all_stats, status, stat) keeps it *outcome*-varied but the *mechanic* is identical.
- **Cooking is the de facto HP-growth system.** The chronicle notes the first compound cook ("Cooked my first compound recipe… The dungeon smells like a kitchen for once.", `main.py:2387`). Strong moment.

### Lockpicking
- Economics threshold. Failure costs a charge. 30% alert chance.
- **The fragility of lockpicks is a Tier-1 hint** — players are taught to expect this.
- The friction is *moderate*: a lockpick burn on a failure feels expected. The 65s economics timer per question, however, makes a 3-of-4 quiz feel like a real time commitment.
- Mimic chance (8%, `dungeon.py:1208`) is a great surprise mechanic. The first time a "chest" leaps up and bites for 10-20% of your max HP, it's a lesson the player will remember.

### Pets / NPCs
- **Soul Spheres** spawn 5% per floor (`dungeon.py:1280`). 15% chance a merchant has one. Likely to encounter 3-6 per full run.
- Pets are thrown to land at a target tile; pets follow, fight, evolve at XP thresholds 33 and 66 (`pet_system.py:66-67`).
- **Pet bonding feels rewarding** when a pet evolves — the message "{old} surges with energy and evolves into Voltpaw!" is satisfying. But pets are *combat helpers*, not *companions*; their AI is "stand near player, kill nearby thing." No dialog, no story, no XP gating tied to player action quality.
- **NPCs** are mostly one-shot encounters. Moral NPC encounters (`npc_encounters.py`) are well-written and impactful. Flavor NPCs (`flavor_encounters.py` + JSON) are textured and add color. Both add **break-from-combat moments** that feel like rest beats.
- **The unicorn** (`game_encounters.py:251-300`) is a multi-state slow-trust encounter — fed offerings, becomes trusting, then a science escalator quiz grants buffs. **One of the strongest ambient mechanics in the game**. Single-fire per run.

### Quirks as a meta-loop
- 80+ quirks, each unlocked by a specific behavior (`quirk_system.py:1097-1199`). Average run unlocks 5-15.
- **The cadence is excellent** for the first 30 hours of play: every run unlocks something new.
- **The mythological names resonate with kid-philosopher framing**: Prometheus, Sisyphus, Odysseus, Buddha. A kid who's heard of Hypatia or Cassandra will perk up.
- **Some quirks have grindy unlock conditions** — Cerberus needs 300 stair uses (~3 full runs), Buddha needs 500 turns waiting near monsters (extremely niche), Ahasverus needs 15000 tile moves, Sibyl needs 500 correct answers AND being below floor 20.
- **The "I want to play again" hook** is strongest immediately after a run that unlocks a new quirk. The quirk screen (`w` key, `main.py:2702-2714`) shows progress toward 80 named beats. **This is the meta-game.** (See finding `fun-quirk-meta-loop-strength.md`.)

### The "I want to play again" hook
- **High pull-back beats:**
  - A successful Secret Victory (Abyss). Story popup + reward code.
  - A new quirk unlock screen.
  - A T5 hint from Recall Lore the first time.
  - A boss kill story popup.
  - A bones ghost of a previous character.
- **Low pull-back beats:**
  - Starving to death (no narrative, just "You have starved").
  - Death to chained wander spawns at a maze level (feels random).
  - A run where no mystery altar fired, no NPC encounter triggered, no quirk advanced — *flat* runs are possible if dice roll badly.
- **The chronicle file** persists across runs as a journal (`main.py:213-220`). A kid who keeps re-reading their own journal entries from past runs is exactly the loop the game wants.

---

## TL;DR pacing summary

| Checkpoint | Action mix | Dominant subject | Wonder beats | Friction risks |
|---|---|---|---|---|
| **L1** | Walk, fight, harvest, cook, find altar | math | First lore hint, first ID, dungeon entrance | ID hoard begins; very forgiving |
| **L10** | Above + mystery + NPC + merchant | math (60%) | Crucible, block 2 NPC, first compound cook | Inventory clutter peaks; wonder-subject timers feel slow |
| **L30** | Maze + mob density + mystery + bosses approaching | math + spell | Sphinx riddles, cow level, story milestones | Mazes + wanders + slow ID = attention overload |
| **L60** | Boss fight + post-boss recovery | math | Boss story, L61 altar | Subject monotony in extended boss chain |
| **L90** | Seal demons + wander pressure + Sisyphus | math | Seal demon kills, judgment altar | Recall Lore decays; wonder budget thin |
| **Chase** | Run + fight + pray + stair | math + theology | First Death message, Secret Victory | Act III lacks mechanical identity for 70+ floors |

The game's *wonder budget* is heavily front-loaded (Acts I/II) and back-loaded (Secret Victory). The mid-Chase span and the deep-procedural-grind in the 30-90 band are the **dry zones** where FUN findings concentrate.
