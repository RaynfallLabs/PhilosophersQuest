# Master plan: rebalance every remaining system around the core

Date: 2026-10-06. Nothing in this plan is built. It covers the fifteen systems listed as still needing review, in the order they depend on each other, with nine decisions flagged for you (D9, the target win rates, is decided).

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
| Magic | one cast is worth about one attack; a full mana pool is worth about one fight | Phase 3 |
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

### Phase 3: magic

- **Role.** See decision D2.
- Every spell, wand and scroll priced as shares of the yardsticks: damage in attacks, healing in health bars, control in turns, and mana as a pool worth one fight.
- Intelligence becomes a build (larger pool, mana back on kills) inside the stat ceiling.
- Utility scrolls (mapping, teleport, enchant, identify) checked for supply against one floor's time and gold.
- Wands of wonder, wish and polymorph: confirm nothing can produce a permanent gain outside the caps.

Exit: a caster who answers science and grammar well clears a floor in about the same time and with about the same losses as a fighter who answers maths well.

### Phase 4: companions and distance (pets, ranged combat)

- **Pets:** damage held at about a quarter of the player's, survival sized against one monster's hit, levelling pace restored, and each special priced like a spell.
- **Ranged:** see decision D4. Ammo supply set against one floor's time so a bow is a choice, not a trickle or a flood.

Exit: with a pet, kills take about a fifth fewer attacks; a ranged player's losses per floor are within 20% of a melee player's.

### Phase 5: who you are (hero builds, quirks, curses and identification)

- **Hero builds:** see decision D5. Signature weapons get a floor-band rule; powers priced like spells; the misnamed build fixed.
- **Quirks:** all 112 unlock thresholds restated against one floor's time, and every reward placed under the caps. See decision D6.
- **Curses and identification:** honour the two item fields the code ignores, and decide where cursed loot can come from. See decision D7.

Exit: the "everything stacked" player is inside the stacking limit at every band.

### Phase 6: the end of the game

- Seal demons, Abaddon and his altars, Death and the climb out, the Abyss ritual, all re-sized against the yardsticks **after** Phases 1 to 5, since they are the place every system meets.
- **Asterion is handled earlier, at the end of Phase 2,** because he is the gate at the end of the gentle floors and should be tuned as soon as health, armor and rest are settled: see decision D9.
- Target for the escape: see decision D8.

Exit: the stated win rates in decision D9.

### Phase 7: what the player sees, and the last tune

- Screen: Wisdom gained, the Inspired effect, the maths tier printed on a weapon, the real clock in the sidebar (it hides haste today), prices, the prayer menu.
- **Context cards**, if you want them: see the parked analysis. They belong here because open-book answers change accuracy in every non-combat system above.
- One final simulator pass with real answer times, then play-test, then release.
- **Splitting `main.py`** is deliberately last: doing it mid-balance would turn every later change into a merge.

## 5. Decisions that are truly yours

Each has my recommendation, weighed against everything already changed.

**D1. The stat design: go ahead?**
Recommend **yes, in two steps.** Step one in Phase 2: the meat decides the stat, Constitution gives 3 health a point and blunts damage, Dexterity gives a dodge, and the gate bosses each leave three gifts. Step two later: the "stars" at 25, 35 and 50. Reason: Wisdom from depth already supplies the baseline clock, so the build's job is no longer to make the game playable, only to make a character distinctive. That means the stat ceilings can be modest (1.6x), which keeps the stacking limit reachable. With depth Wisdom in place, I would cut the Wisdom a build can add by about half from my earlier proposal.

**D2. What is magic for?**
Recommend **a second way to fight, never a way around the clock.** A cast should be worth about one attack and cost a question in another subject, with mana lasting about one fight. Reason: if magic out-damages maths for a child who is weak at sums, the core loop is optional; if it is much weaker, 3,700 science questions gate nothing that matters.

**D3. Should resting be nearly free?**
Recommend **no, but gently.** Raise what rest costs in food until a fully rested floor costs about one extra meal, and keep wandering monsters. Reason: with your 40 to 50% target the top of the range is already reached today by a player who simply rests between every fight (50%), with no build at all. If rest stays free, the stat build and the power-ups have nothing left to add, and the difference between a prepared player and a great one comes from patience rather than knowledge. The aim is not to make the game harder overall, only to move where the wins come from.

**D4. Ranged combat: equal to melee, or a specialist tool?**
Recommend **a specialist tool:** first strike and safety, paid for in ammo and slightly lower damage. Reason: you already ruled that Fafnir must not be killable from range. A general rule makes that boss consistent instead of a special case.

**D5. Hero builds: front-loaded, or level with the dungeon?**
Recommend **signature weapons grow with depth, the starting edge fades.** A hero's named weapon gains a tier each floor band, staying about equal to a good common, with its special trait as the reason to keep it. Reason: a child who earned a secret build should not be told to throw the hero's sword away on floor 12, which is what fixed damage means now that each tier is a real step.

**D6. Quirk rewards: inside the caps or outside?**
Recommend **inside.** Clock seconds become Wisdom, permanent stats count against the same per-stat cap as cooking, and all quirks together stay under 1.25x. Reason: they are the one remaining source that scales with hours played rather than depth, so they are where a patient player would break everything else.

**D7. Cursed loot: where can it come from?**
Recommend **ground loot only, as now, and honour the "cannot be cursed" field.** I tried cursing chest and drop loot this week and it made the early game markedly harder for a child who wears what they find, for no gain in interest.

**D8. Death and the escape: how hard?**
Recommend **the hardest stretch in the game, but short:** about one prepared character in two who kills Abaddon gets out, and the secret kill stays roughly one in fifty. Reason: the design document sets the win at one in five to ten for a master; the escape is where that last factor of two should sit, not in more floors of attrition.

**D9. Who is the game balanced for, in numbers? (DECIDED 2026-10-06)**
Your ruling: a well-prepared, committed build that has learned the systems and answers consistently, especially in maths, should win **40 to 50%** of the time. Most kids are strong enough at simple sums to reach floor 20 most times, but **Asterion should feel like an accomplishment.**

For a child who is good at sums (95% on simple ones, 85% on hard ones):

| Player | Reaches floor 20 | Beats Asterion | Floor 40 | Floor 60 | Floor 80 | Wins |
|---|---|---|---|---|---|---|
| Casual: cooks a little, skips quests | 90% | about half | 30% | 8% | 1% | 0 |
| Prepared: cooks, does the quests | 98% | 85% | 85% | 65% | 48% | 25 to 30% |
| Prepared with a committed build, uses every tool well | 98% | 90% | 90% | 78% | 62% | 40 to 50% |

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
