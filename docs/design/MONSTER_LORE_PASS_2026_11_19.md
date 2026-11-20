# The monster lore pass (2026-11-19): every ordinary monster's numbers from its own lore

## Why this pass exists

Brandon finds 3.5.4 too easy. He is steamrolling everything a few floors in: on floors 6-7 "they don't hit hard enough to be scary". His ruling of 2026-11-19, the third time he has had to make it:

> "Your fix SUCKS AGAIN, because you started using smoothing multipliers to hit a target ... NEVER DO THIS ... Fix the data at the source, create a balanced game. If 10-19 are too easy, then look at the monsters and gear and edit it."

He also wants "the more diverse and unique our monsters are, the better".

**What the data looks like today.** Earlier balance passes seated every monster on a floor curve, which ironed the monsters flat:
- Every floor-1 kind bites for 1d2, with 6d6 or 2d10+6 HP.
- Every floor-16 kind (troll, xorn, specter, banshee, two-headed ogre) hits for 1d8+2, with 16d10+62 HP.
- `py tools/balance/monster_bands.py` shows a landed blow is about 5% of the floor's hero's health on every floor from 1 to 99. One monster turn costs about 3%, flat.
- On floors 4-22 the median monster has only 56-73% of the HP the hero's weapons were tuned for (floor_curve.target_hp). So most of them die to the first maths chain and never swing. That is the 10-19 steamroll.

**The job:** re-author each monster's combat numbers from what it IS:
- its body size and build;
- its natural weapons, or the weapon it carries;
- its skill and ferocity;
- its speed;
- its signature power.

The numbers must stay readable against the hero who meets it on its home floor. The curve then comes out of a population of creatures that each differ.

**What is banned:** any formula or blanket multiplier applied across monsters ("x1.8 for floors 6-12", "set every floor-10 kind to 2d6"). Each monster gets its own numbers and a one-line lore reason. Two kinds on one floor should rarely share a damage line.

## The hero you are writing against

These are the simulated full-system hero's AC and max HP per floor (3.5.4, 200 runs). AC is descending, 10 bare. A monster hits on d20 >= thac0 - AC.

| floor | 1 | 3 | 5 | 7 | 10 | 13 | 16 | 20 | 25 | 30 | 40 | 50 | 60 | 70 | 80 | 90 | 99 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AC | 9.5 | 9.6 | 8.8 | 7.9 | 6.9 | 5.7 | 5.3 | 3.5 | 2.2 | 1.1 | -2.2 | -3.9 | -6.7 | -8.4 | -10.0 | -10.3 | -10.8 |
| max HP | 30 | 38 | 47 | 58 | 73 | 88 | 103 | 124 | 149 | 173 | 227 | 298 | 350 | 424 | 500 | 562 | 627 |

A slow kid (half to 0.7x Brandon's answer speed) meets the same monsters with about the same gear. Fights last longer for the kid, so the kid takes more swings.

## How a monster's numbers work in the engine

- `attacks`: a list. Each turn an ordinary monster picks ONE at random. A ranged monster at range prefers its ranged attacks, and a dragon keeps its breath for the approach.
  - `multi_attack_count: N` makes it fire its first N attacks every turn: a full routine such as claw, claw, bite.
  - Use a routine only where the anatomy and lore really make one: big cats, bears, owlbears, trolls, hydras.
- A rider (`effect`, `effect_chance`, `effect_duration`) is the creature's power:
  - Hard control (paralyzed, sleeping, stunned, frozen, immobilized, petrifying, feared) is negated by a save. Its duration is clamped by status_effects.CONTROL_CAP (paralysis 4, sleep 5, stun 3).
  - Soft control (confused, charmed, slowed) is halved by a save.
  - Damage-over-time riders (poisoned, burning, bleeding) tick 2% of the hero's max HP every turn (`status_effects.dot_tick`). Keep them 3-8 turns, and up to 12 only for a legendary venom.
  - `diseased` costs no health a turn (AI-1, Grave Rot, `src/grave_rot.py`): while it lasts the hero's rest does not mend him and every heal does half, and now and then it saps a point of STR or CON. Write its `effect_duration` 4-8 like any rider; a kind whose lore makes the sickness linger (mummy rot, a plague-bringer) also sets `disease_linger` (its turns are multiplied by it, at most 60 in all).
  - `draining` is a ring's curse (1% of max HP on about a sixth of turns), not a monster's rider: give a draining creature a `type: "drain"` attack (or `drains_life: true` on a necrotic touch), which lowers the hero's max HP by half of a landed blow (Life Drained, `src/life_drain.py`).
  - Non-damaging debuffs (weakened, slowed, blinded, hallucinating, silenced) can last 8-30 turns. Brandon's ask is that a landed power lasts into the next fight.
- The hero's head armour, family wards and counters (wax, mirror shield, cold iron) shrug off a share of riders. Powers can be strong.
- `hp`: dice. The hero's weapons are calibrated so that a balance child kills a monster of floor_curve.target_hp(floor) HP in about 1.4 maths chains.
- `speed`: 12 is a man. Speed 14 or more gets in first.

## What to write for each monster in your list

For each id, read its current entry: name, lore text, family, tags, size (data/monster_sizes.json), attacks, ai_pattern, peak_floor, spread and min_level. Then decide what it IS and write its numbers.

### 1. Damage dice per attack

The size of a landed blow, as a share of the health of the hero at the monster's `peak_floor` (the table above), should match its role:

| role (from lore) | one landed blow | notes |
|---|---|---|
| swarm, tiny vermin (rats, bats, rot grubs, pixies) | 1-4% | numbers and packs are their danger |
| skirmisher, thief, small fey, imp | 3-7% | higher to-hit, riders, hit and run |
| soldier, medium beast, armed man, ghoul | 5-10% | |
| brute, large beast or giant-kin (ogre, bear, troll, minotaur) | 9-16% | often slow; worse to-hit is fine |
| apex of its floor (huge, legendary predator) | 12-22% | |
| caster, archer, gazer, singer | 3-8% damage | the rider is the point |
| ooze, plant, construct, mindless dead | low to middling | toughness, riders or grip |

- One monster TURN (all of a routine, before the hit roll) must stay at or under 25% of that hero's health.
- Use real dice shapes that say what the weapon is: a club is 2d6+3, a dagger 1d4+2, a great maul 3d6+6, a bite 1d8+2, a sting 1d3 plus venom. Do not flatten.

### 2. thac0

Its skill. Today's values follow the hero's AC down the floors, so keep each within about 2 of today's:
- lower it for trained fighters, archers and hunting predators;
- raise it for clumsy, mindless or blind things.

`thac0_lore` is an older lore estimate you may consult.

### 3. HP dice

From size and toughness. Around the floor's anchor the spread should be wide:
- tiny, frail or swarm: 0.4-0.7 of floor_curve.target_hp(peak_floor);
- medium: 0.8-1.1;
- large or tough (undead, constructs, trolls, oozes): 1.1-1.6;
- huge: 1.5-2.2.

The band's weighted median must land at about 0.95-1.05 of the anchor (monster_bands.py prints it). On floors 4-22 that means most kinds gain HP: they are below the weapon curve today.

### 4. speed

Only where lore says so: wolves, cats and wasps are fast; zombies, oozes and golems are slow. Most stay as they are.

### 5. multi_attack_count

Sparingly, as above.

### 6. Riders

Riders are the creature's power: set effect_chance and effect_duration by lore, within the duration rules above. You may add a rider to an existing attack where the lore has one and the data lacks it. Do not strip a rider the lore supports.

### 7. Pack fields

Set `pack: true` (and `pack_size: [min, max]`, the whole pack) only where lore says the creature hunts, swarms or raids in groups:
- wolves, rats, jackals, hyenas, ghouls, harpies, hounds;
- goblins, kobolds, gnolls, bats, ravens, stirges, locusts.

A separate session builds pack tactics on these flags. Packs on floors 1-6 stay small (2-3 in all).

### 8. `opener` (NEW field; a separate session implements it next)

It names the power a creature opens with, before the hero can strike. Write it as:

```json
"opener": {"attack": "<exact name of one of its existing attacks>", "range": N}
```

- **range 1** means a pounce, lunge, charge or leap: on the turn it first closes to the hero it strikes with that attack at once. Use it only for lore creatures that charge or pounce: wolves lunge, big cats pounce, the minotaur gores, ghouls leap, a boar charges.
- **range 2-7** means it opens from a distance with that attack when the hero is in its sight. The attack must be a range, gaze, voice or breath delivery: the archer's first volley, the basilisk's gaze, the harpy's song, the banshee's wail, a drake's breath.
- Give an opener only where the lore has a signature opening move, somewhere around a third to a half of kinds. A plain rat or zombie has none.
- An opener range should not exceed what the creature can see. The hero sees about 5 tiles today and will carry torches soon. Archers at 5-7, gazes and voices 3-5, breath 3-5.

### 9. peak_floor, min_level and spread

Move these only when the creature's LORE threat does not belong where it sits, so it is moved rather than nerfed or puffed up. Keep moves small. Never move a kind across a 20-floor tier boundary (1-20, 21-40, 41-60, 61-80, 81-100) without listing it under `_tier_moves` with the reason: harvest tiers, dishes and the tier census follow those boundaries.

## What you must NOT touch

- **Text and lore:** name, lore, family, tags, resistances, weaknesses, shrugs_off, status_immune, harvest_tier, treasure, symbol, color, pronoun.
- **Attack names:** never rename or remove an existing attack. tells.json, enemy_lore.json, combat lines and family techniques refer to attacks by name.
- **Attack keys:** keep every key an attack already has (steal, quip, piercing, ranged, type, delivery). You may add a new attack only where lore demands it, such as a goblin's sling. Give it name, damage, type and delivery, plus `ranged: true` for a missile.
- **Out of scope:** named foes (is_boss, is_mini_boss, is_seal_demon) and kinds not in your list. Easter-egg kinds are already left out of the lists.

## How to work

- Write proposals into a scratch JSON file (the 2026-11-19 pass used `_monster_lore_2026_11_19/<band>.json`, untracked), as:

```json
{
  "_why": {"giant_rat": "terrier-sized rodent: weak bite, comes in packs; HP small"},
  "_tier_moves": {},
  "giant_rat": {"hp": "3d6+2", "attacks": [ ...the full list, every key kept... ], "pack": true, "pack_size": [2, 4]}
}
```

  - Include only the fields you change, but always the FULL `attacks` list when you change any attack.
  - Every id in your list gets a `_why` line, even one you leave as it is ("kept: ...").
- Save as you go: work through your list in chunks of about 20 and write the file after each chunk, so a crash loses little.
- Check your band as you go:

```
py tools/balance/monster_bands.py --over _monster_lore_2026_11_19/<your band>.json --floors <your floors> --kinds 12
```

- **The band targets the checker should show when you are done.** These are the spawn-weighted means; the individual kinds must differ widely around them:
  - **hp_med/anchor:** 0.95-1.05 on every floor.
  - **turn%:** about 3.5-4.5 on floors 1-3, 4.5-5.5 on floors 4-9, 5-6.5 on floors 10-30, and 5-6.5 from 31 down. Today it is a flat 3.
  - **p10-p90:** wide. The 90th percentile kind should hurt at least 3-4 times the 10th.
  - **opener:** about 30-50%.

  Openers and packs, coming in the next sessions, add threat on top. That is why the turn% targets are moderate.
- If a band misses a target, fix it by re-judging specific monsters (which ones are underwritten for what they are?). Never move all of them by a common factor. If you cannot reach a target honestly by lore, stop and say so in your report. Do not force it.
- Do NOT edit data/monsters.json or any code. The session that started you applies the proposals.
- Do NOT spawn sub-agents.

## Your report

Keep it short:
- the band table before and after (paste the checker's output);
- the ten biggest changes and why;
- every `_tier_moves` entry;
- anything that looked wrong in the data (lore that contradicts the numbers, broken attacks, missing riders).
