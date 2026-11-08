# Armour redesign: core AC, slot wards, a tiered enchantment stable (plan)

Brandon, 2026-11-07, after the equipment review
(`EQUIPMENT_BALANCE_REVIEW_2026_11_07.md`):

> "armor is so broken... How does AD&D do this? Maybe only the core armor and
> shield matter for AC, and other items, like a helm, gloves, cloak give you
> protection from certain attack types and carry enchantments that can ONLY be
> found on those items... let's plan."

> "we need to make sure that there are increasing levels of enchantment and
> more powerful enchantments as we go deeper... And enough different
> enchantments for each class that the player will have to choose what's
> best: something that locks mind control or something that increases quiz
> timer? blocks poison or adds damage (gloves)? We need a ROBUST stable here,
> and the material only matters for rust/acid. Double check the plan, make
> sure we're doing enough with variation and the tiers/threshold/power are all
> balanced and have correct distribution through the game."

Status: **plan, revision 2, awaiting rulings** (section 10). Nothing is
built. Scope: armour and shields. Weapons keep their own material curve (it is
smooth; see the review, section 3D). Rings, amulets and belts keep theirs.

---

## 1. Why the current model cannot be tuned

Nine slots add AC, each new material tier raises all nine at once, and the
minor slots are the cheapest AC in the game (one question each). A real run
wears AC -6 by floor 15 and -50 by floor 100 (loot census). Monster accuracy
climbs too (median THAC0 19 on floors 1-10, -15 on 91-100) but cannot keep
up, so from about floor 15 every blow is decided by the 30% hit floor and no
armour found after that changes anything.

## 2. How AD&D does it

- **Armour type sets the base AC** (2e: leather 8, chain 5, plate 3, full
  plate 1, from an unarmoured 10); **a shield improves it by one**; magic
  armour and shields add their plus; DEX adds a little. That is nearly all
  of AC.
- **Other worn gear gives no AC.** Helms, gauntlets, boots and cloaks are
  where the special magic lives, each kind with its own family (helms of
  telepathy, gauntlets of ogre power, boots of elvenkind, cloaks of
  displacement), found only on that kind of item.
- **Protection items are the narrow exception** (ring or cloak of
  protection; bracers of defense help only a wearer with no armour). 3e made
  it a rule that bonuses of one type do not stack.
- **Touch attacks ignore armour** (3e "touch AC").
- **The plus is the depth curve.** A +1 shield is common, a +5 one is a
  deep-dungeon find. AC stays inside about 10 to -10 while monster accuracy
  climbs with Hit Dice, so good armour matters at every level.

## 3. The item model: who decides what

| Part | Decides | No longer decides |
|---|---|---|
| **Template** (what it is: padded, chain, plate, buckler, tower, gauntlets...) | slot, weight class, base AC (body and shield only), base ward (minor slots), base weight | — |
| **Material** (what it is made of) | which wear can hit it: rust, acid, fire (the existing `_can_rust` / `_can_corrode` / `_can_scorch` rules), and its name | AC, tier, quiz tier, enchantment cap, resistances |
| **Enchantment** (its magic) | the tier (I-V), so the geography quiz tier and the equip threshold; the plus on body armour and shields; the one power on a minor piece | — |

So depth comes from the enchantment, exactly as AD&D's plus does, and the
floor only decides *which tier is likely to be found*; the magnitudes are
fixed per tier in data (LORE NOT FLOOR holds).

Rust, acid and fire keep working as now (`items.wear_down`): body armour and
shields lose a point of plus; a minor piece's enchantment drops one tier; a
smith's repair gives it back. Material decides whether the hazard can touch
the piece at all (iron rusts, leather burns, adamantine does neither).

## 4. Core AC: body armour and shield

```
AC = 10 - body armour (base + plus) - shield (base + plus)
        - DEX (cap 3) - one protection source (the best of a ring of
          protection and a cloak of Protection) - temporary effects
```

Base AC by template (heavier is better, so no template is dominated):

| Body | padded 1, leather 2, studded / hide 3, chain shirt / ringmail 3, scale 4, chainmail 5, breastplate 5, banded / splint 6, plate 7, full plate 8 |
|---|---|
| **Shield** | buckler 1, light 1, heavy wooden 2, kite 2, tower 3 |

**The plus is the enchantment tier**: +1 at tier I up to +5 at tier V (an
Enchant Armour scroll adds one, to +5 at most).

**The AC line checked against what will be found** (prepared hero, the
expected tier of section 5):

| Floor | What a prepared hero wears | AC | Target |
|---|---|---|---|
| 1 | leather 2, light shield 1, plain | 7 | 8 |
| 20 | chainmail 5 +1, kite 2 +1 | 1 | 2 |
| 50 | plate 7 +3, kite 2 +3, DEX 1 | -6 | -4 |
| 100 | full plate 8 +5, tower 3 +5, DEX 2 | -13 | -12 |

The best possible kit (plus a cloak of Protection V and DEX 3) reaches about
-17 at floor 100; an unarmoured hero is 10.

**Monster accuracy is rebaked to the line** (written into `monsters.json` by
`tools/balance/scale_monsters.py`): THAC0 = line AC + 10, so a typical monster
hits a prepared hero about 55% of the time at every depth, an under-armoured
one about 80%, a best-kit one about 30%. With AC bounded, the 30% floor drops
to the natural 20 for ordinary monsters (named foes keep a higher floor).

## 5. Enchantment tiers through the game

A found piece is plain or carries one enchantment of tier I-V. The tier is
drawn from bells by floor (peaks 6, 26, 46, 66, 86; spread about 11; a tier
cannot appear before floors 1 / 12 / 30 / 50 / 70). The plain share falls
from 40% on floor 1 to 15% by floor 100. Computed shares of found pieces:

| Floors | Plain | I | II | III | IV | V | Expected tier when enchanted |
|---|---|---|---|---|---|---|---|
| 1-10 | 39% | 61% | | | | | 1.0 |
| 11-20 | 36% | 32% | 32% | | | | 1.5 |
| 21-30 | 34% | 7% | 58% | 2% | | | 1.9 |
| 31-40 | 31% | | 35% | 33% | | | 2.5 |
| 41-50 | 29% | | 13% | 57% | 2% | | 2.9 |
| 51-60 | 26% | | 2% | 37% | 35% | | 3.5 |
| 61-70 | 24% | | | 14% | 60% | 2% | 3.8 |
| 71-80 | 21% | | | 2% | 40% | 37% | 4.5 |
| 81-90 | 19% | | | | 15% | 66% | 4.8 |
| 91-100 | 16% | | | | 4% | 80% | 5.0 |

(A 60% plain share was tried first: it left under one enchanted piece per slot
per 10 floors before floor 30; see section 8.)

Every band has a new tier arriving and an old one leaving, so there is an
upgrade every few floors, never a 37-floor plateau.

## 6. Equip cost follows power

The geography quiz tier is the enchantment tier (a plain piece: tier 1). The
number of questions:

| Tier | plain / I | II | III | IV | V |
|---|---|---|---|---|---|
| Body or shield, light | 1 | 1 | 2 | 2 | 3 |
| Body or shield, medium | 2 | 2 | 3 | 3 | 4 |
| Body or shield, heavy | 3 | 3 | 4 | 4 | 5 |
| Minor slot | 1 | 1 | 2 | 2 | 3 |
| (heavy minor template, stronger ward) | +1 | +1 | +1 | +1 | +1 |
| (a named unique) | +1 | +1 | +1 | +1 | +1 |

What suiting up costs (body, shield and the seven minor slots; cloak and shirt
have no heavy templates; today it is 13 at every depth):

| Floors (expected tier) | Light kit | Heavy kit |
|---|---|---|
| 1-10 (I) | 9 | 18 |
| 41-50 (III) | 18 | 27 |
| 91-100 (V) | 27 | 36 |

That matches the accessories, the one family that already works (their
tier 1 asks 2, tier 5 asks 3-5).

## 7. The minor slots: a ward each, and a stable of enchantments

### 7.1 Base ward (every piece, from its template)

Each minor slot guards against particular attack deliveries, already present
in the monster data (1,153 attacks; a `delivery` field is written onto each by
a tool from its name, `ranged` flag and damage type, checked by hand):

| Slot | Guards against | Share of monster attacks | Riders it shrugs off |
|---|---|---|---|
| Head | voice and mind (wail, mind blast, charm, hex), gaze | 7% | confused, feared, stunned, sleeping, hallucinating |
| Hands | touch (draining, death, rotting touch, pseudopod, engulf), grapple | 10% | paralyzed, weakened |
| Arms | ranged (bolts, rays, shards, hurled things) | 8% | blinded, stunned |
| Legs | bites, stings, tail strikes | 15% | poisoned, bleeding |
| Feet | trample and charge; traps and footing | 2% + hazards | slowed, immobilized |
| Cloak | breath and spray; elements washing over you | 5% + elements | burning, frozen |
| Shirt | what gets under the armour | any | diseased, poisoned, bleeding (weaker) |

Base strength by weight class (fixed, no depth): light 10% / medium 20% /
heavy 30% chance to shrug off a listed rider from a matching attack, and
5 / 10 / 15% of its damage turned aside. A **touch** attack rolls against AC
without body armour and shield (3e "touch AC"); the gloves' ward is the
defence.

### 7.2 The stable: three lanes per slot, five tiers each

Every slot offers enchantments in three lanes, so a slot is always a choice
between keeping something out, helping with that slot's work, and doing more:

- **Guard**: a stronger ward against one named threat.
- **Craft**: help with the quiz the slot's work belongs to. (Only combat
  maths is timed, so craft for the untimed subjects is forgiveness and an
  easier quiz, never a struck-out choice: gold and magic buy a second chance,
  never the answer.)
- **Might / Way**: damage, technique, movement, senses.

**Standard ladders** (tier I -> V), shared so the stable stays comparable:

| Ladder | I | II | III | IV | V |
|---|---|---|---|---|---|
| Rider guard: chance to shrug off its riders | 20% | 35% | 50% | 65% | 80% (immune at V for one narrow rider) |
| Damage guard: share of matching damage turned aside | 10% | 18% | 26% | 34% | 42% |
| Element guard (cloak, one element, every source) | 10% | 20% | 30% | 40% | 50% |
| Craft (one subject) | first wrong answer forgiven once a floor | once a quiz | and quiz tier -1 | and one question fewer (at least 1) | and quiz tier -2 (at least 1) |
| Combat clock (maths) | +2 s | +4 s | +6 s | +8 s | +10 s |
| Might: your blows' damage | +4% | +8% | +12% | +16% | +20% |
| Rider on your blow | 10% | 17% | 24% | 31% | 38% |

**Head (helm, hood, crown)**
- Guard: *Iron Will* (fear and charm; immune to fear at V); *Clear Mind*
  (confusion and hallucination); *Steady* (stun and sleep); *Unblinking*
  (gaze: paralysis and blinding from a stare); *Mindshield* (psionic and magic
  damage).
- Craft: *the Scholar* (philosophy: identify); *the Reader* (grammar: scrolls
  and spellbooks); *the Adept* (science: casting).
- Way: *Night Eyes* (sight in dark rooms, +1 to +3; III+ sees through magical
  dark); *Alertness* (warned of unseen things coming, radius 2 to 6).

**Hands (gloves, gauntlets)**
- Guard: *Grounding* (paralysis by touch or grapple); *Life-Grip* (draining
  and necrotic touch damage; weakness); *Iron Grip* (constriction and engulf
  damage, and breaking free); *Sure Hands* (thieves' stealing).
- Craft: *the Locksmith* (economics: lockpicking); *the Cook* (cooking);
  *the Hunter* (animal: harvesting).
- Might: *Striking* (your blows' damage); *Venom* (your blows poison);
  *Spellfire* (your touch spells, +damage on the might ladder).

**Arms (bracers, vambraces)**
- Guard: *Deflection* (ranged damage); *Shatterproof* (blinding and stun from
  missiles).
- Craft: *Swift Strokes* (combat clock).
- Might / Way: *Parrying* (a melee blow that lands is parried: 6 / 10 / 14 /
  18 / 22%); *Archery* (ranged damage); *Mighty Throw* (throw range and
  damage); *Defense* (AC +1 to +5, only with no body armour: the caster's
  path).

**Legs (greaves, leggings)**
- Guard: *Snakeskin* (poison from bites and stings); *Mailed Shins* (bite,
  sting and tail damage); *Clotting* (bleeding).
- Craft: *the Kneeler* (theology: prayer, the theology quiz eased).
- Way: *Endurance* (max SP +5 / 10 / 15 / 20 / 25%); *Springing* (leap 2 to 4
  tiles, once a fight); *Sure-Footed* (knockback and trips); *Wading* (water
  costs no speed).

**Feet (boots, sandals)**
- Guard: *Steadfast* (trample and charge damage, knockback); *Free Stride*
  (slowing and immobilizing riders); *Trapwise* (trap damage and the chance to
  avoid one); *Firewalker* (burning ground and lava).
- Craft: *the Wanderer* (geography: putting armour on).
- Way: *Elvenkind* (sleepers stir less, `sleepers.py`: -20 to -80%);
  *Fleet* (one free step away from a foe each fight); *Water Walking*
  (tier IV-V only).

**Cloak**
- Guard: *Flameward*, *Frostward*, *Stormward*, *Acidward* (one element each,
  every source, and its rider); *Vapourward* (breath and spray of any kind).
- Way: *Protection* (AC +1 / +1 / +2 / +2 / +3: the protection source; it
  takes the cloak's one enchantment, so it is a choice against an element);
  *Shrouding* (monsters notice you later: their awareness range -1 to -3);
  *Night-Cloak* (unseen in dark rooms until adjacent, III+).

**Shirt**
- Guard: *Clean Linen* (disease); *Padding* (bleeding and the stun of a
  heavy blow); *Warmth* (cold damage); *Vigil* (magical sleep).
- Craft: *the Hair Shirt* (theology: prayer cooldown -10 to -30%).

**Body armour and shield properties** (tier III and up, in addition to the
plus; found only on those):
- Body: *Fortification* (stun and bleeding from blows); *Thorns* (a melee
  attacker takes damage); *Featherweight* (weight halved); *Hush* (no noise:
  sleepers).
- Shield: *Reflection* (a bolt or ray turned back, 10 to 30%); *Bulwark*
  (trample and knockback); *Bash* (a blocked blow stuns the attacker);
  *Spellward* (magic damage).

That is **64 enchantments**, 5 tiers each: 56 on the minor slots (head 10,
hands 10, arms 7, legs 8, feet 8, cloak 8, shirt 5; every slot has at least
two guards and something outside the guard lane) and 8 body and shield
properties.

### 7.3 Rules that keep the stable honest
- **One home per power.** Rings and amulets keep statuses and stat raises
  (searching, regeneration, haste, telepathy, displacement, levitation, the
  resist statuses, +WIS / CON / INT / STR / PER / DEX). No armour enchantment
  copies one; the stable above is wards, quiz craft, technique and senses,
  which no accessory grants. (Ruling 4 covers the famous AD&D names that would
  overlap: boots of speed, gauntlets of ogre power, helm of telepathy, cloak
  of displacement.)
- **Magnitudes are data**, `data/enchantments.json` (id, slot, lane, the five
  tier values, what it hooks, its name). The floor never scales them.
- **Hidden until identified** (philosophy), like any property; a known
  enchantment shows in the name ("Iron Helm of Iron Will III").
- **Cursed** pieces keep their enchantment, are welded, and work one tier
  lower until uncursed.
- **Blessed** minor pieces work one tier higher (cap V); blessed body armour
  and shields keep +1 AC. (`altar.blessing_helps` stays true for all of them.)

## 8. Balance and distribution checks (built with the plan, held by tests)

**Value per tier.** A tool, `tools/balance/enchant_audit.py`, prices every
enchantment at every tier on the floors that tier is found, from the game's own
data:
- a guard: the share of the damage taken (or the rider turns suffered) it
  removes, using the monsters, their attacks, deliveries, riders and spawn
  weights on those floors;
- might: the share of the hero's damage it adds (against `ONE_ATTACK`);
- craft: the questions saved per floor on its subject (from how many
  lockpicks, cooks, identifies, reads and prayers a floor holds);
- a way: judged by hand, then placed on the same scale.

Lanes are compared by one exchange rate (ruling 5; default: 1% of damage
taken = 1% of damage dealt = 0.1 questions saved a floor). The test: inside a
slot, every enchantment's tier-N value is within 35% of that slot's tier-N
median, and every ladder rises with tier. A guard against something that is
rare at its depth (trample is 2% of attacks) gets a steeper ladder until it is
worth taking.

**Enough to choose from.** A run finds about 1.1 armour pieces per slot on
floors 1-10, 1.7 on 11-20 and 2.3-3.4 per 10 floors after that (census, 5
runs, floors 1-100). Enchanted options per minor slot per 10 floors:

| Floors | 1-10 | 11-20 | 21-30 | 31-40 | 41-50 | 61-70 | 91-100 |
|---|---|---|---|---|---|---|---|
| Today's loot roll | 0.7 | 1.1 | 1.5 | 1.7 | 2.3 | 2.6 | 2.4 |
| With 45 / 35 / 15 | 1.2 | 1.9 | 2.7 | 3.0 | 3.9 | 4.5 | 4.1 |

Target: at least 1 on floors 1-10, 2 on 11-30, 3 from floor 31. To get
there: the room gear roll moves from 60% weapon / 20% armour / 15% shield to
45 / 35 / 15, chests lean to armour the same way, and traders stock enchanted
minor pieces (which closes the small gap on floors 11-20). The census grows a
per-slot, per-tier count, and a test pins the target per band.

**The AC line.** The census reports worn AC per floor; a test holds it within
2 of the line in section 4 at floors 10, 30, 50, 70 and 100, and the hit
chance against a prepared hero within 45-65%.

## 9. Build order (each phase ends playable)

1. **Rulings** (section 10).
2. **Item model and core AC**: template / material / enchantment split; body
   and shield base AC and plus; thresholds and quiz tier from the
   enchantment; shield thresholds; monster accuracy rebake; the hit floor.
   Minor slots keep a small temporary AC until phase 3, so no build ships
   naked.
3. **Wards**: `delivery` on every attack; base wards; the touch rule; minor
   AC removed in the same commit.
4. **The enchantment engine**: data, tier bells, plain share, roll, naming,
   identification, cursed and blessed, wear and repair, equip cost.
5. **The stable**, lane by lane (guard, then craft, then might and way), each
   with its hook and a test.
6. **Body and shield properties**.
7. **Uniques**: the 56 minor-slot uniques and every body and shield unique,
   placed on the tier ladder with their signature powers kept.
8. **Distribution and balance**: the gear roll, chests, traders; the
   enchantment audit and the census tests; tuning.
9. **Saves, text sweep, docs**: saved pieces recomposed on load (the armour
   recompose in `main.py` about line 1464 is the pattern); Kit and character
   sheet show plus, ward and enchantment; help, hints, docs.

Play-test points: after 2 (AC on floors 1-20), after 3 (is a helm worth
wearing against a wailing spirit?), after 5 (are the choices real?).

This is a 3.4 release (combat at every depth, saves), on its own branch once
3.3.2 ships, built one phase a session.

## 10. Rulings needed

1. **Material only for wear**: it decides rust, acid and fire and the name.
   Does it keep **weight** too (mithril light, adamantine heavy), or does
   weight come from the template alone?
2. **The tier curve and plain share** of section 5: right pace?
3. **The equip cost** of section 6: suiting up goes from 9-18 questions on
   floor 1 to 27-36 on floor 100 (today 13 everywhere). Right scale?
4. **The famous overlaps**: keep armour and accessories apart (no boots of
   speed, no helm of telepathy), or move those powers from rings to their
   slot (a data change on some of the 168 accessories)?
5. **The exchange rate** between lanes (section 8): the default, or another?
6. **More armour in the loot** (45 / 35 / 15) so every slot has choices:
   yes?
7. Carried over from revision 1: the hit floor down to the natural 20 for
   ordinary monsters; the AC line ending about -12 at floor 100; 3.4.0 on its
   own branch.
