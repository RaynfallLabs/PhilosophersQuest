# Play-test list: the rebalance, after the bug bash

Date: 2026-10-08, after two review rounds and the armor and art pass. Nothing here has been played. 2,137 tests pass; they prove the rules do what they say, not that the game feels right.

Run from source: `python src/main.py`

## The rule this build follows

**Lore, not floor.** Nothing multiplies damage or health by the dungeon floor while you play, and no weapon's maths tier ever changes. A thing's power is a real number in its data, or a stated share of what it acts on (a trap takes a share of your health; a hero's scream takes a share of each monster's).

Removed on 2026-10-07 because they broke that rule: the early-floor damage reduction, hero weapons that grew with depth, and a depth multiplier that had been sitting on 27 fixed numbers since v3.0.0.

## Reachable in the first twenty minutes

| What to do | What should happen |
|---|---|
| Look at the sidebar | It says **Clock Ns**. Haste or a prayer to Michael: it rises and turns gold. Confused or stunned: it falls and turns red. |
| Open the character sheet | Two new readouts, **Dodge** and **Tough**. A starting character with Constitution 10 has 30 health; each point above or below is 3. |
| Look at any weapon's card | It starts with **Tier N Sums**. That tier never changes. |
| Open the Recipes menu on a prime cut | The preview says **Feeds Strength** (or whichever stat the meat carries). No number is promised. |
| Cook it properly | "You feel it doing you good. (Strength: 1 of 2 meals toward +1)". Cook a cut of the same stat on the next floor: "Your Strength increases by 1!". This did not work at all before the bug bash. |
| Stand still hurt (hold `.`) | Health climbs to 60% and stops. |
| Meditate (hold `.` with mana missing) | After half a mana bar: "This floor's quiet is spent for good. Another floor has its own." Going down and back up does not refill it. |
| Fight on floors 1 to 13 | Monsters miss noticeably more often than before (their chance to hit is lower in the data). Their hits are full size. |
| Read a teleport scroll (Blink, Teleportation, Recall) | It works. It crashed every time before. |
| Step on a polymorph trap with something in your pack | An item changes. It crashed every time before. |
| Hatch a pet | Its bite and health come from a table by its own level (`data/pet_growth.json`). |
| Kill Arachne (mini-boss, around floor 9) | She drops Arachne's Silk Cloak. Identify it and open its card: under Special Abilities it says what it does (a monster that strikes you hand to hand is slowed for 3 turns). |
| Find Martin's Half Cloak, the Cestus of Polydeuces, the Bracers of Atalanta or Becket's Hair Shirt (floors 5 to 20) | Each has an icon, a story, and a line on its card such as **Toughness +3%** or **Dodge +4%**. The character sheet's Dodge and Tough readouts rise by that much when it is worn. |
| Put on any unidentified armor | The log says "You equip the pair of worn sandals", not "the A Pair of Worn Sandals". |
| Put a named piece on, then take it off (Cloth of Penelope on floor 10 is the easy one) | Its status goes with it. Regenerating, Hasted, Blinded and Displacement used to stay for the rest of the run. |
| Walk the first floors | No monster shows as a letter: all 71 that had no art have a sprite now (bandits, cultists, kobolds, gnolls, orcs and goblins are the early ones). |

## Hero builds

- **Achilles** starts with Achilles' Spear: base 125, tier 3 sums. **Leonidas**: the Dory of Leonidas, base 30, tier 2. **Prometheus**: the Torch, base 137, tier 3. **Geralt**: silver blade 30, tier 2. **Ciri**: Zireael 74, tier 3. **Ash Williams**: Boomstick 74 and Chainsaw 69, tier 3.
- These are meant to be unbalanced. A floor-1 Achilles who gets one tier-3 answer in six seconds kills anything in sight. Achilles' Spear, Romulus' Spear and the Torch can also be found as loot, around floors 55, 28 and 58.
- **Dad**: the punch is base 9999 at tier 1 and the chain is cubed. Summoned Dad hits for 999,999.
- **Sherlock, Tesla, Joan and Musashi can be typed now** (the name box stopped at 30 characters). Tesla is typed `nikola tesla`.
- Hero names show in Title Case. Empower and Ciri's Charge last until your next strike.
- Those numbers are my reading of each legend. Tell me which ones are wrong.

## Asterion (floor 20)

- He should be a wall for a character who has cooked little and has no Thread, and a fair fight otherwise. Measured: he beats about half the casual players who reach him.
- Every blow he swings is 2% heavier than the last, and the log says so in his own line ("Asterion's breath comes harder...").
- Leave the fight for 25 turns, or leave the floor and come back: he has mended. He no longer mends while he is still swinging at you or while you are hitting him with spells.
- When he dies a panel opens with three gifts. Press 1, 2 or 3. Escape does nothing on purpose. Nobody who died that turn is offered it.

## Cannot be play-tested in reasonable time (covered by tests and the simulator)

The other three gift panels; Fenrir and the Sandal; Abaddon; Death's scythe on the climb out; trait points held and paid as you descend; lucky stat points running out; pets and summoned allies at depth.

## The climb out: measured, changed, not played

Death now comes up the stair a few turns behind you instead of waiting on your path. Keep moving and he rarely touches you; every turn you stand still in the last fifty floors costs about one blow, at 8% of your full health each. Floors you cleared on the way down are safe to cross; floors you left full are not. The old chase was measured by simulation on real maps; the changed one has not been re-measured or played.

## What the numbers say now

For a child who is 95% right on simple sums, 480 simulated runs each (a "win" is Abaddon dead):

| Player | Reaches floor 20 | Wins | Target |
|---|---|---|---|
| Casual: cooks a little, skips quests | 86% (about half then beat Asterion) | 0 | 90%, about half |
| Prepared: cooks, does the quests | 99% | 26% | 25 to 30% |
| Committed stat build | 100% | 38% | |
| Committed build with a pet | 99% | 52% | 40 to 50% |
| Committed, found the four secrets | 99% | 40% | |
| Everything: build, secrets, pet, magic | 99% | 55% | 60 to 70% |
| Rests as long as it takes | 98% | 40% | within 15 of prepared |

Each figure carries about four points of noise.

Full account: `REBALANCE_MASTER_PLAN.md`. The section "Correction, 2026-10-07" at the top lists what the bug bash found and what was undone.
