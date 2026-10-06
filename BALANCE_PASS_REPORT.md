# Balance pass: is the game hard for a player who answers most questions right?

> **Superseded in part (2026-10-05, later).** The tier seconds described below were removed, the basis changed to a child who is good at simple sums, and monsters and bosses were re-sized again. See `DESIGN_AND_BALANCE_PLAN.md`, section 0, for the current state.

Date: 2026-10-05. Everything here is committed locally, not pushed, and **not play-tested**. The numbers come from a simulator, not from a person at the keyboard.

## The short version

Before this pass the game was easy on offence and a coin-flip on defence, for a reason nobody had seen: **from about floor 12, combat stopped asking questions.** Tier-1 maths has 488 questions; once a player had answered them all, every attack landed at chain 5 automatically, and one attack killed 96 to 100 percent of monsters for the rest of the run. Meanwhile the player still had about 35 HP on floor 39, so deaths were single unlucky hits, not decisions.

Now every attack asks a question, the sums get harder with depth, HP grows with cooking the way the design document always said it should, and monsters are tuned against that.

| Simulated player (cooks, wears what drops, has done the boss quests) | Reaches floor 20 | Reaches floor 40 | Reaches floor 100 | Wins |
|---|---|---|---|---|
| 95% right, finds a healing spell | 88% | 83% | 76% | about 50 to 60% |
| 95% right, no healing spell | 86% | 69% | 30% | 20% |
| 90% right, finds a healing spell | 74% | 64% | 50% | 24% |
| 90% right, no healing spell | 71% | 50% | 11% | 7% |
| 85% right, finds a healing spell | 57% | 38% | 10% | 4% |
| 85% right, no healing spell | 50% | 19% | 0% | 0% |
| 75% right | 16% | 2% | 0% | 0% |
| Any accuracy, but does not cook or prepare | 0% | 0% | 0% | 0% |

200 runs per row; treat each figure as plus or minus 7 points. "Accuracy" is the tier-1 figure; the simulator lowers it 3 points per maths tier, which is generous to a real child on tier-5 sums against a clock, so real results deep down will be harder than these.

**My read:** it is hard for the 85 and 90 percent player, which is what you asked for. The near-perfect player with a healing spell still wins about half the time, and that is the one place I would tighten after you have played it (see "If it is still too easy").

## What the simulator is

`tools/balance/difficulty_sim.py` plays 100-floor runs using the game's real floor generator, monsters, attack rolls, player class, loot and cooking caps. It models the quiz (answer speed and accuracy against the shared clock) and the player's decisions. It does not model the map, wands, scrolls, ranged weapons, pets, quirks or monster summons, so it is a measuring stick, not a prediction.

```bash
python tools/balance/difficulty_sim.py --trials 200
```

## What changed, and why

### 1. Combat asks questions again

| Before | Now |
|---|---|
| A cleared maths tier auto-landed chain 5 with no question. | In combat a cleared tier's questions simply come round again. Every other subject keeps its auto-pass. |
| Every common weapon on every floor asked tier-1 sums. The line that sets it was missing (armor and shields had it). | A weapon asks the maths of its depth band: tier 1 to floor 19, tier 2 to 39, tier 3 to 59, tier 4 to 79, tier 5 below. |
| One clock of WIS seconds for any sum. | Harder sums add time: +2, +5, +8, +10 seconds for tiers 2 to 5. |

I first tried moving the fight up a tier whenever one was cleared. The simulator showed it asked tier 3 and 4 sums on floors 21 to 39, well ahead of the design, so I dropped it.

### 2. Hit points come from cooking, as designed

The design document sets the cooking cap at 4 max HP per floor reached (80 by floor 20, 400 by floor 100). The live table had drifted to zero through floor 20 and 139 at floor 100, and ordinary meals gave no max HP at all.

- The cap is now 4 per floor, and it is a real cap (the old one never stopped anything).
- Every properly cooked meal adds 2 max HP, up to 5 a floor. A cook who keeps at it tracks the cap; one who does not falls behind.
- Simulated max HP for a diligent cook: about 65 on floors 1 to 19, 135 on 21 to 39, 200 on 41 to 59, 280 on 61 to 79, 375 on 81 to 99.

### 3. Monsters

- **132 monsters patched** from the spawn audit: to-hit brought back to the design curve on 94 kinds, mini-bosses attack twice a turn, 18 guardians and statues now ambush instead of standing idle.
- **Armor turns blows but nothing is untouchable.** A miss still connects 30% of the time (40% for named foes). It was 5%, and a full kit made the deep floors safer than the middle ones.
- **29 kinds of plant, mold, ooze and statue never attacked at all.** A bug: fixed.
- **Monster HP and damage re-scaled by depth**, all 480-odd ordinary monsters: tougher and harder-hitting early (floor-1 monsters do about 4 a hit, up from 1.5), lighter HP deep, where tier-5 sums already slow every kill. Damage levels off at about 18 to 20 a hit from floor 60.
- **No ordinary attack is more than 2.6 times a normal hit for its floor.** The worst had been 3.4 times: one Curse Bolt on floor 30 was two thirds of a health bar.
- **Drain** used to cost a point of CON, and so max HP, on every hit with no save. It now gets a saving throw and takes at most 2 a floor.
- **Poison, bleeding and burning** cost 2% of max HP a turn. They were a flat 1 at any depth.
- **Fear** can be saved against and gives the usual grace window. It was an unbreakable lock.
- **Maze floors** (10, 30, 50, 70, 90) started with one to six monsters; they now start with 7 or more, rising with depth.
- **Wandering monsters** refill a floor as you clear it. They never arrived before, because the cap was below every floor's starting count.

### 4. Bosses

| Boss | HP before | HP now | Simulated, 85% player, with quest | Without quest |
|---|---|---|---|---|
| Asterion | 600 | 1,500 | 14 attacks, 1% die | 14 attacks, 0 to 3% die |
| Medusa | 1,100 | 2,400 | 15 attacks, 3% die | 49% die |
| Fafnir | 2,000 | 4,000 | 13 attacks, 2% die | 61 attacks, 50% die |
| Fenrir | 2,420 | 5,200 | 15 attacks, 0% die | 40% die |
| Abaddon | 4,280 | 6,000 | 10 attacks, 86% die | 88% die |

Before, every gate boss died in two to nine attacks. Their damage is up 60 to 90 percent as well, except Abaddon, whose damage came down (he now faces a player with three times the HP). Mini-bosses carry three to five times an ordinary monster's HP; the deep legends (Tiamat, Surtur, Asmodeus and the rest) were cut back after the first pass made them near-certain death. Named foes no longer bleed out: bleed took 267 a turn off Abaddon.

**Asterion is still too gentle** in the simulator (0 to 3% deaths either way), and the Thread still buys little. That one wants your eyes.

### 5. Healing and rest

- Waiting now makes you hungry, like walking. Resting had been free.
- Natural healing is 2% of max HP a tick instead of a flat 1.
- Meditation gives 1 MP every 8 waits, not every wait. Three waits used to buy a healing spell, for ever.
- Healing potions restore at least 20% (or 40% for extra healing) of max HP, so they stay worth drinking.
- The `regenerating` status heals 1 HP every 3 turns, not every turn.

### 6. Items

- Cold, lightning, poison and magic resistance are now **half damage**, like fire. (Poison resistance still stops you being poisoned at all; drain resistance is still complete.)
- Hide of the Nemean Lion halves physical blows instead of reducing them to 1.
- Displacement makes 15% of attacks miss, down from 30%.
- Scrolls of power give 1 stat (2 at tier 5), down from 3, 5 or 6, and are a fifth as common. Time-stop scrolls are shorter and a fifth as common.
- The three permanent-stat foods are a tenth as common.
- Permanent haste rings and amulets start at floor 50, not 26.
- 62 unique armors and shields raised to at least match a good common piece from their floor.

Fixed in passing: a crash in floor generation on one-room maze floors.

## What I did not do

- **Wand damage.** The audit's raise was sized against chain-5 hits, which nobody lands deep down any more. Left alone.
- **Regeneration rings** stay where they spawn, since regeneration itself is now a third as strong.
- **Haste** still gives two actions per monster action.
- **Stat food** does not yet count against the per-floor stat cap.
- **Old saves** keep tier-1 weapons already generated. New weapons follow the new rule.

## If it is still too easy (or too hard)

All of these are single named values.

| To change | Where |
|---|---|
| Seconds added per maths tier | `MATH_TIER_SECONDS` in `src/quiz_engine.py` |
| Max HP per meal, cap per floor | `COOK_BASE_MAX_HP`, `COOKING_SOFTCAP_PER_FLOOR` in `src/player.py` |
| How often a missed blow lands anyway | `MIN_HIT_ORDINARY`, `MIN_HIT_NAMED` in `src/monster.py` |
| Natural healing, meditation, wandering caps | `src/floor_curve.py` |
| Boss HP | `GATE_BOSS_HP` in `tools/balance/respawn_by_hp.py`, then run it with `--write` |
| Damage or HP of all ordinary monsters | try it first with `--knobs mon_dmg=1.2` in the simulator |

The one I would reach for first, if the best players still stroll: raise Abaddon's damage and the gate bosses' damage with the quest, since ordinary floors barely scratch a 95% answerer.

## Play-test list

None of this is proven until you play it. In rough order of how soon you will meet it:

1. **Floor 1 to 3.** Monsters hit for about 4 now. Does the opening feel dangerous but fair with 30 HP?
2. **Cook a meal.** You should see "Good food builds you up. (+2 max HP)", up to 5 a floor.
3. **Wait with `.`** Hunger should tick; "You meditate..." most turns and "+1 MP" every eighth.
4. **Stand next to a mold or a vine.** It should attack.
5. **Around floor 12**, once tier-1 maths is cleared: the message should say the sums come round again, and the next attack should still ask a question.
6. **Pick up a weapon on floor 20 or deeper.** It should ask tier-2 sums and give 2 more seconds.
7. **Asterion.** 1,500 HP. Is he a fight now, and is the Thread worth having?
8. **A maze floor (10 or 30).** It should not be empty.
9. **Drink a healing potion at high max HP.** It should restore at least a fifth.

The deep floors, the other bosses, drain, and the resistance changes are covered by tests rather than play (1,978 passing), which shows the rules do what they say, not that they feel right.
