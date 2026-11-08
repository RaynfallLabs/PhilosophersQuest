# Armour redesign: core AC, slot guards, a priced enchantment stable (plan)

Brandon, 2026-11-07, after the equipment review
(`EQUIPMENT_BALANCE_REVIEW_2026_11_07.md`):

> "armor is so broken... How does AD&D do this? Maybe only the core armor and
> shield matter for AC, and other items, like a helm, gloves, cloak give you
> protection from certain attack types and carry enchantments that can ONLY be
> found on those items."

> "increasing levels of enchantment and more powerful enchantments as we go
> deeper... enough different enchantments for each class that the player will
> have to choose... a ROBUST stable... the material only matters for
> rust/acid... tiers/threshold/power all balanced with correct distribution."

Rulings on revision 2: material keeps weight; tier pace proven by simulation
with standard deviations; "more powerful gear has a higher tier, complexity
and benefit set the threshold"; take powers from rings to the iconic gear,
fewer rings, still covering rising strength; the loot roll about 45 / 45 / 10;
"make the math work... prove it."

Status: **plan, revision 3: every number below comes from
`tools/balance/armor_model.py`** (section 9), run on the game's own data.
Nothing in the game is built yet. Scope: armour, shields, and the ring and
amulet powers that move. Weapons keep their own (smooth) curve.

---

## 1. Why the current model cannot be tuned

Nine slots add AC; each material tier raises all nine; the minor slots are
the cheapest AC in the game. Real runs wear AC -6 by floor 15 and -50 by
floor 100 (loot census), past the monsters' reach, so from about floor 15
every blow lands at the 30% hit floor and no armour found after it matters.

## 2. How AD&D does it

Armour type sets the base AC (2e: leather 8, chain 5, plate 3, full plate 1,
from 10), a shield improves it by one, magic adds its plus, DEX a little.
Helms, gauntlets, boots and cloaks give no AC: they carry their own magic,
found only on that kind of item. Rings of protection improve AC *and saving
throws*. Touch attacks ignore armour (3e). The plus is the depth curve; AC
stays inside about 10 to -10 while monster accuracy climbs.

## 3. The item model

| Part | Decides |
|---|---|
| **Template** (padded, chain, plate, buckler, tower, gauntlets...) | slot, weight class, base AC (body and shield), base guard (minor slots), base weight |
| **Material** | which wear can touch it (rust, acid, fire: the existing `_can_rust` / `_can_corrode` / `_can_scorch`), its **weight** (mithril light, adamantine heavy) and its name. Not AC, tier, quiz tier, cap or resistances. |
| **Enchantment** (level 1-10; tier I-V = level 1-2, 3-4 ... 9-10) | the geography quiz tier, part of the threshold, the plus on body armour and shields, a minor piece's one power |

The floor decides only *which* level is likely to be found; magnitudes are
fixed per level in data (LORE NOT FLOOR). Rust, acid and fire keep working
(`items.wear_down`): a core piece loses a point of plus, a minor piece one
level; a smith's repair gives it back.

## 4. Core AC

```
AC = 10 - body armour (base + plus) - shield (base + plus) - DEX (cap 3)
        - temporary effects (shielded, stand, parry...)
```

No ring, amulet, cloak or minor slot gives AC (section 8 shows why a +1 AC
ring cannot be balanced against any other ring).

| Body | padded 1, leather 2, studded / hide 3, chain shirt / ringmail 3, scale 4, chainmail / breastplate 5, banded / splint 6, plate 7, full plate 8 |
|---|---|
| **Shield** | buckler 1, light 1, heavy wooden 2, kite 2, tower 3 |
| **Plus** | the tier: +1 (I) to +5 (V); an Enchant Armour scroll adds one, to +5 |

Template weight classes have their own depth bells (light from floor 1, peak
1; medium from 4, peak 22; heavy from 12, peak 50), so plate is not found on
floor 3 (the first model pass showed that spike: mean AC 0.8 on floor 10).

**What a run wears** (3,000 runs, DEX 10, no starting kit; the hero keeps the
best body armour and shield found):

| Floor | 1 | 5 | 10 | 15 | 20 | 30 | 40 | 50 | 60 | 70 | 80 | 90 | 100 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Mean AC | 9.1 | 6.2 | 4.1 | 1.4 | -0.3 | -2.6 | -4.7 | -6.1 | -7.8 | -8.6 | -10.0 | -10.6 | -10.8 |
| SD across runs | 1.38 | 1.98 | 1.49 | 1.96 | 1.96 | 1.57 | 1.30 | 0.96 | 0.90 | 0.71 | 0.73 | 0.57 | 0.40 |
| p10 / p90 | 7 / 10 | 4 / 9 | 3 / 7 | -1 / 4 | -3 / 2 | -5 / 0 | -6 / -3 | -7 / -5 | -9 / -7 | -9 / -8 | -11 / -9 | -11 / -10 | -11 / -10 |

AD&D's own range (10 to about -11). The run-to-run spread never exceeds 2 AC
points (largest 1.99, floor 16) and narrows to 0.4 deep: luck moves a run by
about one blow in ten early and less later. (The census's real starting kits
make floors 1-10 better and steadier than this.)

**Monster accuracy rebaked to that line**: each monster's THAC0 = the mean AC
at its peak floor + 10 + half its current offset from its floor's median
(relative accuracy kept). Hit chance of each floor's own monsters:

| Floor | 1 | 10 | 20 | 30 | 50 | 70 | 90 | 100 |
|---|---|---|---|---|---|---|---|---|
| Against the mean hero | 55% | 54% | 50% | 56% | 56% | 57% | 56% | 56% |
| Across runs, p10 - p90 | 45-60% | 49-69% | 36-61% | 44-69% | 51-61% | 55-60% | 54-59% | 55-60% |

Today the same monsters hit 32% from floor 15 to 100 whatever is worn. With
AC bounded, the 30% floor drops to the natural 20 for ordinary monsters
(named foes keep a higher floor).

## 5. Enchantment levels through the game

Ten levels, two per tier (a lesser and a greater form: "Helm of Iron Will II",
"Helm of Greater Iron Will II"), drawn by depth bells; the plain share falls
from 40% on floor 1 to 15%. Pace, from the model (minor slots pooled):

| First floor a slot holds tier | I | II | III | IV | V |
|---|---|---|---|---|---|
| Mean (SD) | 7.1 (5.1) | 18.2 (5.1) | 36.4 (4.6) | 55.5 (4.2) | 75.3 (4.0) |
| p10 - p90 | 1-14 | 13-25 | 31-43 | 51-62 | 71-81 |

Every tier reaches every run (none missing by floor 100); 80% of runs see a
tier arrive within the same 10-12 floors.

**Upgrades** (floors 5-80; 81-100 is the tier-V and unique end game;
`armor_model.py --cadence --runs 1000 --seed 5`):

| | Five levels | **Ten levels** |
|---|---|---|
| Mean floors between upgrades of any kind | 2.48 | **1.81** |
| Longest dry stretch, mean (p90) | 8.5 (12) | **4.4 (6)** |
| Longest stretch with no AC change, mean (p90) | 16.7 (22) | 16.8 (21) |

So ten levels: an upgrade every two floors (CURVE.md principle 8 asks 2-3),
and never more than about six floors without one. Core AC steps every ~16
floors either way (the plus is the tier); the minor slots fill between. A
10-floor lag on shield tiers was tested and changed nothing.

**Choices** (enchanted options per minor slot per 10 floors, 45 / 45 / 10
loot roll):

| Floors | 1-10 | 11-20 | 21-30 | 31-40 | 41-50 | 61-70 | 91-100 |
|---|---|---|---|---|---|---|---|
| Mean (SD) | 1.45 (1.20) | 2.43 (1.56) | 2.76 (1.67) | 3.36 (1.84) | 4.07 (2.03) | 4.53 (2.13) | 5.09 (2.25) |
| P(at least 2) | 42% | 70% | 76% | 85% | 91% | 94% | 96% |

Traders' stock of enchanted minor pieces closes floors 1-20.

## 6. Equip cost

Tier (power) sets the geography quiz tier. **Complexity and benefit set the
threshold**: complexity is the template's weight class (light 1, medium 2,
heavy 3); benefit is the enchantment (body and shield: +1 at tiers III-IV, +2
at V; minor pieces: +1 at III-IV, +2 at V); a named unique +1; at most 5.

## 7. The minor slots: one guard family each, and three lanes

### 7.1 What the model showed about guards

The first two revisions' narrow guards (one rider, one delivery) were priced
and failed: Unblinking, Shatterproof, Vigil, Steadfast, Grounding and Clean
Linen could not reach a fifth of an AC point **even at 100%**, because what
each guards is too rare where it is found (snakebite poison is 0.78 AC points
of harm on tier-I floors and 0.17 on tier-III ones). A guard is bounded by the
harm its threat does, so **each slot owns one whole family**:

| Slot | Guard | Family it covers | Value at 100%, AC points, tier I..V |
|---|---|---|---|
| Head | **Iron Will** | voice and gaze attacks; mind, stun and blinding riders from any attack | 1.08 1.00 0.80 0.83 0.96 |
| Hands | **Life-Grip** | touch and grapple attacks; paralysis, holds, freezing from any attack | 1.81 1.47 1.59 1.49 1.08 |
| Arms | **Deflection** | ranged attacks and their riders | 0.60 0.93 1.11 0.93 1.15 |
| Legs | **Mailed Shins** | bites and stings; poison and disease from any attack | 2.40 2.20 1.10 0.97 1.48 |
| Feet | **Free Stride** | trample; slowing, holds, freezing from any attack; stun from blows | 0.70 0.69 0.74 0.71 1.09 |
| Cloak | **Elementward** / **Vapourward** | fire, cold, lightning, acid from every source / breath | 0.76-2.75 / 0.41-1.35 |
| Shirt | **Vigor** | poison, drain and necrotic damage; blood riders | 2.17 2.07 1.82 2.76 3.41 |

(One AC point = the harm one point of AC turns away on that floor: every
attack's hit chance down 5%. Values are weighted over the floors each tier is
found on; their spread across those floors (cv) is 0.25-0.46.)

### 7.2 The budget, and why every option in a slot is worth the same

You wear every slot, so slots do not compete; **the choice inside a slot does**.
Every option in a slot is priced to one schedule: the largest schedule rising
at least 0.05 AC points a tier that every slot's guard can reach at 80% or
less:

| Tier | I | II | III | IV | V |
|---|---|---|---|---|---|
| **Budget (AC points)** | **0.41** | **0.46** | **0.51** | **0.56** | **0.61** |

Each ladder is the rising magnitude closest to that budget (isotonic
regression on log need, so tier V is never weaker than IV); a tier where the
fit lands outside 0.67-1.5x budget is one the enchantment does not roll at:

| Ladder (tier I..V) | I | II | III | IV | V |
|---|---|---|---|---|---|
| Iron Will (shrug / turn aside) | 38% | 46% | 64% | 65% | 65% |
| Life-Grip | 23% | 31% | 32% | 37% | 57% |
| Deflection | 54% | 54% | 54% | 57% | 57% |
| Mailed Shins | 17% | 21% | 46% | 49% | 49% |
| Free Stride | 58% | 66% | 67% | 67% | 67% |
| Elementward | — | 28% | — | 28% | 57% |
| Vapourward | — | 63% | 63% | — | 80% |
| Vigor | 19% | 22% | 22% | 22% | 22% |
| **Striking** (hands: your damage) | +8% | +9% | +9% | +10% | +11% |
| **Parrying** (arms: a landed melee blow parried) | 5% | 5% | 6% | 6% | 7% |

(Lesser and greater forms of a tier take the tier's value and the halfway
point to the next.) Absolute protection rises much faster than the budget:
one AC point turns aside 2.0% of the health bar per fight on floor 86 and 0.5%
on floor 6, so the same budget protects about four times as much of a far
larger health bar deep down.

### 7.3 Same value, different risk: the real choice

Simulated fights (one hero against one monster of the floor, 12,000 fights
per variant on common random numbers; P = a fight costing over half the
health bar):

| Floor 86 (tier V) | Mean harm | SD | P(over half) | Change |
|---|---|---|---|---|
| Plain | 20.7% | 17.4% | 5.92% | |
| One more AC point | 18.7% | 16.5% | 4.54% | -1.38 +/- 0.12 |
| Striking +11% | 18.7% | 15.9% | 3.66% | -2.26 +/- 0.14 |
| Iron Will 65% | 19.1% | 15.5% | 4.02% | -1.90 +/- 0.13 |
| Free Stride 67% | 18.9% | 15.5% | 4.02% | -1.90 +/- 0.13 |
| Life-Grip 57% | 19.1% | 15.8% | 4.45% | -1.47 +/- 0.11 |
| Vigor 22% | 19.2% | 16.5% | 4.72% | -1.19 +/- 0.10 |
| Mailed Shins 49% | 19.6% | 16.7% | 5.11% | -0.81 +/- 0.08 |
| Deflection 57% | 19.5% | 17.5% | 5.76% | -0.16 +/- 0.04 |

At the same average value, guards against riders that take turns away (Iron
Will, Free Stride) halve the *bad fights* far more than damage guards do,
and Striking cuts both by ending fights sooner. That is the choice the player
makes on every slot: safety against the worst fight, or a lower average, or
speed. The order shifts with the monsters of each depth (on floor 46
Life-Grip leads the guards, on floor 6 Iron Will and Life-Grip tie), but the
pattern holds on every floor tested: the turn-taking riders are insurance,
the damage guards trim the average.

### 7.4 The three lanes

Every slot offers its guard plus at least one option from the other lanes,
each priced to the same budget:
- **Guard**: the slot's family (above).
- **Craft**: help with the quiz the slot's work belongs to, in its own
  currency. A craft enchantment cuts its subject's failed quizzes by the same
  fraction a guard of its tier cuts bad fights (the fight model: 15-20%), and
  it does it **without chance** (the game's rule: performance decides):
  the first wrong answer of every Nth quiz on that subject is forgiven, N from
  the game's own per-subject accuracy (`J` telemetry): about every 5th quiz at
  tier I to every 3rd at tier V. Head: the Scholar (philosophy), the Reader
  (grammar), the Adept (science); hands: the Locksmith (economics), the Cook,
  the Hunter (animal); arms: Swift Strokes (the combat clock, +2 to +10 s);
  legs: the Kneeler (theology); feet: the Wanderer (geography).
- **Might and Way**: Striking and Parrying (priced above), and the iconic
  powers that move from rings (section 8): Telepathy, Night Eyes and True
  Sight (head), Ogre Power and Dexterity (hands), Speed and Levitation
  (feet), Displacement and Shrouding (cloak), Alertness (head), Elvenkind
  (feet). Those that change fights are priced by the tool when built; the
  rest (senses, movement) are set by hand against the budget.

## 8. Rings and amulets after ruling 4

Priced on the same scale (value at 100%, tier I..V):

| Ring | I | II | III | IV | V |
|---|---|---|---|---|---|
| (a +1 AC ring, for comparison) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Protection as saving throws (every rider, any attack) | 2.47 | 2.25 | 2.02 | 2.01 | 2.19 |
| Spell Turning (magic, shadow, psionic damage) | 1.29 | 0.95 | 0.79 | 0.98 | 1.46 |

A +1 AC ring is a full AC point (it touches every attack), more than any
other ring can reach at 90%, so **no ring gives AC**: the ring of Protection is
AD&D's other half, a saving throw against every rider, laddered to the ring
budget. The powers armour now owns leave the rings: elemental resistance
(cloak), free action (hands and feet), mind protection (head), and the
iconic ones of section 7.4 (telepathy, sight, haste, levitation,
displacement, strength, dexterity, warning). What stays a ring or an amulet:
Protection (saves), Spell Turning, Regeneration, Invisibility, Sustenance,
Wizardry; amulets of Life Saving and the mental stats (WIS, INT, CON). Fewer
kinds (the 89 common rings and amulets become about a dozen kinds), each
tiered I-V on the same bells, so a ring found deep is stronger. The 79 named
and plot uniques keep their stories; a power that moved is kept only where the
lore makes it that item's own.

## 9. The proof: method, checks and limits

`python tools/balance/armor_model.py --runs 3000 --census <census file>`
(about two minutes; `--sensitivity` adds the rider-cost sweep; `--cadence`
compares five and ten levels). The census file is
`python tools/balance/loot_census.py --runs 8 --floors 1-100 > file`.

- **Inputs**: the game's own spawn pool per floor (`dungeon._build_spawn_pool`),
  every monster's attacks, damage dice, riders, durations and THAC0;
  `floor_curve.HEALTH_BAR` and `ONE_ATTACK`; the templates; a loot census
  (8 runs, floors 1-100) for gear and rings per floor, found at 90%.
- **Runs**: Poisson finds per floor, the loot split, a uniform slot, a
  template by weight-class bell, plain or a level by the bells.
- **Pricing**: expected harm per monster turn (damage plus rider cost, rider
  cost = turns lost x the floor's harm per turn, or damage over time); an
  enchantment's value is the harm it removes over the harm one AC point
  removes. Fights: one-on-one to the death of one, hero dealing `ONE_ATTACK`
  per turn he can act, one random monster attack per turn.
- **Statistics**: means with standard deviations and p10/p50/p90 across runs;
  weighted mean and cv over each tier's floors; paired differences with
  standard errors on common random numbers.
- **Sensitivity**: with every rider cost halved or raised by half, the budget
  scales (tier V 0.41 / 0.61 / 0.81) but its shape, the binding slots, the
  availability pattern and the ordering of ladders hold (Iron Will at V: 61% /
  65% / 71%). The judgement calls set the size, not the design; telemetry
  from play can refine them and the tool regenerates every ladder.
- **Limits**: no packs (one monster at a time), no uniques, no starting kit
  (both improve the early floors), no monster specials beyond attacks and
  riders, attack delivery read from names until the `delivery` field is
  written into `monsters.json` (phase 3). The build adds tests that hold the
  census and the tool to these figures.

## 10. Build order (each phase ends playable)

1. **Item model and core AC**: template / material / enchantment; body and
   shield base AC and plus; weight-class bells; thresholds and quiz tier;
   monster accuracy rebake to the line in section 4; the hit floor; no AC
   from rings. Minor slots keep a small temporary AC until phase 2.
2. **Guards**: `delivery` on every attack; the seven families; the touch
   rule (touch attacks roll against AC without body armour and shield).
3. **The enchantment engine**: ten levels, bells, plain share, roll, naming,
   identification, cursed (one level lower, welded) and blessed (one level
   higher), wear and repair.
4. **The lanes**: craft (forgiveness every Nth quiz), Striking, Parrying,
   and the moved iconic powers.
5. **Rings and amulets**: the dozen kinds, tiered; Protection as saves; the
   79 uniques reviewed.
6. **Uniques**: the 56 minor-slot and all body and shield uniques on the
   ladder, signature powers kept.
7. **Distribution**: the 45 / 45 / 10 roll, chests, traders; the census and
   model tests.
8. **Saves, text sweep, docs** (saved pieces recomposed on load).

Play-test after 1 (AC on floors 1-20), 2 (does a helm feel worth wearing
against a wailing spirit?), and 4 (are the choices real?). A 3.4 release on
its own branch once 3.3.2 ships, one phase a session.

## 11. Left open

Nothing blocks phase 1. Two things the model cannot decide: the rider costs
(section 9: set the size, not the shape; refine from play), and the
hand-set lanes (senses, movement), which are judged against the budget.
