# Master plan: rebalance every remaining system around the core

Date: 2026-10-06. **Phases 0 to 6 are built** (each has an "As built" note under its heading); Phase 7 is not. It covers the fifteen systems listed as still needing review, in the order they depend on each other, with nine decisions flagged for you (D2, what magic is for, and D9, the target win rates, are decided).

## 1. The idea in one paragraph

The core is settled: every action is a quiz, the combat clock is Wisdom in seconds, a weapon asks the maths of its material, and each tier is a real step up. What is missing is that the other systems were each sized on their own, at different times, against numbers that have since moved. The plan fixes that by giving every system the same six yardsticks to be measured against, and one shared limit on how much optional power can stack. No system is tuned against "the core" alone; it is tuned against the yardsticks **with the other systems switched on**.

## 2. The six yardsticks

These already exist in code or in the simulator. Every number in every later phase is written as a share of one of them, never as a bare figure.

| Yardstick | What it is today | Where it lives |
|---|---|---|
| **The clock** | Wisdom in seconds: 10 at the start, +1 per 3 floors, 43 at floor 100 | `Player.learn_from_depth` |
| **One attack** | What a floor-typical weapon does in one chain at that floor's clock | to be added to `floor_curve.py` (today only the simulator knows it) |
| **One monster** | Ordinary monster HP and one ordinary hit, by floor | `floor_curve.HP_ANCHORS`, `DMG_ANCHORS` |
| **One health bar** | Player max HP by floor for a steady cook: about 65 / 140 / 220 / 310 / 420 at floors 10 / 30 / 50 / 70 / 90 | to be added to `floor_curve.py` |
| **One floor's gold** | 150 + 90 x floor | `economy.floor_income` |
| **One floor's time** | Questions asked and turns taken on a floor: about 95 questions early, 380 deep | simulator only; to be made a stated target |

Two of these ("one attack" and "one health bar") are not yet written down anywhere the game can read. Phase 0 adds them, because most of the bugs you have been finding are a fixed number that should have been a share of one of these.

## 3. The stacking limit

The systems below all add power on top of a plain character: a stat build, a prayer, haste, a pet, magic, a hero kit, quirks, a named weapon. Each one looks reasonable alone. Together they multiply. The plan gives each a ceiling, and the simulator checks the product.

| Source of extra power | Proposed ceiling, alone | Notes |
|---|---|---|
| Stat build (one stat fed all run) | 1.6x damage or 1.6x toughness | from the stat design, section D1 |
| Michael, Guide My Hand | 1.9x damage for 8 turns, once per fight | built |
| Haste | 1.25x clock and double actions | exists; permanent sources start at floor 50 |
| A pet | 0.25 of the player's own damage | Phase 4 |
| Magic | changes a fight's shape (control, area, position); single-target damage under one weapon chain; worth about a fifth off a floor's losses | Phase 3 |
| Hero kit | 1.3x at the start, falling to 1.1x by floor 40 | Phase 5 |
| Quirks, all earned | 1.25x in total by floor 100 | Phase 5 |
| A named unique | 1.25x a common of its floor, or equal with a side benefit | built |

**Rule:** a character with everything stacked should be about 3x a plain prepared character in a short burst and no more than 2x sustained. Above that the game is solved; the simulator will report the product at floors 20, 40, 60, 80 and 100 after every phase.

## 4. The phases

Each phase ends the same way: simulator table against the previous phase, tests, one commit, and a short note of what moved. I will not hand a phase back with a list of loose ends.

### Phase 0: measurement (do first, everything else leans on it)

- **Record real answer times.** The game logs seconds per answer by subject and tier to a file. Every chain and damage figure so far rests on five guesses; you have confirmed one (tier 1, about 1.7 seconds). One evening of your kids playing fixes the other four.
- **Write down "one attack" and "one health bar"** as functions in `floor_curve.py`, with tests that the live data matches them.
- **Teach the simulator what it cannot see:** spell and wand use, ranged weapons, a pet, quirks earned, and the stat build chosen. Without this, Phases 3 to 5 are guesswork.
- **Add a "everything stacked" player and a "plain" player** to the simulator, so the stacking limit is measured, not asserted.

Exit: simulator reports all six yardsticks and the stacking product per floor band.

### Phase 1: things that hurt the player by a fixed amount

The mirror image of the bug class you have been finding. Player health grew from 30 to about 430; monster damage and status ticks were scaled; these were not.

- Floor traps, chest traps, pit falls, the throne's and fountain's penalties, grave hazards, starvation, the duck, cursed-item effects, monster reflect and aura damage against the player.
- Each becomes a share of one health bar, sized by how avoidable it is: an unseen floor trap about 10%, a chest trap from a failed lock 15 to 25%, a throne or fountain gamble 20%, starvation 2% a tick.
- Healing that is still a flat number gets the same treatment in the other direction (spells, wands, food, fountains), against a stated healing budget per floor: about 0.6 of a health bar from finite supply, the rest from prayer and rest.

Exit: no hazard is under 3% or over 35% of a health bar on any floor; healing supply per floor is within 0.5 to 0.8 of a health bar.

### Phase 2: the character sheet (stats, armor, hunger and rest)

These three are one system: they decide how much damage arrives, how much health absorbs it, and how freely it is recovered. Tuning any one alone is what produced the "patient player wins half the time" result.

- **Stats.** Constitution, Dexterity and Perception are close to dead weight. See decision D1.
- **Armor and hit chance.** Check that each point of armor is worth about the same share of incoming damage at floor 10 as at floor 90, and that light, medium and heavy armor are real choices.
- **Hunger and rest.** Resting fully between fights removes most deep-floor danger and food is plentiful. See decision D3.
- **Cooking.** Make the stat stamped on each cut count (it is ignored today), and give the 893 recipes a stated budget: health from every proper meal, a stat from the first good one per floor.

Exit: a plain prepared player and a patient one are within 15 points of each other in win rate; each of the six stats, fed all run, lands inside its ceiling in section 3.

**As built (2026-10-06).** Measured with the simulator, 480 runs per player type over four independent sets of dungeons, a child who is 95% right on simple sums.

| Player | Reaches floor 20 | Past Asterion | Floor 40 | Floor 60 | Floor 80 | Wins | Target |
|---|---|---|---|---|---|---|---|
| Casual: cooks a little, skips quests | 90% | 47% of all runs (he beats about half who reach him) | 0 | 0 | 0 | 0 | 90% to floor 20, about half past Asterion |
| Prepared: cooks, does the quests | 100% | 100% | 94% | 58% | 43% | **26%** | 25 to 30% |
| Committed build (Strength and Constitution) | 100% | 100% | 96% | 71% | 52% | **39%** | 40 to 50% |
| Committed, and found the four secrets | 99% | 99% | 92% | 68% | 51% | **42%** | 60 to 70% |
| Rests as long as it takes before every fight | 99% | 99% | 94% | 64% | 50% | **35%** | within 15 points of prepared |

What was built, in the order it was found to be needed:

- **Constitution** is 3 hit points a point and takes 1% off every blow per point over 10 (40% at most). **Dexterity** gives a 0.75% chance per point over 10 to slip a blow from something beside you (30% at most), and its armor is capped at 3 points. The character sheet shows both as Dodge and Tough.
- **The meat decides the stat.** A proper meal from a prime cut is banked toward the stat stamped on that cut; two such meals, on two floors, make one point. One lesson a floor. A run feeds about fifty points. One stat can take 2 plus a point per five floors from cooking (22 at the bottom); Wisdom half that, because depth already teaches it.
- **Gate bosses leave three gifts; you take one, for good.** Asterion: Strength, Perception or Intelligence +4. Medusa: Wisdom +3, Dexterity +5 or Constitution +5. Fafnir: Strength +6, Constitution +6 or Wisdom +3. Fenrir: Intelligence, Dexterity or Perception +7. One more point if you solved that boss's quest (the Thread, the Aegis, the strike from the pit, the ribbon). Data in `data/boss_boons.json`.
- **Armor needed no change.** Two points of armor take 13 to 20% off incoming hits at every depth from floor 10 to 100.
- **A gate boss left alone heals.** After 25 turns without being hurt it regains 3% of its health a turn. Before this, anyone could walk away, recover and return to a boss still carrying every wound: no gate could be lost to by a patient player.
- **Asterion grows furious.** Each blow he swings adds 2% to his damage (up to double). He now beats about half the casual players who reach him (a third of those carrying the Thread) and almost no one who arrives prepared. That last part is short of the 85% I proposed: a prepared character absorbs three to four times its own health in that fight through potions and prayer, and any setting that threatens it kills every casual player. He is a gate for the typical child, and a reward for the prepared one.
- **Rest mends to 60% of health and no further; meditation gives back half a mana bar per floor.** This is decision D3. The first half alone was not enough: the measured edge of the patient player (71% wins against 35%) came from waiting for mana and casting fifteen to twenty healing spells a floor, not from sleeping. With both limits the patient player wins 35%.
- **The first floors go easy.** An ordinary monster's blow lands for three quarters of its damage down to floor 13, easing to full by floor 26. Two early outliers were softened by hand (the dark elf's poison, the anzu bird's six-turn paralysis).
- **Deep monsters hit harder,** because the new stats made a prepared character roughly twice as durable: nothing at floor 26, about x1.1 at floor 50, x1.35 at floor 100, ordinary monsters only (`tools/balance/SCALE_LOG.md`).

Two things this phase did not reach, and where they are handled:

- **The secrets are worth 3 points, not 20.** They pay at their own bosses, and with the ordinary quest items those bosses are already nearly safe (Fenrir with the ribbon kills no one, so the Sandal saves nothing). That is Phase 6: when the gates are made dangerous, the secrets become worth what they should.
- **A committed build is 13 points ahead of a plain one, not 15 to 20.** In the simulator "committed" means only where the stat points go. Magic, pets, hero kits and quirks (Phases 3 to 5) are the other tools a committed player uses and a plain one does not.

### Phase 3: magic

- **Role (decided, D2):** a variable, fun way to play that changes the shape of a fight. Never a substitute for maths.
- Every spell, wand and scroll priced by its effect: control in turns, area in targets, reach, position, information, escape, healing in health bars. Single-target damage is capped below a weapon chain.
- A variety pass: list what each one does that a sword cannot; merge or replace the ones that are only "the same, bigger".
- Intelligence becomes a build that casts more often and makes effects last or reach further, inside the stat ceiling.
- Utility scrolls (mapping, teleport, enchant, identify) checked for supply against one floor's time and gold.
- Wands of wonder, wish and polymorph: confirm nothing can produce a permanent gain outside the caps.

Exit: a player who uses magic well takes noticeably fewer losses per floor than one who does not (about a fifth), still kills with sums, and no spell or wand alone ends a fight with a named foe.

**As built (2026-10-06).**

- **One cast now lands under one weapon chain.** Measured against the attack yardstick (`python tools/balance/magic_audit.py`), one spell, for one science question and no clock, was doing 0.9 to 1.6 weapon attacks from a plain character and up to 2.4 from an Intelligence build; a wand charge up to 3. Magic was the better damage track, which is the opposite of your ruling. Now the strongest bolt of each tier is about 0.7 of one attack on the floors it is found on, area spells 0.35 to 0.6 per target, a wand charge about 0.85. Effects that only bite the undead may reach one attack. A test holds every spell and wand to those lines.
- **Intelligence gives reach, not a bigger number.** It was +10% damage a point (an Intelligence of 36 multiplied every spell by 4.6). Now it adds 1.5% a point to damage and healing (at most +40%), and 3% a point to how long a spell's effect lasts and how far it reaches (at most +75%). It still gives one mana a point, so a caster casts more often.
- **Nothing ends a named fight alone.** Checked every instant-kill and banish effect (death ray, disintegrate, power word, annihilation, banishment, extinction): each already skips named foes and bites them for no more than half an ordinary monster's health. Hard control on a named foe is capped at three turns and does not stack. No change was needed.
- **Lucky stat points have one allowance for the run:** 3, plus 1 per ten floors. A wish, a fountain, a throne and a scroll of great power each gave "+1, no limit", and the wish is a spell that can be cast on every floor. Scripted rewards (quests, encounters, mysteries) are outside it.
- **Two top-tier spells were the same spell.** Deep Slumber and Mass Paralyze both paralysed everything in sight for 8 turns at the same price. Deep Slumber is now a 20-turn sleep that a blow breaks (for slipping past, or taking a room one at a time); Mass Paralyze holds through blows for 8.
- **Supply was measured and left alone.** A full run finds about 250 wands, 250 spellbooks, 30 each of mapping and identify, 17 teleports and 88 enchant scrolls; enchantment is already capped per item.

What the simulator can and cannot say about the exit line:

- It models fights one monster at a time, and an ordinary monster dies in one or two chains. In that model there is nothing for control magic to change: a simulated player who cast Hold on everything lost 12 points of win rate (wasted turns, and mana that would have been healing). One who hastes and slows only for long fights does about as well as a non-caster overall (32% against 35%, inside the noise) and clearly better at Abaddon (40 to 51% deaths against 51 to 68%).
- So "a fifth fewer losses per floor" is **not shown**. What magic is for in this game, area effects on a room that has surrounded you, sleep to split a group, a blink out of a corner, is exactly what a one-at-a-time model cannot see. This is a play-test question: does a room of five feel different with Mass Sleep in hand?
- Healing spells are the part of magic the simulator does see, and they are strong: limiting the mana that waiting gives back (Phase 2) cost every caster about 15 points.

### Phase 4: companions and distance (pets, ranged combat)

- **Pets:** damage held at about a quarter of the player's, survival sized against one monster's hit, levelling pace restored, and each special priced like a spell.
- **Ranged:** see decision D4. Ammo supply set against one floor's time so a bow is a choice, not a trickle or a flood.

Exit: with a pet, kills take about a fifth fewer attacks; a ranged player's losses per floor are within 20% of a melee player's.

**As built (2026-10-06).**

- **Pets were strong at the top and useless at the bottom.** A pet's bite was 72% of the player's own attack on floor 5 and 7% on floor 100, and deep down it died to two or three hits. A pet that keeps pace with the dungeon (its level about equal to the floor, which is the pace they level at) now bites for a quarter of one weapon attack at every depth, has 70% of the player's health bar for that depth (four to eleven hits' worth), and regenerates 1% of its health every third turn. Pets in old saves are brought up to date on load.
- **Pet specials needed no change:** 1.2 to 2.5 times the pet's bite (so 0.3 to 0.6 of one attack) plus a short status, about once a floor.
- **Sketched monsters no longer hit several times too hard.** A drawing copied a monster's current-scale dice and was then multiplied by the depth scale again.
- **Measured with a pet (committed build):** 6% fewer attacks per kill, about 10% less damage taken per monster, 66% reach floor 80 against 48%, wins 42% against 38%. The plan said "a fifth fewer attacks"; with most monsters dying in one chain there is not a fifth to save, and a quarter of the player's damage is the ceiling the stacking table allows a pet.
- **Ranged (decision D4, built as recommended: a specialist's tool).** Measured, and it already has that shape, so nothing was changed: a bow's base equals a blade's of the same material; a floor yields about 15 shots against the 30 or so attacks it takes to clear; and a shot gets no Strength multiplier, so a Strength build's blade out-hits its bow by up to two thirds. The code now says so where the multiplier is, and tests hold all three facts. The simulator does not fire bows, so "losses within 20% of melee" is not measured; ranged here is an opening shot on top of melee, never a replacement for it.

### Phase 5: who you are (hero builds, quirks, curses and identification)

- **Hero builds:** see decision D5. Signature weapons get a floor-band rule; powers priced like spells; the misnamed build fixed.
- **Quirks:** all 112 unlock thresholds restated against one floor's time, and every reward placed under the caps. See decision D6.
- **Curses and identification:** honour the two item fields the code ignores, and decide where cursed loot can come from. See decision D7.

Exit: the "everything stacked" player is inside the stacking limit at every band.

**As built (2026-10-06).**

- **A hero's named weapon grows with the dungeon (decision D5, built as recommended).** The six signature weapons (Achilles' Spear, Romulus' Spear, the Torch of Prometheus, the Witcher's Silver Blade, Zireael, the Boomstick) start at three to five times a floor-1 sword, so the starting edge is real and fades by itself. From about floor 12 the weapon's base is kept at 1.3 times a typical common's of the deepest floor reached, easing to 1.1 times by floor 40, and at floors 20, 40, 60 and 80 it starts asking that band's sums, exactly as a common of that depth would. Nobody is told to throw the hero's sword away. Only the copy a hero starts with grows; the same unique found as loot does not. The log says when it grows and when it starts asking harder sums.
- **Trait (quirk) rewards are inside the caps (decision D6, built as recommended).** Stat points from traits are paid from an allowance that grows with depth: 4 at the top, 16 at the bottom. What a trait gives beyond today's allowance is held and comes in as the player descends, with a message each time; nothing earned is lost. Seconds a trait adds to the combat clock become Wisdom (the same thing, a point is a second) and are counted in the same allowance. Before this, 112 traits each gave "+1 or +2, no limit": the one source of power that grew with hours played instead of depth.
- **`can_be_cursed: false` is honoured (decision D7, built as recommended).** 108 items carried the field and nothing read it. They are never found cursed now. Chest and drop loot stays uncursed, as before.
- **Not done: the 112 unlock thresholds were not restated one by one.** They are conditions in code, not data, and each needs reading by hand. With the rewards capped, a threshold that is too easy can no longer break anything; it only decides when a held point is earned. Hero powers were already sized to the floor in an earlier pass and were not revisited. The Tesla build's name is still on your list.

**Where the table stands after Phases 3 to 5** (400 runs each): prepared 19%, committed 29%, everything stacked (build, secrets, pet, magic) 50%. Capping lucky stat points and flattening what Intelligence adds to healing cost every profile 7 to 10 points since Phase 2. The curve is brought back onto the targets in Phase 6, together with the gates, because Abaddon alone now takes a fifth of everyone who reaches him.

### Phase 6: the end of the game

- Seal demons, Abaddon and his altars, Death and the climb out, the Abyss ritual, all re-sized against the yardsticks **after** Phases 1 to 5, since they are the place every system meets.
- **Asterion is handled earlier, at the end of Phase 2,** because he is the gate at the end of the gentle floors and should be tuned as soon as health, armor and rest are settled: see decision D9.
- Target for the escape: see decision D8.

Exit: the stated win rates in decision D9.

**As built (2026-10-06).** 480 runs per player type over four independent sets of dungeons, a child who is 95% right on simple sums. "Wins" here means Abaddon dead and the Stone in hand; the climb out is not simulated (see below).

| Player | Reaches floor 20 | Past Asterion | Floor 40 | Floor 60 | Floor 80 | Wins | Target |
|---|---|---|---|---|---|---|---|
| Casual: cooks a little, skips quests | 93% | 52% of all runs | 0 | 0 | 0 | 0 | 90% to floor 20, about half past Asterion |
| Prepared: cooks, does the quests | 98% | 98% | 92% | 61% | 44% | **32%** | 25 to 30% |
| Committed build (stat choices only) | 100% | 100% | 95% | 67% | 48% | **35%** | |
| Committed build with a pet | 100% | 100% | 98% | 85% | 68% | **55%** | 40 to 50% (build plus the tools) |
| Committed, and found the four secrets | 100% | 100% | 93% | 70% | 56% | **45%** | |
| Everything: build, secrets, pet, magic | 99% | 99% | 95% | 84% | 67% | **59%** | 60 to 70% |
| Rests as long as it takes | 100% | 100% | 94% | 67% | 48% | **35%** | within 15 points of prepared |

Each figure carries about four points of noise. The pet is the single most valuable tool (twenty points), which is more than its "quarter of your damage" suggests: a kill that comes one turn sooner is one monster turn never taken.

- **Fenrir is now worth a quest.** With the ribbon he killed no one, so Vidar's Sandal saved nothing and the secret was worthless. His blows are about 60% heavier. Measured on fresh characters: he kills about a third of prepared players who come without the ribbon, about one in twenty with it, and none who wear the Sandal.
- **Abaddon is not a coin-flip any more.** He was taking half of everyone who reached him and used the altars. His blows are a fifth lighter: about four in ten with the altars, two in ten with the Sword of Michael, and in whole runs the Sword-carriers lose almost no one on floor 100.
- **The secrets now pay ten points** (35% to 45%) on their own, against three before. Still short of what I had in mind for "even more"; the rest of the top row comes from the pet and magic.
- **Floors 40 to 90 were eased by about 7%** to undo what Phase 3 took: capping lucky stat points and flattening Intelligence on healing had cost every profile 7 to 10 points.
- **Death's scythe takes a share of your health** (decision D8, see below): 8% of full health a blow, or the written 2d12+15 if that is more. The written number was nearly half of a 60-point health bar when it was set and a scratch on the 450-point one a winner carries.
- **Seal demons were measured and left alone:** four to five attacks each, and they kill about 1% of fresh characters. They are a toll on the way to Abaddon, not a gate.

**Not simulated: the climb out.** Death's chase is geometry (who reaches the stair first on a hundred maps), and the simulator has no map. So the table's "wins" stop at the Stone. I set the scythe so that the dozen or two blows a climber takes over the last twenty-five floors each cost something and none ends the run alone; whether that makes the escape a tense coda or a second boss can only be told by doing it. This is the one number in the plan I could not measure.

### Phase 7: what the player sees, and the last tune

- Screen: Wisdom gained, the Inspired effect, the maths tier printed on a weapon, the real clock in the sidebar (it hides haste today), prices, the prayer menu.
- **Context cards**, if you want them: see the parked analysis. They belong here because open-book answers change accuracy in every non-combat system above.
- One final simulator pass with real answer times, then play-test, then release.
- **Splitting `main.py`** is deliberately last: doing it mid-balance would turn every later change into a merge.

## 5. Decisions that are truly yours

Each has my recommendation, weighed against everything already changed.

**D1. The stat design: go ahead? (Step one BUILT 2026-10-06 on the recommendation below; say if you want it changed.)**
Recommend **yes, in two steps.** Step one in Phase 2: the meat decides the stat, Constitution gives 3 health a point and blunts damage, Dexterity gives a dodge, and the gate bosses each leave three gifts. Step two later: the "stars" at 25, 35 and 50. Reason: Wisdom from depth already supplies the baseline clock, so the build's job is no longer to make the game playable, only to make a character distinctive. That means the stat ceilings can be modest (1.6x), which keeps the stacking limit reachable. With depth Wisdom in place, I would cut the Wisdom a build can add by about half from my earlier proposal.

**D2. What is magic for? (DECIDED 2026-10-06)**
Your ruling: magic is a **variable way to play.** Spells cause effects and delays, open new ways to fight, hit areas, chain between targets. It should make playing more **fun**, not replace maths. Mental maths is the core skill being trained; the rest the player picks up casually along the way.

What that fixes for Phase 3:
- Magic is priced by what it **does**, not as a second damage track: control in turns, area in targets, position, information, escape. Raw single-target damage stays below a weapon chain, always.
- No magic build skips the clock. A fight is still won with sums; a spell changes the shape of the fight (who is in it, for how long, from where).
- Variety is the measure of success: every tier of spell and wand should offer something a sword cannot do, and no two should be the same effect with a bigger number.
- Intelligence makes magic available more often and makes its effects last or reach further. It does not make it hit harder than a blade.

**D3. Should resting be nearly free? (BUILT 2026-10-06 on the recommendation below, as limits rather than a food price: rest mends to 60%, meditation gives half a mana bar a floor. Food turned out too plentiful for a price in meals to bind.)**
Recommend **no, but gently.** Raise what rest costs in food until a fully rested floor costs about one extra meal, and keep wandering monsters. Reason: with your 40 to 50% target the top of the range is already reached today by a player who simply rests between every fight (50%), with no build at all. If rest stays free, the stat build and the power-ups have nothing left to add, and the difference between a prepared player and a great one comes from patience rather than knowledge. The aim is not to make the game harder overall, only to move where the wins come from.

**D4. Ranged combat: equal to melee, or a specialist tool? (Measured 2026-10-06: it already is a specialist tool; left as is.)**
Recommend **a specialist tool:** first strike and safety, paid for in ammo and slightly lower damage. Reason: you already ruled that Fafnir must not be killable from range. A general rule makes that boss consistent instead of a special case.

**D5. Hero builds: front-loaded, or level with the dungeon? (BUILT 2026-10-06 as recommended.)**
Recommend **signature weapons grow with depth, the starting edge fades.** A hero's named weapon gains a tier each floor band, staying about equal to a good common, with its special trait as the reason to keep it. Reason: a child who earned a secret build should not be told to throw the hero's sword away on floor 12, which is what fixed damage means now that each tier is a real step.

**D6. Quirk rewards: inside the caps or outside? (BUILT 2026-10-06 as recommended.)**
Recommend **inside.** Clock seconds become Wisdom, permanent stats count against the same per-stat cap as cooking, and all quirks together stay under 1.25x. Reason: they are the one remaining source that scales with hours played rather than depth, so they are where a patient player would break everything else.

**D7. Cursed loot: where can it come from? (BUILT 2026-10-06 as recommended.)**
Recommend **ground loot only, as now, and honour the "cannot be cursed" field.** I tried cursing chest and drop loot this week and it made the early game markedly harder for a child who wears what they find, for no gain in interest.

**D8. Death and the escape: how hard? (Built 2026-10-06 GENTLER than recommended below: your ruling on D9 counts a win as getting out, and a one-in-two escape would have halved every figure in that table. Death's blow is 8% of full health. Say if you want the climb to be the coin-flip I first proposed.)**
Recommend **the hardest stretch in the game, but short:** about one prepared character in two who kills Abaddon gets out, and the secret kill stays roughly one in fifty. Reason: the design document sets the win at one in five to ten for a master; the escape is where that last factor of two should sit, not in more floors of attrition.

**D9. Who is the game balanced for, in numbers? (DECIDED 2026-10-06)**
Your ruling: a well-prepared, committed build that has learned the systems and answers consistently, especially in maths, should win **40 to 50%** of the time. Most kids are strong enough at simple sums to reach floor 20 most times, but **Asterion should feel like an accomplishment.**

For a child who is good at sums (95% on simple ones, 85% on hard ones):

| Player | Reaches floor 20 | Beats Asterion | Floor 40 | Floor 60 | Floor 80 | Wins |
|---|---|---|---|---|---|---|
| Casual: cooks a little, skips quests | 90% | about half | 30% | 8% | 1% | 0 |
| Prepared: cooks, does the quests | 98% | 85% | 85% | 65% | 48% | 25 to 30% |
| Prepared with a committed build, uses every tool well | 98% | 90% | 90% | 78% | 62% | 40 to 50% |
| The same, and has worked out the secret quests | 98% | 95% | 93% | 85% | 75% | 60 to 70% |

**The secret quests pay (your ruling):** a player who figures out the hidden ones (the Cow Level, Vidar's Sandal, Reforged Gram, the Sword of Michael) should win even more. Each is worth a clear, measured step at its own boss (the Sandal at Fenrir, Gram at Fafnir, the Sword at Abaddon, the Cow Level as a mid-game windfall), and the simulator gets a "found the secrets" player so that step is checked rather than assumed. The 60 to 70% figure is my reading of "even more"; say if you want it higher.

What this means against today's numbers:

- **Floors 1 to 19 stay gentle.** They are about right now for a prepared player (98%) and slightly rough for a casual one (about 80% since the loot fixes); the casual line comes up to 90%.
- **Asterion gets harder, not easier.** Today he kills nobody who is prepared and about a quarter of casual players, in 20 to 24 attacks. The target is a fight a casual kid loses about half the time and a prepared one wins five times in six, with the Thread clearly mattering. He is the first place the game says "you have to have learned something".
- **The deep game is close already.** The prepared player wins about 26 to 35% today and the patient one about 50%. The work is to make that 40 to 50% come from a committed build and good use of the tools, not from resting for free.

Every phase is tuned toward this table.

## 6. What I will decide myself, unless you object

- The order of phases, and that `main.py` is split last.
- Exact shares for each hazard, spell and pet, within the ceilings above.
- That every new fixed number goes through the yardsticks, with a test that fails if one is added raw.
- That old saves keep working but are not migrated.

## 7. Size

Phases 0 and 1 are about a day each. Phases 2 and 3 are the large ones, two to three days each including simulator work. Phases 4 to 6 are about a day each. Phase 7 depends on play-testing and on whether context cards go ahead. Play-test checkpoints: after Phase 2, after Phase 5, and before release.
