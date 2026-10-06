# Tiers, stat builds, power-ups, and the balance plan that follows

Date: 2026-10-05. Sections 1 and 2 are **done and committed locally**. Sections 3 to 6 are **proposals**: nothing in them is built. All balance figures come from the simulator, and every figure involving maths speed rests on my guess of 1.8 / 2.6 / 4.5 / 6 / 7 seconds per answer for tiers 1 to 5. Nobody has timed a child.

## 0. Current state (2026-10-05, final pass of the day)

Built, tuned and committed locally. Not pushed. Not play-tested: the outcome figures are simulated and rest on guessed answer speeds. **Sections 3 to 6 below are the earlier proposals; where they disagree with this section, this section is what the game does.**

**What the game does now**

- **Wisdom from depth:** +1 for every 3 floors of new depth (16 on floor 20, 23 on 40, 30 on 60, 43 on 100). The combat clock is exactly wisdom in seconds, plus earned effects.
- **The prayer key opens a menu** (`src/prayers.py`; more prayers can be added and gated by karma):
  1. **Lord, Have Mercy:** the existing prayer, unchanged.
  2. **Michael, Guide My Hand:** wisdom lent for a short burst, as a share of your own.

| Theology chain | Wisdom lent | Lasts |
|---|---|---|
| 1 | +30% | 3 turns |
| 2 | +45% | 4 turns |
| 3 | +60% | 5 turns |
| 4 | +80% | 6 turns |
| 5 | +100% (the clock doubles) | 8 turns |
| 5 at an altar | +120% | 10 turns |

  Prayed at a quarter health or less: 2 more turns and a 3-turn shield. Karma moves the length by one turn at most. Same cooldown as any prayer.
- **Each weapon tier is a real step up:** base damage x1.9 / x3.1 / x3.5 / x4.9 for tiers 2 to 5.
- **Monsters and bosses re-sized** to match (history in `tools/balance/SCALE_LOG.md`). Gate bosses: Asterion 9,000 HP, Medusa 21,700, Fafnir 44,900, Fenrir 66,400, Abaddon 86,400.
- **Every fixed damage number follows the dungeon's scale** (`floor_curve.scaled`): pets, hero and quirk powers, thrown and trap damage, weapon bonus dice, scrolls, auras, bare hands, monster poison and monster regeneration. Wands and spells scale by tier. Healing does not scale, because the player's hit points did not.

**Simulated result** (good kid: 95% right on tier 1, 90% on tier 2, 85% below; 200 runs, plus or minus 7)

| Player | Reaches floor 20 | Floor 40 | Floor 60 | Floor 80 | Floor 100 | Wins |
|---|---|---|---|---|---|---|
| Prepared: cooks, wears what drops, does the boss quests, prays for the hand at bosses | 100% | 98% | 69% | 55% | 44% | 26% |
| Patient: the same, and rests fully between fights | 98% | 96% | 82% | 80% | 78% | 50% |
| Casual: one meal a floor, skips the quests | 92% | 0% | | | | 0% |

- **Low floors:** nobody prepared dies before floor 20, and a casual kid gets there nine times in ten and beats Asterion nine times in ten. Kills take about 1.2 attacks.
- **The twenties:** a casual kid fades out between floors 22 and 30 (typically around 27), which is the design document's "past Asterion, loses before Medusa".
- **Floor 40 down:** about 2% deaths a floor at 41 to 59, 5% at 61 to 79, 11% at 81 to 99 for the prepared kid; about 1% or less for the patient one. Kills take about 1.7 attacks.
- **Bosses with the quest:** 13 to 19 attacks; Medusa kills about 5%, Fafnir about 10%, Fenrir about 1%. **Without the quest:** Medusa 71%, Fafnir 62%, Fenrir 39%. Abaddon kills 40 to 60% of those who reach him.

**Two things only play can settle**

- **How long a deep attack feels.** The clock is 30 to 43 seconds from floor 60, and a deep floor asks about 380 sums. Space strikes early.
- **Real answer speed.** If your kids are faster or slower than my guesses on tier 3 to 5 sums, the deep floors move with them. `tools/balance/scale_monsters.py` re-scales in one command once we know.

## 0b. The gold economy (2026-10-05)

One module, `src/economy.py`, now holds every gold rule.

- **Income is a line:** a floor pays about 150 + 90 x floor in gold (235 on floor 1, 1,950 on floor 20, 8,250 on floor 90), measured from the real generator. The old price formula matched that deep down and was six times too low at the top.
- **Merchant:** unchanged shares (a consumable is about a sixth of a floor, an accessory about two floors, a named unique about four), now against the right income. A floor-1 potion is 30 gold, not 5.
- **Encounters and mysteries:** their written gold costs and rewards were about 3% of a floor's income at every depth, so paying was never a decision. They are multiplied by 6 when a run's encounters are chosen (10 to 35% of a floor), and a price quoted in an option's label is rewritten to match.
- **Found gold** (graves, thrones) and the lockpick scrap value follow the floor instead of being flat.
- **Bribe (Gilgamesh):** costs 5 to 15% of the floor's income and holds the monster 3 turns. It was 1 to 100 gold for one turn.
- **Two bugs fixed:** the bribe and the Brisingamen amulet both used a gold counter that does not exist, so each raised an error when used.

## 1. Fixed this round

| Your point | What was done | Commit |
|---|---|---|
| 1. Material sets the tier | Every material file now has one explicit `tier`. Weapons, armor and shields all inherit it (maths tier for a weapon, geography tier for armor). Adamantine disagreed with itself (tier 4 as a sword, 5 as armor); it is tier 4. | `2edadd9` |
| 3. No arbitrary seconds | The seconds I added for higher tiers are gone. The clock is wisdom, times earned effects (haste, blessed), plus earned seconds (Ancile, quirks). | `2edadd9` |
| 2. Uniques sized by power | See section 2. | `d6a6345` |
| Bug found on the way | "Heroic" and "Brilliant" cooked meals permanently removed 2 STR, or 1 INT and 1 WIS, every time. Fixed. | same |

1,981 tests pass. Not play-tested.

## 2. Unique items: audit and fixes

All 349 uniques were scored against commons of the same slot, class, hands and floor, sampled through the game's own generator.

**What the audit found**

- **Tier is a huge lever on a weapon and nearly free on everything else.** One tier costs a weapon roughly a quarter to a half of its damage (harder sums, same clock). On armor and accessories it only changes which question is asked, and the equip can be retried.
- **Weapons:** tier already matched depth for 85 of 89. One-handed uniques are comfortably above commons (median 1.8×). **Eleven two-handed uniques were weaker than a common two-hander**, because the earlier rebase compared them against all swords.
- **Armor and shields:** AC is at or above a good common for 77 of 82. Thirteen unique shields are effectively just a good common shield, with nothing special that matters.
- **Accessories:** "one tier above depth" turned out to be a coherent rule, not drift: an accessory's tier is its power (a +3 ring is tier 3) and it is found one band early. I kept that rule. The real problem was power: 18 uniques were weaker than a plain ring from their own floor.

**What was changed (58 items)**

- 11 two-handed weapons raised to 1.25× a common two-hander of their floor.
- 7 weapon tiers moved to match power (for example Echidna's Fang and Oathkeeper asked tier-3 sums on floor 24; now tier 2).
- 4 armor tiers and 1 shield tier corrected; two shields given a small real benefit.
- 21 accessory tiers corrected; 16 weak uniques raised by a point or two.
- Hero starting items were left alone.

**Left for you to decide**

- **Cow King's Horns** adds one link to every chain and never misses: 1.8× to 2.4× all damage. It looks like a deliberate secret.
- **Jade Cicada** cheats death once per floor and is found on floor 25. I raised its tier and equip threshold; it may want to be once per run.
- **Gram** asks tier-5 sums on floor 60; the rule says tier 4.
- **Needs code:** four shields advertise spell reflection that nothing reads; `cursed: true` in item data is not read (Hand of Glory and Necklace of Harmonia are not actually cursed).

The audit also listed twenty benefits the engine already supports that are not damage (clock time on a shield, forgiveness on a wrong first answer, free identifies, reveal the stairs on arrival, and so on). Those are the natural way to make the plain unique shields and two-handers special.

## 3. Proposal: stat builds

### What is wrong today

- **Wisdom does not grow.** Median WIS is 10 until floor 40 and 16 at floor 100.
- **Cooking cannot build it.** Only 14 of 893 recipes grant WIS, and stat cooking barely exists before floor 40.
- **Three stats are dead weight.** CON gives 1 HP a point, and drain pulls it to 2 or 3 by floor 39. DEX stops mattering past about 22. PER stops past 18.
- **Every prime cut already carries a stat** in the data (90 of 516 are WIS). The cooking code ignores it.

### Three rules a child can hold

1. **You are what you eat.** The first properly cooked prime cut on each floor raises the stat stamped on the meat by 1. Corpses, cuts and the cook menu show that stat.
2. **Every gate boss leaves three gifts. Take one.**
3. **Stars.** A stat earns a star at 25, 35 and 50, and each star does one named thing.

### The numbers

- One stat meal a floor stays (99 chosen points a run). The lifetime cap per stat becomes `2 + floor ÷ 4`: 7 at floor 20, 12 at 40, 27 at 100, replacing the flat +15.
- **Gate gifts**, permanent and exclusive, +1 if you carry that boss's quest item:

| Boss | Gift 1 | Gift 2 | Gift 3 | Size |
|---|---|---|---|---|
| Asterion (20) | The Bull's Horn: STR | Ariadne's Clew: PER | Daedalus's Design: INT | +4 |
| Medusa (40) | Athena's Counsel: WIS | Hermes's Sandals: DEX | The Healing Vein: CON | +5 |
| Fafnir (60) | Sigurd's Arm: STR | The Dragon's Bath: CON | The Roasted Heart: WIS | +6 |
| Fenrir (80) | The Dwarves' Cunning: INT | A Cat's Footfall: DEX | The Wolf's Nose: PER | +7 |

Wisdom is offered at floors 40 and 60, exactly where the sums get hard. The quest bonus finally gives the Thread a reason to exist.

- **Where a main stat lands** (cooking plus gifts, no gear): about 17 to 21 at floor 20, 27 at 40, 37 at 60, 43 at 80, 48 at 100. Rings add up to 12 to 20 more deep down. A balanced player has about 14 / 18 / 22 / 27 / 31 in everything.

### What each stat does when it is high

| Stat | Formula change | Stars at 25 / 35 / 50 |
|---|---|---|
| WIS: more answers | none | Confusion no longer shrinks the clock / one wrong answer per chain does not end it / a second one |
| STR: each answer hits harder | none (+3% melee a point) | Overkill spills to a neighbour / a big hit staggers / a wrong first answer still lands half |
| CON: take more | 3 HP a point; up to 40% less damage taken; drain mostly stopped | Heal through poison / immune to drain / survive one killing blow a floor |
| DEX: get hit less | Dodge up to 30%, rolled after the hit roll | Free step away / a dodge loads a 1.5× counter / first attack of a fight misses |
| INT: skip the clock | 3 MP a point | MP back on kills / wands sometimes keep a charge / spells cost half |
| PER: kill it first | Ranged damage +3% a point, like STR | Traps always seen / first hit on a fresh monster 1.5× / never ambushed |

The star that matters most for your "85% but feels super" aim is **Second Thought** (WIS 35): a single slip no longer ends the chain. At tier-3 sums it lifts an 85% child's average chain from 3.8 to 5.4.

### Risks

- Wisdom and strength multiply. Fed together they are about 3.5× today's deep damage. One stat meal a floor and exclusive gifts are the brake, but **monsters must be re-tuned from floor 40 down or this trivialises the game** (section 5 shows it).
- Fountains are an uncapped source today (about 19 random stat points for a patient player). Proposed: a fountain dries when it grants a stat.

## 4. Proposal: power-ups

### What +N wisdom is worth

Damage multiplier from a temporary boost, no other buff, 85% accuracy:

| Sums | +3 | +5 | +8 | +12 |
|---|---|---|---|---|
| Tier 1 | 1.2× | 1.35× | 1.5× | 1.7× |
| Tier 3 | 1.3× | 1.5× | 1.8× | 2.2× |
| Tier 5 | 1.25× | 1.4× | 1.65× | 1.9× |

It is worth most exactly where the sums are hard. Haste multiplies on top (1.25×), and deep players often have permanent haste.

### The mechanism

- One status, **Inspired**, with a size. The clock reads `WIS + bonus`; the real stat is never touched, so nothing can leak the way the cooking bug did.
- A new boost takes the larger size and the longer time. They never add. Cap +12.
- Short: 4 to 8 attacks. A 15-turn boost would cover an entire boss fight.
- The child must see it: a gold "Inspired +7" chip, "WIS 11 +7" in the sidebar, a gold frame on the quiz clock with a notch where the normal clock would end. (The sidebar timer today does not show haste either; this fixes that.)

### Prayer as the super move

A second prayer, **Pray For Insight**, beside today's prayer (Mercy). Same theology chain, same cooldown. The cost is the heal you did not ask for. The fit is Solomon, who asked for wisdom instead of long life.

| Prayer chain | Wisdom | Attacks it lasts | Roughly |
|---|---|---|---|
| 1 | +3 | 4 | 1.3× |
| 3 | +5 | 6 | 1.5× |
| 5 | +9 | 7 | 1.9× |
| 5 at an altar | +10 | 8 | 2× |

A secret: praying for Insight at a quarter health or less gives +3 more.

### Items

- **Scrolls** (grammar question; a wrong answer burns it): five rungs from Scroll Of Recollection (+3) to Scroll Of Solomon's Dream (+10), 6 to 8 attacks. About one found per 20 floors.
- **Potions** (no quiz): Potion Of Insight (+4) from floor 6, Elixir Of Clear Sight (+8) from floor 45.
- **Break glass: Phial Of The Eleventh Hour.** Only works at a third of your health or less. +12 for three attacks, clears confusion and blindness, shields for three turns. Proposed: one placed on each gate-boss floor, so there are exactly five and bosses can be tuned around them.
- **Cooked meals** that today claim a "quiz timer bonus" become a small, long Inspired +1: meals are the slow burn, prayer is the burst.

## 5. Balance today, against your basis

"Kid model": 95% right on tier 1, 90% on tier 2, 85% from tier 3 down; flat wisdom clock; cooks, wears what drops, has done the boss quests. 120 runs per row, plus or minus 8 points.

| | Chain by band (1-19 / 21-39 / 41-59 / 61-79 / 81-99) | Reaches floor 20 | Floor 60 | Floor 100 | Wins | Gate bosses with quest |
|---|---|---|---|---|---|---|
| **Today** (WIS stays near 10) | 3.9 / 3.5 / 2.9 / 1.5 / 1.4 | 81% | 72% | 31% | 18% | 12 to 19 attacks |
| + balanced cook under the new stat rules | 4.3 / 5.0 / 4.2 / 2.2 / 2.2 | 90% | 85% | 79% | 60% | 8 to 10 attacks |
| + feeds wisdom | 4.8 / 6.1 / 4.5 / 2.7 / 2.9 | 85% | 78% | 78% | 70% | 6 to 8 attacks |
| + feeds wisdom, takes both wisdom gifts | 5.0 / 7.2 / 5.6 / 3.6 / 3.6 | 85% | 80% | 79% | 77% | 5 to 8 attacks |

What this says:

- **Today the low floors are too rough and the deep floors are a wall.** One run in five dies before floor 20, which is not "pretty easily" for a good kid. Deep down the clock fits two answers, chains sit at 1.4, and a floor asks 300+ questions.
- **Today a higher-tier weapon is often worse.** At WIS 10 the best tier-1 sword does 63 a swing, the best tier-2 does 67, and the best tier-3 does 50. A steel sword stays competitive to about floor 60.
- **With the stat design and today's monsters, the game is won.** After floor 20 almost nobody dies, and bosses fall in 5 to 10 attacks. Power-ups would push that further.

So the stat and power-up designs cannot ship without the plan below, and the plan below cannot be tuned finely without real answer times.

## 6. The balance plan

In order. Each step is measured in the simulator before the next.

1. **Time real children.** Have the game record seconds per answer by tier. An hour of play replaces my five guesses, which every number here depends on.
2. **Build the stat core:** the cut decides the stat, the new cap, CON made real, gate gifts. Build Inspired, Pray For Insight and the items. Teach the simulator to follow a stat policy and to use power-ups at bosses.
3. **Set the wisdom the game expects per band.** Proposed: a balanced cook should fit about four answers at the tier of the floor, a wisdom build six or seven. Under my guesses that is the balanced line above.
4. **Make each tier step worth taking.** Rule: at the wisdom a balanced cook has when a tier begins, the first material of the new tier out-damages the best of the old one by about 15%. That means a real jump in base damage at floors 20, 40, 60 and 80 (today it is smooth).
5. **Derive ordinary monster HP from it**, replacing both the original anchors and my re-scale: typical weapon for the floor × the chain a balanced cook reaches there × hits to kill (about 1.5 on the low floors, rising to 2.5 deep). Deep HP comes back up sharply.
6. **Ease the low floors.** Undo most of my early damage raise. Target for the kid model: under 1 death in 200 per floor on floors 1 to 10.
7. **Size bosses for a balanced cook plus one prayer burst and one consumable:** 15 to 20 attacks with the quest, punishing without it. A specialist should finish faster and feel it.
8. **Targets to tune toward** (kid model):

| Player | Reaches floor 20 | Floor 40 | Floor 60 | Floor 80 | Wins |
|---|---|---|---|---|---|
| Balanced cook | 95% | 75% | 55% | 35% | 10 to 15% |
| Committed build, uses power-ups well | 95% | 85% | 70% | 50% | 25 to 30% |
| Does not cook or prepare | 70% | 15% | 0 | 0 | 0 |

These targets are mine. Change them and the tuning follows.

## Decisions I need from you

1. **Prayer choice.** You removed the prayer picker in v2.13.0. This brings back a two-way choice, Mercy or Insight. Yes, or should Insight be automatic when a monster is in view?
2. **Stat design:** go with the three rules (cut decides the stat, gate gifts, stars)? Stars are the largest piece; wisdom and CON stars could ship first.
3. **Mind-Weary:** after Inspired ends, no new Inspired for 10 turns. It stops potion-chaining through a boss, but it is a small "no" shown to a child.
4. **Phial:** five guaranteed, one per gate boss, or a rare random treasure?
5. **Win-rate targets** in step 8.
6. **Answer-time recording:** shall I add it?
7. **Cow King's Horns, Jade Cicada, Gram** (section 2).
